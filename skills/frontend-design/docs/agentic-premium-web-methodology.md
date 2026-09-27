# Agentic Premium Web Methodology

Используй эту выжимку для задач вида: "сделай стильный сайт", "премиальный лендинг", "не generic AI UI", "докрути визуал и конверсию", "сайтолог/маркетолог + дизайнер".

## Главная идея

Премиальный сайт через ИИ-агента строится не с команды "сверстай красиво", а через управляемый конвейер:

1. **Design**: зафиксировать визуальную систему и коммерческую логику.
2. **Development**: реализовать интерфейс в коде, сохраняя систему и product logic.
3. **Deployment**: проверить скорость, адаптивность, аналитику, оплату/лиды и живой сценарий пользователя.

Если пропустить Design-фазу, результат почти всегда скатывается в AI slop: одинаковые hero, случайные карточки, декоративные градиенты, слабая иерархия и размытый CTA.

## Context engineering

Качество агентного UI зависит не от размера контекста, а от точности контекста.

Правила:

- не использовать broad whole-codebase context без причины;
- ссылаться на конкретные файлы и секции, которые реально затрагиваются;
- для отдельной функции, секции или визуального эксперимента держать отдельный короткий рабочий контекст;
- не смешивать в одном проходе hero, pricing, backend, аналитику, анимации и оплату, если они не должны меняться одновременно;
- после длинной итерации делать короткий handoff: что изменено, что проверено, что остаётся риском;
- если задача большая, применять `YOLO small`: маленький проверяемый шаг -> browser/screenshot/test -> следующий шаг.

Красный флаг: агент начинает переписывать соседние компоненты, добавлять лишние зависимости или менять product logic ради визуального редизайна. В таком случае сузить scope и вернуть его к конкретному файлу/секции.

## Rule architecture: AGENTS.md, MDC, SKILL.md

Для повторяемого качества не держи все инструкции в одном огромном промпте.

Предпочтительный порядок:

- сначала читать и уважать существующие `AGENTS.md`, `design.md`, design tokens, component docs и локальные conventions;
- если инструмент поддерживает path-scoped rules, разделять правила по смыслу: UI, backend, tests, security, deployment;
- не смешивать CSS/landing instructions с database/auth/infra rules, если текущий шаг касается только интерфейса;
- для Codex-compatible проектов использовать вложенные `AGENTS.md` там, где нужны локальные правила поддерева;
- для Cursor-compatible проектов можно использовать `.cursor/rules/*.mdc`, чтобы подгружать правила по `globs`, а не держать монолитный `.cursorrules`;
- для повторяемых процедур вроде screenshot loop, premium landing audit или component injection оформлять `SKILL.md`/docs вместо копирования длинного текста в каждый чат.

Принцип: правила должны сужать свободу агента там, где качество зависит от консистентности, но не перегружать контекст нерелевантными деталями.

## Design-фаза перед кодом

Перед крупным редизайном или новым лендингом сформулируй короткий `design.md`-аналог прямо в плане или, если проект долгий, создай/обнови файл в проекте.

Минимальный состав:

```md
Brand / product:
Audience:
Business goal:
Primary CTA:
Secondary CTA:
Visual mood:
Typography:
Color palette:
Surface model:
Radius scale:
Spacing scale:
Motion rules:
Proof assets:
Anti-patterns:
```

Правила:

- visual identity должна быть source of truth для всех секций;
- цвета, шрифты, радиусы, shadows и spacing не выбираются заново в каждом блоке;
- одна страница = один главный коммерческий путь;
- декоративность не должна перекрывать лицо, продукт, цену, форму, CTA или proof;
- если реальные proof assets отсутствуют, честно называй мокапы демо-сценарием, не отзывами и не кейсами.

## Content-first before layout

Не строить premium landing на `Lorem ipsum` или абстрактных блоках.

Перед layout:

- сформулировать реальный H1, subheadline, CTA и post-click text;
- понять боли аудитории и decision objections;
- написать pricing / risk reversal / FAQ на реальных условиях;
- только потом подбирать typography, grid и visual rhythm под длину настоящего текста.

Если copy слабый, красивый layout не спасает. Если copy меняется после верстки, обязательно проверять переполнение, переносы, высоту карточек и мобильную композицию.

## Agentic workflow

1. **Inspect**: стек, существующие tokens/components, контент, платежи/формы/аналитика, mobile screenshots.
2. **Define direction**: аудитория, оффер, CTA, доказательства, visual mood, layout rhythm.
3. **Reference pass**: если качество/стиль важны, собрать 2-5 референсов или публичных лучших практик. Не копировать вслепую, а извлечь композицию, типографику, rhythm и proof mechanics.
4. **Build pass**: structure -> copy hierarchy -> typography/spacing -> surfaces/color -> states -> responsive -> motion.
5. **Screenshot loop**: открыть результат в браузере, сделать desktop/mobile screenshots, найти overlap, weak hierarchy, overflow, плохой crop, тяжёлый CTA или сломанный safe area.
6. **Refine pass**: исправить по скринам, затем повторить browser/screenshot check.
7. **Conversion pass**: проверить, что путь пользователя не распался: CTA, форма/оплата, success state, Telegram/CRM handoff, next step.
8. **Production pass**: build/deploy/smoke, если задача включает live-сайт.

## Extract -> Generate -> Polish stack

Для коммерческого лендинга сильнее всего работает не один "магический" генератор, а цепочка:

1. **Extract**: из референса, URL, Figma, скриншота или бренд-материалов извлечь tokens, spacing, typography, surface model, brand voice и CTA semantics.
2. **Generate**: собрать sections/components в подходящем стеке, обычно вокруг текущего проекта и его design system.
3. **Polish / Review**: пройти taste layer, copy conversion review, anti-slop pass, WCAG/mobile checks, visual diff/screenshot QA.

Если текущий проект уже живой, extract может быть внутренним: прочитать существующие tokens/components и реальные страницы. Если проект новый, extract может быть внешним: референс, скрин, сайт конкурента, Figma или бренд-kit.

Не начинать с generator, если не понятны extracted tokens, real copy, proof assets и CTA path. Иначе генератор быстро производит красивый, но generic output.

## SPARC-style control

Для автономных агентов используй SPARC как лёгкий контроль хаоса, а не бюрократию:

- **Specify**: зафиксировать задачу, аудиторию, CTA, constraints и что нельзя трогать;
- **Plan**: разбить на маленькие независимые шаги;
- **Architect**: выбрать structure, components, state boundaries, rules/docs и verification path;
- **Refine**: после каждого шага читать результат, логи и screenshots, затем чинить узко;
- **Complete**: закрыть только после проверки user path, visual gates и handoff.

Если задача маленькая, SPARC может быть устным mini-checklist. Если задача большая, оформить его в план или project docs.

## 40/20/40 effort model

Для сложного лендинга не пытаться сделать всё one-shot. Держи ориентир:

- **40% Inspiration & Planning**: аудитория, offer architecture, референсы, content-first copy, дизайн-система, proof strategy.
- **20% Structural Build**: каркас, секции, компоненты, формы, роутинг, базовая адаптивность.
- **40% Polish Phase**: типографика, spacing, реальные переносы, microinteractions, media crop, mobile, performance, browser QA.

One-shot генерация допустима только для черновика. Production-grade результат почти всегда появляется во второй половине работы — на полировке и верификации.

## Two-pass screenshot loop

Для premium UI визуальная проверка обязательна, если есть browser/dev server:

- desktop: широкий viewport, первый экран, pricing/CTA, финал;
- mobile: 360-430px, header, hero, sticky CTA, widget, pricing, форма/оплата;
- проверять не только "страница открылась", а:
  - лицо/продукт не перекрыты текстом;
  - CTA виден и не спорит с вторичными действиями;
  - текст не вылезает и не давит;
  - нет horizontal overflow;
  - motion не мешает чтению;
  - floating widgets не закрывают цену, форму и финальный CTA.

Если скрин плохой, считать задачу незавершённой.

## Visual prompting

Абстрактные просьбы вроде "сделай премиально" дают случайный результат. Для сложного визуала лучше:

- использовать скриншоты референсов, бренд-материалы, реальные фото, реальные product screenshots;
- просить агента извлечь не "стиль целиком", а конкретные свойства: grid, rhythm, typography, contrast, spacing, surface depth, motion pattern;
- явно сказать, что нельзя копировать бренд/композицию 1-в-1, если это чужой продукт;
- после генерации сравнить результат со скрином и перечислить расхождения перед правкой.

Если референсов нет, агент обязан сформулировать собственную visual direction до кода, а не угадывать из общих слов.

## Measurable UI gates

Премиальность должна проходить базовые измеримые проверки:

- body text contrast: WCAG AA, обычно `>= 4.5:1`;
- large text / крупные UI-сигналы: обычно `>= 3:1`;
- touch targets для важных мобильных действий: примерно `44x44px` или больше;
- простые hover/focus/active transitions: чаще `150-300ms`, без вязкой анимации;
- motion должен иметь `prefers-reduced-motion` или спокойный fallback where relevant;
- line length для длинного чтения держать в человеческом диапазоне, обычно около `45-75` символов;
- текст, плашки и widgets не должны закрывать лицо, продукт, цену, форму, CTA или proof.

Если визуал выглядит богато, но проваливает эти гейты, это не production-grade UI.

## Vertical style heuristics

Выбор визуального языка привязывай к нише и офферу, но не превращай таблицы стилей в догму:

- SaaS / Tech / AI: строгий bento/minimal/AI-native, холодные акценты, много воздуха, аккуратный glow только там, где он усиливает hierarchy.
- Fintech / B2B / Ops: чистая сетка, спокойные trusted colors, сильная читаемость цифр, минимум декоративной кинетики.
- Beauty / Lifestyle: мягкие surfaces, tactile shadows, контрастные serif headlines, очень деликатная motion.
- Luxury / Ecommerce: spatial minimalism, качественная media-first композиция, монохром/металл/акцент, никаких хаотичных sale-плашек.

Анти-паттерн: выбирать "модный" стиль без связи с аудиторией, ценой, доверием и действием пользователя.

## CRO-first architecture

Для продажных страниц приоритет выше визуального вау:

- **Speed to lead**: форма/оплата/Telegram/CRM должны вести к быстрому контакту, а не к тупику.
- **Founder proof**: если продукт founder-led, личность и проверяемый публичный трек важнее абстрактных AI-картинок.
- **Risk reversal**: честно объяснить, что фиксируется, что оплачивается, что будет после клика, где ограничения.
- **Primary CTA discipline**: один главный путь; вторичные CTA визуально тише.
- **Sticky mobile CTA**: полезен на длинных лендингах, но не должен перекрывать контент.
- **Proof before polish**: реальные кейсы, скрины, видео, публичные ссылки и payment/success flow сильнее декоративных мокапов.
- **Benefits > features**: технические фичи переводить в результат, скорость, контроль, снижение риска, доступ к экспертизе.
- **Text condensation**: длинные объяснения убирать в FAQ/accordion, оставляя над fold короткое решение и CTA.

## Generator and component injection strategy

UI-генераторы и библиотеки — это не автопилот, а ускорители:

- использовать генератор/готовый компонент для structural scaffold или сложного паттерна;
- затем адаптировать под текущие tokens, copy, CTA path, accessibility и responsive rules;
- избегать default bias: не выбирать React/Tailwind/shadcn/3D/motion только потому, что инструмент так любит;
- не добавлять тяжёлую библиотеку ради одного декоративного эффекта;
- готовые premium components проверять как чужой код: зависимости, bundle impact, a11y, responsiveness, visual fit.

Хорошая роль агента здесь — assembler/integrator: взять зрелый паттерн, встроить в систему и убрать лишнее, а не выдумывать дизайн из статистического шума.

## Tool/repo selection protocol

GitHub-каталоги, awesome lists, MCP registries и skill packs использовать как discovery layer, а не как источник истины.

Перед тем как тащить repo/tool в проект:

- проверить live README, дату обновления, license, install path, dependencies, stars/forks only if they matter, demo/examples и открытые issues where relevant;
- не додумывать `forks`, `license`, `demo/live`, если они не видны;
- понять класс инструмента: design workspace, extractor, design-to-code bridge, rule/skill pack, landing generator, copy system, visual QA;
- выбирать инструмент под стадию pipeline, а не по популярности;
- предпочитать local-first/BYOK/multi-model только если это реально важно для privacy, cost control или автономности;
- не заменять локальную дизайн-систему чужим repo без проверки visual fit и maintainability.

Минимальная карта выбора:

- нужен референс -> код: extractor / screenshot-to-code / Figma bridge;
- нужен быстрый MVP landing: design workspace or landing generator;
- страница звучит generic: taste layer / copy critique / anti-slop review;
- нужен pixel/brand fidelity: visual diff, screenshot loop, design tokens;
- нужен production flow: generator + QA + payment/lead smoke, not just HTML preview.

## Premium component registries and MCP

Компонентные реестры вроде 21st.dev / Magic UI / Aceternity / shadcn-blocks / Magic MCP полезны как источник зрелых паттернов, но только после проверки доступности инструмента и совместимости со стеком.

Правила:

- не утверждать, что конкретный MCP, registry или repo доступен, пока это не проверено в текущей среде;
- импортированный компонент считать third-party code: проверить зависимости, a11y, responsive behavior, bundle impact и license where relevant;
- адаптировать component code под локальные tokens, semantic colors, copy и CTA path;
- удалять лишние эффекты, если они спорят с коммерческим фокусом;
- не подключать компонентный registry ради одной простой кнопки или карточки.

## Component and motion choices

Используй библиотеки только когда они помогают задаче:

- `shadcn/ui` / Radix: формы, dialog, popover, tabs, accordion, menu, accessible primitives.
- `lucide-react`: иконки для понятных действий.
- `Framer Motion` / GSAP: сложная, осмысленная motion-логика, scroll scenes, staged reveals.
- Magic UI / React Bits / AlignUI / 21st.dev-style компоненты: только после проверки совместимости со стеком и дизайн-системой.

Motion правила:

- motion должен усиливать понимание, доверие или premium feel;
- для hero/founder/product loops предпочитай короткие muted loop/cinemagraph, poster, lazy loading, `prefers-reduced-motion`;
- для тяжёлого 3D/video рассмотри canvas/image-sequence или статичный fallback;
- не ставь несколько конкурирующих motion layers рядом с ценой, формой или оплатой.

## Polish phase

Премиальность чаще рождается не в первом черновике, а в деталях:

- ровный type scale и line-height;
- consistent section rhythm;
- точный crop фото/видео;
- устойчивые размеры карточек и CTA;
- hover/focus/active/loading states;
- микродвижения, которые объясняют состояние или добавляют доверие;
- аккуратное скрытие длинного текста в accordions;
- отсутствие визуальных конфликтов между widget, sticky CTA, pricing и forms.

Не использовать Lenis/Framer/GSAP/Three.js как обязательный знак премиальности. Использовать только когда они поддерживают историю продукта и проходят performance budget.

## Taste, copy and anti-slop layer

AI slop бывает не только визуальным, но и текстовым.

Отдельно проверяй:

- brand fidelity: страница звучит и выглядит как конкретный продукт/основатель, а не как template;
- copy conversion logic: H1, subheadline, pricing, FAQ и CTA отвечают на реальные objections;
- tone variants: для high-ticket offer полезно сравнить 2-3 тона, но выбрать один голос, а не смешивать стили;
- no AI-isms: убрать пустые фразы, "революционный", "инновационный", "уникальный опыт" без proof;
- no fake proof: synthetic screenshots/mockups можно использовать как demo, но нельзя выдавать за реальные отзывы/кейсы;
- review checklist: в конце прогнать страницу как skeptical buyer, copywriter и visual QA.

Лучший polish часто выглядит как удаление лишнего: меньше одинаковых карточек, меньше tool names, больше ясного результата, цены, proof и next step.

## Project structure and naming guardrails

Сначала следуй структуре текущего проекта. Если проекта ещё нет и нужен разумный default:

- `components/layout` — header, footer, shell, sidebar;
- `components/ui` — атомарные primitives: button, input, dialog, tabs;
- `components/shared` — reusable product blocks: pricing card, testimonial, lead form, founder proof;
- visual components — `PascalCase`;
- hooks, utils, constants, types — обычно `kebab-case` or local convention;
- не плодить новые папки и layers без реальной повторяемости.

Для Next.js App Router:

- cookies читать/писать server-side через `cookies()` / route handlers / `NextResponse.cookies`, не через browser APIs на сервере;
- localStorage, viewport, theme и browser-only state держать в client components или проверенных hooks;
- заранее думать о hydration mismatch, особенно в mobile/theme/media-query логике.

## Performance and deployment guardrails

Перед live:

- изображения: WebP/AVIF where possible, known dimensions, no huge unbounded PNG;
- видео: muted, loop, playsInline, poster, no audio stream unless required;
- lazy-load below-fold media;
- avoid heavy JS for decorative effects;
- smoke payment/form/success path, not just visual page;
- after deploy, check live URLs and key strings, not only local build.

## Verification and QA loop

Для интерактивных компонентов:

- если есть бизнес-логика, сначала сформулировать тест-кейсы или acceptance cases;
- для сложных форм/калькуляторов/checkout использовать unit/integration tests where practical;
- для визуального UX использовать browser automation: открыть, кликнуть, проскроллить, снять скрин, проверить console/network when relevant;
- проверять не только happy path, но и loading/error/success/disabled states;
- после production deploy проверять live, а не считать local build достаточным.

## Self-correction loop

После существенных UI-правок агент должен закрывать цикл:

1. Выполнить доступные проверки (`lint`, `typecheck`, `build`, тесты или targeted browser check).
2. Если проверка упала, читать конкретный лог и чинить минимально нужный участок.
3. Повторить проверку после исправления.
4. Для visual work дополнительно открыть страницу и проверить desktop/mobile screenshots.

Если проект большой или проверки дорогие, явно выбрать самый релевантный smoke вместо слепого запуска всего подряд.

Саб-агенты полезны для независимых аудитов: CRO, copy, mobile, a11y, performance, visual QA. После их работы результат нужно синтезировать, проверить самому и закрыть агентов.

## Anti-slop checklist

Остановись и перепридумай, если видишь:

- generic bento/grid без коммерческой роли;
- purple-blue AI gradient по умолчанию;
- одинаковые карточки с одинаковой важностью;
- CTA ниже fold без причины;
- много provider/tool names вместо результата для пользователя;
- фейковые отзывы, неатрибутированные кейсы или AI-мокапы, поданные как реальные;
- текст поверх лица, продукта, цены, формы или proof;
- mobile выглядит как сжатый desktop;
- красивое видео, которое не помогает продаже;
- pricing без объяснения "что после клика" и "что фиксирует оплата".

## Короткий prompt-шаблон для агента

```md
Сначала сделай Design-фазу:
- зафиксируй visual direction и CTA path;
- проверь existing tokens/components;
- сузь контекст до конкретных файлов и секций;
- напиши/проверь реальный content-first copy;
- определи proof assets и анти-паттерны.

Потом реализуй:
- работай маленькими итерациями, не one-shot;
- structure -> hierarchy -> typography/spacing -> color/surfaces -> states -> responsive -> motion.

После реализации:
- сделай desktop/mobile screenshots;
- исправь overlap/overflow/crop/CTA conflicts;
- проверь form/payment/success или lead handoff;
- только потом считай задачу готовой.
```
