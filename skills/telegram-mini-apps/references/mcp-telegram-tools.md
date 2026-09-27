# MCP Telegram Tools Reference

Полный справочник инструментов mcp-telegram для управления Telegram через Model Context Protocol.

## 🚀 Установка и настройка

### Установка mcp-telegram
```bash
uv tool install mcp-telegram
```

### Первый вход
```bash
mcp-telegram login
```

Потребуется:
1. **API ID** и **API Hash** — получить на [my.telegram.org/apps](https://my.telegram.org/apps)
2. **Номер телефона** — в международном формате (+79991234567)
3. **Код подтверждения** — придёт в Telegram
4. **2FA пароль** — если включена двухфакторная аутентификация

### Конфигурация в Codex/Claude Code
```json
{
  "mcpServers": {
    "mcp-telegram": {
      "command": "mcp-telegram",
      "args": ["start"],
      "env": {
        "API_ID": "your_api_id",
        "API_HASH": "your_api_hash"
      }
    }
  }
}
```

**Путь к конфигу:**
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
- **Linux**: `~/.config/claude/claude_desktop_config.json`

## 📨 Messaging Tools

### send_message
Отправка текстовых сообщений или файлов в чаты/каналы.

**Параметры:**
- `entity` (string, required) — username, phone, или chat ID
- `message` (string, optional) — текст сообщения
- `file` (string, optional) — путь к файлу для отправки
- `parse_mode` (string, optional) — `markdown` или `html`
- `link_preview` (boolean, optional) — показывать превью ссылок

**Примеры:**
```typescript
// Отправить текст
await mcp.send_message({
  entity: '@username',
  message: 'Привет! Это тестовое сообщение.',
  parse_mode: 'markdown'
});

// Отправить файл
await mcp.send_message({
  entity: '+79991234567',
  file: '/path/to/document.pdf',
  message: 'Вот документ'
});

// Отправить в канал
await mcp.send_message({
  entity: '@my_channel',
  message: '**Важное объявление**',
  parse_mode: 'markdown',
  link_preview: false
});
```

### edit_message
Редактирование ранее отправленных сообщений.

**Параметры:**
- `entity` (string, required) — username, phone, или chat ID
- `message_id` (integer, required) — ID сообщения для редактирования
- `text` (string, required) — новый текст
- `parse_mode` (string, optional) — `markdown` или `html`

**Пример:**
```typescript
await mcp.edit_message({
  entity: '@username',
  message_id: 12345,
  text: 'Обновлённый текст сообщения',
  parse_mode: 'markdown'
});
```

### delete_message
Удаление одного или нескольких сообщений.

**Параметры:**
- `entity` (string, required) — username, phone, или chat ID
- `message_ids` (array, required) — массив ID сообщений для удаления
- `revoke` (boolean, optional) — удалить для всех (default: true)

**Примеры:**
```typescript
// Удалить одно сообщение
await mcp.delete_message({
  entity: '@username',
  message_ids: [12345],
  revoke: true
});

// Удалить несколько сообщений
await mcp.delete_message({
  entity: '@username',
  message_ids: [12345, 12346, 12347],
  revoke: true
});
```

### get_messages
Получение истории сообщений из чата.

**Параметры:**
- `entity` (string, required) — username, phone, или chat ID
- `limit` (integer, optional) — количество сообщений (default: 100, max: 1000)
- `offset_id` (integer, optional) — ID сообщения для пагинации
- `min_id` (integer, optional) — минимальный ID сообщения
- `max_id` (integer, optional) — максимальный ID сообщения
- `from_user` (string, optional) — фильтр по отправителю
- `search` (string, optional) — поиск по тексту

**Примеры:**
```typescript
// Получить последние 50 сообщений
const messages = await mcp.get_messages({
  entity: '@username',
  limit: 50
});

// Поиск по тексту
const searchResults = await mcp.get_messages({
  entity: '@username',
  search: 'важно',
  limit: 20
});

// Сообщения от конкретного пользователя
const userMessages = await mcp.get_messages({
  entity: '@group_chat',
  from_user: '@specific_user',
  limit: 100
});
```

## 🔍 Search & Navigation Tools

### search_dialogs
Поиск чатов, групп и каналов по имени или username.

**Параметры:**
- `query` (string, required) — поисковый запрос
- `limit` (integer, optional) — количество результатов (default: 10)

**Пример:**
```typescript
const dialogs = await mcp.search_dialogs({
  query: 'Python',
  limit: 20
});

// Результат содержит:
// - id: ID чата
// - name: Название
// - username: Username (если есть)
// - type: 'user', 'group', 'channel'
```

### message_from_link
Получение сообщения по Telegram ссылке.

**Параметры:**
- `link` (string, required) — ссылка на сообщение (t.me/...)

**Пример:**
```typescript
const message = await mcp.message_from_link({
  link: 'https://t.me/channel/123'
});

// Возвращает полную информацию о сообщении
```

## 📝 Draft Management Tools

### get_draft
Получение текущего черновика сообщения для чата.

**Параметры:**
- `entity` (string, required) — username, phone, или chat ID

**Пример:**
```typescript
const draft = await mcp.get_draft({
  entity: '@username'
});

if (draft) {
  console.log('Черновик:', draft.text);
}
```

### set_draft
Создание или очистка черновика сообщения.

**Параметры:**
- `entity` (string, required) — username, phone, или chat ID
- `text` (string, optional) — текст черновика (пустая строка для очистки)
- `parse_mode` (string, optional) — `markdown` или `html`
- `link_preview` (boolean, optional) — показывать превью ссылок

**Примеры:**
```typescript
// Создать черновик
await mcp.set_draft({
  entity: '@username',
  text: 'Не забыть отправить отчёт',
  parse_mode: 'markdown'
});

// Очистить черновик
await mcp.set_draft({
  entity: '@username',
  text: ''
});
```

## 📂 Media Handling Tools

### media_download
Скачивание фото, видео и документов из сообщений.

**Параметры:**
- `entity` (string, required) — username, phone, или chat ID
- `message_id` (integer, required) — ID сообщения с медиа
- `path` (string, optional) — путь для сохранения (default: текущая директория)
- `thumb` (boolean, optional) — скачать миниатюру вместо полного файла

**Примеры:**
```typescript
// Скачать медиа из сообщения
await mcp.media_download({
  entity: '@username',
  message_id: 12345,
  path: '/Users/me/Downloads/'
});

// Скачать миниатюру
await mcp.media_download({
  entity: '@username',
  message_id: 12345,
  path: '/Users/me/Downloads/',
  thumb: true
});
```

## 🎯 Практические сценарии

### Сценарий 1: Уведомления о завершении задачи
```typescript
// После завершения долгой задачи
async function notifyCompletion(taskName: string, result: string) {
  await mcp.send_message({
    entity: '@my_username',
    message: `✅ **Задача завершена**\n\n` +
             `Задача: ${taskName}\n` +
             `Результат: ${result}\n` +
             `Время: ${new Date().toLocaleString('ru-RU')}`,
    parse_mode: 'markdown'
  });
}
```

### Сценарий 2: Отправка отчётов в канал
```typescript
async function sendDailyReport(stats: any) {
  const report = `
📊 **Ежедневный отчёт**

Пользователи: ${stats.users}
Транзакции: ${stats.transactions}
Выручка: ${stats.revenue}₽

_Сгенерировано автоматически_
  `.trim();
  
  await mcp.send_message({
    entity: '@my_reports_channel',
    message: report,
    parse_mode: 'markdown'
  });
}
```

### Сценарий 3: Мониторинг упоминаний
```typescript
async function checkMentions(username: string) {
  const dialogs = await mcp.search_dialogs({
    query: username,
    limit: 50
  });
  
  for (const dialog of dialogs) {
    const messages = await mcp.get_messages({
      entity: dialog.username,
      search: username,
      limit: 10
    });
    
    if (messages.length > 0) {
      console.log(`Найдено ${messages.length} упоминаний в ${dialog.name}`);
    }
  }
}
```

### Сценарий 4: Автоматическое резервное копирование
```typescript
async function backupImportantChats(chatList: string[]) {
  for (const chat of chatList) {
    const messages = await mcp.get_messages({
      entity: chat,
      limit: 1000
    });
    
    // Сохранить в файл
    const backup = JSON.stringify(messages, null, 2);
    await fs.writeFile(`backup_${chat}_${Date.now()}.json`, backup);
    
    // Уведомить о завершении
    await mcp.send_message({
      entity: '@my_username',
      message: `✅ Резервная копия ${chat} создана`
    });
  }
}
```

### Сценарий 5: Интеграция с Mini App
```typescript
// Backend API для Mini App
app.post('/api/send-notification', async (req, res) => {
  const { userId, message } = req.body;
  
  try {
    await mcp.send_message({
      entity: userId,
      message: message,
      parse_mode: 'markdown'
    });
    
    res.json({ success: true });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});
```

## ⚠️ Важные моменты

### 1. Rate Limits
Telegram имеет ограничения на частоту запросов:
- **Сообщения**: ~30 сообщений в секунду
- **Поиск**: ~10 запросов в секунду
- **Медиа**: зависит от размера файла

**Рекомендация**: добавляй задержки между запросами
```typescript
await sleep(100); // 100ms между запросами
```

### 2. Безопасность
- **Никогда не коммить** API_ID и API_HASH в git
- Используй переменные окружения
- Храни session файл в безопасном месте

### 3. Обработка ошибок
```typescript
try {
  await mcp.send_message({
    entity: '@username',
    message: 'Test'
  });
} catch (error) {
  if (error.message.includes('FLOOD_WAIT')) {
    // Превышен лимит, нужно подождать
    console.log('Rate limit exceeded');
  } else if (error.message.includes('USER_NOT_FOUND')) {
    // Пользователь не найден
    console.log('User not found');
  } else {
    console.error('Unknown error:', error);
  }
}
```

### 4. Валидация entity
```typescript
function isValidEntity(entity: string): boolean {
  // Username
  if (entity.startsWith('@')) return true;
  
  // Phone number
  if (entity.startsWith('+') && /^\+\d+$/.test(entity)) return true;
  
  // Chat ID
  if (/^-?\d+$/.test(entity)) return true;
  
  return false;
}
```

## 🔧 Управление сессией

### Проверка статуса
```bash
mcp-telegram status
```

### Выход из аккаунта
```bash
mcp-telegram logout
```

### Очистка сессии
```bash
mcp-telegram clear-session
```

### Список доступных команд
```bash
mcp-telegram --help
```

## 🐛 Troubleshooting

### Database Locked Error
Если видишь ошибку "database is locked":
```bash
# Остановить все процессы mcp-telegram
pkill -f "mcp-telegram"  # macOS/Linux
taskkill /F /IM mcp-telegram.exe  # Windows

# Перезапустить
mcp-telegram start
```

### Session Expired
Если сессия истекла:
```bash
mcp-telegram logout
mcp-telegram login
```

### Connection Issues
Проверь интернет-соединение и доступность Telegram:
```bash
ping telegram.org
```

## 📊 Best Practices

1. **Используй username вместо phone** — более стабильно
2. **Кешируй результаты search_dialogs** — не ищи каждый раз
3. **Batch операции** — группируй несколько действий
4. **Логируй все операции** — для отладки
5. **Graceful degradation** — обрабатывай ошибки корректно
6. **Мониторинг rate limits** — отслеживай FLOOD_WAIT
7. **Используй markdown** — для красивого форматирования
8. **Тестируй на тестовом аккаунте** — перед продакшеном

## 🔗 Полезные ссылки

- [mcp-telegram GitHub](https://github.com/dryeab/mcp-telegram)
- [Telethon Documentation](https://docs.telethon.dev/)
- [Telegram API Documentation](https://core.telegram.org/api)
- [MTProto Protocol](https://core.telegram.org/mtproto)
