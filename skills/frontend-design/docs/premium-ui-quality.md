# Premium UI Quality Guide

Выжимка из `(внутренняя выжимка, путь удалён при экспорте)` для `frontend-design`. Используй этот файл, когда задача больше tiny edit и от результата ожидают production-grade визуальную планку.

## Цель

Делать интерфейсы, которые:

- визуально специфичны для продукта, а не похожи на generic AI SaaS;
- согласованы по typography, spacing, color, radius, depth, layout и motion;
- адаптированы под mobile, tablet, laptop и desktop;
- доступны с клавиатуры и понятны screen readers where practical;
- сохраняют существующую product logic и архитектуру проекта;
- покрывают реальные состояния, а не только happy path.

Если есть конфликт между декоративностью и ясностью, выбирай ясность.

## Быстрый workflow

1. Inspect before changing: framework, routing, component library, tokens, Tailwind config, CSS variables, package manager, scripts, current responsive behavior.
2. Classify the UI: marketing landing, SaaS dashboard, admin, onboarding, checkout, settings, auth, form-heavy flow, analytics/reporting, reusable component.
3. Define visual direction:

```md
Audience:
Product category:
Primary user action:
Mood:
Layout pattern:
Typography direction:
Color atmosphere:
Surface/depth style:
Motion style:
Anti-patterns to avoid:
```

4. Reuse design tokens and local components first.
5. Plan affected files before editing.
6. Implement in passes: structure, typography/spacing, color/surfaces, states, responsive, accessibility, motion, polish.
7. Verify with available scripts and browser/screenshot checks where practical.

## UI Quality Model

- Information hierarchy: пользователь сразу понимает, что важнее всего.
- Layout rhythm: spacing не случайный, а повторяемый.
- Typography: scale, weight, line-height и measure помогают читать и сканировать.
- Color system: цвета работают на hierarchy, brand и state.
- Component consistency: повторяющиеся паттерны выглядят и ведут себя одинаково.
- Interaction states: hover, active, focus-visible, disabled, loading, empty, error, success покрыты where relevant.
- Responsive behavior: каждый breakpoint выглядит спроектированным, а не просто сжатым.
- Accessibility: keyboard, focus, labels, contrast, semantics.
- Motion restraint: анимация объясняет состояние или повышает perceived quality, не отвлекает.
- Content fit: layout рассчитан на реальный текст и реальные данные.

## Visual Principles

### Hierarchy

- Один главный visual focus на экран.
- Одно главное action на экран.
- Secondary actions должны выглядеть secondary.
- Cards не должны иметь одинаковую visual weight, если данные разные по важности.
- Above the fold отвечает: что это, зачем важно, что сделать дальше.

### Typography

- Используй deliberate type scale.
- Обычно хватит weights `400`, `500`, `600`, `700`.
- Body text не должен быть слишком широким.
- Captions и metadata заметно тише, но читаемы.
- Для dashboards используй scan-friendly labels, крупные key metrics, right-aligned numeric columns и tabular numbers where available.
- Не масштабируй font-size через viewport width; лучше responsive breakpoints.

### Spacing

Работай по шкале, а не случайными margin:

```text
4px  - tiny internal detail
8px  - tight pair spacing
12px - compact component gap
16px - standard internal padding
24px - card/section internal rhythm
32px - major block separation
48px - section group separation
64px - large section spacing
96px - hero/major landing spacing
128px - high-end landing breathing room
```

Связанные элементы ближе, разные группы дальше. Внутренний padding card меньше, чем gap между cards.

### Layout

- Marketing pages: max-width container, sections, visible next section hint in hero where relevant.
- Dashboards/admin: density, scan speed, low visual noise, predictable navigation.
- Tables: explicit mobile strategy, not accidental overflow.
- Mobile: отдельная композиция, а не desktop squeezed into one column.

Recommended containers:

```text
Text/narrow content: 640-760px
Standard content: 1024-1200px
Wide landing: 1280-1440px
Dashboard shell: full width with constrained card groups where useful
```

### Color

- Neutrals carry most UI.
- Brand/accent color marks decisions and emphasis.
- Semantic colors только для semantic meaning.
- Не используй red/green как decoration.
- Text contrast and control contrast are part of correctness.
- Avoid one-note palettes and dominant purple-blue gradients unless brand requires it.

### Surfaces

- Выбери border-led или shadow-led surface model; не делай всё сразу.
- Radius scale должен быть повторяемым.
- Shadows reserved for elevation: dropdowns, popovers, modals, special hero visuals.
- Avoid cards inside cards and heavy nested shadows.

Suggested radius:

```text
xs 4px
sm 6px
md 8px
lg 12px
xl 16px
2xl 24px
full 9999px
```

## Component Standards

### Buttons

- Variants: default, hover, active, focus-visible, disabled, loading where relevant.
- Primary button is visually dominant.
- Loading buttons preserve width to avoid layout shift.
- Icon-only buttons have accessible labels and tooltips if meaning is not obvious.

### Forms

- Visible label, placeholder is not a label.
- Required fields are clear.
- `autocomplete`, helper text, `aria-describedby`, inline errors near fields.
- Preserve user input on error.
- Form states: empty, focused, filled, invalid, valid, submitting, success, server error, disabled.

### Cards

Cards need a reason:

- group related content;
- create scannable sections;
- support interaction if clickable.

Bad signs: every element boxed, no hierarchy inside, too much border/shadow noise, nested cards.

### Navigation

- Current location is visible.
- Primary nav is not overloaded.
- Mobile nav is intentional.
- Dashboard nav supports repeated scanning.
- Breadcrumbs help deep admin flows.

### Modals, Sheets, Dropdowns, Popovers

Prefer Radix/shadcn/local wrappers. Focus moves into modal and returns after close. Escape closes where expected. Destructive confirmations are explicit.

### Tables And Data Grids

- Text left, numbers right.
- Sorting/filtering states visible.
- Loading does not cause major layout shift.
- Empty state explains what happened and what to do next.
- Mobile strategy: horizontal scroll, stacked cards, or priority columns.

### Charts

- Chart answers a question; it is not decoration.
- Units and ranges are clear.
- Tooltips for dense data.
- Do not rely only on color.
- Loading/empty/error states exist.

## Page Patterns

### Marketing Landing

Goal: trust and action.

- Hero says what the product does or what outcome it creates.
- Subheadline says who it is for and why it matters.
- Primary CTA is obvious; secondary CTA is quieter.
- Visual motif supports the product category.
- Sections have jobs: proof, problem, outcome, how it works, features/use cases, pricing/offer, FAQ, final CTA.
- Remove decorative filler.

### SaaS Dashboard

Goal: fast comprehension and action.

- Most important metric is obvious.
- Date range/filter context is visible.
- Cards are not all equally loud.
- Tables and charts have hierarchy.
- Empty/loading/error states exist.
- Visual noise is lower than in marketing pages.

### Admin Panel

Goal: repeated operational work.

- Prefer predictable layout over expressive composition.
- Keep actions close to the data they affect.
- Destructive actions require clear confirmation.
- Permission/disabled states are explicit.

### Onboarding Flow

Goal: move user to first value.

- One main decision per step.
- Progress is visible.
- Skip/back behavior is clear.
- Errors explain how to proceed.
- First-use state teaches through action, not long instructions.

### Checkout Or Payment

Goal: trust, clarity, low anxiety.

- Price, terms, selected plan, taxes/fees where relevant are visible.
- Errors preserve input.
- Loading prevents duplicate submission.
- Security/trust copy is factual and not bloated.

## Anti-Patterns

### Visual

- Random gradients without brand logic.
- Purple-blue AI SaaS palette by default.
- Cards everywhere with equal weight.
- All sections centered.
- Heavy shadows on flat dashboards.
- Low contrast gray text.
- Decorative icons in every bullet.
- Hero copy with no product specificity.
- Bento grid when content does not need it.

### Interaction

- No hover/focus states.
- Disabled buttons without explanation where user can fix something.
- Empty states with no next action.
- Loading states that shift layout.
- Clickable `div` instead of semantic `button` or `a`.
- Critical actions hidden behind hover.

### Engineering

- New dependency for one simple component.
- Duplicating existing local components.
- Hardcoded colors instead of tokens.
- Breaking data fetching, routing, auth, permissions or analytics during visual redesign.
- One huge component when local patterns prefer smaller pieces.
- Ignoring existing build/type/lint errors without reporting them.

## Quality Gate

A UI task is not done until these are true or explicitly reported as unavailable:

```text
[ ] Existing project conventions preserved.
[ ] Primary user action is visually clear.
[ ] Typography, spacing, radius, border/shadow and color follow a system.
[ ] Interactive states exist where relevant.
[ ] Loading/empty/error/success/permission/first-use states exist where relevant.
[ ] Forms have labels, helper/errors and keyboard flow.
[ ] Mobile and desktop layouts checked.
[ ] No obvious contrast/readability problems.
[ ] Motion is restrained and purposeful.
[ ] Lint/typecheck/build/tests/browser checks run where practical or limitations reported.
```

## Completion Summary Template

```md
UI direction:
- ...

Changed files:
- `path` - what changed

Visual improvements:
- ...

Responsive behavior:
- ...

States added:
- Loading:
- Empty:
- Error:
- Disabled:
- Focus:

Verification:
- Typecheck:
- Lint:
- Tests:
- Build:
- Browser/screenshot:

Notes / limitations:
- ...
```
