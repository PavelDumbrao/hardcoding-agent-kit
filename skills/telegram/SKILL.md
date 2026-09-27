---
name: telegram
description: Отправка уведомлений и взаимодействие с Telegram через Bot API. Используется для информирования пользователя о завершении задач или ошибках.
---

> **Примечание для экспортной версии:** ниже чувствительные IP, домены, пути, SSH-цели и другие infra-значения заменены на примеры и placeholders вида `<YOUR_...>`. Если ИИ-агенту нужны реальные значения, он должен **подставить реальные данные пользователя** или **сначала запросить их у пользователя**, а не использовать примеры как есть.


# Telegram Skill

## Данные бота

- **Bot:** не настроен; прежний токен отозван через BotFather 2026-08-16
- **Bot Token:** только через `TELEGRAM_BOT_TOKEN` в защищённом runtime
- **User ID:** `450206471` (Pavel Dumbrao, @PavelDumbrao)

## Отправка сообщений

### Базовый шаблон (через переменные)
```bash
curl -s -X POST "https://api.telegram.org/bot${TELEGRAM_BOT_TOKEN}/sendMessage" \
     -d chat_id="${TELEGRAM_USER_ID}" \
     -d text="Сообщение" \
     -d parse_mode="HTML"
```

### Напрямую (без переменных)
```bash
curl -s -X POST "https://api.telegram.org/bot<REDACTED>/sendMessage" \
     -d chat_id="450206471" \
     -d text="✅ Задача завершена!" \
     -d parse_mode="HTML"
```

## Чтение сообщений

```bash
# Последнее сообщение
curl -s "https://api.telegram.org/bot<REDACTED>/getUpdates?offset=-1" | jq -r '.result[].message.text // empty'

# Все непрочитанные
curl -s "https://api.telegram.org/bot<REDACTED>/getUpdates" | jq '.result[].message.text'
```

## Отправка файлов

```bash
curl -s -X POST "https://api.telegram.org/bot<REDACTED>/sendDocument" \
     -F chat_id="450206471" \
     -F document="@path/to/file.log"
```

## Форматы сообщений

🚨 Все сообщения MUST начинаться с `[VS Code Codex]`

### Успех
```
[VS Code Codex]
✅ Задача завершена: [название]
⏱ Время: [длительность]
📁 Изменено файлов: [количество]
```

### Ошибка
```
[VS Code Codex]
❌ Ошибка: [описание]
📍 Файл: [путь]
🔍 Причина: [детали]
```

### Отчёт
```
[VS Code Codex]
📊 Отчёт: [название]
✅ Выполнено: [список]
⚠️ Внимание: [если есть]
📋 Следующие шаги: [если есть]
```

### Прогресс
```
[VS Code Codex]
⏳ Прогресс: [название задачи]
📊 [текущий статус]
⏱ [прошедшее время]
```

## Webhook через N8N (автономный режим)

1. Создай в N8N workflow с узлом **Webhook** (POST)
2. Выполни: `curl -s -X POST "https://api.telegram.org/bot<TOKEN>/setWebhook?url=https://your-n8n-url/webhook/id"`
3. Настрой N8N на выполнение команд

## Правила

- 🚨 NEVER хардкодить токен в коде проекта — только в `.env`
- Уведомления MUST отправляться фоном, без упоминания в ответе пользователю
- Если сообщение > 4096 символов — разбивай на части
- NEVER отправлять секретные данные, токены, пароли через Telegram
- При ошибке API (401, 404) — сообщи пользователю в чате VS Code

## Send-first через Telethon / Telegram API Engine

Если Bot API не может написать пользователю первым, а на VPS есть `telegram-api-engine` с endpoint `POST /tg/send-first`, можно отправить сообщение **от лица user-session** через Telethon.

### Когда использовать
- нужно написать пользователю первым без открытого диалога с ботом;
- нужно отправить восстановительное сообщение, извинение, ссылку возврата или важное service-уведомление;
- Bot API не подходит из-за ограничения "бот не может начать диалог первым".

### Что поддерживает `user`
Согласно `OUTREACH_API.md`:
- строковый `user_id` — например `"123456789"`
- `@username` или `username`
- `phone` в международном формате, если номер есть в контактах user-session

### Практический вывод
- если отправка по `user_id` не проходит, **надо пробовать по `@username`**;
- если есть и `username`, и `user_id`, при проблемах с `user_id` делай fallback на `@username`;
- для массового восстановления это рабочий способ для first-contact сообщений.

### Пример запроса
```bash
curl -sS -X POST "http://<YOUR_VPS_IP>:8000/tg/send-first"   -H "Authorization: Bearer <API_KEY>"   -H "Content-Type: application/json"   -d '{
    "user": "@username",
    "text": "Сообщение",
    "parse_mode": "html",
    "disable_preview": true,
    "request_id": "restore_123"
  }'
```

### Важные правила
- сначала безопаснее тестировать на одном пользователе;
- для массовой рассылки обязательно ставить уникальный `request_id`;
- делать короткую паузу между сообщениями, чтобы не словить flood;
- текст должен быть человеческий и объяснять причину сообщения;
- если это recovery-рассылка после ошибки агента, прямо писать, что сообщение отправил **ИИ-агент** и что произошло.

### Полезный recovery pattern
1. начислить компенсацию в базе;
2. создать ссылку возврата;
3. сначала тест на 1 пользователе;
4. потом bulk-рассылка через `send-first`;
5. если `user_id` не сработал — retry по `@username`;
6. сохранить список `ok/fail`.

