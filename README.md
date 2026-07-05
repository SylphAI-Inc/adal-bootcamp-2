# AdaL Bootcamp 2

Learn to build with [AdaL](https://docs.sylph.ai) — the agent that engineers loops. From vibe coding to vertical agent SaaS.

## Classes

| Class | Topic | Slides |
|-------|-------|--------|
| **Class 1 — Beyond Loop Engineering** | Vibe coding → loop engineering → AdaL's full offering → vertical agent SaaS | [HTML](slides/class-1-beyond-loop-engineering.html) · [MD](slides/class-1-beyond-loop-engineering.md) |
| **Class 1 — AdaL Setup** | Install, launch (engineer vs worker), model recommendations | [HTML](slides/class-1-adal-setup.html) |
| **Class 2 — Building Custom Agents** | Custom prompts, custom tools, AdaL Cloud, SDK, live demo | [HTML](slides/class-2-custom-agents.html) · [MD](slides/class-2-custom-agents.md) |

Open any slide deck in your browser:

```bash
open slides/class-1-beyond-loop-engineering.html
```

## Note: AdaL Engineer Cloned the Landing Page Autonomously

The AdaL Engineer agent autonomously cloned a landing page end-to-end — research, design extraction, implementation, and visual verification — all driven by the loop-engineering workflow taught in Class 1.

![AdaL Engineer cloned the landing page autonomously](slides/assets/screenshots/adal-engineer-clone.png)

The prompt we used for this:

```
Clone the hero section of the landing page, https://www.hyperspell.com/ , put it inside of hyperspell-clone, needs to be exactly the same, from animation, content, font, color, styling, everything, pixel level, and video level including all effects 

You have the two docs to refer to:


1. clone_guide_v2.md (operational guide + appendices) — the one you follow
2. clone_landing_page_101.md (deep reference) — the one you consult when stuck


Use MiniMax M3 Browser Use for both evaluator and builder 
```

> The screenshot shows the agent's autonomous cloning workflow in action.

## Key Resources

- **AdaL Docs:** [docs.sylph.ai](https://docs.sylph.ai)
- **AdaL Cloud:** [cloud.adal.sylph.ai](https://cloud.adal.sylph.ai/)
- **SDK:** [github.com/SylphAI-Inc/adal-sdk](https://github.com/SylphAI-Inc/adal-sdk)
- **YC Agent Landscape:** [adalagent.ai/research/yc-landscape/](https://adalagent.ai/research/yc-landscape/)

## Structure

```
slides/
├── class-1-beyond-loop-engineering.html   # 12-slide deck
├── class-1-beyond-loop-engineering.md     # markdown source
├── class-1-adal-setup.html                # 5-slide setup deck
├── class-2-custom-agents.html             # 10-slide deck
├── class-2-custom-agents.md               # markdown source
└── assets/
    ├── adal-logo-horizontal.svg           # pink AdaL wordmark
    ├── adal-logo.svg                      # pink "A" icon
    ├── adal-architecture.svg              # engineer mode + workers diagram
    ├── bottleneck-shift.svg               # Karpathy Rule IX visual
    └── screenshots/
        └── adal-engineer-clone.png        # autonomous clone demo
docs/
└── clone-web/                             # clone reference docs
```

## Author

**Li Yin** — [github.com/liyin2015](https://github.com/liyin2015)

## License

MIT
