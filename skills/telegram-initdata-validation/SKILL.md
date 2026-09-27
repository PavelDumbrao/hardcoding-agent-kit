---
name: telegram-initdata-validation
description: Валидация Telegram Mini App initData через HMAC-SHA256 для безопасной аутентификации. Используй при работе с Telegram Mini Apps и защите от подмены user_id.
---

> **Примечание для экспортной версии:** ниже чувствительные IP, домены, пути, SSH-цели и другие infra-значения заменены на примеры и placeholders вида `<YOUR_...>`. Если ИИ-агенту нужны реальные значения, он должен **подставить реальные данные пользователя** или **сначала запросить их у пользователя**, а не использовать примеры как есть.


# Telegram InitData Validation

## 🎯 Когда использовать этот skill

- Валидация данных от Telegram Mini App на сервере
- Защита от подмены `telegram_user_id`
- Извлечение безопасных данных пользователя
- Реализация secure layer для Mini App
- Проверка подлинности Telegram initData
- Предотвращение replay attacks

## 🚨 Критическое правило безопасности

**НИКОГДА не доверяй `user_id` или `telegram_user_id`, пришедшим с клиента напрямую!**

Всегда валидируй `initData` на сервере и извлекай `telegram_user_id` только после успешной проверки HMAC-SHA256 подписи.

## 🔐 Как работает валидация

Telegram подписывает `initData` используя HMAC-SHA256 с секретным ключом, полученным из bot token.

### Алгоритм валидации (официальный)

1. Получить `initData` как query string
2. Извлечь параметр `hash`
3. Удалить `hash` из параметров
4. Отсортировать оставшиеся параметры по ключу (алфавитный порядок)
5. Создать `data_check_string` в формате `key=value\nkey=value\n...`
6. Создать `secret_key = HMAC-SHA256(bot_token, "WebAppData")`
7. Вычислить `calculated_hash = HMAC-SHA256(data_check_string, secret_key)`
8. Сравнить `calculated_hash` с `hash` из initData

## 🚀 Быстрый старт

### Node.js / TypeScript
```typescript
import crypto from 'crypto'

function validateTelegramInitData(
  initData: string,
  botToken: string
): boolean {
  try {
    const urlParams = new URLSearchParams(initData)
    const hash = urlParams.get('hash')
    
    if (!hash) {
      return false
    }
    
    // Удалить hash и отсортировать
    urlParams.delete('hash')
    urlParams.sort()
    
    // Создать data-check-string
    const dataCheckArray: string[] = []
    for (const [key, value] of urlParams.entries()) {
      dataCheckArray.push(`${key}=${value}`)
    }
    const dataCheckString = dataCheckArray.join('\n')
    
    // Создать secret key
    const secretKey = crypto
      .createHmac('sha256', 'WebAppData')
      .update(botToken)
      .digest()
    
    // Вычислить hash
    const calculatedHash = crypto
      .createHmac('sha256', secretKey)
      .update(dataCheckString)
      .digest('hex')
    
    // Сравнить
    return calculatedHash === hash
  } catch (error) {
    console.error('Validation error:', error)
    return false
  }
}
```

### Deno (для Supabase Edge Functions)
```typescript
async function validateTelegramInitData(
  initData: string,
  botToken: string
): Promise<boolean> {
  try {
    const urlParams = new URLSearchParams(initData)
    const hash = urlParams.get('hash')
    
    if (!hash) {
      return false
    }
    
    urlParams.delete('hash')
    urlParams.sort()
    
    // Создать data-check-string
    let dataCheckString = ''
    for (const [key, value] of urlParams.entries()) {
      dataCheckString += `${key}=${value}\n`
    }
    dataCheckString = dataCheckString.slice(0, -1) // Удалить последний \n
    
    const encoder = new TextEncoder()
    
    // Создать secret key
    const secretKeyData = await crypto.subtle.importKey(
      'raw',
      encoder.encode('WebAppData'),
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    )
    
    const secretKey = await crypto.subtle.sign(
      'HMAC',
      secretKeyData,
      encoder.encode(botToken)
    )
    
    // Вычислить hash
    const hashKeyData = await crypto.subtle.importKey(
      'raw',
      secretKey,
      { name: 'HMAC', hash: 'SHA-256' },
      false,
      ['sign']
    )
    
    const calculatedHashBuffer = await crypto.subtle.sign(
      'HMAC',
      hashKeyData,
      encoder.encode(dataCheckString)
    )
    
    const calculatedHash = Array.from(new Uint8Array(calculatedHashBuffer))
      .map(b => b.toString(16).padStart(2, '0'))
      .join('')
    
    return calculatedHash === hash
  } catch (error) {
    console.error('Validation error:', error)
    return false
  }
}
```

## 📦 Извлечение данных пользователя

После успешной валидации можно безопасно извлечь данные пользователя.

```typescript
interface TelegramUser {
  id: number
  first_name: string
  last_name?: string
  username?: string
  language_code?: string
  is_premium?: boolean
  photo_url?: string
}

function extractTelegramUser(initData: string): TelegramUser | null {
  try {
    const urlParams = new URLSearchParams(initData)
    const userParam = urlParams.get('user')
    
    if (!userParam) {
      return null
    }
    
    const user = JSON.parse(decodeURIComponent(userParam))
    return user as TelegramUser
  } catch (error) {
    console.error('Error extracting user:', error)
    return null
  }
}
```

## 🎨 Архитектурные паттерны

### Паттерн 1: Supabase Edge Function (Secure Layer)
```typescript
// supabase/functions/validate-telegram/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

serve(async (req) => {
  // CORS headers
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type'
      }
    })
  }
  
  try {
    const { initData, question, lesson_id, lesson_title, source } = await req.json()
    
    // 1. Валидация initData
    const botToken = Deno.env.get('TELEGRAM_BOT_TOKEN')
    if (!botToken) {
      throw new Error('Bot token not configured')
    }
    
    const isValid = await validateTelegramInitData(initData, botToken)
    
    if (!isValid) {
      return new Response(
        JSON.stringify({
          ok: false,
          error: {
            code: 'INVALID_INIT_DATA',
            message: 'Invalid Telegram initData'
          }
        }),
        {
          status: 401,
          headers: { 'Content-Type': 'application/json' }
        }
      )
    }
    
    // 2. Извлечь telegram_user_id
    const user = extractTelegramUser(initData)
    if (!user) {
      return new Response(
        JSON.stringify({
          ok: false,
          error: {
            code: 'USER_NOT_FOUND',
            message: 'User data not found in initData'
          }
        }),
        { status: 400, headers: { 'Content-Type': 'application/json' } }
      )
    }
    
    // 3. Сформировать memory_key
    const memory_key = `tg_${user.id}`
    
    // 4. Вызвать AI webhook
    const webhookUrl = Deno.env.get('VASYA_WEBHOOK_URL')
    const webhookSecret = Deno.env.get('VASYA_WEBHOOK_SECRET')
    
    if (!webhookUrl) {
      throw new Error('Webhook URL not configured')
    }
    
    const webhookResponse = await fetch(webhookUrl, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(webhookSecret && { 'X-Webhook-Secret': webhookSecret })
      },
      body: JSON.stringify({
        telegram_user_id: user.id.toString(),
        memory_key,
        question,
        lesson_id,
        lesson_title,
        source,
        app_context: 'club_lms'
      })
    })
    
    if (!webhookResponse.ok) {
      throw new Error(`Webhook failed: ${webhookResponse.statusText}`)
    }
    
    const webhookData = await webhookResponse.json()
    
    // 5. Нормализовать ответ
    const answer = typeof webhookData === 'string' 
      ? webhookData 
      : webhookData.answer || webhookData.response || JSON.stringify(webhookData)
    
    return new Response(
      JSON.stringify({
        ok: true,
        data: {
          answer,
          sources: webhookData.sources || [],
          suggestions: webhookData.suggestions || []
        }
      }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )
  } catch (error) {
    console.error('Error:', error)
    return new Response(
      JSON.stringify({
        ok: false,
        error: {
          code: 'INTERNAL_ERROR',
          message: error.message || 'Internal server error'
        }
      }),
      {
        status: 500,
        headers: { 'Content-Type': 'application/json' }
      }
    )
  }
})
```

### Паттерн 2: Express.js Middleware
```typescript
import { Request, Response, NextFunction } from 'express'

interface AuthenticatedRequest extends Request {
  telegramUser?: TelegramUser
}

export function validateTelegramMiddleware(
  req: AuthenticatedRequest,
  res: Response,
  next: NextFunction
) {
  const initData = req.headers['x-telegram-init-data'] as string
  
  if (!initData) {
    return res.status(400).json({
      ok: false,
      error: { code: 'MISSING_INIT_DATA', message: 'Missing initData' }
    })
  }
  
  const botToken = process.env.TELEGRAM_BOT_TOKEN
  if (!botToken) {
    return res.status(500).json({
      ok: false,
      error: { code: 'SERVER_ERROR', message: 'Bot token not configured' }
    })
  }
  
  const isValid = validateTelegramInitData(initData, botToken)
  
  if (!isValid) {
    return res.status(401).json({
      ok: false,
      error: { code: 'INVALID_INIT_DATA', message: 'Invalid initData' }
    })
  }
  
  const user = extractTelegramUser(initData)
  if (!user) {
    return res.status(400).json({
      ok: false,
      error: { code: 'USER_NOT_FOUND', message: 'User not found' }
    })
  }
  
  req.telegramUser = user
  next()
}

// Использование
app.post('/api/ask-vasya', validateTelegramMiddleware, async (req, res) => {
  const user = req.telegramUser!
  const { question, lesson_id } = req.body
  
  // Безопасно использовать user.id
  const memory_key = `tg_${user.id}`
  
  // ...
})
```

### Паттерн 3: Frontend отправка initData
```typescript
// lib/api/askVasya.ts
import { useTelegram } from '@/hooks/useTelegram'

export async function askVasya(
  question: string,
  lessonId: string,
  lessonTitle: string
) {
  const { initData } = useTelegram()
  
  if (!initData) {
    throw new Error('Telegram initData not available')
  }
  
  const response = await fetch('/api/ask-vasya', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Telegram-Init-Data': initData // Отправить initData в header
    },
    body: JSON.stringify({
      question,
      lesson_id: lessonId,
      lesson_title: lessonTitle,
      source: 'miniapp'
    })
  })
  
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.error?.message || 'Request failed')
  }
  
  return response.json()
}
```

## 🔒 Дополнительные меры безопасности

### 1. Проверка времени (защита от replay attacks)
```typescript
function validateWithTimestamp(
  initData: string,
  botToken: string,
  maxAgeSeconds: number = 3600 // 1 час
): boolean {
  // Сначала валидация hash
  if (!validateTelegramInitData(initData, botToken)) {
    return false
  }
  
  // Проверка auth_date
  const urlParams = new URLSearchParams(initData)
  const authDate = urlParams.get('auth_date')
  
  if (!authDate) {
    return false
  }
  
  const authTimestamp = parseInt(authDate, 10)
  const currentTimestamp = Math.floor(Date.now() / 1000)
  const age = currentTimestamp - authTimestamp
  
  if (age > maxAgeSeconds) {
    console.warn(`InitData expired: ${age}s old (max ${maxAgeSeconds}s)`)
    return false
  }
  
  return true
}
```

### 2. Whitelist пользователей (опционально)
```typescript
function isUserAllowed(userId: number): boolean {
  const allowedUsers = process.env.ALLOWED_TELEGRAM_USERS?.split(',').map(Number) || []
  
  // Если whitelist пустой, разрешить всем
  if (allowedUsers.length === 0) {
    return true
  }
  
  return allowedUsers.includes(userId)
}

// Использование
const user = extractTelegramUser(initData)
if (!user || !isUserAllowed(user.id)) {
  return res.status(403).json({
    ok: false,
    error: { code: 'FORBIDDEN', message: 'Access denied' }
  })
}
```

### 3. Rate limiting
```typescript
// Простой in-memory rate limiter
const requestCounts = new Map<number, { count: number; resetAt: number }>()

function checkRateLimit(
  userId: number,
  maxRequests: number = 10,
  windowMs: number = 60000 // 1 минута
): boolean {
  const now = Date.now()
  const userLimit = requestCounts.get(userId)
  
  if (!userLimit || now > userLimit.resetAt) {
    requestCounts.set(userId, {
      count: 1,
      resetAt: now + windowMs
    })
    return true
  }
  
  if (userLimit.count >= maxRequests) {
    return false
  }
  
  userLimit.count++
  return true
}
```

## ⚠️ Частые ошибки

### 1. Неправильный порядок создания secret key
```typescript
// ❌ НЕПРАВИЛЬНО
const secretKey = crypto
  .createHmac('sha256', botToken)
  .update('WebAppData')
  .digest()

// ✅ ПРАВИЛЬНО
const secretKey = crypto
  .createHmac('sha256', 'WebAppData')
  .update(botToken)
  .digest()
```

### 2. Забыть отсортировать параметры
```typescript
// ❌ НЕПРАВИЛЬНО
const dataCheckString = [...urlParams.entries()]
  .map(([k, v]) => `${k}=${v}`)
  .join('\n')

// ✅ ПРАВИЛЬНО
urlParams.sort() // Обязательно!
const dataCheckString = [...urlParams.entries()]
  .map(([k, v]) => `${k}=${v}`)
  .join('\n')
```

### 3. Неправильный формат data-check-string
```typescript
// ❌ НЕПРАВИЛЬНО (запятая вместо \n)
const dataCheckString = [...urlParams.entries()]
  .map(([k, v]) => `${k}=${v}`)
  .join(',')

// ✅ ПРАВИЛЬНО (перенос строки \n)
const dataCheckString = [...urlParams.entries()]
  .map(([k, v]) => `${k}=${v}`)
  .join('\n')
```

### 4. Доверять user_id с клиента
```typescript
// ❌ ОПАСНО!
app.post('/api/data', (req, res) => {
  const { user_id } = req.body // Легко подделать!
  // ...
})

// ✅ БЕЗОПАСНО
app.post('/api/data', validateTelegramMiddleware, (req, res) => {
  const user_id = req.telegramUser!.id // Проверено!
  // ...
})
```

## 🎯 Best Practices

### 1. Всегда валидируй на сервере
Никогда не валидируй initData на клиенте — это бессмысленно для безопасности.

### 2. Храни bot token в секретах
```env
# ✅ В .env (не коммитить!)
TELEGRAM_BOT_TOKEN="<REDACTED>"

# ✅ В Supabase Edge Functions secrets
supabase secrets set TELEGRAM_BOT_TOKEN=123456:ABC-DEF...

# ❌ НИКОГДА в коде
const BOT_TOKEN = "<REDACTED>"
```

### 3. Логируй попытки валидации
```typescript
function validateWithLogging(initData: string, botToken: string): boolean {
  const isValid = validateTelegramInitData(initData, botToken)
  
  if (!isValid) {
    console.warn('Invalid initData attempt:', {
      timestamp: new Date().toISOString(),
      initData: initData.substring(0, 50) + '...' // Не логировать полностью
    })
  }
  
  return isValid
}
```

### 4. Используй HTTPS везде
Telegram Mini Apps требуют HTTPS. В dev используй:
- `mkcert` для локальных сертификатов
- `ngrok` для туннелирования
- Vite с `--https` флагом

## 📖 Тестирование

### Юнит-тест (Jest)
```typescript
import { validateTelegramInitData } from './validate'

describe('validateTelegramInitData', () => {
  const BOT_TOKEN = 'test-bot-token'
  
  it('should validate correct initData', () => {
    const initData = 'query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A279058397%7D&auth_date=1662771648&hash=c501b71e775f74ce10e377dea85a7ea24ecd640b223ea86dfe453e0eaed2e2b2'
    
    const isValid = validateTelegramInitData(initData, BOT_TOKEN)
    expect(isValid).toBe(true)
  })
  
  it('should reject tampered initData', () => {
    const initData = 'query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A999999999%7D&auth_date=1662771648&hash=c501b71e775f74ce10e377dea85a7ea24ecd640b223ea86dfe453e0eaed2e2b2'
    
    const isValid = validateTelegramInitData(initData, BOT_TOKEN)
    expect(isValid).toBe(false)
  })
  
  it('should reject missing hash', () => {
    const initData = 'query_id=AAHdF6IQAAAAAN0XohDhrOrc&user=%7B%22id%22%3A279058397%7D'
    
    const isValid = validateTelegramInitData(initData, BOT_TOKEN)
    expect(isValid).toBe(false)
  })
})
```

## 🔗 Полезные ссылки

- [Telegram Mini Apps Docs](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
- [HMAC-SHA256 Spec](https://datatracker.ietf.org/doc/html/rfc2104)
- [Supabase Edge Functions](https://supabase.com/docs/guides/functions)
- [Node.js Crypto](https://nodejs.org/api/crypto.html)
- [Web Crypto API (Deno)](https://deno.land/api@v1.30.0?s=crypto)

## 💡 Для Club LMS проекта

### Полный пример Edge Function
```typescript
// supabase/functions/ask-vasya/index.ts
import { serve } from 'https://deno.land/std@0.168.0/http/server.ts'

// Валидация initData
async function validateTelegramInitData(
  initData: string,
  botToken: string
): Promise<boolean> {
  // ... (код из примера выше)
}

// Извлечение пользователя
function extractTelegramUser(initData: string) {
  // ... (код из примера выше)
}

serve(async (req) => {
  if (req.method === 'OPTIONS') {
    return new Response(null, {
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'POST',
        'Access-Control-Allow-Headers': 'Content-Type'
      }
    })
  }
  
  try {
    const { initData, question, lesson_id, lesson_title } = await req.json()
    
    // Валидация
    const isValid = await validateTelegramInitData(
      initData,
      Deno.env.get('TELEGRAM_BOT_TOKEN')!
    )
    
    if (!isValid) {
      return new Response(
        JSON.stringify({ ok: false, error: 'Invalid initData' }),
        { status: 401 }
      )
    }
    
    // Извлечь user
    const user = extractTelegramUser(initData)
    const memory_key = `tg_${user.id}`
    
    // Вызвать webhook
    const response = await fetch(Deno.env.get('VASYA_WEBHOOK_URL')!, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        telegram_user_id: user.id.toString(),
        memory_key,
        question,
        lesson_id,
        lesson_title,
        source: 'miniapp',
        app_context: 'club_lms'
      })
    })
    
    const data = await response.json()
    
    return new Response(
      JSON.stringify({ ok: true, data }),
      {
        status: 200,
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        }
      }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ ok: false, error: error.message }),
      { status: 500 }
    )
  }
})
```

### Environment variables для Edge Function
```bash
# Установить секреты
supabase secrets set TELEGRAM_BOT_TOKEN=your-bot-token
supabase secrets set VASYA_WEBHOOK_URL=https://your-n8n-instance.com/webhook/vasya
supabase secrets set VASYA_WEBHOOK_SECRET=optional-secret

# Проверить секреты
supabase secrets list
```
