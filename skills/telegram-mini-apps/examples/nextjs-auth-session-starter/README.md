# Next.js auth/session starter for Telegram Mini Apps

Это не полный продукт, а **reusable starter-layer** для Mini App с:
- initData-first auth;
- optional browser session fallback;
- surface-aware UX для browser guest / browser authenticated user.

## Что внутри
- `lib/miniapp-client.ts` — client transport + surface/error helpers
- `components/ui/BrowserAuthNotice.tsx` — общий browser fallback notice
- `app/login/page.tsx` — browser login entry screen
- `app/login/telegram/route.ts` — server-side login redirect
- `snippets/profile-page.tsx` — пример profile UX
- `snippets/checkout-page.tsx` — пример gated checkout UX
- `snippets/progress-action.tsx` — пример gated mutation UX
- `.env.example` — обязательные env переменные для auth слоя

## Как использовать
1. Скопируй `lib/miniapp-client.ts`.
2. Скопируй `BrowserAuthNotice.tsx`.
3. Добавь `/login` и `/login/telegram`.
4. На backend реализуй `getViewerContextWithSessionFallback()`.
5. Раскати browser notice по ключевым экранам.
6. Переведи checkout / mutation flows на gated pattern.

## Что это НЕ покрывает целиком
- Prisma schema
- business-specific access logic
- payment provider integration
- complete route handlers for every product page

Для backend слоя смотри:
- `../../docs/nextjs-auth-session-pattern.md`
- `../../docs/browser-fallback-ux-pattern.md`
