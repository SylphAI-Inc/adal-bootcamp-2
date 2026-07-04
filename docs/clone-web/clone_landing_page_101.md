# Clone Landing Page 101: The Definitive Hero-Cloning Playbook

> **POC:** Engineering / AI Agents cloning landing-page hero sections
> **TL;DR:** Trust your eyes first, scaffold fast (80%), then snipe exact CSS math (20%). This guide synthesizes the original Visual-First recipe with hard-won, battle-tested learnings from cloning Framer sites (xtract.framer.ai). It includes Framer-aware "Sniper CSS" snippets that walk the DOM tree, a gotcha catalog, and a quality checklist.
> **Audience:** An AI agent or developer using a **browser-use agent** (an AI mode that drives a real Chrome browser via `navigate` / `computer` / `javascript_tool`) — or Chrome DevTools MCP / Playwright — to clone any landing page with pixel-perfect fidelity. Section 2.5 documents the browser-use toolset; the recipe in Section 3 and the runbook in Section 8 give you the exact tool calls.

---

## 1. Philosophy & Mindset

When building a high-fidelity landing-page clone, the biggest trap is relying purely on DOM trees and raw CSS dumps. Modern website builders (**Framer**, **Webflow**) generate deeply nested "div soup" and obfuscated CSS to create their visual effects.

**The Golden Rule:** Trust your "eyes" (screenshots) first. But when an effect looks too complex to be pure CSS, switch to **Deep DOM Interrogation** to steal the *exact* asset — never guess the math.

### The 80/20 Cloning Philosophy
Divide your workflow into two distinct phases so you don't get bogged down pixel-pushing too early:

1. **The 80% Sprint (Speed & Structure).** Get the page laid out rapidly. Fetch the semantic HTML, scaffold the React component tree (`Navbar`, `Hero`, `Features`), and apply basic Tailwind for layout (Flex/Grid) and spacing. Accept approximations: solid colors instead of gradients, standard shadows, static backgrounds. **Move fast.**
2. **The 20% Polish (Pixel Perfection & Physics).** Once the structure is on screen, shift to meticulous engineering. Use "Sniper CSS" to extract exact multi-stop gradients, rip WebGL canvas backgrounds to `.webm`, map massive multi-layer box-shadows, and implement Framer Motion spring physics.

### Why DOM Dumps Fail
- **`getComputedStyle` returns 500+ properties** — it overwhelms your context window and induces hallucination. Query *only* the properties you need.
- **Builders nest the real styles.** On Framer, the element you select (`nav a`) is rarely the element that carries the visual style. The text node lives several `<div>`/`<p>`/`<span>` levels deeper (see Gotcha #1).
- **Effects aren't where they look.** A background "aura" is usually two rotated, multi-stop gradient orbs — not one radial blur. Eyeballing turns a sharp galaxy-arm into a muddy blob.

---

## 2. Tech Stack Setup

**Recommended stack** (opinionated, battle-tested):

| Layer | Choice | Why |
|-------|--------|-----|
| Framework | **Next.js** (App Router) or **Vite + React** | Fast HMR, easy font loading, SSR optional |
| Styling | **Tailwind CSS** | Arbitrary values (`max-w-[900px]`, `tracking-[-2.2px]`) map 1:1 to extracted tokens |
| Animation | **Framer Motion** | Spring physics + hover/scroll orchestration that matches Framer originals |
| Icons/Assets | Local `src/assets/media/` | Store ripped SVGs, noise overlays, `.webm` backgrounds |

### Folder Structure
```
src/
  components/
    layout/        # Navbar.tsx, Footer.tsx        (global elements)
    sections/      # Hero.tsx, Features.tsx, ...    (page blocks)
    ui/            # Button.tsx, Badge.tsx, GlassCard.tsx  (reusable micro-components)
  assets/
    media/         # extracted videos, noise overlays, icons, SVG logos
  styles/
    globals.css    # font-face, CSS variables for design tokens
```

### Font Loading (critical for fidelity)
A clone looks instantly fake with the wrong font. Identify the exact family early (see Sniper Script 1) and load it before measuring anything.

```css
/* globals.css — example for a Figtree-based site */
@import url('https://fonts.googleapis.com/css2?family=Figtree:wght@400;500;600;700&display=swap');

:root {
  --font-sans: 'Figtree', sans-serif;
}
```
```js
// next/font alternative
import { Figtree } from 'next/font/google';
const figtree = Figtree({ subsets: ['latin'], weight: ['400','500','600','700'] });
```

> **Framer tell:** Framer font-families often read `Figtree, "Figtree Placeholder", sans-serif`. The `"... Placeholder"` is Framer's fallback shim — ignore it; load the real font.

---

## 2.5. Browser-Use Agent: Setup & Tools

The **browser-use agent** is an AI agent mode that controls a real Chrome browser. It is the primary engine for this guide: you navigate to the target, screenshot it, and snipe CSS by executing JavaScript directly on the live page. Treat the tools below as your instrument panel.

### Core Tools

| Tool | Signature | Use |
|------|-----------|-----|
| **navigate** | `navigate(url)` | Open a URL in the browser |
| **computer** | `computer(tab_id, action=...)` | Interact with the page. Actions: `screenshot`, `wait`, `click`, `scroll`, `type`, `key` (e.g. `cmd+Home`) |
| **javascript_tool** | `javascript_tool(tab_id, action="javascript_exec", text="...")` | **PRIMARY CSS-extraction tool.** Runs JS on the page and returns the value as a string |
| **resize_window** | `resize_window(tab_id, width, height)` | Resize the viewport (responsive testing + full-section screenshots) |
| **tabs_context** | `tabs_context` | List open tabs / their `tab_id`s |
| **bash** | `bash(command)` | Shell — save files, decode data URIs, CDP screenshots |
| **read_file / create_file** | — | Read/write local files (token sheets, components, assets) |

### Key Workflow Patterns

**Pattern 1 — Screenshot capture** (viewport-only; resize height to fit a section):
```
resize_window(tab_id=1, width=1440, height=1400)
javascript_tool(tab_id=1, action="javascript_exec", text="window.scrollTo(0, 0); 'ok';")
computer(tab_id=1, action="wait", duration=2)   // let animations settle
computer(tab_id=1, action="screenshot")
```

**Pattern 2 — Sniper CSS extraction** (IIFE that returns `JSON.stringify`):
```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => {
  const h1 = document.querySelector('h1');
  const s = getComputedStyle(h1);
  return JSON.stringify({ color: s.color, fontSize: s.fontSize }, null, 2);
})()
")
```

**Pattern 3 — Framer-aware deep text walk** (`TreeWalker` to the real text node):
```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => {
  function deepTextStyle(root, textNeedle) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      if (walker.currentNode.textContent.trim().includes(textNeedle)) {
        const el = walker.currentNode.parentElement;
        const s = getComputedStyle(el);
        return { tag: el.tagName, color: s.color, fontSize: s.fontSize, fontFamily: s.fontFamily, fontWeight: s.fontWeight };
      }
    }
    return null;
  }
  return JSON.stringify(deepTextStyle(document.body, 'Home'), null, 2);
})()
")
```

**Pattern 4 — SVG extraction + local save:**
```
// 1. Extract markup
javascript_tool(tab_id=1, action="javascript_exec", text="(() => document.querySelector('svg').outerHTML)()")
// 2. Save via bash heredoc
bash("cat > assets/media/icon.svg << 'EOF'
<svg xmlns=\"...\">...</svg>
EOF")
```

**Pattern 5 — Data-URI logo extraction:**
```
// 1. Find all data-URI backgrounds
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => JSON.stringify(
  Array.from(document.querySelectorAll('div'))
    .filter(d => getComputedStyle(d).backgroundImage.startsWith('url(\"data:image'))
    .map((d, i) => ({ index: i, bg: getComputedStyle(d).backgroundImage,
                      size: d.getBoundingClientRect().width + 'x' + d.getBoundingClientRect().height })),
  null, 2))()
")
// 2. Decode + save via node
bash("node -e \"const bg='...'; const uri=bg.match(/url\\(\\\"(.*)\\\"\\)/)[1]; require('fs').writeFileSync('assets/media/logo.svg', decodeURIComponent(uri.split(',')[1]));\"")
```

**Pattern 6 — Full-page screenshot via CDP** (when viewport resize can't reach the whole page):
```
bash("node << 'NODE'
const WebSocket = require('ws');
// Connect to Chrome debugging endpoint, call Page.captureScreenshot with a clip rect.
NODE")
```

> See **Section 4 → Browser-Use Agent Gotchas** for the five rules that prevent silent failures, and **Section 8** for the end-to-end runbook.

---

## 3. The 6-Step Visual-First Recipe

### Step 0: Project Scaffolding
Establish the folder structure above. Componentize from the start: `layout/`, `sections/`, `ui/`. Create empty `Hero.tsx`, `Navbar.tsx`, `Button.tsx`, `Badge.tsx` shells so you have somewhere to drop extracted values.

### Step 1: Visual Grounding (The "Eye Test")
**Before reading a single line of code, ground yourself visually.**

**Browser-use tool calls:**
```
navigate("https://target.framer.ai/")
resize_window(tab_id=1, width=1440, height=1400)
javascript_tool(tab_id=1, action="javascript_exec", text="window.scrollTo(0, 0); 'ok';")
computer(tab_id=1, action="wait", duration=2)
computer(tab_id=1, action="screenshot")          // desktop hero
resize_window(tab_id=1, width=390, height=1400)
computer(tab_id=1, action="wait", duration=2)
computer(tab_id=1, action="screenshot")          // mobile hero
```

**Analyze** each screenshot (the agent sees it directly) and name the *Vibe*:
- **Backgrounds:** Flat? Subtle radial? Sweeping SVG waves? Floating blurred orbs? Star/particle field?
- **Buttons:** Flat? Glassmorphic (backdrop-blur)? Glowing aura? Multi-layer shadow?
- **Typography:** Which words are highlighted? Gradient text clips? Tight negative letter-spacing?
- **Badges/pills:** Compound components (pill-in-a-pill)?

Capture at **desktop (1440px)** and **mobile (390px)** so you record responsive breakpoints. Always `wait` ~2s after a resize/scroll so animations settle before the shot.

### Step 2: Macro Structure Capture (Semantic HTML)
*Best for: the general section-by-section layout (Nav, Hero, Bento Grid, Footer) and the real copy/text.*

- Pull a **text/structure snapshot** by executing JS — grab the section landmarks and the real copy in one shot:
```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => JSON.stringify({
  h1: document.querySelector('h1')?.innerText,
  navLinks: Array.from(document.querySelectorAll('nav a')).map(a => a.innerText.trim()).filter(Boolean),
  buttons: Array.from(document.querySelectorAll('a, button')).map(b => b.innerText.trim()).filter(Boolean).slice(0, 12),
  sections: Array.from(document.querySelectorAll('section')).length
}, null, 2))()
")
```
- **Do NOT blindly copy the DOM.** Distill the nested builder divs into clean, semantic React: `<nav>`, `<section>`, `<h1>`, `<button>`. A 12-deep Framer `<div>` chain becomes one `<button>`. Note that Framer often duplicates button text (`"Book a callBook a call"`) — dedupe it (Gotcha #8).

### Step 3: Micro Extraction (Sniper CSS)
*Best for: exact pixel-perfect design tokens during the 20% Polish.*

**Tool:** `javascript_tool(tab_id, action="javascript_exec", text="...")`. **Never** dump the whole `getComputedStyle` — snipe only the properties you need. Every script is an IIFE that returns `JSON.stringify(...)` so the agent gets a small, clean JSON string back.

```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => {
  const s = getComputedStyle(document.querySelector('h1'));
  return JSON.stringify({ fontFamily: s.fontFamily, fontSize: s.fontSize,
                          fontWeight: s.fontWeight, letterSpacing: s.letterSpacing,
                          lineHeight: s.lineHeight, color: s.color }, null, 2);
})()
")
```

See the full **Sniper CSS Script Library** in Section 5 — every snippet is already wrapped in the `javascript_tool` call format, including Framer-aware variants that walk the DOM tree to find the *real* styled node.

### Step 4: Deep DOM Interrogation (The Secret Sauce)
*Best for: complex glows, overlapping animations, fluid/WebGL backgrounds, multi-layer shadows.*

When an effect is too complex to eyeball, **do not guess** — interrogate the layered DOM with `javascript_tool` (use **Script 5** for orbs, **Script 9** for pseudo-elements):
- **Layered gradient orbs:** Find each decorative `<div>` and read its `background`, `transform` (rotation!), `filter` (blur is usually surprisingly small), and `opacity`. Framer originals often stack **two** orbs of different sizes at different angles inside a parent that carries `opacity` + `blur`.
- **WebGL / canvas backgrounds:** You can't reproduce shader math cheaply. Screen-record the canvas (or use the CDP `bash` pattern) and export a looping `.webm`, then drop it behind the hero with `<video autoplay loop muted playsinline>`.
- **Pseudo-elements:** Effects hidden in `::before`/`::after` — pass the pseudo string to `getComputedStyle(el, '::before')` (Script 9).

### Step 5: Asset Extraction (SVGs, Logos, Videos)
- **Inline SVG:** Extract `outerHTML` via `javascript_tool`, then save with `bash` (Pattern 4):
```
javascript_tool(tab_id=1, action="javascript_exec", text="(() => document.querySelector('svg').outerHTML)()")
bash("cat > assets/media/icon.svg << 'EOF'\n<svg ...>...</svg>\nEOF")
```
- **`data:image/svg+xml` background logos:** Trust/logo carousels frequently render as **CSS `background-image` data-URIs on `<div>`s — not `<img>` tags** (Gotcha #3). Use **Script 7** to list them, then decode + save with `node` (Pattern 5).
- **Background videos:** Capture as `.webm`/`.mp4` (CDP/screen-record), store in `assets/media/`.

### Step 6: Polish & Animation
- Map extracted spring/easing to Framer Motion.
- Recreate hover micro-interactions (e.g., Framer's double-text button swap — Gotcha #8).
- Verify forced line-breaks (`max-w-[…]`) so text wraps identically (Sniper Script 4).
- Run the **Quality Checklist** (Section 7).

---

## 4. Common Gotchas & Solutions

These are real traps discovered cloning **xtract.framer.ai** and similar Framer/Webflow sites.

| # | Gotcha | Symptom | Solution |
|---|--------|---------|----------|
| 1 | **Framer nests text deeply** | `nav a` reports default browser styles: `rgb(0,0,238)`, `12px`, `sans-serif` | The real style is on a nested `<p>`/`<span>`. **Walk the DOM tree** to the deepest text node (Sniper Script 1F). |
| 2 | **Layered gradient orbs, not radial blur** | Background aura looks like a soft radial glow | It's **two overlapping gradient divs** (e.g., 406px + 300px) with multi-stop *linear* gradients at specific angles (e.g., 229deg / 141deg), wrapped in a parent with `opacity: 0.6` + `blur(10px)`. Extract each orb separately (Script 5). |
| 3 | **Logos are data-URI backgrounds** | `document.querySelectorAll('img')` returns nothing for the trust carousel | Logos are inline `data:image/svg+xml` URIs set as CSS `background-image` on `<div>`s. Query `backgroundImage` (Script 7). |
| 4 | **Multi-layer box-shadows** | Your single shadow looks flat vs. the original's depth | Buttons can have **6 layers** of rgba shadows at specific offsets. Extract the full `boxShadow` string verbatim (Script 2). |
| 5 | **Compound badge ('New' pill)** | Badge looks like one element | It's an **outer pill** (`rgba(13,13,13,0.8)`, `border-radius: 20px`) containing an **inner colored pill** (`rgb(129,74,200)`, `border-radius: 12px`) + text. Build as nested components. |
| 6 | **Star/particle backgrounds** | Faint texture behind hero you can't place | Full-width container at low opacity (~0.5) behind hero content. Rip as image/`.webm` or recreate with a tiled noise/star SVG. |
| 7 | **Negative letter-spacing everywhere** | Type looks "looser" than original | Framer sites use negative tracking site-wide (e.g., h1 `-2.2px`, body `-0.28px`). Extract and apply per element with `tracking-[-2.2px]`. |
| 8 | **Double text in buttons** | DOM shows `"Book a callBook a call"` | Framer renders button text twice for a hover slide/swap animation. **Render it once**; optionally implement the hover text-swap with Framer Motion. |
| 9 | **`getComputedStyle` overload** | Context window flooded, hallucinated values | Snipe only needed properties. Never `JSON.stringify(getComputedStyle(el))`. |
| 10 | **Fluid wrapping ≠ original** | Headline wraps on a different word | Extract the container width and force it: `max-w-[900px]` (Script 4). |

### Browser-Use Agent Gotchas

Five rules that prevent silent failures when driving the live browser:

| # | Gotcha | Rule |
|---|--------|------|
| B1 | **Screenshots are viewport-only** | The agent only captures what's in the viewport. **`resize_window` the height** (e.g. 1400px) to fit a full section *before* `computer(action="screenshot")`. |
| B2 | **`javascript_tool` returns strings** | Always wrap in an IIFE and `JSON.stringify()` your result: `(() => { ...; return JSON.stringify(obj, null, 2); })()`. Returning a raw object gives you `[object Object]`. |
| B3 | **Framer deep nesting** | For any text style, use the `TreeWalker` / deep-walk pattern (Script 1F). **Never** trust the outer element's computed style — `nav a` reports browser defaults. |
| B4 | **Wait after scroll/resize** | Always `computer(tab_id, action="wait", duration=2)` after a scroll or resize so animations/lazy content settle before screenshotting or measuring. |
| B5 | **Always pass `tab_id`** | Specify `tab_id` on every `computer` / `javascript_tool` / `resize_window` call. Use `tabs_context` to confirm what's open. |

---

## 5. Sniper CSS Script Library

Production-ready payloads for the browser-use agent. Each returns a small, focused JSON blob. **Framer-aware variants (suffix `F`) walk the DOM tree** to find the real styled node.

**Copy-paste format.** Drop any script below into the `text` argument of a `javascript_tool` call:
```
javascript_tool(tab_id=1, action="javascript_exec", text="<SCRIPT>")
```
The scripts are written as IIFEs returning `JSON.stringify(...)` (Gotcha B2), so the agent receives clean JSON. The bare `() => {...}` form shown is the function body; in browser-use mode invoke it inline, e.g. `(() => { ...; return JSON.stringify(obj, null, 2); })()`.

### Script 1: Typography Tokens
```javascript
() => {
  const el = document.querySelector('h1');
  const s = window.getComputedStyle(el);
  return JSON.stringify({
    fontFamily: s.fontFamily,
    color: s.color,
    fontSize: s.fontSize,
    fontWeight: s.fontWeight,
    letterSpacing: s.letterSpacing,
    lineHeight: s.lineHeight
  }, null, 2);
}
```

### Script 1F: Framer-Aware Typography (Walk to Deepest Text Node)
*Why: `nav a` and many Framer headings report default browser styles. The real style is on a deeply nested `<p>`/`<span>`. This walks down to the deepest element that actually contains the visible text.*
```javascript
(selector = 'h1') => {
  const root = document.querySelector(selector);
  if (!root) return "Not found";
  // Descend to the deepest element whose text matches the root's text.
  const target = (root.textContent || '').trim();
  let el = root;
  while (true) {
    const child = Array.from(el.children).find(
      c => (c.textContent || '').trim() === target
    );
    if (!child) break;
    el = child;
  }
  const s = window.getComputedStyle(el);
  return JSON.stringify({
    matchedTag: el.tagName,
    depthFromRoot: (function(){let d=0,n=el;while(n!==root){n=n.parentElement;d++;}return d;})(),
    fontFamily: s.fontFamily,
    color: s.color,
    fontSize: s.fontSize,
    fontWeight: s.fontWeight,
    letterSpacing: s.letterSpacing,
    lineHeight: s.lineHeight
  }, null, 2);
}
```

### Script 2: Bounding Box, Overflow & Full Box-Shadow
*Why: find exact dimensions, whether glows bleed (`overflow: visible`), and capture all shadow layers verbatim.*
```javascript
(label = 'Get Started') => {
  const btn = Array.from(document.querySelectorAll('a, button'))
    .find(l => (l.textContent || '').includes(label));
  if (!btn) return "Not found";
  const r = btn.getBoundingClientRect();
  const s = window.getComputedStyle(btn);
  return JSON.stringify({
    width: r.width, height: r.height,
    display: s.display,
    padding: s.padding,
    borderRadius: s.borderRadius,
    overflow: s.overflow,
    background: s.background,
    boxShadow: s.boxShadow   // capture ALL layers, do not summarize
  }, null, 2);
}
```

### Script 3: Glassmorphism & Backgrounds
```javascript
(selector = 'nav') => {
  const el = document.querySelector(selector);
  const s = window.getComputedStyle(el);
  return JSON.stringify({
    background: s.background,
    backdropFilter: s.backdropFilter || s.webkitBackdropFilter,
    border: s.border,
    borderRadius: s.borderRadius,
    height: el.getBoundingClientRect().height,
    padding: s.padding
  }, null, 2);
}
```

### Script 4: Forced Line-Breaks (Container Width)
*Why: a clone looks fake if text wraps differently. Extract the exact width and lock it.*
```javascript
() => {
  const el = document.querySelector('h1');
  const r = el.getBoundingClientRect();
  return JSON.stringify({
    containerMaxWidth: r.width   // → Tailwind max-w-[900px] to force identical wraps
  }, null, 2);
}
```

### Script 5: Abstract Glows & Layered Orbs
*Why: auras are usually hard-shaped, multi-stop linear gradients with precise rotation + a tight blur — not a radial blob. Extract every decorative orb.*
```javascript
() => {
  // Grab all absolutely-positioned decorative divs in the hero.
  const hero = document.querySelector('section') || document.body;
  const orbs = Array.from(hero.querySelectorAll('div')).filter(d => {
    const s = getComputedStyle(d);
    return s.position === 'absolute' &&
           (s.backgroundImage.includes('gradient') || parseFloat(s.filter && s.filter.includes('blur') ? 1 : 0));
  }).slice(0, 6);
  return JSON.stringify(orbs.map(d => {
    const s = getComputedStyle(d);
    const r = d.getBoundingClientRect();
    return {
      size: `${Math.round(r.width)}x${Math.round(r.height)}`,
      background: s.backgroundImage,   // multi-stop gradient
      transform: s.transform,          // rotation matrix
      filter: s.filter,                // often a small blur
      opacity: s.opacity,
      mixBlendMode: s.mixBlendMode
    };
  }), null, 2);
}
```

### Script 6: Named Framer Layer (when you know the data-framer-name)
```javascript
(name = 'Big Circle') => {
  const el = document.querySelector(`[data-framer-name="${name}"]`);
  if (!el) return "Not found";
  const s = window.getComputedStyle(el);
  return JSON.stringify({
    background: s.backgroundImage,
    transform: s.transform,
    filter: s.filter,
    opacity: s.opacity
  }, null, 2);
}
```

### Script 7: Data-URI Logo Extraction (Trust Carousels)
*Why: logos are CSS `background-image` data-URIs on `<div>`s, invisible to `img` queries.*
```javascript
() => {
  const nodes = Array.from(document.querySelectorAll('div'))
    .filter(d => getComputedStyle(d).backgroundImage.startsWith('url("data:image'));
  return JSON.stringify(nodes.slice(0, 20).map((d, i) => {
    const bg = getComputedStyle(d).backgroundImage;
    return {
      index: i,
      size: `${Math.round(d.getBoundingClientRect().width)}x${Math.round(d.getBoundingClientRect().height)}`,
      uriPreview: bg.slice(0, 80) + '...',   // full string is the asset; decode & save
      fullLength: bg.length
    };
  }), null, 2);
}
```
> To save: read the full `backgroundImage`, strip `url("` / `")`, URL-decode the `data:image/svg+xml,...` payload, and write it to `assets/media/logo-N.svg`.

### Script 8: Compound Component Audit (Badge / Pill-in-Pill)
```javascript
(label = 'New') => {
  const inner = Array.from(document.querySelectorAll('div, span'))
    .find(e => (e.textContent || '').trim() === label);
  if (!inner) return "Not found";
  const outer = inner.parentElement;
  const dump = el => {
    const s = getComputedStyle(el);
    return { background: s.background, borderRadius: s.borderRadius, padding: s.padding, color: s.color };
  };
  return JSON.stringify({ outer: dump(outer), inner: dump(inner) }, null, 2);
}
```

### Script 9: Pseudo-Element Extraction
```javascript
(selector, pseudo = '::before') => {
  const el = document.querySelector(selector);
  if (!el) return "Not found";
  const s = window.getComputedStyle(el, pseudo);
  return JSON.stringify({
    content: s.content, background: s.background,
    width: s.width, height: s.height,
    transform: s.transform, filter: s.filter, opacity: s.opacity
  }, null, 2);
}
```

---

## 6. Design Token Extraction Template

Document every extracted value in this structured format. **Worked example: xtract.framer.ai.**

### Colors
| Token | Hex | RGB |
|-------|-----|-----|
| Page background | `#000000` | `rgb(0,0,0)` |
| Primary purple | `#814AC8` | `rgb(129,74,200)` |
| Bright purple glow | `#DF7AFE` | `rgb(223,122,254)` |
| Dark translucent surface | — | `rgba(13,13,13,0.8)` |
| White text | `#FFFFFF` | `rgb(255,255,255)` |
| Description gray | `#CCCCCC` | `rgb(204,204,204)` |

### Typography
| Element | Size | Weight | Line-height | Letter-spacing | Notes |
|---------|------|--------|-------------|----------------|-------|
| H1 | 70px | 600 | 77px | -2.2px | max-width ~900px |
| Body / nav | 14px | 500 | 16.8px | -0.28px | |
| Description | 18px | 500 | 27px | -0.36px | |

**Font family:** `Figtree, "Figtree Placeholder", sans-serif` (load real Figtree; ignore the Placeholder shim).

### Spacing & Components
| Component | Value |
|-----------|-------|
| Navbar height | ~65px |
| Navbar padding | 10px 40px |
| Button border-radius | 6px |
| Button padding | 9px 13px |
| Badge outer | border-radius 20px, padding 2px 10px 2px 2px |
| Badge inner ('New') | border-radius 12px, padding 4px 8px |

### Effects (capture verbatim — do not summarize)
```
Hero orbs:
  Orb A: 406px, linear-gradient(229deg, …), rotate(…), opacity within parent
  Orb B: 300px, linear-gradient(141deg, …)
  Parent wrapper: opacity 0.6, filter blur(10px)

Button box-shadow: <full 6-layer rgba shadow string>
Star/particle layer: full-width, opacity ~0.5, behind hero content
```

### Tailwind Mapping (copy-paste pattern)
```jsx
// H1
<h1 className="text-[70px] font-semibold leading-[77px] tracking-[-2.2px] max-w-[900px] text-white">

// Body/nav
<span className="text-[14px] font-medium leading-[16.8px] tracking-[-0.28px]">

// Primary button
<button className="rounded-[6px] px-[13px] py-[9px] bg-[#814AC8]">
```

---

## 7. Quality Checklist

Verify your clone before declaring done. Compare side-by-side with the reference screenshot at 1440px and 390px.

**Layout & Structure**
- [ ] Semantic HTML (`nav`, `section`, `h1`, `button`) — no copied div-soup
- [ ] Section order and spacing match
- [ ] Responsive breakpoints behave like the original

**Typography**
- [ ] Correct font family loaded (not a fallback)
- [ ] Font sizes, weights, line-heights match extracted tokens
- [ ] Negative letter-spacing applied per element
- [ ] **Headline wraps on the same word** (forced `max-w-[…]`)

**Color & Surfaces**
- [ ] Background color exact
- [ ] Translucent surfaces use the exact `rgba(...)`
- [ ] Text colors (white, gray, accents) match

**Effects (the 20%)**
- [ ] Gradient orbs reproduced as separate layered divs (size, angle, blur, opacity)
- [ ] Multi-layer box-shadows copied verbatim
- [ ] Glassmorphism (`backdrop-filter`) present where used
- [ ] Star/particle/noise background layer present at correct opacity

**Components**
- [ ] Compound badge built as nested pills
- [ ] Buttons render text once (no Framer double-text)
- [ ] Hover micro-interactions implemented (text swap, glow)

**Assets**
- [ ] Trust/logo carousel extracted from data-URIs (not missing)
- [ ] Inline SVGs saved as components
- [ ] WebGL/canvas backgrounds ripped to `.webm` and looping

**Final**
- [ ] Side-by-side screenshot diff shows no obvious deltas
- [ ] No console errors; fonts/assets load without flashes

---

## 8. Complete Hero Clone Workflow (Browser-Use Runbook)

A mechanical, end-to-end sequence an AI agent can follow to go from a URL to a fully-extracted hero. Run each step in order; paste results into the Section 6 token sheet as you go. Assumes `tab_id=1`.

### 0. Scaffold the project (local)
```
bash("mkdir -p src/components/{layout,sections,ui} src/assets/media src/styles")
create_file("docs/tokens.md", "<empty Section-6 template to fill in>")
```

### 1. Navigate to the target
```
navigate("https://target.framer.ai/")
tabs_context                                   // confirm tab_id
```

### 2. Resize viewport (desktop) + settle
```
resize_window(tab_id=1, width=1440, height=1400)
javascript_tool(tab_id=1, action="javascript_exec", text="window.scrollTo(0, 0); 'ok';")
computer(tab_id=1, action="wait", duration=2)
```

### 3. Screenshot the hero (desktop + mobile)
```
computer(tab_id=1, action="screenshot")                         // desktop
resize_window(tab_id=1, width=390, height=1400)
computer(tab_id=1, action="wait", duration=2)
computer(tab_id=1, action="screenshot")                         // mobile
resize_window(tab_id=1, width=1440, height=1400)                // back to desktop for extraction
computer(tab_id=1, action="wait", duration=2)
```
Read both screenshots; name the Vibe (Step 1). Then snipe in the desktop viewport.

### 4. Extract navbar styles (Script 3)
```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => {
  const el = document.querySelector('nav');
  const s = getComputedStyle(el);
  return JSON.stringify({ background: s.background, backdropFilter: s.backdropFilter || s.webkitBackdropFilter,
    border: s.border, borderRadius: s.borderRadius,
    height: el.getBoundingClientRect().height, padding: s.padding }, null, 2);
})()
")
```
→ navbar height, padding, glass background. Also run the **deep text walk (Script 1F)** on a nav link to get the *real* link color/size (Gotcha B3 / #1).

### 5. Extract heading styles (Script 1F + Script 4)
```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => {
  function deepTextStyle(root) {
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const t = walker.currentNode.textContent.trim();
      if (t) { const el = walker.currentNode.parentElement; const s = getComputedStyle(el);
        return { tag: el.tagName, color: s.color, fontFamily: s.fontFamily, fontSize: s.fontSize,
                 fontWeight: s.fontWeight, letterSpacing: s.letterSpacing, lineHeight: s.lineHeight }; }
    }
    return null;
  }
  const h1 = document.querySelector('h1');
  return JSON.stringify({ style: deepTextStyle(h1), containerMaxWidth: h1.getBoundingClientRect().width }, null, 2);
})()
")
```
→ H1 font/size/weight/letter-spacing + the `max-w-[…]` to force identical wraps.

### 6. Extract button styles (Script 2)
```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => {
  const btn = Array.from(document.querySelectorAll('a, button')).find(l => (l.textContent||'').includes('Get Started'))
            || document.querySelector('a, button');
  const r = btn.getBoundingClientRect(); const s = getComputedStyle(btn);
  return JSON.stringify({ width: r.width, height: r.height, display: s.display, padding: s.padding,
    borderRadius: s.borderRadius, overflow: s.overflow, background: s.background, boxShadow: s.boxShadow }, null, 2);
})()
")
```
→ button radius/padding + the full multi-layer `boxShadow` verbatim (Gotcha #4).

### 7. Extract badge styles (Script 8)
```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => {
  const inner = Array.from(document.querySelectorAll('div, span')).find(e => (e.textContent||'').trim() === 'New');
  if (!inner) return 'Not found';
  const outer = inner.parentElement;
  const dump = el => { const s = getComputedStyle(el);
    return { background: s.background, borderRadius: s.borderRadius, padding: s.padding, color: s.color }; };
  return JSON.stringify({ outer: dump(outer), inner: dump(inner) }, null, 2);
})()
")
```
→ the pill-in-pill structure (Gotcha #5).

### 8. Extract decorative elements (Script 5)
```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => {
  const hero = document.querySelector('section') || document.body;
  const orbs = Array.from(hero.querySelectorAll('div')).filter(d => {
    const s = getComputedStyle(d);
    return s.position === 'absolute' && s.backgroundImage.includes('gradient');
  }).slice(0, 6);
  return JSON.stringify(orbs.map(d => { const s = getComputedStyle(d); const r = d.getBoundingClientRect();
    return { size: Math.round(r.width)+'x'+Math.round(r.height), background: s.backgroundImage,
             transform: s.transform, filter: s.filter, opacity: s.opacity, mixBlendMode: s.mixBlendMode }; }), null, 2);
})()
")
```
→ each gradient orb's size, angle, blur, opacity (Gotcha #2). Capture verbatim.

### 9. Extract logo assets (Script 7 + decode)
```
javascript_tool(tab_id=1, action="javascript_exec", text="
(() => JSON.stringify(
  Array.from(document.querySelectorAll('div'))
    .filter(d => getComputedStyle(d).backgroundImage.startsWith('url(\"data:image'))
    .map((d, i) => ({ index: i, bg: getComputedStyle(d).backgroundImage })), null, 2))()
")
```
Then for each, decode + save (Pattern 5):
```
bash("node -e \"const bg='...'; const uri=bg.match(/url\\(\\\"(.*)\\\"\\)/)[1]; require('fs').writeFileSync('src/assets/media/logo-0.svg', decodeURIComponent(uri.split(',')[1]));\"")
```
→ trust-carousel logos saved locally (Gotcha #3).

### 10. Compile the token sheet
Fold every extracted value into the **Section 6** template (`docs/tokens.md`): colors, type scale, spacing, effects verbatim. Then build components from the tokens and run the **Section 7 Quality Checklist** — comparing your clone against the desktop (1440px) and mobile (390px) screenshots from step 3.

> **Loop:** screenshot your clone → diff against reference → re-snipe any element that's off → repeat until the checklist is green.

---

## 9. How Browser-Use Powers the Full Clone Lifecycle

The browser-use agent isn't just an extraction tool — it's your **eyes throughout the entire clone lifecycle**. Here's how it integrates into every phase:

### Phase 1: Research (Sections 3.1–3.5)
**What browser-use does:** Navigate to target → resize viewport → screenshot → run Sniper CSS scripts → extract assets.
**Without it:** You're guessing colors, fonts, and spacing from static markdown. You'll get it wrong.

### Phase 2: Building (the 80% Sprint)
**What browser-use does:** While your coding worker writes React components, browser-use runs your local dev server and screenshots it for comparison.

```
// 1. Coding worker builds components, starts dev server
bash("cd /project && npm run dev")  // runs on port 5173

// 2. Browser-use opens your clone
navigate("http://localhost:5173")
resize_window(tab_id=1, width=1440, height=1400)
computer(tab_id=1, action="screenshot")  // screenshot YOUR clone

// 3. Compare against original reference screenshot
// The agent can see both images and identify deltas:
//   - "H1 is too large — original is 70px, yours looks ~80px"
//   - "Badge is missing the inner purple pill"
//   - "Button shadow is a single layer, needs 6 layers"
```

**Key pattern — the Build→Screenshot→Fix loop:**
1. Coding worker builds/updates a component
2. Browser-use screenshots the local clone
3. You (or browser-use) compare against the original screenshot
4. Identify specific deltas
5. Send the coding worker targeted fixes with exact pixel values
6. Repeat until the section matches

### Phase 3: Polish (the 20% Perfection)
**What browser-use does:** Side-by-side pixel comparison. Open TWO tabs — one with the original, one with your clone — and screenshot both at the same viewport.

```
// Tab 1: Original
navigate("https://xtract.framer.ai/")
resize_window(tab_id=1, width=1440, height=1400)
computer(tab_id=1, action="screenshot")

// Tab 2: Your clone  
navigate("http://localhost:5173")  // opens in new tab
resize_window(tab_id=2, width=1440, height=1400)
computer(tab_id=2, action="screenshot")

// Now the agent sees both and can identify:
// - Gradient orb position is off by ~50px
// - Letter-spacing on description is too tight
// - Trust bar logos are missing
```

### Phase 4: Visual QA (Section 7 Checklist)
**What browser-use does:** Systematically verify each checklist item by running targeted JS on both the original and clone, comparing values programmatically.

```
// Verify font-family matches
javascript_tool(tab_id=1, text="getComputedStyle(document.querySelector('h1')).fontFamily")  // original
javascript_tool(tab_id=2, text="getComputedStyle(document.querySelector('h1')).fontFamily")  // clone
// Compare: both should return "Figtree, ..."
```

### The Three Roles of Browser-Use

| Phase | Role | What It Does |
|-------|------|-------------|
| **Research** | 🔍 Investigator | Extracts CSS tokens, SVG assets, layout structure from the target |
| **Building** | 👁️ Eyes | Screenshots your local clone so the coding agent can see what it built |
| **QA** | ✅ Verifier | Side-by-side comparison, programmatic CSS value checks, checklist verification |

### Why This Matters
Without browser-use in the build loop, the coding worker is **blind** — it writes CSS values but never sees the result. The build→screenshot→fix loop is what turns a "close enough" clone into a pixel-perfect one. **The agent that writes code should never be the only agent that judges quality.** Use browser-use as the independent verifier.

---

## 10. Multi-Agent Orchestration Strategy

For maximum efficiency, run **two workers in parallel**:

### Worker 1: Browser-Use Agent (GPT 5.5)
- Mode: `browser-use`
- Responsible for: navigation, screenshots, CSS extraction, asset ripping, visual QA
- Stays in browser-use mode throughout the project

### Worker 2: Coding Agent (GPT 5.5)
- Mode: `coding`
- Responsible for: scaffolding, writing React/Tailwind components, fixing deltas
- Receives exact pixel values and screenshots from Worker 1

### Supervisor (Engineer)
- Creates plans, briefs workers, reviews diffs
- Runs `npm run dev` and validation commands
- Coordinates the build→screenshot→fix loop between workers
- Edits docs and plans directly

### Workflow Sequence
```
Supervisor: "Worker 1, extract navbar CSS tokens"
Worker 1:   → runs Sniper CSS scripts → returns token JSON
Supervisor: "Worker 2, build Navbar.tsx with these exact values: {tokens}"
Worker 2:   → writes Navbar.tsx
Supervisor: runs `npm run dev`
Supervisor: "Worker 1, screenshot localhost:5173 and compare with original"  
Worker 1:   → screenshots both → reports deltas
Supervisor: "Worker 2, fix these deltas: {list}"
Worker 2:   → updates component
... repeat until checklist passes ...
```

This separation ensures the **coder never guesses** (it gets exact values) and the **verifier is independent** (it doesn't judge its own work).

---

## 11. Lessons Learned: Real-World Clone Session (Xtract.framer.ai)

These are hard-won lessons from a complete end-to-end clone session. Follow this and you can clone any landing page hero in **under 1 hour**.

### The Fastest Path: Single Browser-Use Worker (GPT 5.5)

We initially planned two workers (browser-use for research + coding worker for implementation). **The simplest and fastest approach is one browser-use worker (GPT 5.5) that does everything:**

1. Navigates to the target and extracts CSS tokens via `javascript_tool`
2. Extracts SVG assets and saves them via `bash`
3. Scaffolds the project and writes all components
4. Starts the dev server, opens the clone in a new tab
5. Screenshots both tabs and compares them
6. Fixes deltas and re-screenshots until it matches

**GPT 5.5 in browser-use mode is the best model for this task** — it can both write visual UI code AND see the results. One worker, one loop, fast convergence.

### The Exact Session Sequence That Works

```
Step 1: Research & Extract (3 min)
  └─ Navigate to target → resize 1440x1400 → screenshot
  └─ Run 6-8 Sniper CSS scripts (navbar, h1, buttons, badge, description, orbs, trust bar)
  └─ Extract SVG logo assets (data-URI decode)
  └─ Result: Complete design token sheet

Step 2: Build (3 min)
  └─ Scaffold Vite + React + Tailwind
  └─ Configure fonts (e.g. Figtree via Google Fonts)
  └─ Create all components in one pass with exact token values
  └─ npm run build → verify no errors
  └─ npm run dev → open clone in browser tab

Step 3: Compare & Fix (4 min, 2-3 rounds)
  └─ Round 1: Screenshot clone + original → identify top 8-10 deltas → fix all in one pass
  └─ Round 2: Re-screenshot → identify top 3-5 remaining → fix
  └─ Round 3 (if needed): Final pixel adjustments

Total: ~10 minutes for a production-quality hero clone
```

### What the Build→Screenshot→Fix Loop Actually Looks Like

Each round follows this exact pattern:

```
1. Worker screenshots clone at localhost:5173 (tab 2)
2. Worker screenshots original at target URL (tab 1)
3. Worker compares and reports specific deltas with pixel positions:
   "H1 is 15px too high (clone y=579, original y=589)"
   "Nav links gap is 16px, should be 26px"  
   "Star field is tiled/grid pattern, needs random placement"
4. Supervisor sends targeted fixes with exact values
5. Worker applies all fixes in one pass
6. Repeat from step 1
```

**Key insight: the comparison report must include PIXEL POSITIONS**, not vague descriptions. "Button is too wide" is useless. "Button is 116px wide, should be 90px" is actionable.

### Top 10 Things That Go Wrong (And How to Fix Them Fast)

| # | What Goes Wrong | How We Fixed It | Time Saved |
|---|----------------|-----------------|------------|
| 1 | **Logo is CSS-approximated** instead of real SVG | Extract the actual SVG from the page with `javascript_tool` → `outerHTML` → save to file | 15 min |
| 2 | **Navbar button has an unwanted arrow** | Pass `showArrow={false}` prop — make arrow opt-in, not default | 2 min |
| 3 | **Nav links are too compressed** | Extract exact link positions from original, calculate gap (~26px not 16px) | 5 min |
| 4 | **Star field looks tiled/grid-like** | Replace CSS `radial-gradient` pattern with 150 randomly-positioned absolute `<div>` dots using deterministic seed | 10 min |
| 5 | **Hero content is 15-20px too high** | Adjust top padding incrementally (180→200→210px) guided by screenshot comparison | 3 min |
| 6 | **Purple glow is too ring-like** | The original uses TWO overlapping gradient divs at DIFFERENT angles — extract each separately | 10 min |
| 7 | **Button text arrows are ugly ↗ glyphs** | Replace with proper SVG `<path>` arrow icons | 5 min |
| 8 | **Button width doesn't match** | Remove forced width, add `whitespace-nowrap`, fine-tune padding | 3 min |
| 9 | **View services button has arrow but original doesn't** | Check EACH button individually — don't assume both have same treatment | 2 min |
| 10 | **Trust logos return nothing from `img` queries** | They're CSS `background-image` data URIs on `<div>`s — use Script 7 | 10 min |

### Component Architecture That Works

```
src/
  components/
    layout/
      Navbar.jsx          # Logo (real SVG import) + links + CTA button
    sections/
      Hero.jsx            # Orchestrates: DecorativeGlow + StarField + Badge + content + TrustCarousel
    ui/
      Badge.jsx           # Outer pill + inner colored pill + text
      Button.jsx          # Accepts variant="primary"|"dark", showArrow prop
  assets/
    media/
      xtract-logo.svg     # Extracted real logo
      logo-1..N.svg       # Trust carousel logos (decoded from data URIs)
```

**Key design decisions:**
- **`showArrow` prop on Button** — navbar button has no arrow, primary CTA has arrow, secondary CTA has no arrow. Make it opt-in.
- **`variant` prop on Button** — "primary" (purple bg) vs "dark" (translucent dark bg). Same shadow, different background.
- **StarField as a component** — uses `useMemo` with deterministic seed so stars don't re-randomize on re-render.
- **DecorativeGlow as a component** — two absolutely-positioned gradient divs inside a parent with opacity + blur.
- **TrustCarousel** — repeats logo array 4x for infinite scroll effect, uses CSS animation.

### Token-to-Tailwind Cheat Sheet

These exact mappings were verified against the live site:

```jsx
// Heading
className="text-[70px] font-semibold leading-[77px] tracking-[-2.2px] max-w-[900px] text-center text-white"

// Description  
className="text-lg font-medium leading-[27px] tracking-[-0.36px] max-w-[600px] text-center text-[#CCCCCC]"

// Nav links
className="text-sm font-medium leading-[16.8px] tracking-[-0.28px] text-white"

// Brand name
className="text-[21px] font-bold leading-[25.2px] tracking-[-1.26px] text-white"

// Primary button
className="rounded-[6px] px-[13px] py-[9px] bg-[#814AC8] text-white text-[15px] font-medium"
style={{ boxShadow: "rgba(0,0,0,0.15) 0px 0.71px 0.71px -0.625px, ..." }}

// Dark button  
className="rounded-[6px] px-[13px] py-[9px] bg-[rgba(13,13,13,0.8)] text-white text-[15px] font-medium"

// Badge outer pill
className="rounded-[20px] bg-[rgba(13,13,13,0.8)] px-[10px] py-[2px] pl-[2px] flex items-center gap-[5px]"

// Badge inner "New" pill
className="rounded-[12px] bg-[#814AC8] px-[8px] py-[4px] text-sm font-medium text-white"

// Gradient orb (outer, 406px)
className="rounded-full bg-[linear-gradient(229deg,#DF7AFE_13%,transparent_35%,transparent_64%,#814AC8_88%)]"
// Size: w-[406px] h-[406px]

// Gradient orb (inner, 300px)  
className="rounded-full bg-[linear-gradient(141deg,#DF7AFE_13%,transparent_35%,transparent_64%,#814AC8_88%)]"
// Size: w-[300px] h-[300px]

// Glow wrapper
className="opacity-60 blur-[10px]"
```

### Animation Cloning: The GIF Capture Method

Animations are invisible to static CSS extraction. Use the built-in `gif_creator` tool to record and analyze them:

**Step 1: Capture the entrance animation**
```
gif_creator(tab_id=1, action="start_recording")
computer(tab_id=1, action="screenshot")              // pre-animation state
navigate(tab_id=1, url="https://target.site/")       // hard-refresh triggers entrance anim

// Rapid screenshot burst — 10-12 frames over ~6 seconds
computer(tab_id=1, action="wait", duration=0.3)
computer(tab_id=1, action="screenshot")
computer(tab_id=1, action="wait", duration=0.5)
computer(tab_id=1, action="screenshot")
// ... repeat 8-10 more times with 0.5-1.0s waits ...

gif_creator(tab_id=1, action="stop_recording")
gif_creator(tab_id=1, action="export", download=true, filename="entrance-animation.gif")
```

**Step 2: Analyze the frames**
For each frame, identify:
- Which elements are visible/invisible
- Animation type per element (fade, slide-up, scale, blur-to-sharp)
- Approximate timing and stagger order
- Continuous vs one-shot animations

**Step 3: Map to Framer Motion**

Common Framer site animation patterns discovered from the Xtract clone:

| Element | Animation | Timing | Framer Motion |
|---------|-----------|--------|---------------|
| Purple glow | Appears first, continuous morph/rotation | 0s (always visible) | CSS `@keyframes` or `animate={{ rotate: 360 }}` with `repeat: Infinity` |
| Navbar | Slide down + fade in | ~0.1-0.3s | `initial={{ y: -20, opacity: 0 }} animate={{ y: 0, opacity: 1 }}` |
| Badge ("New") | Fade + scale in | ~0.3-0.5s | `initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }}` |
| H1 heading | Fade in + slide up | ~0.4-0.6s | `initial={{ y: 30, opacity: 0 }} animate={{ y: 0, opacity: 1 }}` |
| Description | Fade in + slide up | ~0.5-0.7s | Same pattern, staggered |
| CTA buttons | Fade in + slide up | ~0.6-0.8s | Same pattern, staggered |
| Stars | Fade in | ~0.2-0.5s | `initial={{ opacity: 0 }} animate={{ opacity: 0.5 }}` |

**Key insight:** Most Framer hero animations use a simple **staggered fade-up** pattern. The glow/orb is the only continuously animated element.

```jsx
// Staggered entrance — covers 90% of Framer hero animations
import { motion } from 'framer-motion';

const container = {
  hidden: {},
  visible: { transition: { staggerChildren: 0.12, delayChildren: 0.1 } }
};

const fadeUp = {
  hidden: { opacity: 0, y: 30 },
  visible: { 
    opacity: 1, y: 0,
    transition: { duration: 0.6, ease: [0.25, 0.46, 0.45, 0.94] }
  }
};

<motion.div variants={container} initial="hidden" animate="visible">
  <motion.div variants={fadeUp}><Badge /></motion.div>
  <motion.div variants={fadeUp}><h1>...</h1></motion.div>
  <motion.div variants={fadeUp}><p>...</p></motion.div>
  <motion.div variants={fadeUp}><Buttons /></motion.div>
</motion.div>
```

### The "Clone Any Hero" Speedrun Prompt

Copy-paste this to a browser-use agent (GPT 5.5) to clone any hero section:

```
Clone the hero section of [TARGET_URL].

1. Navigate to the target. Resize to 1440x1400. Screenshot.

2. Extract ALL design tokens using javascript_tool:
   - Page background color
   - Navbar: bg, height, padding, link styles (use TreeWalker for real text styles)
   - H1: font-family, size, weight, line-height, letter-spacing, color, max-width
   - Description: same properties
   - Buttons: bg, color, padding, border-radius, box-shadow (capture ALL layers)
   - Badge/tags: structure, bg, border-radius, padding
   - Decorative elements: gradients, transforms, blur, opacity
   - Trust/logo bar: text styles + logo extraction (check data-URI backgrounds!)

3. Extract assets:
   - Logo SVG: querySelector('svg').outerHTML → save to file
   - Trust logos: filter divs by backgroundImage data:image → decode → save
   
4. Scaffold: npm create vite@latest . -- --template react && npm install tailwindcss @tailwindcss/vite

5. Build ALL components in one pass using extracted tokens.
   Map every value to Tailwind arbitrary values: text-[70px], tracking-[-2.2px], etc.

6. Start dev server. Open clone in new tab. Screenshot both.
   Compare and fix. Repeat 2-3 times until matching.
```

---

*Battle-tested on xtract.framer.ai. Cloned hero section in ~10 minutes using a single GPT 5.5 browser-use worker. The build→screenshot→fix loop converged in 2-3 rounds. When in doubt: screenshot first, snipe second, never guess the math.*
