# Hard Coding Agent Kit

## Единый стартовый набор HARD CODING PRO

**Этот репозиторий — единый официальный стартовый набор курса для всех потоков и всех агентов: Claude Code, Codex, ZCode.** Правила, 19 Skills и Hooks ставятся сразу, одной ссылкой. Ученику достаточно отправить агенту ссылку на этот репозиторий и фразу из [`PROMPT.md`](PROMPT.md): **«Установи всё по инструкции, но адаптируй под меня!»**

Старый архив «Agent Kit Full 18 Skills» с сайта гайдов больше не используется. Если он уже стоит, этот набор безопасно ставится поверх: installer делает резервные копии изменённых Skills и конфигов, не трогает твою существующую инструкцию и добавляет только свои hook-группы. Два набора не нужно держать параллельно.

[Общая интерактивная карта обучения](https://hardcoding.proaicommunity.online/guides/) рассчитана на все потоки.

## Windows

Команды ниже написаны для Mac и Linux. На Windows:

- вместо `python3` — `py` (ставится вместе с Python с [python.org](https://www.python.org/downloads/));
- вместо `bash install.sh --runtime <...>` — `py install.py --runtime <...>`.

Если Python нет, агент предлагает поставить его с python.org и ждёт твоего «да». Installer на Windows сам прописывает Hooks в форме, которая работает в PowerShell, cmd и Git Bash: `py -3 "C:/Users/<ты>/.hardcoding-agent-kit/hooks/<hook>.py" --runtime <агент>`. Проверка `verify_install.py` на Windows отдельно проверяет, что команды Hooks подготовлены для Windows.

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
- `skills/` — **19 готовых Agent Skills**: `hardcoding-verify-done` + 18 практических (лендинги и маркетинг: expert-landing-express, marketing-landing-cro, viral-hooks, viral-short-form; дизайн и документы: cc-design, mobile-html-artifact, frontend-design, google-sheets-design; Telegram: telegram, telegram-mini-apps, telegram-initdata-validation, telegram-telegraph-publisher; инженерия: deployment-guide, hostinger-vps, supabase-integration, systematic-debugging, owasp-security, epic-planner). Все санитизированы — без секретов, только плейсхолдеры.
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

На Windows: `py ~/.hardcoding-agent-kit/configure_telegram.py`.

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

На Windows те же команды через `py` вместо `python3`.

`smoke.py` проверяет локальную логику. `verify_install.py` проверяет wiring. `test_notify.py` делает реальный Telegram E2E.

---

Принцип Practical: **смысл → карта → AI делает технику → маленькие победы → evidence → E2E → Definition of Done**.
