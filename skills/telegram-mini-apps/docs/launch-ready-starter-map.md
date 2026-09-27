# Launch-ready starter map for Telegram Mini Apps

Этот документ нужен, чтобы быстро собрать **новый Telegram Mini App** на уже подтверждённом auth/session паттерне без копирования всего старого проекта.

## Что брать сразу
Из `examples/nextjs-auth-session-starter/` можно почти без изменений брать:
- `lib/miniapp-client.ts`
- `components/ui/BrowserAuthNotice.tsx`
- `app/login/page.tsx`
- `app/login/telegram/route.ts`
- `.env.example`

## Что брать как reference, а не как слепую копию
- `snippets/profile-page.tsx`
- `snippets/checkout-page.tsx`
- `snippets/progress-action.tsx`

Это не «готовый полный продукт», а проверенные куски для surface-aware UX.

## Что нужно добавить из backend слоя
Новый проект всё равно должен реализовать:
- `lib/telegram.ts`
- `lib/telegram-auth.ts`
- `lib/auth.ts` (если есть browser fallback)
- `getViewerContextWithSessionFallback()`
- свою access model
- свои route handlers

Подробности смотри в `docs/nextjs-auth-session-pattern.md`.

## Минимальный стартовый порядок
1. Подними Next.js app.
2. Подключи `lib/miniapp-client.ts`.
3. Подключи `BrowserAuthNotice`.
4. Сделай `/login` и `/login/telegram`.
5. Реализуй backend helper `getViewerContextWithSessionFallback()`.
6. Переведи route handlers на единый helper.
7. Переведи read-only pages на browser notice.
8. Переведи checkout / progress pages на gated browser UX.
9. Прогони smoke-check.

## Что заменить под свой продукт
- copy и CTA тексты
- product routes (`/course`, `/club`, `/pay` и т.д.)
- access model / rights
- payment provider
- user/profile shape
- Prisma models / DB слой

## Когда starter считается подключённым корректно
- browser guest видит понятные CTA на login, а не баги;
- browser authenticated user видит те же персональные данные, что и в профиле;
- checkout не запускается без session;
- progress mutation не ломается без объяснения;
- `/login/telegram` даёт ожидаемый redirect.
