# Agentic Premium Web Methodology

Use for premium websites, high-converting landing pages, founder-led pages, booking/payment pages, and any artifact where "beautiful" must also mean "commercially clear".

## 3D pipeline

Do not start with pixels or code. Use:

1. **Design**: define the visual system and conversion path.
2. **Development**: build the artifact while preserving hierarchy, copy, states, and responsive behavior.
3. **Deployment / Delivery**: verify the actual user path and final screenshots.

Skipping Design creates AI slop: generic hero, random cards, purple gradients, fake proof, weak CTA, and mobile compression.

## Context engineering

Better design comes from precise context, not huge context.

- Do not use broad whole-project context unless architecture truly requires it.
- Reference exact files, screenshots, sections, brand assets, and copy blocks.
- Split large work into `YOLO small` loops: small change -> render -> screenshot -> refine.
- Do not combine hero, pricing, backend, motion, analytics, and payment work in one blind pass unless the task explicitly requires a full rebuild.
- Keep one short handoff after long iterations: changed, checked, unresolved.

If the agent starts changing unrelated sections, adding dependencies, or altering product logic for a visual task, narrow scope immediately.

## Rule architecture

Do not rely on one giant prompt for repeatable design quality.

- Read existing `AGENTS.md`, `design.md`, tokens, component docs, and local conventions first.
- Keep visual rules separate from backend, database, security, and deployment rules.
- Use nested `AGENTS.md` for Codex-compatible local subtree guidance.
- Use `.cursor/rules/*.mdc` in Cursor-compatible projects when path-scoped rules are useful; avoid monolithic `.cursorrules` for mixed tasks.
- Turn repeated workflows such as premium landing audit, screenshot loop, or component injection into `SKILL.md`/reference docs.

Good rules narrow the agent where consistency matters without flooding the context with unrelated instructions.

## Design phase checklist

Before a serious landing/prototype build, define:

```md
Audience:
Offer:
Primary action:
Secondary action:
Proof assets:
Founder / product signal:
Visual mood:
Typography:
Palette:
Surface model:
Radius / spacing:
Motion rules:
Anti-patterns:
```

If this becomes a real project, turn it into a `design.md`-style source of truth.

## Content-first

Do not design premium landing pages around placeholder text.

Before layout:

- write the real H1, subheadline, CTA, pricing language, risk reversal, FAQ, and success/next-step copy;
- identify objections and proof needs;
- then design spacing, grid, and typography around real text length.

If copy changes after visual layout, re-check line breaks, card height, mobile composition, and CTA visibility.

## Extract -> Generate -> Polish stack

The strongest AI web workflow is a chain, not one generator:

1. **Extract**: from URL, screenshot, Figma, brand material, or existing app, capture tokens, spacing, type hierarchy, surface model, brand voice, and CTA semantics.
2. **Generate**: build sections/components in the current stack and design system.
3. **Polish / Review**: run taste layer, conversion copy review, anti-slop pass, WCAG/mobile checks, visual diff or screenshot QA.

Do not start with a generator if tokens, real copy, proof assets, and CTA path are unclear. That is where generic output begins.

## 40/20/40 effort model

Do not treat one-shot generation as production work.

- **40% Inspiration & Planning**: audience, offer architecture, references, content-first copy, design system, proof strategy.
- **20% Structural Build**: sections, components, forms, routing/basic interactions, responsive skeleton.
- **40% Polish Phase**: typography, spacing, media crop, microinteractions, mobile, performance, browser QA.

The expensive-looking result usually appears in the polish phase, not in the first generated draft.

## SPARC-style control

Use SPARC as a lightweight guardrail for autonomous agents:

- **Specify**: task, audience, CTA, constraints, non-scope.
- **Plan**: split into small independent steps.
- **Architect**: choose structure, components, state boundaries, rules/docs, verification path.
- **Refine**: inspect output, logs, and screenshots after each step; fix narrowly.
- **Complete**: only finish after visual gates, user path, and handoff are clear.

For small tasks, this can be an internal checklist. For large tasks, write it into the plan/project docs.

## CRO hierarchy

For sales pages, conversion mechanics outrank decoration:

- one primary CTA;
- visible post-click path: form, payment, booking, Telegram/CRM, success;
- founder proof or product proof near the decision point;
- risk reversal: what is fixed, what is paid, what happens next, what is not promised;
- proof before polish: real screenshots, videos, cases, public links beat decorative mockups;
- sticky mobile CTA can help, but must not cover price, payment, form, or final CTA;
- long copy belongs in accordions when it blocks the decision path.

## Visual prompting

Avoid vague prompts like "make it premium". Use visual evidence:

- screenshots, brand assets, product screenshots, real photos, competitor/reference pages;
- extract properties: grid, rhythm, typography, contrast, spacing, surface depth, motion pattern;
- do not clone another brand 1:1;
- after render, compare screenshot to goal/reference and fix named differences.

If no references exist, define the visual direction explicitly before building.

## Measurable UI gates

Premium UI still needs objective checks:

- body text contrast should meet WCAG AA, usually `>= 4.5:1`;
- large text and meaningful UI graphics should usually be `>= 3:1`;
- important mobile touch targets should be around `44x44px` or larger;
- simple state transitions usually belong around `150-300ms`;
- support reduced-motion fallbacks where motion is meaningful;
- keep long reading lines roughly within `45-75` characters;
- never cover faces, product details, prices, forms, CTAs, or proof with labels/widgets/overlays.

If the screen looks expensive but fails these gates, keep polishing.

## Vertical style heuristics

Choose visual language by audience and offer:

- SaaS / Tech / AI: bento/minimal/AI-native, disciplined glow, cold accents, strong hierarchy.
- Fintech / B2B / Ops: clean grids, trusted colors, readable numbers, minimal decorative motion.
- Beauty / Lifestyle: soft surfaces, delicate shadows, serif contrast, gentle reveals.
- Luxury / Ecommerce: media-first spatial minimalism, restrained monochrome/metal accents, no chaotic sale noise.

Treat these as heuristics, not brand truth.

## Generator and component injection

UI generators and component libraries are accelerators, not strategy.

- Use generated scaffolds or premium components for structure and hard interaction patterns.
- Adapt them to local tokens, copy, CTA path, accessibility, and responsive rules.
- Avoid default bias: do not use React/Tailwind/shadcn/3D/motion just because a generator defaults to it.
- Treat imported premium components as third-party code: check dependencies, bundle impact, a11y, responsiveness, and visual fit.

The agent's best role is assembler/integrator: use mature patterns, remove excess, and fit them into the product system.

## Tool/repo selection protocol

Use GitHub catalogs, awesome lists, MCP registries, and skill packs as discovery, not truth.

Before using a repo/tool:

- check live README, update date, license, installation path, dependencies, examples/demo, and issues where relevant;
- do not infer missing forks, license, or demo links;
- classify the tool: design workspace, extractor, design-to-code bridge, rules/skills pack, landing generator, copy system, or visual QA;
- choose by pipeline stage, not popularity;
- prefer local-first/BYOK/multi-model only when privacy, cost control, or offline autonomy matter.

Selection map:

- reference -> code: extractor / screenshot-to-code / Figma bridge;
- idea -> MVP landing: design workspace or landing generator;
- generic copy/visuals: taste layer / copy critique / anti-slop review;
- pixel/brand fidelity: visual diff, screenshot loop, design tokens;
- production: generator + QA + lead/payment smoke, not just HTML preview.

## Premium registries and MCP

Registries such as 21st.dev, Magic UI, Aceternity, shadcn-blocks, and Magic MCP can speed up premium composition, but only after checking current tool availability and stack fit.

- Do not claim a registry/MCP/repo is available until verified in the current environment.
- Treat imported components as third-party code: review dependencies, accessibility, responsiveness, bundle impact, and license where relevant.
- Adapt code to local tokens, semantic colors, copy, and CTA path.
- Remove effects that fight the conversion path.
- Do not add a registry for one simple button/card.

## Visual reference loop

For premium quality:

1. Use references for composition, type rhythm, proof mechanics, or motion behavior.
2. Extract principles, do not clone blindly.
3. Render the artifact.
4. Screenshot desktop and mobile.
5. Compare against the goal and references.
6. Fix overlap, crop, weak hierarchy, overflow, CTA conflict, face/product coverage.
7. Screenshot again after the final edit.

No final screenshot means the design is not done.

## Motion and media

Motion should sell trust, product reality, or comprehension.

- Prefer short muted loops, cinemagraphs, WebM/MP4 with poster, and reduced-motion fallback.
- For heavy 3D/video, consider image sequence/canvas or a static fallback.
- Do not place multiple motion layers near pricing/payment.
- Never let overlays cover faces, product details, forms, prices, or CTAs.

## Taste, copy, and anti-slop layer

AI slop is visual and textual.

- Brand fidelity: the page should sound and look like a specific product/founder.
- Copy conversion logic: H1, subheadline, pricing, FAQ, and CTA must answer real objections.
- Tone variants are useful for exploration, but final page needs one voice.
- Remove AI-isms: empty claims like "revolutionary", "innovative", "unique experience" without proof.
- Synthetic proof may be demo content, never real testimonials or cases.
- Final review should include skeptical buyer, copywriter, and visual QA passes.

Often the best polish is deletion: fewer equal cards, fewer tool names, clearer outcome, price, proof, and next step.

## Project structure and server/client boundaries

Follow the current project first. If creating a new app and no convention exists, a reasonable default is:

- `components/layout` for global shells;
- `components/ui` for atomic primitives;
- `components/shared` for reusable product blocks;
- `PascalCase` for visual components;
- local convention or `kebab-case` for hooks, utilities, constants, and types.

For Next.js App Router, avoid hydration problems:

- read/write cookies on the server through `cookies()`, route handlers, or `NextResponse.cookies`;
- keep localStorage, viewport, theme, and browser-only state in client components or stable hooks;
- verify theme/mobile branches in the browser.

## QA and verification loop

For app-like or interactive prototypes:

- define acceptance cases before implementation;
- if business logic exists, use tests where practical;
- use browser automation to click, scroll, inspect console/network, and screenshot;
- verify loading, error, success, disabled, and empty states where relevant;
- if it will be deployed, check the live URL and live user path, not only local rendering.

After substantial UI edits, run the most relevant self-correction loop: lint/typecheck/build/test where practical, fix logs narrowly, then browser/screenshot check for desktop and mobile.

Subagents are useful for independent CRO, copy, mobile, a11y, performance, and visual QA passes. Synthesize their results yourself and close them after work.

## Anti-slop stop signs

Rework before delivery if you see:

- decorative gradient hero without brand reason;
- equal-weight cards everywhere;
- fake testimonials or synthetic proof presented as real;
- provider/tool names instead of user outcomes;
- CTA below fold without intent;
- mobile as a squeezed desktop;
- text over face/product;
- beautiful visuals that do not support trust, proof, or action;
- payment/lead flow not actually checked.
