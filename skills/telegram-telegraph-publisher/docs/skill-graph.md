# Карта skill: Telegram + Telegraph Publisher

```text
telegram-telegraph-publisher
  |
  +-- источник и сюжет
  |     +-- локальные файлы / вложения
  |     +-- официальный web-поиск для свежих фактов
  |
  +-- лонгрид и teaser
  |     +-- templates/telegraph-longread.md
  |     +-- templates/telegram-teaser.md
  |
  +-- публикация
  |     +-- browser-automation
  |     +-- проверка URL, title, preview-текста и консоли
  |
  +-- доставка
        +-- telegram-user-session: Saved Messages или точный chat_id
        +-- telegram: только Bot API и настоящие inline-кнопки
        +-- проверка message_id и MessageMediaWebPage
```

## Переходы

- Если нужна только редактура: остановиться после создания двух черновиков.
- Если нужна публикация без Telegram: остановиться после проверки Telegraph URL.
- Если нужно `Избранное`: продолжить через `telegram-user-session`.
- Если нужна отдельная кнопка под сообщением: переключиться на `telegram` и Bot API после уточнения адресата.

