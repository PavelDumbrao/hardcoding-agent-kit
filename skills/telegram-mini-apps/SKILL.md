---
name: telegram-mini-apps
description: Use when creating, fixing, or shipping a Telegram Mini App on Next.js/React. Covers initData-first auth, optional server session fallback, bot entrypoints, personal invite links, deployment, and production smoke checks.
---

> **Примечание для экспортной версии:** ниже чувствительные IP, домены, пути, SSH-цели и другие infra-значения заменены на примеры и placeholders вида `<YOUR_...>`. Если ИИ-агенту нужны реальные значения, он должен **подставить реальные данные пользователя** или **сначала запросить их у пользователя**, а не использовать примеры как есть.


# Telegram Mini Apps

Коротко: этот skill нужен, чтобы **сразу правильно собирать Telegram Mini App**, а не чинить потом auth, invite links, web fallback, cookies и продовый деплой по кускам.

## Когда использовать
- нужно создать Telegram Mini App с нуля;
- нужно переделать Mini App под production-ready архитектуру;
- нужно правильно связать Mini App ↔ Bot ↔ backend;
- нужно реализовать auth через Telegram `initData`;
- нужен web fallback login вне Telegram WebView;
- нужно настроить payment / access / progress / profile flow;
- нужно задеплоить Mini App и прогнать production smoke-check.

## Когда НЕ использовать
- задача только про HMAC-проверку `initData` и secure parsing — тогда сначала смотри skill `telegram-initdata-validation`;
- задача только про Telegram Bot API без Mini App UI;
- это обычный web app без Telegram entrypoint;
- нужен только один разовый ответ про `window.Telegram.WebApp` без архитектуры.

## Главный принцип
**Mini App = обычное web-приложение внутри Telegram WebView, но auth-модель у него не обычная web-first.**

Канонический порядок такой:
1. **Primary auth** = Telegram `initData`
2. **Server validation** = backend валидирует raw `initData`
3. **Optional secondary auth** = backend может держать свою session/cookie для browser fallback
4. **Никогда** не доверять `user_id` с клиента без валидации

## Каноническая архитектура

### 1. Entry surfaces
Telegram Mini App обычно открывается из:
- menu button бота;
- inline / keyboard button;
- direct app link / `startapp`;
- browser fallback URL.

### 2. Auth model
Используй модель:
- **внутри Telegram WebView** → auth через raw `initData`;
- **в обычном браузере** → web login fallback, например Auth.js / session cookie.

### 3. Unified auth layer
Не делай special-case только для `/profile`.

Если есть fallback session, все route должны использовать **единый helper**:
- сначала пробует `initData`;
- если его нет — пробует server session;
- возвращает единый `viewer/user/access` context.

### 4. UI routing model
Для переходов используй понятные ссылки:
- переход на экран = `<Link>` / `<a>`;
- не использовать JS-only кнопки там, где это просто navigation;
- warning/fallback CTA должны вести по прозрачному маршруту.

Канонический web fallback flow:
- `/login` → `/login/telegram` → OAuth → `/profile`

### 5. Backend access model
На backend желательно иметь явные слои:
- `User`
- `AccessRight`
- `Progress`
- `PaymentEvent`
- `ViewerContext`

### 6. Invite links / private chat access
Если Mini App или bot открывают закрытый чат/клуб:
- invite link должна быть **персональной**;
- старая активная ссылка пользователя должна отзыватьcя при новой выдаче;
- join request должен проверять соответствие `invite.tg_id == user_id`;
- после входа invite должна помечаться как `used`.

## Recommended build order
1. Определи surfaces: bot menu, direct link, browser fallback.
2. Настрой bot и HTTPS URL.
3. Реализуй получение `initData` на клиенте.
4. Реализуй server-side validation `initData`.
5. Вынеси единый `viewer/auth helper`.
6. Подключи helper ко **всем** route handlers.
7. Добавь web fallback session только как secondary path.
8. Реализуй access / progress / payment domain model.
9. Задеплой и прогоняй smoke-check по чек-листу.

## Proven production patterns

### Pattern A — client transport
Клиент должен передавать raw `initData` на backend в каждом auth-sensitive запросе.

Рабочий паттерн:
- брать `window.Telegram.WebApp.initData`
- прокидывать в header, например `x-telegram-init-data`
- не доверять `initDataUnsafe` как источнику истины

### Pattern B — server validation
Backend должен:
- взять raw `initData`;
- проверить подпись;
- проверить `auth_date` / freshness;
- распарсить пользователя;
- только после этого работать с `telegramId`.

### Pattern C — optional backend session
После успешной валидации `initData` можно:
- либо оставаться полностью initData-first;
- либо дополнительно выдать свою server session/cookie для browser fallback.

Это **допустимый production pattern**, но cookie не заменяет validation логики Telegram path.

### Pattern D — route handler helper
В Next.js App Router делай один helper уровня:
- `getViewerContext(initData, courseSlug?)`
- `getViewerContextWithSessionFallback(request, courseSlug?)`

И route handlers не должны вручную размазывать auth-логику по файлам.

### Pattern E — surface-aware browser UX
Если есть browser fallback, у клиента должен быть **общий surface/error слой**:
- `getMiniAppSurface()`
- `MiniAppApiError`
- `isMiniAppApiError()`
- единый warning component вроде `BrowserAuthNotice`

Это позволяет не плодить ad-hoc проверки по страницам и отличать:
- browser guest read-only state;
- browser authenticated state;
- session expired / `401` state;
- Telegram WebView state.

## Starter extraction layer
Если задача уже не про один проект, а про **переиспользуемый стартовый слой**, используй:
- `docs/nextjs-auth-session-pattern.md`
- `docs/browser-fallback-ux-pattern.md`
- `docs/launch-ready-starter-map.md`
- `examples/nextjs-auth-session-starter/`

Этот набор нужен, когда хочешь быстро собрать новый TMA на базе уже подтверждённого initData-first + browser-fallback паттерна, а не копировать весь старый проект целиком.

## Важные реальные anti-patterns

### 1. Profile-only fallback
Плохой паттерн:
- `/api/profile` умеет session fallback,
- а `/api/courses`, `/api/course/...`, `/api/module/...` — нет.

Симптом:
- в профиле пользователь «как будто авторизован»,
- в остальных вкладках — как будто гость.

### 2. Доверять user_id с клиента
Никогда не принимать `telegram_user_id` из body как trusted identity.

### 3. Возвращать raw Prisma object в JSON
Если в модели есть `BigInt`, raw-ответ может падать сериализацией.
Нужен JSON-safe object.

### 4. Ожидать camelCase Telegram payload без нормализации
Telegram payload часто приходит в snake_case:
- `first_name`
- `last_name`
- `language_code`
- `is_premium`
- `photo_url`
- `allows_write_to_pm`

### 5. Generic postgres hostname в shared Docker environment
В shared docker/runtime лучше избегать хоста `postgres` без namespace — это легко создаёт конфликт.

### 6. Internal sync через public domain без явного понимания trade-off
Работает, но при рестартах/redeploy может давать transient `502`/timeout.

## Recommended file structure for Next.js TMA
- `lib/miniapp-client.ts` — client helper для headers/initData
- `lib/telegram.ts` — raw validation/parsing helpers
- `lib/telegram-auth.ts` — unified viewer/auth layer
- `lib/auth.ts` — web fallback session layer
- `app/api/...` — route handlers, все через единый helper
- `app/login/*` — browser fallback login
- `app/profile/*` — profile и progress
- `app/course/*`, `app/module/*`, `app/lesson/*` — main learning flow

## Smoke tests

### Auth smoke
- Telegram WebView с валидным `initData` → authorized
- Browser without session → guest / 401 where expected
- Browser with valid session → same user context on all protected route

### Route consistency smoke
Проверять одинаковый auth state на:
- `/api/profile`
- `/api/courses`
- `/api/course/[slug]`
- `/api/module/[slug]`
- `/api/lessons/[slug]`
- `/api/progress`

### Invite smoke
- пользователь получает персональную ссылку;
- старая ссылка становится невалидной после новой выдачи;
- другой пользователь не может использовать чужую ссылку;
- после успешного входа invite → `used`.

### Deploy smoke
- container rebuilt and recreated;
- app healthy;
- public route 200/401/403 совпадают с ожиданием;
- login fallback route даёт ожидаемый redirect.

## Practical decision points

### Если Mini App только внутри Telegram
Можно жить почти полностью на `initData-first` path.

### Если есть browser fallback
Нужен secondary session layer и **обязательная унификация route handlers**.

### Если есть private club/chat
Нужны персональные invite links + join request validation.

## Related files in this skill
- `checklists/pre-deploy.md` — общий pre-deploy checklist
- `references/deployment-guide.md` — deploy notes
- `references/tma-sdk-hooks.md` — SDK hooks
- `references/mcp-telegram-tools.md` — Telegram MCP reference
- `docs/nextjs-auth-session-pattern.md` — канонический auth/session паттерн для Next.js TMA
- `docs/browser-fallback-ux-pattern.md` — surface-aware UX pattern для browser fallback
- `docs/launch-ready-starter-map.md` — как собирать новый стартовый слой из готовых кусков
- `docs/production-pitfalls.md` — реальные баги и red flags
- `examples/nextjs-auth-session-starter/` — готовые reusable snippets для старта нового проекта

## Red flags
- auth logic размазана по route handlers вручную;
- `/profile` и остальные экраны работают по-разному;
- user identity берётся из client payload без проверки;
- отсутствует clear fallback story вне Telegram;
- invite links не персональные;
- production smoke не отличает guest / session / initData сценарии.

## What to do first when this skill is loaded
1. Выясни entry surfaces.
2. Проверь auth model: `initData-only` vs `initData + session fallback`.
3. Найди, есть ли единый viewer helper.
4. Если helper нет — создай его до любых UI правок.
5. Если helper уже есть, но browser UX размазан — подними общий surface/error слой и единый browser notice component.
6. Только потом трогай pages, payments и deploy.
