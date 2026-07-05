# Class 2: Building Custom Agents with AdaL Cloud
## From Coding Agent to Agent Platform

![AdaL Logo](assets/adal-logo-horizontal.svg)

**AdaL Bootcamp 2 · Class 2 · taught by Zach Wilson · by Li Yin**

---

## Slide 1: The Vision

AdaL isn't just a coding agent — it's an agent you can **customize and deploy**.

- **Custom system prompt** = your agent's brain (persona, rules, domain context)
- **Custom tools** = your agent's hands (Python functions it can call)
- **Cloud platform** = your agent's home (create, manage, stream chat over HTTP)

You define what the agent knows and what it can do. AdaL handles the rest.

---

## Slide 2: Three Layers

| Layer | What it is | Link |
|-------|-----------|------|
| **Cloud Platform** | Create agents, manage sessions, stream chat over HTTP | [cloud.adal.sylph.ai](https://cloud.adal.sylph.ai/) |
| **SDK** | Embed AdaL in your Python app — async, permission callbacks | [github.com/SylphAI-Inc/adal-sdk](https://github.com/SylphAI-Inc/adal-sdk) |
| **Custom Prompts + Tools** | Define your agent's persona and capabilities | [docs.sylph.ai](https://docs.sylph.ai) |

---

## Slide 3: Authentication

| Method | How it works |
|--------|-------------|
| **CLI** | First run opens browser for auth (Google/email). Cached at `~/.adal/adal_oauth_creds.json`. |
| **SDK (cached)** | Run `adal` once → SDK picks up credentials automatically. `AdalAgentOptions(workspace=".")` |
| **SDK (explicit)** | Pass `auth_token` (JWT) for headless/CI. Extract: `cat ~/.adal/adal_oauth_creds.json \| python3 -c "import json,sys; print(json.load(sys.stdin)['access_token'])"` |
| **Cloud** | Sign in at cloud.adal.sylph.ai with Google or email. |

---

## Slide 4: Custom System Prompt

By default, AdaL is a **coding agent**. Two ways to give it your own persona:

| Method | How it works |
|--------|-------------|
| `AGENTS.md` | Auto-loaded every turn from workspace root. Shared team context committed to the repo. |
| `--prompt-file` | Replaces the default role prompt entirely. Per-script persona overrides. |

```bash
# Use a custom persona
adal --prompt-file prompts/security-auditor.md
```

Link: [docs.sylph.ai/features/custom-system-prompt](https://docs.sylph.ai/features/custom-system-prompt)

---

## Slide 5: Custom Tools — Part 1: Choose From Built-in Tools

AdaL ships with a full toolset. You control which tools the agent can see and use:

| Flag | What it does |
|------|-------------|
| `--enabled-default-tools` | Choose which built-in tools the agent can see and use |
| `--disabled-default-tools` | Strip built-in tools entirely — invisible + unexecutable |

Tool groups: `Bash`, `Edit`, `Read`, `Search`, `Web`, `Image`, `Video`, `Consult`

```bash
# Agent can only read and search — no edits, no bash
adal --disabled-default-tools "Bash,Edit,Image,Video"
```

> Full tool-choice documentation: [docs.sylph.ai/features/built-in-tools](https://docs.sylph.ai/features/built-in-tools)

---

## Slide 6: Custom Tools — Part 2: Add Your Own

Place `tools.py` in `.adal/` — the runtime auto-loads it.

```python
from adalflow.core.types import ToolOutput

def get_catalog(category: str) -> ToolOutput:
    """Get products in a category.
    Args:
        category: Product category to filter by.
    """
    products = query_db(category)
    return ToolOutput(
        output=products,
        observation=f"Found {len(products)} items",
        display=f"📦 {len(products)} products",
        status="success",
    )

CUSTOM_TOOLS = [get_catalog]
```

### Approval control

Use the dict form to override name, description, or approval per tool:

```python
CUSTOM_TOOLS = [
    {"function": safe_read_only_tool, "require_approval": False},
    dangerous_write_tool,  # keeps default require_approval=True
]
```

- Tool name = function name, description = docstring
- Type hints are extracted for the tool schema
- Async tools supported
- Approval flow built in (`require_approval=True` by default)

Link: [docs.sylph.ai/features/custom-tools](https://docs.sylph.ai/features/custom-tools)

---

## Slide 7: Live Demo — Customer Sales Agent

**"Lumen Sales Concierge"** — a premium audio storefront agent.

| Tool | What it does |
|------|-------------|
| `get_catalog` | Look up products by category |
| `build_quote` | Calculate bundle pricing and discounts |
| `capture_lead` | Save customer details for follow-up |

The agent uses these tools to provide real-time product availability, calculate discounts, and capture leads — all in natural conversation.

**Try it:** [ruf2xych2b.us-west-2.awsapprunner.com](https://ruf2xych2b.us-west-2.awsapprunner.com/)

---

## Slide 8: AdaL Cloud

Create and manage agents from the browser — no infrastructure needed.

1. **Create an agent** — name + custom system prompt + custom tools (Python)
2. **Start a session** — instant-on, pick your model
3. **Stream chat over HTTP** — use from your own apps
4. **Download full HTML API docs** — available in the cloud app

**Link:** [cloud.adal.sylph.ai](https://cloud.adal.sylph.ai/)

---

## Slide 9: SDK Quickstart

Embed AdaL in your Python app:

```bash
pip install git+https://github.com/SylphAI-Inc/adal-sdk.git
```

```python
import asyncio
from adal_agent_sdk import AdalAgentOptions, query

async def main():
    async for event in query(
        prompt="Summarize this codebase",
        options=AdalAgentOptions(
            enabled_default_tools=["Read", "Web"],
            # Auth: cached from CLI (recommended) or pass auth_token for CI
        ),
    ):
        print(event)

asyncio.run(main())
```

- Persistent client for multi-query sessions
- Permission callbacks (`can_use_tool`)
- Mid-session model switching
- Links: [github.com/SylphAI-Inc/adal-sdk](https://github.com/SylphAI-Inc/adal-sdk) · [docs.sylph.ai/sdk/quickstart](https://docs.sylph.ai/sdk/quickstart)

---

## Slide 10: Build Your Own — The Flow

1. **Define persona** → `AGENTS.md` + `--prompt-file`
2. **Choose tools** → `--enabled-default-tools` or `--disabled-default-tools`
3. **Add custom tools** → `.adal/tools.py` with `CUSTOM_TOOLS`
4. **Create agent on Cloud** → name + prompt + tools
5. **Start session** → stream chat via HTTP API
6. **Or embed via SDK** → `pip install adal-sdk` in your app

---

## Materials & Links

- **Cloud Platform:** [cloud.adal.sylph.ai](https://cloud.adal.sylph.ai/)
- **SDK:** [github.com/SylphAI-Inc/adal-sdk](https://github.com/SylphAI-Inc/adal-sdk)
- **SDK Docs:** [docs.sylph.ai/sdk/quickstart](https://docs.sylph.ai/sdk/quickstart)
- **Custom System Prompt:** [docs.sylph.ai/features/custom-system-prompt](https://docs.sylph.ai/features/custom-system-prompt)
- **Custom Tools:** [docs.sylph.ai/features/custom-tools](https://docs.sylph.ai/features/custom-tools)
- **Live Demo (Sales Agent):** [ruf2xych2b.us-west-2.awsapprunner.com](https://ruf2xych2b.us-west-2.awsapprunner.com/)
