# Telegram Mini App production pitfalls

## 1. Snake case Telegram payload
Нужно нормализовать поля вроде:
- `first_name`
- `last_name`
- `language_code`
- `is_premium`
- `photo_url`
- `allows_write_to_pm`

## 2. Raw Prisma JSON response
Не отдавать raw Prisma objects, если там может быть `BigInt`.

## 3. Profile-only auth fallback
Если session fallback реализован только в `/api/profile`, пользователь будет видеть себя авторизованным только в профиле.

## 4. Public-domain internal bridge
Если internal sync идёт через public domain, при restart/redeploy могут быть transient `502`/timeout.

## 5. Invite links must be personal
Для private chat / club link должна быть:
- персональная,
- отзываемая,
- проверяемая на join request,
- помечаемая как `used`.

## 6. Shared docker hostname drift
Не использовать слишком generic DB hostnames в shared runtime.
