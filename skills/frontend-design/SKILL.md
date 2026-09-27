---
name: frontend-design
description: >
  Use when building, redesigning, polishing, or reviewing production frontend UI in
  React/Next.js/Tailwind: premium visual polish, SaaS dashboards, admin panels, forms,
  onboarding, landing pages, responsive layouts, shadcn/Radix components, accessibility,
  and complete interaction states.
---

> **Примечание для экспортной версии:** ниже чувствительные IP, домены, пути, SSH-цели и другие infra-значения заменены на примеры и placeholders вида `<YOUR_...>`. Если ИИ-агенту нужны реальные значения, он должен **подставить реальные данные пользователя** или **сначала запросить их у пользователя**, а не использовать примеры как есть.


# Frontend Design Skill

Коротко: этот skill отвечает за production UI в кодовой базе: React/Next.js/Tailwind-интерфейсы, которые должны быть не только рабочими, но и визуально зрелыми, адаптивными, доступными, специфичными для продукта и коммерчески осмысленными.

Для нетривиального UI перед дизайном или реализацией дополнительно открой `docs/premium-ui-quality.md`: там лежит компактная выжимка из premium UI-гайда по визуальной и компонентной планке.

Для задач про премиальные сайты, лендинги, "сайтологию", CRO, визуальный вау без AI slop, агентное создание интерфейсов или screenshot-loop дополнительно открой `docs/agentic-premium-web-methodology.md`.

## Когда использовать
- Пользователь просит сделать, улучшить, отполировать, пересобрать или оценить UI в React/Next.js/Tailwind.
- Нужны SaaS/dashboard/admin surfaces, формы, таблицы, onboarding, settings, auth, landing page или reusable components.
- Запрос звучит как "сделай красиво", "premium UI", "визуально докрути", "не как generic AI UI", "улучши UX", "адаптируй под mobile".
- Нужно перенести Figma/скриншот/референс в production frontend code.

## Когда НЕ использовать
- Backend-only, database, infra, CLI, API или workflow-задачи без пользовательского интерфейса.
- HTML-first артефакты, визуальные прототипы, slide-like demos и дизайн-варианты без production app code: там сначала используй `cc-design`.
- Motion-heavy HTML demos, MP4/GIF exports и direction-heavy visual exploration: там сначала используй `huashu-design`, если задача не про production app.

## Рабочий режим для нетривиального UI
1. Сначала изучи существующий проект: routing, components, tokens, Tailwind config, CSS variables, package scripts и текущие UI-конвенции.
2. Классифицируй поверхность: landing, dashboard, admin, form flow, onboarding, checkout, settings, auth, data table, chart или reusable component.
3. Сформулируй короткое visual direction: audience, primary action, mood, layout pattern, typography, color, surfaces, motion, anti-patterns.
4. Переиспользуй локальные компоненты и tokens до добавления новых abstractions или зависимостей.
5. Сохраняй product logic: data fetching, routing, auth, permissions, forms, analytics и side effects не ломаются ради визуального редизайна.
6. Реализуй проходами: structure -> typography/spacing -> color/surfaces -> states -> responsive -> accessibility -> restrained motion -> polish.
7. Проверь lint/typecheck/build/browser where practical и явно сообщи, что не удалось проверить.
8. Для больших UI-задач управляй контекстом узко: конкретные файлы/секции, маленькие проверяемые шаги, отдельные итерации для copy, layout, motion, backend/payment и QA.
9. Если качество должно повторяться, проверь instruction architecture: `AGENTS.md`, `design.md`, локальные docs/skills или path-scoped rules вместо одного огромного промпта.

## Agentic premium web workflow
Для новых или серьёзно переделываемых продажных сайтов используй 3D-конвейер:

1. **Design**: перед кодом зафиксируй `design.md`-аналог: аудитория, бизнес-цель, primary CTA, визуальное настроение, typography, palette, surface model, spacing/radius, proof assets и анти-паттерны.
2. **Development**: реализуй проходами, не ломая product logic: structure -> copy hierarchy -> typography/spacing -> color/surfaces -> states -> responsive -> motion.
3. **Deployment**: проверь живой пользовательский путь: форма/оплата/Telegram/CRM handoff, success state, analytics where relevant, live smoke.

Обязательный premium loop:

- собрать или явно сформулировать референсы;
- использовать content-first copy до layout, без `Lorem ipsum`;
- не пытаться сделать production landing one-shot: ориентир `40/20/40` = planning/content, structural build, polish/QA;
- сделать desktop/mobile screenshot после реализации;
- исправить overlap, bad crop, horizontal overflow, слабую иерархию, конфликт CTA, widget overlap;
- повторить screenshot/browser check после последней правки.

Для продажных лендингов CRO выше декоративности: founder proof, реальные кейсы, risk reversal, speed-to-lead, sticky mobile CTA и понятный post-click flow важнее красивого, но пустого visual layer.

## Технологический стек
- **Framework**: React / Next.js (App Router)
- **Styling**: Tailwind CSS v4 + CSS Variables
- **Components**: Shadcn UI (копируемые компоненты, не npm-зависимость)
- **Primitives**: Radix UI (доступность из коробки: focus traps, keyboard nav, ARIA)
- **Icons**: Lucide React
- **Анимации**: Framer Motion / tw-animate-css
- **Тестирование a11y**: @axe-core/react, @axe-core/playwright

## Инициализация проекта
```bash
npx create-next-app@latest my-app --typescript --tailwind --app
npx shadcn@latest init
# ✅ CSS variables: Yes
# ✅ Dark mode: Yes
# ✅ TypeScript strict: Yes
```

### Добавление компонентов Shadcn
```bash
npx shadcn@latest add button dialog tabs dropdown-menu
```
Компоненты копируются в проект — ты владеешь кодом, нет внешних зависимостей.

## Принципы работы

### 0. Premium UI is correctness
- Визуальная планка является частью корректности, а не финальным "украшением".
- Каждый экран должен иметь один главный фокус и одно главное действие.
- Дизайн должен быть специфичным для продукта: не используй generic SaaS layout без связи с аудиторией, контентом и сценарием.
- Интерактивные компоненты должны покрывать `default`, `hover`, `focus-visible`, `active`, `disabled`, `loading` where relevant.
- Data surfaces должны покрывать `loading`, `empty`, `no results`, `error`, `success/confirmation`, `permission`, `first-use` where relevant.
- Для русского продукта весь user-facing copy, labels, placeholders, errors, empty states и confirmations по умолчанию на русском.

### 1. Mobile First
Всегда начинай с мобильных разрешений, расширяй для больших экранов:
```tsx
<div className="px-4 md:px-8 lg:px-16">
  <h1 className="text-xl md:text-2xl lg:text-4xl">Заголовок</h1>
</div>
```

### 2. Компонентный подход (Atomic Design)
- **Atoms**: Button, Input, Badge
- **Molecules**: SearchBar (Input + Button), Card (Image + Title + Text)
- **Organisms**: Navbar, Sidebar, DataTable
- **Templates**: Layout с Sidebar + Content area
- **Pages**: Конкретные страницы приложения

### 3. Доступность (A11y) — обязательна
Radix UI обеспечивает из коробки:
- Focus traps в модальных окнах
- Keyboard navigation (Tab, Enter, Escape, Arrow keys)
- ARIA-атрибуты автоматически

Дополнительно:
- Семантический HTML (`<nav>`, `<main>`, `<section>`, `<article>`)
- Контрастность цветов (WCAG AA: 4.5:1 для текста)
- `alt` для всех изображений
- `aria-label` для иконок-кнопок

### 4. Дизайн-система через CSS Variables
```css
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --primary: 221.2 83.2% 53.3%;
    --primary-foreground: 210 40% 98%;
  }
  .dark {
    --background: 222.2 84% 4.9%;
    --foreground: 210 40% 98%;
  }
}
```

### 5. Tailwind Best Practices
- Используй стандартные утилиты, избегай кастомного CSS.
- Группируй классы логически: layout → spacing → typography → colors → effects.
- Предпочитай semantic tokens и CSS variables вместо одноразовых цветов и теней.
- Не добавляй production dependency ради одного простого UI-компонента без явной пользы.
- Используй `cn()` (из shadcn) для условного объединения классов:
```tsx
import { cn } from "@/lib/utils";

<button className={cn(
  "px-4 py-2 rounded-lg transition-colors",
  variant === "primary" && "bg-blue-600 text-white hover:bg-blue-700",
  variant === "outline" && "border border-gray-300 hover:bg-gray-50",
  disabled && "opacity-50 cursor-not-allowed"
)}>
```

### 6. Research-backed UI guardrails

- **Native first**: сначала выбирай нативные HTML-элементы. Кастомные combobox/dialog/menu/slider делай через проверенные primitives (`Radix UI`, `shadcn/ui`) или строго по `WAI-ARIA APG`, а не через самодельную клавиатурную модель.
- **State completeness**: для product UI явно проектируй `default`, `hover`, `focus`, `active`, `disabled`, `loading`, `empty`, `no results`, `error`, `success/confirmation`, `permission`, `first-use`.
- **Forms**: всегда используй видимые labels, а не placeholder вместо label; добавляй `autocomplete`, helper text, `fieldset/legend` для связанных полей, `aria-describedby` для пояснений и inline error text рядом с полем. Не делай неожиданных submit/context changes на focus или ввод.
- **Responsive accessibility**: компонент должен корректно работать при zoom 200–400%, сохранять логичный DOM/source order, использовать `rem/em` для текста, не прятать критичные действия только в hover-состоянии и иметь удобные touch targets.
- **Feedback**: ошибки и успехи должны быть видимы текстом и визуально; для больших форм используй и summary, и локальные сообщения у полей.
- **Empty states**: пустое состояние должно заменять отсутствующий контент и вести пользователя к одному главному следующему действию, а не оставлять «пустую рамку» таблицы или перегруженный набор CTA.

### 7. Anti-generic UI guardrails
- Не делай однотипные белые SaaS-страницы с фиолетово-синими gradients, bento grid, одинаковыми cards и hero без продуктовой конкретики.
- Не ставь декоративные icons в каждый блок, если они не улучшают понимание.
- Не смешивай heavy shadows, borders и glassmorphism в каждом компоненте.
- Не центрируй все секции подряд; используй hierarchy, grid, grouping и intentional asymmetry.
- Не делай tables, dashboards и admin panels как marketing page: им нужна плотность, сканируемость и низкий визуальный шум.
- Не прячь важные действия только за hover и не удаляй focus rings; их можно оформить, но нельзя исчезать.

## Где искать лучшие UI-кейсы и паттерны

### Приоритет источников
1. **Official docs и design systems**: `W3C/WAI`, `ARIA APG`, `web.dev`, `ui.shadcn.com`, Radix UI, USWDS, Carbon, Primer, Material.
2. **Context/docs connector или web.run**: для актуальной документации библиотек, design-system guidance и accessibility details.
3. **GitHub tools / code search / repo search**: для зрелых open-source реализаций dashboard, forms, auth screens, tables, settings pages и других production patterns.
4. **Web search**: для свежих best practices, сравнений подходов и конкретных UX-паттернов, когда официальных источников недостаточно.

### Когда поиск обязателен
- Если нужен не абстрактный UI, а референсный экран, зрелый паттерн или готовая композиция компонентов.
- Если проект требует dashboard, сложные формы, таблицы, onboarding, empty/loading/error states или мобильные паттерны.
- Если есть сомнение в лучшем UX-решении, доступности или адаптивном поведении.

### Как искать
- Ищи не «красивый дизайн вообще», а конкретный сценарий: `dashboard filters`, `settings form`, `auth form`, `billing table`, `mobile drawer navigation`.
- Предпочитай готовые паттерны из design systems и зрелых репозиториев, а не случайные dribbble-like концепты без кода.
- Для форм отдельно проверяй labels, validation, error states, keyboard navigation и mobile behavior.
- Для custom widgets отдельно проверяй keyboard model, focus management, screen reader naming/description и соответствие APG или library docs.
- Если используешь найденный паттерн, фиксируй источник и адаптируй его под русский интерфейс, доступность и текущий стек.

### Референсы для premium landing / CRO
- Сначала ищи не "красивый сайт", а конкретный паттерн: founder-led landing, high-ticket pricing, booking checkout, proof section, mobile sticky CTA, video testimonial lazy loading, payment success flow.
- Сравнивай референс с коммерческой задачей: какой CTA, какой proof, где risk reversal, как объясняется цена и что происходит после клика.
- Не копируй Dribbble/Awwwards как источник истины для конверсии: используй их как visual reference, а CRO проверяй через реальные landing best practices и зрелые product examples.
- Если используешь motion/3D/video, заранее задай performance budget и fallback: poster, reduced-motion, lazy loading, WebP/AVIF, short muted loop или canvas/image-sequence where appropriate.

## Адаптивная сетка
```tsx
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 md:gap-6">
  {items.map(item => <Card key={item.id} {...item} />)}
</div>
```

## Чек-лист реализации
- [ ] Адаптивность: 320px, 375px, 768px, 1024px, 1440px
- [ ] Темная тема работает корректно
- [ ] Все интерактивные элементы: hover, focus, active, disabled
- [ ] Продуманы ключевые состояния: loading, empty, no results, error, success, disabled, first-use
- [ ] Keyboard navigation работает (Tab, Enter, Escape)
- [ ] DOM/source order совпадает с логикой навигации по Tab на всех брейкпоинтах
- [ ] Изображения оптимизированы (Next.js Image) с alt
- [ ] Формы: валидация, понятные ошибки на русском
- [ ] Формы: видимые labels, autocomplete, helper text и связанные descriptions/errors
- [ ] Контрастность текста ≥ 4.5:1 (WCAG AA)
- [ ] Крупный текст/UI-сигналы держат достаточный контраст, обычно ≥ 3:1
- [ ] Нет горизонтального скролла на мобильных
- [ ] Zoom 200%+ не ломает layout и чтение интерфейса
- [ ] Touch targets достаточно крупные для мобильного использования, ориентир 44x44px для важных действий
- [ ] Motion не навязчивый: простые переходы ~150-300ms и есть reduced-motion/fallback where relevant
- [ ] Loading/skeleton states для асинхронных данных
- [ ] Для нетривиального UI найдены и проверены референсные кейсы или готовые паттерны
- [ ] Для premium landing зафиксирован `design.md`-аналог: audience, CTA, mood, palette, typography, surfaces, proof, anti-patterns
- [ ] Для premium landing выбран pipeline stage: extract -> generate -> polish/review, а не one-tool magic
- [ ] Для premium landing использован content-first copy: реальные заголовки, CTA, pricing, FAQ и success/next-step text до финального layout
- [ ] Большая UI-задача разбита на маленькие проверяемые шаги, а не выполнена one-shot
- [ ] Для продажной страницы проверен post-click flow: форма/оплата/Telegram/CRM/success state
- [ ] Desktop/mobile screenshots сделаны после последней значимой визуальной правки
- [ ] После существенных UI-правок запущен релевантный self-correction loop: lint/typecheck/build/test/browser smoke where practical
- [ ] Primary action и visual hierarchy понятны без объяснений
- [ ] Spacing, radius, shadows, borders и typography используют повторяемую систему
- [ ] UI не выглядит generic AI output: есть продуктовая конкретика, уместная плотность и осознанная композиция
- [ ] Если использовался внешний repo/tool/MCP, live-проверены README, license/deps/install path и fit под текущий стек
- [ ] После значимых frontend-изменений выполнена browser/screenshot-проверка, если dev server доступен

## Финальный отчёт по UI-задаче
Коротко фиксируй:
- UI direction: какая визуальная логика выбрана.
- Changed files: что реально изменено.
- Visual improvements: hierarchy, spacing, typography, color, surfaces, motion.
- Responsive behavior: что проверено на mobile/desktop.
- States added: loading, empty, error, disabled, focus where relevant.
- Verification: lint, typecheck, tests, build, browser/screenshot check, или почему check недоступен.

## Полезные паттерны

### Responsive Dialog → Drawer на мобильных
```tsx
import { useMediaQuery } from "@/hooks/use-media-query";

const isDesktop = useMediaQuery("(min-width: 768px)");
// Desktop → Dialog, Mobile → Drawer
```

### Оптимистичные обновления UI
Обновляй UI сразу, не дожидаясь ответа сервера. Откатывай при ошибке.
