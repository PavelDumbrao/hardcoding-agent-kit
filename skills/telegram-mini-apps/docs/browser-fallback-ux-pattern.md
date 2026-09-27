# Browser fallback UX pattern for Telegram Mini Apps

Этот документ фиксирует не backend-auth, а именно **что должен видеть пользователь**, если Mini App открыт не внутри Telegram WebView, а в обычном браузере.

## Главная мысль
Browser fallback не должен быть «секретным режимом», который якобы поддерживается, но визуально выглядит как баг.

Пользователь всегда должен понимать:
- он сейчас внутри Telegram или в браузере;
- почему часть действий доступна, а часть gated;
- что сделать дальше;
- использует ли текущий экран уже активную browser session.

## Канонические состояния

| Surface | Auth state | Что говорить пользователю |
|---|---|---|
| Telegram WebView | initData valid | Ничего extra не нужно, всё работает как primary path |
| Browser | guest | Это browser fallback / read-only / для персональных действий нужен вход через Telegram |
| Browser | authenticated | Browser session уже активна, этот экран использует тот же viewer context |
| Browser | session expired | Войди через Telegram ещё раз и повтори действие |

## Page types

### 1. Read-only pages
Примеры:
- landing
- каталог
- курс
- модуль
- access/offers витрина

Правило:
- guest browser user может смотреть открытые данные;
- экран явно показывает browser notice;
- CTA ведёт на `/login/telegram` и/или `/profile`.

### 2. Profile / personal state pages
Пример:
- `/profile`

Правило:
- если session нет, экран не должен выглядеть как random error;
- нужен чёткий state: «подключить Telegram к профилю»;
- после login экран должен подтверждать, что browser session уже активна.

### 3. Mutation pages
Пример:
- отметка прогресса урока

Правило:
- открытый контент можно читать;
- mutation action gated до login;
- disabled state должен объяснять причину;
- `401` = re-login prompt, не generic fallback.

### 4. Checkout pages
Примеры:
- `/pay/course`
- `/club`

Правило:
- guest browser user не должен запускать checkout молча;
- пока session нет, checkout button gated;
- после login пользователь остаётся на том же surface и может продолжить flow.

## Канонический UI primitive
Для этих состояний лучше использовать один reusable component, например `BrowserAuthNotice`.

Что он должен уметь:
- guestTitle / guestDescription
- authenticatedTitle / authenticatedDescription
- guestActions / authenticatedActions
- одинаковый visual language на всех страницах

## CTA policy
- переход на auth route = только link (`<Link>` / `<a>`)
- не использовать `button + signIn()` как канонический UI pattern
- один и тот же visual action должен вести себя одинаково на всех экранах

## Red flags
- browser guest видит `Неавторизован`, но не понимает что делать дальше;
- `/profile` объясняет browser fallback, а `/pay/course` и `/club` — нет;
- progress action выглядит доступным, но потом падает `401`;
- browser authenticated user не видит подтверждения, что session уже активна.
