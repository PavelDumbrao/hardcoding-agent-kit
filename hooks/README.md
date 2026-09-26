# ZCode hooks — runbook

Обновлено: 2026-09-25 (порт набора Claude → ZCode 2026-09-25; env-переменные переименованы `CLAUDE_TG_*` → `ZCODE_TG_*`, vault env — `ZCODE_SECOND_BRAIN_VAULT`). Правишь хуки → обнови этот файл и прогони smoke.

## Состав

| Событие (config.json → `hooks.events`) | Скрипт | Что делает |
|---|---|---|
| SessionStart | `session_start.py` | Инъекция континуити: project-файлы, vault-превью (hot ≤4k, focus ≤2k chars), восстановление после компакции по маркеру. Раз в сессию чистит state (`cleanup_state`). |
| UserPromptSubmit | `user_prompt_submit.py` | Роутинг second-brain интентов (save/ingest/query) → obsidian-скиллы. Паттерны в `second_brain.py`. |
| PreToolUse (matcher `Bash\|Write\|Edit\|MultiEdit`) | `pre_tool_use.py` | Deny: rm -rf по корням/системным путям/дому целиком; sudo; shell-чтение секретов (`.env`, приватные ключи, `.pem`) в контекст — закрывает чтение через `cat`/`grep`/`python3 -c` (исключения: identity-аргумент `ssh/scp -i <ключ>` чтением не считается — фикс ложняка 02.07.2026; **присваивание пути-ключа в переменную** — `KEY=/…/id_ed25519`, обычно затем `ssh -i "$KEY" … | grep/tail/node -e` — тоже не чтение, фикс ложняка 06.07.2026; ЛИТЕРАЛЬНОЕ `cat /…/id_ed25519` без присваивания остаётся под блоком; **ЗАПИСЬ значения в `.env` разрешена** — `>> .../.env` / `tee -a .../.env` / `cat >> .../.env <<EOF` / `F=.../.env` — значение идёт В ФАЙЛ, не в stdout/контекст, фикс 04.07.2026; при этом ЧТЕНИЕ `.env` в stdout остаётся под блоком даже в той же команде; **тело heredoc и экранированный `\.env`-паттерн — не чтение**, фикс ложняка 07.07.2026; **загрузка `.env` в ОКРУЖЕНИЕ из кода и правка файла на месте разрешены** — `load_dotenv()`, `require('dotenv').config({path:…})`, `sed -i '' 's/…/…/' …/.env` — значение уходит в окружение процесса или в сам файл, а не в stdout/контекст, фикс ложняка 09.09.2026; КОМПЕНСАЦИЯ — ENV_PRINT_CODE блокирует печать секрета из кода; **закавыченный паттерн grep/rg — не файл**, фикс 09.09.2026; **фикс 14.09.2026:** `sed -i` с `;`/`|` внутри закавыченного скрипта, разрешены `cp …/.env …/.env.bak-*` и `grep -c/-q/-l` по `.env`); `git add .env`; широкие сканы `find /` (кроме команд, целиком уходящих по ssh); `.js` в TS-проекте (кроме `*.config.js`, dot-файлов, `scripts/`). |
| PostToolUse (все тулы) | `post_tool_use.py` | Телеметрия context-guard: счётчики токенов, riskLevel, сохранение выводов >80k chars в артефакты. Project identity кэшируется в state.json. |
| PostToolUse (matcher `Edit\|Write\|MultiEdit`) | skill `impeccable` (`hook.mjs`) | Быстрая проверка UI-правок. Тихая, guarded (`[ ! -f ] \|\| node`). |
| PreCompact | `pre_compact.py` | **В ZCode НЕ активен**: событие PreCompact рантаймом не поддерживается (семь событий: SessionStart, UserPromptSubmit, PreToolUse, PermissionRequest, PostToolUse, PostToolUseFailure, Stop). Скрипт лежит для будущего и покрывается smoke; ветка «восстановление после компакции» в session_start из-за этого бездействует (маркеры никто не пишет). |
| Stop | `stop_notify.py` (+ `tg_format.py`) | Telegram-уведомление о завершении с **LLM-форматированием**. Пайплайн: ответ ZCode → `gpt-5.4-mini` приводит к Telegram-HTML → санитайзер тегов → balance → разбивка ≤3900 (лимит TG 4096) с переносом открытых тегов. Креды: env `TELEGRAM_*` или `~/.zcode/secrets/telegram.env` (chmod 600). Токен только в памяти (urllib, не argv). Активен с 2026-07-02: бот `@your_bot`, chat_id — в секретах. Спит, если нет TG-кредов. |
| Stop | skill `impeccable` (`hook.mjs`) | Design deep pass по итогам ответа. |

## LLM-форматтер уведомлений (`tg_format.py`)

Порт n8n-пайплайна Павла («LLM HTML» + «CleanText») в один модуль, без зависимости от n8n.

- Модель: `gpt-5.4-mini` через `https://gengruihuan.cn/v1` (OpenAI-совместимый `/chat/completions`).
- Поля в `~/.zcode/secrets/telegram.env`: `LLM_FORMAT_BASE_URL`, `LLM_FORMAT_API_KEY`, `LLM_FORMAT_MODEL`, опц. `LLM_FORMAT_TIMEOUT` (деф. 45с), `LLM_FORMAT_REASONING` (деф. `low`).
- Деградация: любая ошибка/таймаут LLM → plain-текст (`html.escape`), уведомление НЕ теряется. Если Telegram отверг HTML (ok≠true) → авто-ретрай чанка плоским текстом.
- Короткий «сырой» текст (<200 симв. без разметки) LLM НЕ гоняет — быстрый путь ~0.5с.
- Тайминги (замер 02.07): ~27с на 4370 симв. входа. Поэтому хук-таймаут 60с. Длинные отчёты форматируются медленно, но фолбэк страхует.
- SSL: системный python3 на macOS без CA-бандла → `_ssl_context()` берёт `/etc/ssl/cert.pem`.
- Kill-switch: `ZCODE_TG_NOTIFY_DISABLE=1` полностью гасит хук (используется в smoke, чтобы не слать живые сообщения). Отладка: `ZCODE_TG_NOTIFY_DEBUG=1` печатает chunk ok/len в stderr. Тест-флаг `ZCODE_TG_FORCE_FALLBACK=1` — принудительный локальный фолбэк.
- Разбивка режет максимум на 3 сообщения (`MAX_CHUNKS`), вход обрезается до 7000 симв. (`MAX_INPUT`) — уведомление это дайджест, не полный лог.
- Таблицы: Telegram HTML таблиц не умеет — `detable()` до LLM + `strip_table_seps()` в sanitize; фолбэк `md_to_html_basic()` форматирует Markdown→HTML без LLM.

## Пути state

- `~/.zcode/state/hooks/context-guard/<session>/` — телеметрия и артефакты; TTL 7 дней (`cleanup_state`).
- `~/.zcode/state/hooks/compaction/by-task/*.json` — маркеры компакции; TTL 12 часов (в ZCode не пишутся — см. PreCompact).
- `~/.zcode/state/hooks/logs/tool-usage.log` — ротация при >5MB → `.log.1`.

## Проверка

```bash
python3 ~/.zcode/hooks/smoke.py   # 22/22 PASS = норма
```

## Заметки

- 2026-09-25, порт Claude → ZCode: схема вывода хуков ZCode строгая (recognized-ключи только: `continue`/`suppressOutput`/`systemMessage`/`hookSpecificOutput`…) — проверено по `zcode.cjs`; payload несёт `cwd` сессии; Stop получает `last_assistant_message` и временный `transcript_path`. Конфиг событий: `~/.zcode/cli/config.json` → `hooks.events` (без `hooks.enabled: true` раннер выключен).
- **Известный зазор (наследие deny-листа Claude):** permissions-правила вида `Read(**/.env)` в ZCode НЕ настроены (схема permissions в конфиге не подтверждена), а matcher PreToolUse не покрывает инструмент `Read`. Shell-чтение секретов закрыто хуком; инструмент Read читает `.env`/ключи без блокировки. Не удалять guard при рефакторе; guard намеренно ловит и служебный `~/.zcode/secrets/telegram.env`.
- Guard читает `telegram.env` сам; содержимое в контекст нельзя.

- 2026-07-02: `send_telegram` переведён с `curl --config` на `urllib` — quoted-значения curl-конфига не переживали многострочный текст (ok=False на любом `\n`).
- Креды и ключи держи только в `~/.zcode/secrets/telegram.env` — никогда в коде и чате.

> 2026-09-04: BROAD_SCAN (`find /`, `find ~`, `ls -R /`) не применяется к командам, которые целиком уходят по `ssh`/`autossh` (скан выполняется на удалённом хосте). Локальные широкие сканы по-прежнему блокируются. Тесты: smoke-f3 (remote pass), smoke-f4 (local deny).

> 2026-09-25: BROAD_SCAN и GIT_ADD_ENV переведены на текст БЕЗ тела heredoc — упоминание `find /` или `git add .env` внутри тела загружаемого скрипта/документа — данные, не команда (раньше BROAD_SCAN смотрел сырой текст, асимметрично остальным правилам; поймано на питон-хередоке со сканом скиллов). Реальные `find /` вне heredoc по-прежнему под блоком. Тест: smoke «heredoc-mention passthrough» + smoke-f5.

> 2026-09-25, продолжение: heredoc-aware сделаны ВСЕ deny-правила PreToolUse — `cmd_no_heredoc` вынесен наверх и применяется к DANGEROUS_RM и sudo-проверке тоже (слова «rm -rf /» / «sudo» в теле коммит-месседжа или документа ложными блоками не считаются). Известное ограничение дизайна HEREDOC_BODY: `bash <<EOF … rm -rf / … EOF` — тело исполняется, но хук его не видит; высокий риск → держится как trade-off, реальный кейс не зафиксирован. Тесты: smoke «heredoc passthrough for rm/sudo» + smoke-rm2 + smoke-sudo2. Итого smoke: 24/24.

### 09.09.2026 — послабление PreToolUse для секретов

Добавлены `SECRET_SOURCE` и `SECRET_ECHO`.

- **Что открылось:** `set -a; . /path/.env; set +a; <команда с $VAR>` — dot-source конфига, чтобы ИСПОЛЬЗОВАТЬ значение, не печатая его. Раньше блокировалось, если в той же команде был `python3 -c` или grep по чужому файлу.
- **Что закрылось взамен:** печать секрета в stdout — `echo $API_KEY`, `printenv`, голый `env` (только вместе с `.env` в той же команде).
- **Что осталось как было:** `cat`/`grep`/`tail` по `.env`, чтение приватных ключей, запрет добавлять `.env` в git, опасный `rm`, `sudo`, широкие сканы.
- **Грабли при правке (все пойманы за один заход):** 1) `SECRET_ECHO` и git-правило смотрят текст БЕЗ тела heredoc; 2) `\benv` без якоря ловит слово внутри `.env` и роняет `cp .env.example .env`.

Бэкапы истории: `~/.claude/backups/2026-07-02/`, `~/.claude/backups/2026-09-09/pre_tool_use.py.bak`. Проверка: `python3 ~/.zcode/hooks/smoke.py` (22/22).
