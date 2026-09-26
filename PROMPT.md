# 🚀 PROMPT · установка Hard Coding Agent Kit одним сообщением

Скопируй серый блок целиком и отправь своему AI coding agent.

> Важное правило: **токены и пароли не отправляются в чат**. Когда дойдёшь до Telegram, агент должен дать тебе локальную команду `configure_telegram.py` и ждать, пока ты введёшь секрет в терминале сам.

```text
Ты мой AI coding agent. Установи Hard Coding Agent Kit безопасно и докажи результат.

Я не программист. Твоя роль — сделать техническую работу самостоятельно, а мне оставлять только неизбежные человеческие действия.

ИСТОЧНИК:
https://github.com/PavelDumbrao/hardcoding-agent-kit

ПРАВИЛА:
1. Не проси у меня токены, пароли и содержимое .env в обычный чат.
2. Не стирай существующие AGENTS.md / CLAUDE.md / config / hooks.
3. Перед изменением существующего JSON-конфига должен быть backup.
4. Если найдено несколько рантаймов (ZCode / Claude Code / Codex), спроси только какой из них настраиваем.
5. Не говори «готово» без smoke + verify_install. Telegram считается готовым только после реального test_notify.
6. Если предыдущая mutation имеет неизвестный исход — сначала readback, не повторяй её вслепую.

СДЕЛАЙ:

ШАГ 1 · Определи runtime.
- ZCode: ~/.zcode
- Claude Code: ~/.claude
- Codex: ~/.codex
Если найден один — используй его.
Если несколько — задай мне один вопрос: какой главный.

ШАГ 2 · Скачай репозиторий в безопасную временную папку.
Предпочтительно git clone. Если git недоступен — скачай main.zip.
Не исполняй ничего до чтения README.md и install.py.

ШАГ 3 · Проверь installer.
Убедись, что он:
- копирует hooks в ~/.hardcoding-agent-kit/hooks;
- делает backup перед изменением существующего JSON;
- merge-ит hook groups, не затирая другие settings/MCP;
- не перезаписывает существующую постоянную инструкцию;
- ставит Skill hardcoding-verify-done.

ШАГ 4 · Установи:
bash install.sh --runtime <zcode|claude|codex>

Покажи только безопасный итог installer. Не печатай secret-файлы.

ШАГ 5 · Запусти локальный smoke:
python3 ~/.hardcoding-agent-kit/hooks/smoke.py

Норма — все тесты PASS. Если есть FAIL, диагностируй и исправь, затем повтори тот же smoke.

ШАГ 6 · Проверь wiring:
python3 ~/.hardcoding-agent-kit/verify_install.py --runtime <runtime>

Норма — все проверки PASS.

ШАГ 7 · Telegram.
Скажи мне самостоятельно выполнить в терминале:
python3 ~/.hardcoding-agent-kit/configure_telegram.py

ВАЖНО:
- token вводится скрыто в терминале;
- token НИКОГДА не отправлять тебе в чат;
- после моего сообщения «ввёл» запусти:
  python3 ~/.hardcoding-agent-kit/hooks/test_notify.py
- Telegram считается проверенным только если команда PASS и я реально получил сообщение.

ШАГ 8 · Мини-проверка Skill.
Попроси runtime показать/найти Skill `hardcoding-verify-done`.
Затем дай ему тестовую задачу: «Проверь, можно ли честно сказать готово».
Убедись, что он требует evidence, а не просто повторяет статус.

ФИНАЛЬНЫЙ ОТЧЁТ:
- runtime;
- config path;
- backup path, если был;
- hooks path;
- skill path;
- smoke: X/X;
- verify_install: X/X;
- Telegram E2E: PASS / не настраивали;
- что осталось человеку руками.

Не заявляй completion, пока обязательные локальные проверки не пройдены.
```
