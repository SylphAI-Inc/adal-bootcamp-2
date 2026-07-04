# Class 1: Beyond Loop Engineering
## From Vibe Coding to Vertical Agent SaaS

![AdaL Logo](assets/adal-logo-horizontal.svg)

**AdaL Bootcamp 2 · Class 1 · July 4, 2026**

---

## Slide 1: Vibe Coding (Feb 2025)

> "There's a new kind of coding I call 'vibe coding', where you fully give in to the vibes, embrace exponentials, and forget that the code even exists."
> — Andrej Karpathy, Feb 3, 2025

- Describe what you want → AI writes the code → accept by vibe
- The limit: a prompt is typed once and forgotten. The real leverage became the **procedure**

**Three eras of software (Karpathy):**
| Era | "Code" is | When |
|-----|-----------|------|
| Software 1.0 | Handwritten instructions | Since forever |
| Software 2.0 | Neural network weights | 2017 essay |
| Software 3.0 | Prompts in natural language | June 2025 keynote |

Source: [YC — "Software Is Changing (Again)"](https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again)

---

## Slide 2: Anthropic's Pivot (mid-2025)

> "After a few years of prompt engineering being the focus… a new term has come to prominence: context engineering."
> — Anthropic

- Prompt = writing good instructions (static)
- Context = curating the **entire token set** the model sees each turn
- Context is a finite resource — "context rot" sets in

Three techniques: compaction, structured note-taking on disk, sub-agent architectures.

Source: [Anthropic — "Effective Context Engineering"](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)

---

## Slide 3: Loop Engineering (June 2026)

> "Loop engineering is replacing yourself as the person who prompts the agent. You design the system that does it instead."
> — Addy Osmani, Google Cloud, June 7, 2026

> "I don't prompt Claude anymore. I have loops running that prompt Claude. My job is to write loops."
> — Boris Cherny, head of Claude Code (Anthropic)

| Vibe coding | Loop engineering |
|-------------|------------------|
| You type a prompt | You design a procedure |
| You read the output | The loop reads and verifies |
| You decide when done | A separate evaluator checks |
| Runs while you watch | Runs while you sleep |

Source: [Osmani — "Loop Engineering"](https://addyosmani.com/blog/loop-engineering/)

---

## Slide 4: The Reality — Loop Engineering Today

Loop engineering works — but only for the **1%** who can build their own harness.

**What's painful:**
1. **Hand-crafted harness** — hooks, TOML, skills, cron. "Tedious and of questionable value."
2. **Specs are the bottleneck** — "By the time I finish the spec, the agent is waiting."
3. **Slop accumulates** — local pressure selects for short-term survivability over long-term intelligibility
4. **Token costs multiply** — "A money glitch for AI companies"
5. **Trust hasn't been solved** — transcript-only evaluation can't independently verify
6. **Doesn't work for greenfield** — loops need mature codebases with patterns and tests

Sources: [HN — The Coming Loop](https://news.ycombinator.com/item?id=48643180), [Reddit — loop engineering === psyop](https://www.reddit.com/r/ClaudeCode/comments/1ugy7w4/loop_engineering_psyop/)

---

## Slide 5: LOOPS.md — The Design Doc Behind AdaL

> "Most agent systems die not from a weak model but from a weak harness."
> — Andrej Karpathy, LOOPS.md v060726 (June 7, 2026)

Nine rules AdaL is engineered against: write the loop not the prompt · separate the roles · negotiate the contract first · write to disk not context · let the loop restart · score the subjective · read the traces · delete the harness · the bottleneck always moves.

---

## Slide 6: AdaL Changes This

From "build-your-own-harness" to **"just describe what you want."**

![AdaL Architecture](assets/adal-architecture.svg)

- No hook wiring — role separation, contracts, disk state built in
- No TOML — sub-agents, skills, model selection handled automatically
- No hand-crafting — you don't build the harness, you drive it

**Cost-effective loop engineering — you can't burn tier-1 model tokens in a loop.**

---

## Slide 7: Beyond Loop Engineering — AdaL's Full Offering

### [1] Coding Agent
- **Deep research** — sub-agent researches the domain
- **Coding** — implements, tests, surgical edits
- **Browser use** — designs & debugs UIs
- **Engineer mode** — hides complexity, adapts to your tastes

### [2] Agent Solution
- **Agent SDK** — build & deploy agents in your app
- **Agent cloud** — spin up instantly, no servers

Build with it. Then power it.

---

## Slide 8: Vertical Agent SaaS

| Traditional | AdaL |
|-------------|------|
| Research domain yourself (weeks) | Deep-research worker (hours) |
| Dev team builds it (months) | Drive AdaL (days) |
| Hire a designer | Browser-use agent designs |
| Wire infra from scratch | Agent SDK + cloud, instant |
| Maintain harness yourself | Engineer mode handles it |

The next wave of SaaS is vertical agent products. **AdaL is both the builder and the engine.**

**Scope ideation:** [YC Agent Landscape 2024–2026 →](https://adalagent.ai/research/yc-landscape/)

---

## Slide 9: The Ecosystem

| Tool | Introduced | You still build |
|------|------------|-----------------|
| Claude Code | /loop, /goal, hooks, subagents, SKILL.md | Contracts, roles, disk state |
| Codex | Automations, worktrees, /goal | Same — you wire it |
| Cursor | Agent mode, inline edits | Not loop-native |
| OpenCode | Model-agnostic, extensible | Framework only |

Every tool ships *primitives*. AdaL ships the **loop**.

---

## Slide 10: Key People

| Person | Contribution |
|--------|--------------|
| Andrej Karpathy | Vibe coding · Software 3.0 · LOOPS.md |
| Addy Osmani | Named "loop engineering" (June 2026) |
| Boris Cherny | "I don't prompt Claude anymore. I write loops." |
| Peter Steinberger | "Design loops that prompt your agents." |

---

## Materials & Links

- **Slides (HTML):** [class-1-beyond-loop-engineering.html](class-1-beyond-loop-engineering.html)
- **Slides (Markdown):** [class-1-beyond-loop-engineering.md](class-1-beyond-loop-engineering.md)
- **YC Agent Landscape:** [adalagent.ai/research/yc-landscape/](https://adalagent.ai/research/yc-landscape/)
- **Karpathy vibe-coding tweet:** [x.com/karpathy](https://x.com/karpathy/status/1886192184808149383)
- **Karpathy "Software Is Changing (Again)":** [YC Library](https://www.ycombinator.com/library/MW-andrej-karpathy-software-is-changing-again)
- **Anthropic context engineering:** [anthropic.com/engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- **Osmani loop engineering:** [addyosmani.com/blog/loop-engineering](https://addyosmani.com/blog/loop-engineering/)
- **LOOPS.md (v060726):** provided in class materials
