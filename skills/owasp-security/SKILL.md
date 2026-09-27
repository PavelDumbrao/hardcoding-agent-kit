---
name: owasp-security
description: Применение принципов OWASP Top 10 для обеспечения безопасности веб-приложений.
---

> **Примечание для экспортной версии:** ниже чувствительные IP, домены, пути, SSH-цели и другие infra-значения заменены на примеры и placeholders вида `<YOUR_...>`. Если ИИ-агенту нужны реальные значения, он должен **подставить реальные данные пользователя** или **сначала запросить их у пользователя**, а не использовать примеры как есть.


# OWASP Security Skill

## OWASP Top 10 (2021) — с конкретными мерами

### 1. Broken Access Control (A01)
**Проблема:** Пользователь может получить доступ к чужим данным.
```javascript
// ❌ Проверка только на фронтенде
if (user.role === 'admin') showAdminPanel();

// ✅ Проверка на сервере
app.get('/admin', requireRole('admin'), (req, res) => { ... });
```
**Меры:**
- Deny by default — доступ только по явному разрешению.
- Проверяй владельца ресурса: `WHERE user_id = req.user.id`.
- Rate limiting для API.

### 2. Cryptographic Failures (A02)
```python
# ❌ MD5/SHA1 для паролей
hashlib.md5(password.encode()).hexdigest()

# ✅ bcrypt
import bcrypt
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12))
```
**Меры:** HTTPS (TLS 1.2+), bcrypt/Argon2 для паролей, AES-256 для данных at rest.

### 3. Injection (A03)
```javascript
// ❌ Конкатенация SQL
db.query(`SELECT * FROM users WHERE id = '${userId}'`);

// ✅ Параметризованный запрос
db.query('SELECT * FROM users WHERE id = $1', [userId]);
```
**Меры:** ORM (Prisma, Drizzle), параметризованные запросы, экранирование вывода.

### 4. Insecure Design (A04)
**Меры:**
- Threat Modeling на этапе проектирования.
- Принцип наименьших привилегий.
- Разделение обязанностей (separation of concerns).

### 5. Security Misconfiguration (A05)
```bash
# ❌ В продакшене
DEBUG=true
EXPOSE_ERROR_STACK=true

# ✅ В продакшене
NODE_ENV=production
DEBUG=false
```
**Меры:** Удаляй дефолтные пароли, отключай debug, убирай неиспользуемые сервисы.

### 6. Vulnerable Components (A06)
```bash
# Регулярно проверяй зависимости
npm audit
npm audit fix
pip-audit
```
**Меры:** Dependabot/Renovate для автообновлений, `npm audit` в CI/CD.

### 7. Authentication Failures (A07)
```javascript
// Rate limiting для логина
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 минут
  max: 5, // 5 попыток
  message: 'Слишком много попыток входа'
});
app.post('/login', loginLimiter, loginHandler);
```
**Меры:** MFA, сильные пароли (zxcvbn), rate limiting, secure session management.

### 8. Data Integrity Failures (A08)
```javascript
// ✅ Проверка подписи JWT
const jwt = require('jsonwebtoken');
try {
  const decoded = jwt.verify(token, process.env.JWT_SECRET);
} catch (err) {
  return res.status(401).json({ error: 'Недействительный токен' });
}
```
**Меры:** Проверяй подписи JWT, используй SRI для CDN-скриптов, безопасные CI/CD пайплайны.

### 9. Logging & Monitoring Failures (A09)
```javascript
// ✅ Логируй security-события
logger.warn('Failed login attempt', {
  ip: req.ip,
  username: req.body.username,
  timestamp: new Date().toISOString()
});
```
**Меры:** Логируй входы, ошибки авторизации, изменения прав. Настрой алерты.

### 10. SSRF (A10)
```python
# ❌ Пользователь контролирует URL
requests.get(user_provided_url)

# ✅ Валидация URL
from urllib.parse import urlparse
parsed = urlparse(user_provided_url)
if parsed.hostname not in ALLOWED_HOSTS:
    raise ValueError("Недопустимый хост")
```

## Security Headers
```javascript
const helmet = require('helmet');
app.use(helmet());

// Или вручную:
app.use((req, res, next) => {
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '0'); // Устарел, используй CSP
  res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains');
  res.setHeader('Content-Security-Policy', "default-src 'self'");
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  next();
});
```

## Безопасные Cookies
```javascript
res.cookie('session', sessionId, {
  httpOnly: true,    // Недоступна из JavaScript
  secure: true,      // Только через HTTPS
  sameSite: 'strict', // Защита от CSRF
  maxAge: 3600000,   // 1 час
  path: '/',
});
```

## Валидация входных данных
```javascript
// Используй Zod для валидации
import { z } from 'zod';

const userSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().min(0).max(150),
});

const result = userSchema.safeParse(req.body);
if (!result.success) {
  return res.status(400).json({ errors: result.error.issues });
}
```

## Автоматическое тестирование
- **SAST**: ESLint security rules, Semgrep, SonarQube
- **DAST**: OWASP ZAP, Nuclei
- **Dependency**: `npm audit`, `pip-audit`, Snyk
- **Secrets**: git-secrets, TruffleHog

## Чек-лист перед деплоем
- [ ] XSS: все данные экранируются перед выводом
- [ ] SQL Injection: параметризованные запросы везде
- [ ] CSRF-токены для POST/PUT/DELETE
- [ ] Security headers (Helmet.js / ручные)
- [ ] Cookies: HttpOnly, Secure, SameSite
- [ ] Пароли: bcrypt/Argon2, не менее 8 символов
- [ ] Rate limiting на login/register/API
- [ ] Зависимости проверены (`npm audit`)
- [ ] Секреты в .env, не в коде
- [ ] Debug отключён в продакшене
