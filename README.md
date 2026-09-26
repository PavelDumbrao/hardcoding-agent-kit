# Hard Coding Agent Kit

Ученический Practical Hard Coding PRO про три слоя управления AI coding agent:

**Инструкция → Skill → Hook.**

Главная цель — не изучить термины, а собрать маленькую рабочую систему:
- агент получает постоянные правила;
- умеет подгружать отдельный Skill по задаче;
- автоматически блокирует опасное чтение секретов;
- подмешивает continuity при старте;
- присылает Telegram-уведомление после завершения;
- доказывает, что установка реально работает.

## Начни отсюда

1. Открой [`practical/index.html`](practical/index.html) — это основной интерактивный Practical.
2. Если удобнее Markdown — [`PRACTICAL.md`](PRACTICAL.md).
3. Для пути «одна вставка агенту» — [`PROMPT.md`](PROMPT.md).

## Что внутри

- `AGENTS.md` — короткий шаблон постоянной инструкции.
- `skills/hardcoding-verify-done/` — настоящий Agent Skill с `SKILL.md`.
- `hooks/` — универсальное ядро lifecycle hooks.
- `adapters/` — отдельные конфиги для ZCode, Claude Code и Codex.
- `install.py` — безопасный installer с backup + merge, без затирания существующих конфигов.
- `configure_telegram.py` — локальный ввод токена без передачи секрета в чат.
- `verify_install.py` — read-only проверка установки.
- `hooks/smoke.py` — тесты самого набора.
- `practical/index.html` — self-contained mobile-first Practical.

## Безопасность

Никогда не отправляй токены, пароли и содержимое `.env` в обычный чат с агентом.

Telegram token вводится **только локально** через:

```bash
python3 ~/.hardcoding-agent-kit/configure_telegram.py
```

Installer:
- не стирает существующие инструкции;
- перед изменением существующего JSON-конфига делает timestamped backup;
- добавляет только свои hook-группы;
- не удаляет MCP, settings и другие существующие поля;
- при невалидном JSON останавливается без изменений.

## Runtime support

- **ZCode** — adapter по текущей схеме `~/.zcode/cli/config.json`.
- **Claude Code** — adapter в `~/.claude/settings.json`.
- **Codex** — adapter в `~/.codex/hooks.json`.

Hook scripts живут в одном нейтральном каталоге:

`~/.hardcoding-agent-kit/hooks/`

Это убирает ошибку старой версии, где Claude/Codex ссылались на `~/.zcode/hooks`.

## Проверка

После установки:

```bash
python3 ~/.hardcoding-agent-kit/hooks/smoke.py
python3 ~/.hardcoding-agent-kit/verify_install.py --runtime <zcode|claude|codex>
python3 ~/.hardcoding-agent-kit/hooks/test_notify.py
```

`smoke.py` проверяет локальную логику. `verify_install.py` проверяет wiring. `test_notify.py` делает реальный Telegram E2E.

---

Принцип Practical: **смысл → карта → AI делает технику → маленькие победы → evidence → E2E → Definition of Done**.
