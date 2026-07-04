# Landing Page Hero Clone — Concise Playbook v2

> **TL;DR:** Two-agent setup (browser-use + video), discover before you build, reverse-engineer everything, write a plan, then implement in one sprint.
> **Use Part 2 for details:** `docs/clone_guide_v2_part2.md` contains deeper scripts, prompts, responsive checks, animation reverse engineering, and deployment troubleshooting.
> **Battle-tested on:** xtract.framer.ai, hydradb.com

---

## 1. Agent Setup

You need **two browser-use workers** orchestrated by the AdaL Engineer supervisor: a **Builder** and an **Evaluator**. They are NEVER the same worker — the builder cannot evaluate its own output. They must be separate sessions, ideally different models/providers for cross-blind-spot coverage.

> **Note:** The browser-use agent mode now has video analysis built in. A single browser-use worker can record, scrub, and describe animation timing/easing/stagger on its own — there is no longer a separate Video Agent. The second worker is now an adversarial **Evaluator**, not a video analyzer.

### Worker 1 — Builder (Browser-Use): Discovery + Animation Analysis + Coding

```
# Start worker (model/mode set at boot — do NOT switch mid-session)
adal_worker_start(
  work_dir="/path/to/project",
  command=["adal", "--yolo", "--model", "google-gemini-3.5-flash", "--agent-mode", "browser-use"],
  launch_mode="attach",
  alias="builder"
)
```

**Mandatory setup gate:** before delegating any discovery, design, or build work, verify the builder worker is in `browser-use` mode and on the chosen model (configured at boot via `--agent-mode browser-use` and `--model <slug>`). Do not start the clone if this mode setup has not been confirmed.

**Role:** One agent does the full visual loop — navigate target site, take the screenshot matrix, extract CSS/fonts/assets via `javascript_tool`, run the animation scanner, AND analyze screen recordings/GIFs of the hero animation (timing, easing, entrance directions, stagger, visual effects) using its built-in video analysis capability. Then scaffold and build the clone. It both sees and writes code.

### Worker 2 — Evaluator (Browser-Use): Adversarial Visual Verification

```
# Start second worker — SEPARATE session, adversarial role
adal_worker_start(
  work_dir="/path/to/project",
  command=["adal", "--yolo", "--model", "google-gemini-3.5-flash", "--agent-mode", "browser-use"],
  launch_mode="attach",
  alias="evaluator"
)
```

**Mandatory setup gate:** the evaluator must be a DIFFERENT worker, DIFFERENT session (ideally different model/provider than the builder) with an adversarial prompt. It never builds; it only proves the clone correct or broken.

**Role:** After the builder finishes, the evaluator opens the live target site and the clone in separate tabs, screenshots both at every required viewport (1440×1400, 1920×1200, mobile), compares pixel positions/colors/fonts/animation timing/content verbatim, and reports every failure with severity + file/line. Its system belief is "this clone is broken — prove it." It never rubber-stamps.

### Planning Contract (before any clone code)

Before the builder writes a single line of clone code, run the planning loop:

1. **Builder** investigates the repo + discovery findings and writes `team-log/builder_plan.md` (implementation approach, files to touch, component breakdown, font/animation strategy, build validation, questions).
2. **Evaluator** studies the target + discovery and writes `team-log/test_plan.md` (visual fidelity matrix, animation verification, content exactness, design-token assertions, code-review risks, responsive edge cases).
3. **Engineer** mediates — sends each plan to the other worker for critique, adjudicates disagreements, then writes the final `team-log/contract.md` with status `Approved to Build`.
4. **Builder** may start coding only when the contract is accepted. The evaluator evaluates only after the builder reports done.

The four canonical files live in `team-log/`: `builder_plan.md`, `test_plan.md`, `contract.md`, `eval_round_N.md`. Do not invent other variants.

---

## 2. The Process — 4 Phases

### Phase 1: Visual Discovery (10 min)

**Goal:** Understand what you're cloning before touching code.

#### A. Static Analysis (Browser-Use Worker)

1. **Navigate + Screenshot Matrix**

   Always capture the target at multiple sizes before coding. Do not optimize only for the first screenshot.

   | Viewport | Purpose | Required? |
   |---|---|---|
   | `1440×1400` | Primary desktop comparison target | Always |
   | `1920×1200` or larger | Detects false fixed-left layouts and max-width issues | Always |
   | `390×844` or `430×932` | Mobile hero layout and nav behavior | Always unless user explicitly says desktop-only |
   | Initial-load clip/screenshot | Captures entrance animation | If animation matters |
   | Settled screenshot after 8–12s | Captures final resting layout | Always |

   ```
   navigate("https://target-site.com/")
   resize_window(tab_id=1, width=1440, height=1400)
   wait 8-10 seconds (animations settle)
   scroll to top
   screenshot

   resize_window(tab_id=1, width=1920, height=1200)
   wait 2 seconds
   screenshot

   resize_window(tab_id=1, width=390, height=844)
   wait 2 seconds
   screenshot
   ```

2. **Extract Design Tokens** — Use targeted `javascript_tool` calls. NEVER dump full `getComputedStyle`.
   - **Typography:** fontFamily, fontSize, fontWeight, letterSpacing, lineHeight, color (use TreeWalker for Framer sites)
   - **Colors:** backgrounds, accents, text colors
   - **Buttons:** bg, text color, border-radius, padding, boxShadow (verbatim)
   - **Layout:** container max-width, section heights, gaps, padding
   - **Nav:** links, logo, button styles

3. **Extract Assets**
   - Logo SVG: inspect the nav/header area only; do not blindly use the first `document.querySelector('svg')`
   - Data-URI backgrounds: check `backgroundImage` on divs (Framer logo trick)
   - Font files: search `@font-face` rules and `performance.getEntriesByType('resource')` for `.woff2` URLs
   - Self-host extracted fonts in `assets/fonts/`
   - For detailed extraction scripts, use `docs/clone_guide_v2_part2.md`

#### B. Animation Detection & Analysis

The goal is to **detect whether animation exists** and **identify what powers it**. Don't assume canvas = animation. Landing page animations come from many sources.

4. **Step 1 — Detect ALL animated elements.** Run this comprehensive scanner:
   ```javascript
   (() => {
     const results = { animations: [], tech: {}, elements: {} };

     // --- A. CSS Animations & Transitions ---
     // Find elements with active CSS animations or transitions
     const allEls = document.querySelectorAll('*');
     const cssAnimated = [];
     allEls.forEach(el => {
       const s = getComputedStyle(el);
       if (s.animationName && s.animationName !== 'none') {
         cssAnimated.push({
           tag: el.tagName, class: el.className?.toString().slice(0, 60),
           animation: s.animationName, duration: s.animationDuration
         });
       }
       if (s.transition && s.transition !== 'all 0s ease 0s' && s.transition !== 'none') {
         // Only flag if element also has transform/opacity that suggests active animation
         if (s.willChange !== 'auto' || s.transform !== 'none' || parseFloat(s.opacity) < 1) {
           cssAnimated.push({
             tag: el.tagName, class: el.className?.toString().slice(0, 60),
             transition: s.transition.slice(0, 100), willChange: s.willChange
           });
         }
       }
     });
     results.animations.push({ type: 'css', count: cssAnimated.length, samples: cssAnimated.slice(0, 5) });

     // --- B. Canvas elements (2D or WebGL) ---
     const canvases = document.querySelectorAll('canvas');
     results.elements.canvas = Array.from(canvases).map(c => ({
       width: c.width, height: c.height,
       ariaLabel: c.getAttribute('aria-label'),
       role: c.getAttribute('role'),
       parentDataAttrs: Object.fromEntries(
         [...(c.closest('[data-us-project],[data-scene-id]')?.attributes || [])]
           .filter(a => a.name.startsWith('data-')).map(a => [a.name, a.value])
       ),
       rect: (() => { const r = c.getBoundingClientRect(); return { x: r.x|0, y: r.y|0, w: r.width|0, h: r.height|0 }; })()
     }));

     // --- C. Video elements ---
     const videos = document.querySelectorAll('video');
     results.elements.video = Array.from(videos).map(v => ({
       src: v.src || v.querySelector('source')?.src || 'none',
       autoplay: v.autoplay, loop: v.loop, muted: v.muted,
       rect: (() => { const r = v.getBoundingClientRect(); return { x: r.x|0, y: r.y|0, w: r.width|0, h: r.height|0 }; })()
     }));

     // --- D. SVG animations (SMIL or CSS-animated SVGs) ---
     const animatedSvgs = document.querySelectorAll('svg animate, svg animateTransform, svg animateMotion');
     results.elements.svgAnimations = animatedSvgs.length;

     // --- E. Lottie containers (typically a div with a specific player or canvas) ---
     results.elements.lottie = document.querySelectorAll('lottie-player, dotlottie-player, [class*="lottie"]').length;

     // --- F. Rive containers ---
     results.elements.rive = document.querySelectorAll('canvas[class*="rive"], [data-rive-src]').length;

     // --- G. Spline containers ---
     results.elements.spline = document.querySelectorAll('canvas[data-engine="spline"]').length;

     // --- H. iframes (could embed anything — Spline, Rive, Figma prototypes) ---
     const iframes = document.querySelectorAll('iframe');
     results.elements.iframes = Array.from(iframes).map(f => ({
       src: f.src?.slice(0, 150), rect: (() => { const r = f.getBoundingClientRect(); return { x: r.x|0, y: r.y|0, w: r.width|0, h: r.height|0 }; })()
     }));

     // --- I. Detect JS animation libraries via globals ---
     results.tech.gsap = typeof window.gsap !== 'undefined';
     results.tech.threeJS = typeof window.THREE !== 'undefined';
     results.tech.lottie = typeof window.lottie !== 'undefined';
     results.tech.rive = typeof window.rive !== 'undefined';
     results.tech.anime = typeof window.anime !== 'undefined';
     results.tech.mojs = typeof window.mojs !== 'undefined';
     results.tech.velocity = typeof window.Velocity !== 'undefined';
     results.tech.popmotion = typeof window.popmotion !== 'undefined';
     results.tech.unicornStudio = typeof window.UnicornStudio !== 'undefined';
     results.tech.spline = typeof window.SPE !== 'undefined';
     results.tech.pixiJS = typeof window.PIXI !== 'undefined';
     results.tech.p5 = typeof window.p5 !== 'undefined';

     // --- J. Check loaded scripts for animation library signatures ---
     const scriptUrls = performance.getEntriesByType('resource')
       .filter(r => r.name.match(/\.(js|mjs)$/i))
       .map(r => r.name)
       .filter(s => !s.includes('google') && !s.includes('analytics') && !s.includes('gtm'));
     const animLibSignatures = ['gsap', 'three', 'lottie', 'rive', 'anime', 'framer-motion',
       'popmotion', 'unicorn', 'spline', 'pixi', 'p5', 'mo.js', 'velocity', 'scroll-trigger',
       'locomotive', 'barba', 'swiper'];
     results.tech.animationScripts = scriptUrls.filter(url =>
       animLibSignatures.some(sig => url.toLowerCase().includes(sig))
     );
     results.tech.totalScripts = scriptUrls.length;

     // --- K. Framer-specific: check for appear/entrance animation configs ---
     const framerAppear = document.querySelectorAll('[data-framer-appear-id]');
     results.tech.framerAppearElements = framerAppear.length;
     if (framerAppear.length > 0) {
       results.tech.framerAppearSample = Array.from(framerAppear).slice(0, 3).map(el => ({
         id: el.getAttribute('data-framer-appear-id'),
         style: { opacity: el.style.opacity, transform: el.style.transform }
       }));
     }

     return JSON.stringify(results, null, 2);
   })()
   ```

5. **Step 2 — Interpret results.** Use this decision tree:

   | What you found | Animation Tech | How to replicate |
   |---|---|---|
   | `tech.unicornStudio: true` + canvas with `data-us-project` | **Unicorn Studio** (WebGL shader scenes) | Embed: load their runtime JS + init with same project ID |
   | `tech.threeJS: true` + canvas | **Three.js** (3D WebGL) | Capture as looping video, or re-implement if simple |
   | `tech.lottie: true` or `elements.lottie > 0` | **Lottie** (After Effects → JSON) | Find the `.json` file in network tab, use `lottie-react` |
   | `tech.gsap: true` | **GSAP** (scroll/timeline animations) | Re-implement with GSAP or translate to Framer Motion |
   | `elements.rive > 0` or `tech.rive: true` | **Rive** (interactive vector) | Find `.riv` file, use `@rive-app/react-canvas` |
   | `tech.spline: true` or `elements.spline > 0` | **Spline** (3D web scenes) | Embed via iframe or `@splinetool/react-spline` |
   | `tech.pixiJS: true` | **PixiJS** (2D WebGL) | Capture as video or re-implement |
   | `elements.video` with autoplay+loop | **Pre-rendered video** background | Download the MP4/WebM and embed |
   | `elements.svgAnimations > 0` | **SVG SMIL animation** | Copy the SVG markup including `<animate>` elements |
   | `tech.framerAppearElements > 0` + CSS transitions | **Framer entrance animations** | Extract delays/durations, rebuild with Framer Motion |
   | CSS animations only, no libraries | **Pure CSS** | Extract `@keyframes` and `animation` properties |
   | `elements.iframes` with Spline/Figma/external src | **Embedded iframe** | Embed the same iframe or find the underlying asset |
   | Nothing detected but things move | **Scroll-driven CSS** or **IntersectionObserver** | Check for `scroll-timeline`, `animation-timeline`, or custom JS observers |

6. **Step 3 — Record for Video Agent** (optional but valuable):
   - Use screen recording to capture a short GIF/video of the hero animation
   - Send to Video Agent worker: "Describe the animation: entrance sequence, timing, easing, stagger pattern, duration, any looping behavior"
   - The Video Agent excels at describing **what** animates (order, direction, speed) which is hard to extract from static DOM inspection

#### C. Deep Source Inspection

7. **If animation is embeddable** (Unicorn Studio, Lottie, Rive):
   - Find the project/scene ID from data attributes
   - Find the runtime script URL
   - Extract the embed configuration
   - Plan to embed directly rather than re-implementing

8. **If animation needs re-implementation:**
   - Extract Framer appear animation configs from the main script
   - Map entrance animations: delays, durations, directions, easing
   - Identify stagger patterns and spring physics

### Phase 2: Write the Clone Plan (5 min)

Create `docs/clone_plan.md` with:

```markdown
# Clone Plan: [Site Name]

## Target
- URL: https://...
- Scope: Hero section only
- Viewports: 1440×1400, 1920×1200+, mobile 390×844/430×932 unless explicitly out of scope

## Tech Stack Discovery
- Framework: [Framer / Webflow / Custom]
- Animation: [Unicorn Studio / Three.js / Lottie / CSS / etc.]
- Fonts: [Font names + source URLs]

## Design Tokens
- Colors: [list with hex values]
- Typography: [h1, body, nav specs]
- Layout: [container width, heights, gaps]

## Assets to Extract
- [ ] Logo SVG
- [ ] Font files (self-host)
- [ ] Canvas/animation (embed or capture)
- [ ] Background images/videos

## Animation Strategy
- Hero entrance: [describe stagger sequence]
- Canvas/WebGL: [embed vs re-implement]
- Hover effects: [describe]

## Implementation Plan
1. Scaffold Vite + React + Tailwind
2. Build Navbar component
3. Build Hero component
4. Integrate animation
5. Polish + compare
```

### Phase 3: Build (15-20 min)

Use the browser-use worker for everything — it can both code and visually verify.

1. **Scaffold** — `npm create vite@latest . -- --template react`, install Tailwind v4, set `base` for GitHub Pages
2. **Build Components** — Navbar, Hero, with extracted design tokens
3. **Integrate Animation** — Embed or re-implement based on Phase 1 findings
4. **Add Framer Motion** — Entrance animations, hover effects, scroll triggers
5. **Center Layout** — Always use `max-w-[Xpx] mx-auto` for large-screen centering

### Phase 4: Compare & Polish — EVALUATOR'S JOB (not the builder's)

> The builder does NOT self-evaluate. After the builder reports "done" (build + lint pass, files listed), the **Evaluator worker** (separate browser-use session, adversarial prompt) owns this entire phase. The builder's job ends at "compiles and renders without console errors."

1. **Side-by-side comparison** — The Evaluator opens original and clone in separate tabs
2. **Compare all required viewports** — desktop `1440×1400`, large desktop `1920×1200+`, and mobile `390×844`/`430×932` unless mobile is explicitly out of scope
3. **Measure pixel differences** — Evaluator uses `javascript_tool` to compare element positions, computed styles, content verbatim
4. **Report failures** — Evaluator writes `team-log/eval_round_N.md` with pass/fail per acceptance criterion, severity, evidence, and file+line to fix
5. **Iterate** — Engineer sends failures back to the Builder; Builder fixes; Evaluator re-verifies. Repeat until ACCEPT.
6. **Deploy** — Only after the Evaluator returns ACCEPT: commit, push, verify GitHub Pages

**Builder rule (enforce in every builder brief):** "Do NOT self-evaluate, do NOT write any eval report, do NOT judge visual fidelity. Run build + lint and report files changed. Evaluation is the Evaluator's job."

---

## 3. Key Learnings & Gotchas

### Font Extraction
- Framer fonts show as `"FontName Placeholder"` — ignore the placeholder
- Extract actual `.woff2` URLs from `@font-face` rules or `performance.getEntriesByType('resource')`
- Self-host in `assets/fonts/` with `@font-face` in your CSS
- If the exact font is commercial/unavailable, pick the closest Google Fonts alternative

### Framer DOM Gotchas
- **Text styles are deeply nested** — use TreeWalker to find the real styled node
- **Logos are often CSS `background-image` data-URIs**, not `<img>` tags
- **Buttons render text twice** for hover animations — dedupe
- **`getComputedStyle` on outer elements shows browser defaults**, not the real style

### Layout
- Never use fixed `ml-[65px]` — use `max-w-[Xpx] mx-auto` for centering
- The original may look left-aligned at 1440px but it's actually centered at larger widths
- Always test at 1440px, 1920px+, and mobile width unless the user explicitly says desktop-only

### Animation Embedding
- **Unicorn Studio:** Embed with `data-us-project` attribute + load their runtime JS + call `UnicornStudio.init()`
- **Keep a static fallback** (screenshot of the animation) for loading states
- **Framer Motion entrance animations:** Use staggered `initial` + `animate` with incremental delays
- **Always add hover micro-interactions** — they make the clone feel alive

### Canvas/WebGL
- Canvas elements can't be exported via `toDataURL()` if they're WebGL (context locked)
- Use cropped screenshots as static fallbacks
- Check `canvas.getContext('2d')` vs `getContext('webgl')` to determine type
- Look for `aria-label` on canvas — libraries like Unicorn Studio label their canvases

---

## 4. Deployment Checklist

- [ ] `vite.config.js` has `base: '/repo-name/'`
- [ ] `.github/workflows/deploy.yml` configured for GitHub Pages
- [ ] GitHub Pages enabled via `gh api repos/OWNER/REPO/pages -X POST -f build_type=workflow`
- [ ] `npm run build` passes
- [ ] Committed and pushed to main
- [ ] Workflow run succeeded

---

## 5. Quality Checklist (Evaluator-owned — the builder does NOT self-verify these)

- [ ] Font matches original (or closest alternative documented)
- [ ] Colors match (extracted hex values, not eyeballed)
- [ ] Layout centers on large screens
- [ ] Mobile hero/nav behavior is checked or explicitly marked out of scope
- [ ] Nav structure matches (links, buttons, logo)
- [ ] Hero text content is exact
- [ ] Buttons have correct styles (bg, text, border-radius, padding)
- [ ] Animation plays on load (entrance stagger)
- [ ] Canvas/WebGL animation runs (if applicable)
- [ ] Hover effects work (buttons, nav links)
- [ ] Orange/accent separators and decorative elements present
- [ ] Screenshot comparison at 1440×1400 shows 90%+ fidelity
- [ ] Screenshot comparison at 1920×1200+ confirms centered/large-screen fidelity
- [ ] Mobile screenshot comparison passes or mobile is explicitly out of scope
