# Customer Sales Agent — Example App

**Date:** 2026-07-02 · **POC:** AdaL Cloud examples

## TL;DR

An **impressive, real-looking company website** ("Lumen Audio", a premium
headphone & speaker boutique) with a **floating chat button in the bottom-right
corner** — exactly like a real production site's support/sales widget. Clicking
it opens a chat window where **Lumen**, an AI sales concierge, helps visitors
find and buy products. Every factual step (catalog search, stock check, price
quote with live discounts, lead capture) runs through **custom tools**, and the
widget renders each as a **live tool card** — so the audience literally sees the
agent *doing commerce*, not just chatting.

This is the flagship end-to-end example of building a customized agent on
**AdaL Cloud**, fronted by a tiny **backend-for-frontend (BFF) proxy** that holds
the AdaL Cloud credential server-side.

## Why a proxy (and not "just a static page")

AdaL Cloud's API requires a per-user Clerk **JWT** on every request
(`Authorization: Bearer <token>`). A public storefront must **never** embed that
token in client HTML — it would be world-readable. So the demo ships a minimal
**BFF proxy** (`proxy/server.py`, ~180 lines of FastAPI) that:

1. Holds the JWT **server-side** (from `ADAL_JWT` env or a gitignored
   `proxy/.adal_jwt` file).
2. **Auto-creates the agent** on startup from `agent/agent_config.json` (reusing
   it by name on restart) — no manual setup step.
3. Serves the static storefront (`site/`) and proxies the only two browser calls
   — `POST /api/session` and `POST /api/chat/{id}` — to AdaL Cloud, injecting the
   Bearer token and forwarding the SSE stream verbatim.

The browser talks **only** to this proxy's `/api/*`. It never sees the token, the
upstream base URL, or even the agent id. This is the same pattern you'd use to
keep any provider key (OpenAI, Stripe) out of client code.

## What this demonstrates

- Creating a **custom agent** (system prompt + custom Python tools) via the API.
- Instantiating a **session** and streaming a **turn** over SSE.
- Rendering rich streaming events (assistant text + **tool cards**) in a real UI.
- A production-safe **credential-proxy** pattern any company site can copy.

## Layout

```
customer_sales_agent/
  README.md              # this spec
  run_local.sh           # run the proxy locally (http://127.0.0.1:8500/)
  deploy_aws.sh          # build -> ECR -> App Runner (public HTTPS URL)
  agent/
    agent_config.json    # name + system_prompt + custom_tools (the /v1/agents body)
    tools.py             # the CUSTOM_TOOLS source (readable copy of what's embedded)
  proxy/
    server.py            # BFF: holds the JWT, auto-creates the agent, proxies /api/*
    Dockerfile           # container image (bundles proxy + site + agent)
    requirements.txt     # fastapi, uvicorn, httpx
    .gitignore           # ignores .adal_jwt (never commit the token)
    .adal_jwt            # (you create this) the Clerk JWT — gitignored
  site/
    index.html           # the Lumen Audio storefront + floating chat widget
    about/careers/contact/legal.html, 404.html
    assets/              # photorealistic product/lifestyle images (nano-banana-2)
    robots.txt, sitemap.xml, site.webmanifest
```

The storefront (`site/index.html`) goes well beyond a demo harness: a full
shopping funnel (product grid → quick-view PDP with image gallery → add to
cart → slide-out cart drawer → checkout that hands the cart to the concierge
for a live quote), plus a comparison table, reviews, Journal/blog, FAQ,
guarantee strip, newsletter, cookie consent, proactive chat nudge,
back-to-top, and full SEO/a11y/PWA layers (JSON-LD, OG/Twitter meta, skip
link, focus states). No blocking `alert()` dialogs anywhere.

## Running it locally

```bash
cd customized_agent_platform/examples/customer_sales_agent

# Provide the AdaL Cloud JWT one of two ways (never commit it):
export ADAL_JWT="eyJ..."          # env var, OR
echo "eyJ..." > proxy/.adal_jwt   # gitignored file

./run_local.sh                    # serves http://127.0.0.1:8500/
```

Open `http://127.0.0.1:8500/`, click the chat button, and talk to Lumen.

## Deploying to AWS

`deploy_aws.sh` builds the proxy image, pushes it to ECR, and creates/updates an
**App Runner** service with a public HTTPS URL. The JWT is passed as a runtime
env var (never baked into the image):

```bash
cd customized_agent_platform/examples/customer_sales_agent
ADAL_JWT="eyJ..." ./deploy_aws.sh          # prints the live https:// URL
```

Env knobs (all optional):

| Var | Default | Meaning |
|---|---|---|
| `ADAL_JWT` | — (required) | Clerk session JWT the demo runs under. |
| `ADAL_BASE_URL` | the deployed ALB URL | Upstream AdaL Cloud API base (point at `http://localhost:8080` for a local platform). |
| `ADAL_MODEL` | `google-gemini-3-flash-preview` | Per-session model. |
| `PORT` / `HOST` | `8500` / `127.0.0.1` | Where the proxy listens. |

### Widget behavior

- **First open** lazily creates a session (`POST /api/session`) and greets the
  user; subsequent opens reuse the same session id (kept in `sessionStorage`).
- **Sending a message** streams the response via `POST /api/chat/{id}` (SSE),
  rendering assistant text as it arrives and **each tool call as a live card**:
  `tool.started` shows the tool name + argument chips with a spinner, and
  `tool.completed` flips it to ✓ done with a formatted result (quote
  totals/savings, stock status, search hits).
- **Auto-provision**: the first turn auto-provisions the worker (shows a
  connecting state), so no explicit provision/poll is needed.
- Graceful states: connecting, streaming, session-reaped retry, error.

## The agent

**Name:** `Lumen Sales Concierge`

**System prompt (summary):** Lumen, senior sales concierge for a premium audio
boutique. Consultative, warm, never pushy. MUST use tools for all facts (never
invent prices/stock/SKUs/discounts). Ask 1–2 clarifying questions (budget, use
case), recommend at most 2–3 curated products, always `build_quote` before
quoting a price and state the savings, be honest about stock and suggest
in-stock alternatives, and `capture_lead` when the customer shows buying intent.

**Custom tools (`CUSTOM_TOOLS`):**

| Tool | Purpose |
|---|---|
| `search_products(use_case, max_price)` | Find catalog items by use case (travel/studio/gym/home/anc/budget) + budget. |
| `check_stock(sku)` | Live availability for a SKU. |
| `build_quote(skus, loyalty_member)` | Price a cart: 10% bundle discount for 2+ items, +5% for loyalty. Returns line items, discounts, total, savings. |
| `capture_lead(name, email, interested_sku)` | Reserve the item + save contact for follow-up. Call on buying intent. |

**Design choice — deterministic, self-contained tools:** the catalog is an
in-memory dict and pricing is pure logic, so every tool call succeeds live (no
external API to fail mid-demo). Discounts live in `build_quote`, not the prompt,
so the agent physically cannot hallucinate a price — every number on screen came
from a tool result. Swap `_CATALOG` for a real HTTP call later if desired.

## Demo script (shows every tool)

1. Visitor: *"I travel a lot and want great noise cancellation under $400."*
   → `search_products("travel", 400)` → recommends **Lumen One (LX-100)**.
2. *"Is it in stock? What if I add the Mini speaker?"*
   → `check_stock("LX-100")` + `build_quote(["LX-100","SP-Mini"])` → shows the
   **10% bundle discount** live.
3. *"I'll take it — I'm a loyalty member."*
   → `build_quote(..., loyalty_member=True)` → extra **5%** applied.
4. *"Email me the checkout link — jane@example.com."*
   → `capture_lead("Jane", "jane@example.com", "LX-100")` → reserved + next steps.

Each step renders as a tool card in the widget — the "wow": the agent visibly
*doing commerce*, not just chatting.

## Future work

- Persist conversation across page reloads (session id already in sessionStorage).
- Swap the in-memory catalog for a live inventory endpoint.
- A scoped, publishable **embed token** (narrow session-create + chat scope) so a
  pure static page can call AdaL Cloud directly without the BFF proxy.
