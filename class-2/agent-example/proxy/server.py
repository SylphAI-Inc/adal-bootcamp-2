#!/usr/bin/env python3
"""Backend-for-frontend (BFF) proxy for the Lumen Audio demo.

Why this exists: the AdaL Cloud API requires a per-user Clerk JWT on every
request (Authorization: Bearer <token>). A public storefront widget must NEVER
embed that token in client HTML. This tiny server holds the token server-side
and does three things:

  1. On startup, ensures the Lumen agent exists (creates it from
     agent/agent_config.json if absent) — no manual setup step.
  2. Serves the static storefront (site/).
  3. Proxies the two browser-facing calls to AdaL Cloud, injecting the Bearer
     token: POST /api/session (create session) and POST /api/chat (stream turn).

The browser only ever talks to THIS proxy — it never sees the token, the
upstream base URL, or even the agent id.

Config (env vars; never commit the token):
  ADAL_JWT       (required) the Clerk session JWT to run the demo under.
                 Read from the env or from proxy/.adal_jwt (gitignored).
  ADAL_BASE_URL  (default: the AdaL Cloud deployment) upstream API base.
  ADAL_MODEL     (default: google-gemini-3-flash-preview) per-session model.
  PORT / HOST    (default: 8500 / 127.0.0.1) where this proxy listens.

Run:
  ./run.sh            # or: uvicorn server:app --port 8500
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path

import httpx
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("lumen-proxy")

_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent  # customer_sales_agent/
_SITE_DIR = _ROOT / "site"

# Upstream AdaL Cloud API base. Override with ADAL_BASE_URL for local/staging.
# Defaults to the custom domain (cloud.adal.sylph.ai), whose ALB cert matches,
# so TLS verifies properly. If you point ADAL_BASE_URL at the raw
# *.elb.amazonaws.com hostname instead, verification is auto-skipped (its cert
# CN won't match) — see _VERIFY_TLS below.
BASE_URL = os.environ.get(
    "ADAL_BASE_URL",
    "https://cloud.adal.sylph.ai",
).rstrip("/")
MODEL = os.environ.get("ADAL_MODEL", "google-gemini-3-flash-preview")
HOST = os.environ.get("HOST", "127.0.0.1")
PORT = int(os.environ.get("PORT", "8500"))
# Verify TLS only when hitting a properly-named host (custom domain). For the
# raw ALB hostname the cert CN won't match, so skip verification there.
_VERIFY_TLS = "elb.amazonaws.com" not in BASE_URL


def _load_token() -> str:
    """Load the Clerk JWT from ADAL_JWT env or proxy/.adal_jwt (gitignored).

    Never hardcoded, never committed — the file is in .gitignore.
    """
    token = os.environ.get("ADAL_JWT", "").strip()
    if not token:
        token_file = _HERE / ".adal_jwt"
        if token_file.exists():
            token = token_file.read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError(
            "No ADAL_JWT provided. Set the ADAL_JWT env var or write the token to "
            f"{token_file} (gitignored)."
        )
    return token


# Loaded once at import; the whole demo runs under this single identity.
_TOKEN = _load_token()


def _auth_headers() -> dict[str, str]:
    return {"Content-Type": "application/json", "Authorization": f"Bearer {_TOKEN}"}


async def _ensure_agent() -> str:
    """Create the Lumen agent if it doesn't already exist; return its id.

    Idempotent-ish: matches an existing agent by name so repeated boots reuse it
    instead of piling up duplicates.
    """
    import sys
    sys.path.insert(0, str(_ROOT / "agent"))
    from agent import agent_config as _agent_config_fn
    config = _agent_config_fn()
    name = config["name"]
    async with httpx.AsyncClient(timeout=30.0, verify=_VERIFY_TLS, follow_redirects=True) as client:
        # Reuse an existing agent with the same name if present.
        resp = await client.get(f"{BASE_URL}/v1/agents", headers=_auth_headers())
        resp.raise_for_status()
        for agent in resp.json():
            if agent.get("name") == name:
                logger.info("Reusing existing agent %s (%s)", name, agent["id"])
                return agent["id"]
        # Otherwise create it.
        resp = await client.post(
            f"{BASE_URL}/v1/agents", headers=_auth_headers(), json=config
        )
        resp.raise_for_status()
        agent_id = resp.json()["id"]
        logger.info("Created agent %s (%s)", name, agent_id)
        return agent_id


app = FastAPI(title="Lumen Demo BFF Proxy")

# Cached at startup so every browser session reuses the same agent template.
_AGENT_ID: str = ""


@app.on_event("startup")
async def _startup() -> None:
    global _AGENT_ID
    _AGENT_ID = await _ensure_agent()
    logger.info("Lumen proxy ready — upstream=%s model=%s agent=%s", BASE_URL, MODEL, _AGENT_ID)


async def _provision_in_background(session_id: str) -> None:
    """Fire-and-forget: provision the session worker after creation.

    Mirrors what the dashboard's provisionWorker() does — pays the cold-start
    cost up front so the user's first message is instant instead of waiting
    ~30-60s for the worker to spin up mid-stream.
    """
    try:
        async with httpx.AsyncClient(
            timeout=180.0, verify=_VERIFY_TLS, follow_redirects=True
        ) as client:
            resp = await client.post(
                f"{BASE_URL}/v1/sessions/{session_id}/provision",
                headers=_auth_headers(),
            )
            if resp.status_code < 400:
                logger.info("provision[%s] worker ready", session_id)
            else:
                logger.warning("provision[%s] failed: %s %s", session_id, resp.status_code, resp.text[:200])
    except Exception as exc:
        logger.warning("provision[%s] error: %s", session_id, exc)


@app.post("/api/session")
async def create_session() -> dict:
    """Create a chat session and pre-warm its worker in the background.

    Returns the session_id immediately; provisioning runs concurrently so the
    worker is ready (or nearly so) by the time the visitor sends their first
    message — no cold-start wait mid-stream.
    """
    async with httpx.AsyncClient(timeout=30.0, verify=_VERIFY_TLS, follow_redirects=True) as client:
        resp = await client.post(
            f"{BASE_URL}/v1/sessions",
            headers=_auth_headers(),
            json={"agent_config_id": _AGENT_ID, "title": "Website visitor", "model": MODEL},
        )
    if resp.status_code >= 400:
        raise HTTPException(status_code=resp.status_code, detail=resp.text)
    session_id = resp.json()["id"]
    # Kick off provisioning in the background — don't block the response.
    import asyncio
    asyncio.create_task(_provision_in_background(session_id))
    # Only surface the session id to the browser — nothing sensitive.
    return {"session_id": session_id}


@app.post("/api/chat/{session_id}")
async def chat_stream(session_id: str, request: Request) -> StreamingResponse:
    """Proxy one streamed chat turn, forwarding the upstream SSE verbatim."""
    payload = await request.json()
    message = payload.get("message", "")

    async def event_source():
        async with httpx.AsyncClient(timeout=180.0, verify=_VERIFY_TLS, follow_redirects=True) as client:
            async with client.stream(
                "POST",
                f"{BASE_URL}/v1/sessions/{session_id}/chat/stream",
                headers=_auth_headers(),
                json={"message": message},
            ) as upstream:
                if upstream.status_code >= 400:
                    body = await upstream.aread()
                    # Surface a 404 (reaped/unknown session) so the widget can reset.
                    yield f"event: error\ndata: {json.dumps({'status': upstream.status_code, 'error': body.decode('utf-8', 'replace')})}\n\n"
                    return
                async for chunk in upstream.aiter_raw():
                    if chunk:
                        yield chunk

    return StreamingResponse(event_source(), media_type="text/event-stream")


# Serve the static storefront at the root. Mounted last so /api/* wins.
app.mount("/", StaticFiles(directory=str(_SITE_DIR), html=True), name="site")


@app.exception_handler(404)
async def _spa_404(_request: Request, _exc):
    # Serve the branded 404 page for unknown static paths.
    not_found = _SITE_DIR / "404.html"
    if not_found.exists():
        return FileResponse(str(not_found), status_code=404)
    return HTTPException(status_code=404)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=HOST, port=PORT)
