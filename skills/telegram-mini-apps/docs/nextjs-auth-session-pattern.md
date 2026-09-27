# Next.js Telegram Mini App — auth/session pattern

## Цель
Сделать Mini App, где:
- внутри Telegram WebView auth идёт через `initData`;
- в браузере работает fallback session;
- все route handlers видят пользователя одинаково;
- browser UX не маскирует guest/session-expired состояния под generic error.

## Канонический flow
1. Клиент берёт raw `window.Telegram.WebApp.initData`.
2. Клиент отправляет его в `x-telegram-init-data`.
3. Backend валидирует `initData`.
4. Backend извлекает Telegram user и строит `viewer context`.
5. Если `initData` нет, backend может попробовать `auth()` / session fallback.
6. Все route handlers используют один и тот же helper.

## Backend layers

### 1. Низкоуровневый Telegram слой
```ts
export function validateTelegramInitData(initData: string): TelegramValidationResult
export function getTelegramUser(initData: string): TelegramUserPayload | null
export function normalizeTelegramUser(rawUser: unknown): TelegramUserPayload | null
```

Здесь важно:
- валидировать подпись;
- нормализовать snake_case поля;
- не доверять `user_id` без validation.

### 2. Unified viewer helper
```ts
export async function getViewerContext(initData: string | null, courseSlug?: string): Promise<ViewerContext>
export async function getViewerContextWithSessionFallback(request: Request, courseSlug?: string): Promise<ViewerContext>
```

Канонический паттерн:
```ts
export async function getViewerContextWithSessionFallback(request: Request, courseSlug?: string) {
  const initData = getInitDataFromRequest(request);
  const viewer = await getViewerContext(initData, courseSlug);

  if (viewer.isAuthenticated && viewer.user) return viewer;
  if (initData) return viewer;

  const session = await auth();
  const sessionUserId = Number(session?.user?.id);
  if (!Number.isInteger(sessionUserId) || sessionUserId <= 0) return viewer;

  const sessionUser = await prisma.user.findUnique({ where: { id: sessionUserId } });
  if (!sessionUser) return viewer;

  return {
    ...viewer,
    isAuthenticated: true,
    authError: null,
    telegramUser: buildTelegramUserFromStoredUser(sessionUser),
    user: sessionUser,
    access: await resolveUserAccess(sessionUser.id, courseSlug),
  };
}
```

### 3. Route handler pattern
```ts
export async function GET(request: NextRequest) {
  const viewer = await getViewerContextWithSessionFallback(request);

  if (!viewer.user) {
    return NextResponse.json(
      { error: viewer.authError ?? 'Неавторизован' },
      { status: 401 },
    );
  }

  // business logic
}
```

## Client transport layer
Канонический client helper:
```ts
export function getTelegramInitData(): string | null {
  if (typeof window === 'undefined') return null;
  return window.Telegram?.WebApp?.initData || null;
}

export function buildTelegramHeaders(input?: HeadersInit): Headers {
  const headers = new Headers(input);
  const initData = getTelegramInitData();
  if (initData) headers.set('x-telegram-init-data', initData);
  return headers;
}
```

Если есть browser fallback, добавь ещё surface/error слой:
```ts
export type MiniAppSurface = 'telegram' | 'browser';

export class MiniAppApiError extends Error {
  constructor(message: string, public status: number, public payload?: unknown) {
    super(message);
    this.name = 'MiniAppApiError';
  }
}

export function getMiniAppSurface(): MiniAppSurface {
  return getTelegramInitData() ? 'telegram' : 'browser';
}

export function isMiniAppApiError(error: unknown): error is MiniAppApiError {
  return error instanceof MiniAppApiError;
}
```

## Browser fallback UX policy

### Read-only pages
Примеры:
- `/`
- `/learn`
- `/course/[slug]`
- `/module/[slug]`
- `/access`

Поведение:
- browser guest может смотреть экран;
- UI явно говорит, что это guest/browser mode;
- CTA ведёт на `/login/telegram`;
- browser authenticated user видит, что session уже активна.

### Sensitive mutation pages
Пример:
- запись прогресса в уроке

Поведение:
- guest browser user может читать контент, если он открыт;
- mutation action gated до login;
- `401` трактуется как signal для re-login, а не как generic error.

### Checkout pages
Примеры:
- `/pay/course`
- `/club`

Поведение:
- browser guest не должен молча запускать checkout;
- checkout button gated до browser login;
- после login пользователь продолжает checkout в том же surface.

## Canonical browser notice
Для этого хорошо работает единый UI primitive вроде `BrowserAuthNotice`:
```tsx
<BrowserAuthNotice
  isAuthenticated={viewerIsAuthenticated}
  guestTitle="Для browser checkout сначала нужен вход"
  guestDescription="..."
  authenticatedTitle="Веб-сессия активна"
  authenticatedDescription="..."
  guestActions={[
    { label: 'Войти через Телеграм', href: '/login/telegram' },
    { label: 'Открыть профиль', href: '/profile' },
  ]}
/>
```

## Что этот паттерн предотвращает
- `/profile` работает, `/learn` ведёт себя как guest;
- web fallback есть только на одном route;
- auth/session logic размазана по handlers;
- browser user видит generic error вместо понятного next step;
- checkout и progress ломаются без явного объяснения.

## Reusable starter
Если нужно быстро собрать новый проект, смотри:
- `docs/browser-fallback-ux-pattern.md`
- `docs/launch-ready-starter-map.md`
- `examples/nextjs-auth-session-starter/`
