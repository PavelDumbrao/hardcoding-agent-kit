---
name: supabase-integration
description: Интеграция Supabase в React/TypeScript приложения — клиент, аутентификация, БД, RLS, Edge Functions, Storage, типизация. Используй при работе с Supabase в frontend или backend.
---

> **Примечание для экспортной версии:** ниже чувствительные IP, домены, пути, SSH-цели и другие infra-значения заменены на примеры и placeholders вида `<YOUR_...>`. Если ИИ-агенту нужны реальные значения, он должен **подставить реальные данные пользователя** или **сначала запросить их у пользователя**, а не использовать примеры как есть.


# Supabase Integration

## Routing note

Этот skill покрывает **обычную интеграцию Supabase в приложение**:
- SDK клиент;
- auth;
- CRUD;
- RLS;
- Storage;
- типизацию;
- обычные Edge Functions как часть app/backend логики.

Если задача про **официальный Supabase MCP сервер** — feature groups, OAuth, `list_tables`, `execute_sql`, `deploy_edge_function`, pgvector smoke-tests, remote MCP URL, live Edge Functions и automatic embeddings pipeline — используй отдельный skill:
- `supabase-mcp`

Если задача specifically про **Gemini Embedding 2 / `gemini-embedding-2-preview`** — размерности, task formatting, multimodal limits, chunking длинных уроков, retrieval strategy и embedding design — используй отдельный skill:
- `gemini-embedding-2-preview`

## Инициализация клиента

Для **Next.js** (`process.env`):
```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

export const supabase = createClient<Database>(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
)
```

Для **Vite** (`import.meta.env`):
```typescript
// src/lib/supabase.ts
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY
)
```

🚨 После изменения `.env.local` — MUST перезапустить приложение. Просто обновить страницу не поможет.

**Типичные ошибки подключения:**
- `Invalid API key` — проверь ключи в `.env`, убедись в правильных именах переменных
- `relation does not exist` — таблица не создана, вернись к созданию таблицы

## Создание проекта в Supabase

1. Зайди на **supabase.com** → "Start your project" → "Continue with GitHub"
2. Нажми **"New Project"**, заполни:
   - **Name** — латиницей, например `my-app`
   - **Database Password** — нажми **Generate**, скопируй и сохрани в менеджер паролей
   - **Region** — для СНГ выбирай **Frankfurt**
3. Подожди 1-2 минуты пока создаётся проект

### Где взять ключи

Project Settings (шестерёнка слева) → **API**:
- **Project URL** → это `SUPABASE_URL`
- **Data API** → ключ **anon public** → это `SUPABASE_ANON_KEY`

🚨 NEVER передавать ключи в чаты или хранить в обычных заметках. Только менеджер паролей или `.env` файл.

💡 **Free план:** проект "засыпает" после 7 дней без активности. Просыпается за ~1 минуту при первом запросе. Данные не теряются.

## Переменные окружения

🚨 MUST проверить перед стартом:

Для **Next.js**:
```env
NEXT_PUBLIC_SUPABASE_URL=https://xxxx.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...
SUPABASE_SERVICE_ROLE_KEY=eyJ...  # только на сервере, NEVER на клиенте
```

Для **Vite** (React):
```env
VITE_SUPABASE_URL=https://xxxx.supabase.co
VITE_SUPABASE_ANON_KEY=eyJ...
```

Попроси Claude создать файл: _"Создай файл .env.local с переменными VITE_SUPABASE_URL и VITE_SUPABASE_ANON_KEY"_

## Создание таблиц

Используй **SQL Editor** (левое меню в Supabase Dashboard) — Claude даёт SQL, ты копируешь и вставляешь.

Пример запроса к Claude: _"Я делаю приложение для задач. Напиши SQL-команду для создания таблицы в Supabase."_

Типичная структура таблицы:
```sql
CREATE TABLE tasks (
  id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  created_at timestamptz DEFAULT now(),
  title text NOT NULL,
  user_id uuid REFERENCES auth.users(id)
);
```

После выполнения: ✅ `"Success. No rows returned"` — таблица создана.

**Соглашения по именованию:**
- Имена таблиц — латиница, нижний регистр: `tasks`, `users`, `orders`
- Всегда добавляй `id` (uuid) и `created_at` (timestamptz)

**Типичные ошибки:**
- `relation already exists` — таблица с таким именем уже есть, удали или переименуй
- Скопируй ошибку → отправь Claude → он исправит

## Типизация БД

Генерация типов из схемы:
```bash
npx supabase gen types typescript --project-id <project-id> > lib/database.types.ts
```

## CRUD операции

```typescript
// Чтение
const { data, error } = await supabase
  .from('users')
  .select('*')
  .eq('id', userId)

// Создание
const { data, error } = await supabase
  .from('users')
  .insert({ name: 'Иван', email: 'ivan@example.com' })
  .select()

// Обновление
const { data, error } = await supabase
  .from('users')
  .update({ name: 'Пётр' })
  .eq('id', userId)

// Удаление
const { error } = await supabase
  .from('users')
  .delete()
  .eq('id', userId)
```

### Паттерн: загрузить при старте + обновить после создания

```typescript
// Загружаем при монтировании компонента
useEffect(() => {
  loadTasks()
}, [])

async function loadTasks() {
  const { data, error } = await supabase.from('tasks').select('*')
  if (error) console.error('Ошибка загрузки:', error.message)
  else setTasks(data)
}

async function createTask(title: string) {
  const { error } = await supabase.from('tasks').insert({ title })
  if (error) console.error('Ошибка создания:', error.message)
  else loadTasks() // обновляем список после создания
}
```

## Типы ключей Supabase

| Ключ | Где использовать | Доступ |
|---|---|---|
| `anon public` | Браузер, фронтенд | Ограниченный (через RLS) |
| `service_role` | Только сервер/webhook | Полный доступ ко всей БД |

🚨 `service_role` ключ в браузере = любой пользователь получает полный доступ к БД. NEVER.

## Аутентификация

```typescript
// Вход через email
const { data, error } = await supabase.auth.signInWithPassword({
  email: 'user@example.com',
  password: 'password'
})

// Вход через Google
const { data, error } = await supabase.auth.signInWithOAuth({
  provider: 'google'
})

// Выход
await supabase.auth.signOut()

// Текущий пользователь
const { data: { user } } = await supabase.auth.getUser()
```

## RLS (Row Level Security)

🚨 MUST включать RLS для всех таблиц с пользовательскими данными.

```sql
-- Включить RLS
ALTER TABLE users ENABLE ROW LEVEL SECURITY;

-- Политика: пользователь видит только свои данные
CREATE POLICY "users_own_data" ON users
  FOR ALL USING (auth.uid() = user_id);
```

## Storage (файлы)

```typescript
// Загрузка файла
const { data, error } = await supabase.storage
  .from('avatars')
  .upload(`${userId}/avatar.png`, file)

// Получение публичного URL
const { data } = supabase.storage
  .from('avatars')
  .getPublicUrl(`${userId}/avatar.png`)
```

## Realtime подписки

```typescript
const channel = supabase
  .channel('messages')
  .on('postgres_changes', {
    event: 'INSERT',
    schema: 'public',
    table: 'messages'
  }, (payload) => {
    console.log('Новое сообщение:', payload.new)
  })
  .subscribe()

// Отписка при размонтировании
return () => supabase.removeChannel(channel)
```

## Тарифы (актуально на 2025)

| Тариф | Цена | БД | Особенности |
|---|---|---|---|
| Free | $0 | 500 МБ | 2 проекта, засыпает через 7 дней |
| Pro | $25/мес | 8 ГБ | Не засыпает, ежедневные бэкапы |

## Правила работы

- 🚨 NEVER использовать `service_role` ключ на клиенте
- MUST включать RLS для таблиц с пользовательскими данными
- MUST обрабатывать `error` из каждого запроса
- SHOULD генерировать типы из схемы БД
- SHOULD использовать `select()` после `insert/update` для получения данных
- При работе с Next.js — использовать `@supabase/ssr` вместо `@supabase/auth-helpers-nextjs`