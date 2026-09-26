#!/usr/bin/env python3
from __future__ import annotations
import re
from pathlib import Path
from common import deny_pre_tool, emit_json, read_payload, workspace_from_payload

# rm -r/-rf против корней, которые нельзя сносить целиком: голый /, системные
# каталоги, /var вне /var/folders (маковский temp), ~ / $HOME / /Users/<name>
# как целое. Относительные пути и подкаталоги (~/Downloads/x, /tmp/x) — легальны.
DANGEROUS_RM = re.compile(
    r"\brm\s+(?:(?:-[A-Za-z]*r[A-Za-z]*|--recursive)(?:\s+--?[A-Za-z-]+)*)\s+['\"]?"
    r"(?:"
    r"/(?=['\"]?(?:\s|$))"
    r"|/(?:etc|usr|bin|sbin|lib|opt|home|System|Library|Applications)(?:/|\b)"
    r"|/var/(?!folders/)"
    r"|~(?=/?['\"]?(?:\s|$))"
    r"|\$HOME(?=/?['\"]?(?:\s|$))"
    r"|/Users/[A-Za-z0-9._-]+/?(?=['\"]?(?:\s|$))"
    r")"
)

# Чтение секретных файлов шелл-утилитами: cat/grep и т.п. автоапрувнуты в
# settings.json, а deny Read(**/.env) на Bash не действует — закрываем тут.
SECRET_READERS = re.compile(
    r"\b(?:cat|head|tail|less|more|strings|grep|rg|awk|sed|base64|xxd|od|cut|nl|tac)\b"
)
INLINE_EVAL = re.compile(r"\b(?:python3?|node|deno|bun|ruby|perl)\b[^|;&\n]*\s(?:-c|-e|-p|--eval)\b")
SECRET_TARGET = re.compile(
    # `(?<![\w\\-])`: не считаем целью `\.env` (экранированная точка = regex-ПАТТЕРН grep/rg, а не файл) —
    # напр. `grep -nE "\.env" file` инспектирует ЧУЖОЙ файл, а не читает секрет (поймано 07.07.2026).
    r"(?<![\w\\-])\.env(?!\.(?:example|sample|template|dist)\b)(?:\.[\w.-]+)?\b"
    # `(?![\w.-]*\.pub)`: ПУБЛИЧНЫЙ ключ читать безопасно, и имя у него бывает
    # с суффиксом — `id_ed25519_ghdeploy.pub`. Прежний `(?!\.pub)` смотрел
    # только вплотную и такие файлы ложно считал приватными (поймано 09.09.2026
    # при заведении deploy-key на GitHub).
    r"|id_(?:rsa|ed25519|ecdsa|dsa)(?![\w.-]*\.pub)"
    r"|[\w.@/~-]*\.pem\b",
    re.IGNORECASE,
)
# ssh/scp -i <key> — ключ используется как identity-аргумент, а НЕ читается в контекст.
# Без этого исключения ЛЮБАЯ ssh-команда с -i и grep/cat внутри (например, «ssh … 'docker exec … | grep …'»)
# ложно блокировалась как «чтение секрета» (поймано 02.07.2026 на проверках nginx через ssh).
SSH_IDENTITY_ARG = re.compile(r"-i\s+\S*id_(?:rsa|ed25519|ecdsa|dsa)\b(?!\.pub)")
# Присваивание ПУТИ к приватному ключу в переменную (KEY=/…/id_ed25519, обычно затем `ssh -i "$KEY"`).
# Это путь-для-identity — значение НЕ идёт в stdout/контекст. Вырезаем перед reader-сканом, как identity-аргумент.
# Без этого форма «KEY=/…/id_ed25519; ssh -i "$KEY" … | grep …» ложно блокировалась: SSH_IDENTITY_ARG ловит
# только литерал `-i <path>`, а не путь-через-переменную, поэтому литерал id_ed25519 уцелевал в присваивании
# и любой cat/grep/tail/node -e рядом давал ложный блок (поймано 06.07.2026 на ингесте урока через ssh).
# ЛИТЕРАЛЬНОЕ чтение ключа (`cat /…/id_ed25519` без присваивания) под блоком остаётся — там нет `VAR=`.
SSH_KEY_ASSIGN = re.compile(
    r"(?:^|[;&|]|\s)[A-Za-z_]\w*=['\"]?\S*(?:id_(?:rsa|ed25519|ecdsa|dsa)(?!\.pub)|\.pem)\b",
    re.IGNORECASE,
)

# Безопасная ЗАПИСЬ секрета в .env: значение идёт В ФАЙЛ (append-redirect / tee -a / heredoc в .env,
# либо присваивание ПУТИ к .env в переменную), а НЕ в stdout/контекст LLM. Такую запись пропускаем —
# Павел кладёт ключи в .env на VPS через `cat >> .../.env <<EOF`. Эти конструкции вырезаем перед
# reader-проверкой ниже. ВАЖНО: вырезается ТОЛЬКО «.env как цель записи»; если .env остаётся аргументом
# чтения (`cat /x/.env`, `grep KEY /x/.env`, `cat /x/.env >> other`) — он уцелеет в остатке и заблокируется.
SECRET_WRITE = re.compile(
    r">>\s*['\"]?[^\s;&|'\"]*\.env\b['\"]?"                  # append-redirect в .env
    r"|tee\s+-a\s+['\"]?[^\s;&|'\"]*\.env\b"                 # tee -a .env
    r"|(?:^|[;&|]|\s)[A-Za-z_]\w*=[^\s;&|]*\.env\b",         # присваивание пути к .env (F=/opt/.../.env)
    re.IGNORECASE,
)

# Dot-source `.env` для ИСПОЛЬЗОВАНИЯ значения (`set -a; . /opt/x/.env; set +a; curl -H "…$API_KEY"`):
# значение уходит в окружение шелла и дочернего процесса, а НЕ в stdout/контекст LLM. Раньше такая форма
# ложно блокировалась, если в той же команде стоял `python3 -c` или grep по ЧУЖОМУ файлу — из-за этого
# нельзя было дёрнуть API движка его же ключом (поймано 09.09.2026 на отчётах ytdl-bot в @vektor_assist_bot).
# Вырезаем конструкцию source перед reader/target-сканом.
# КОМПЕНСАЦИЯ: SECRET_ECHO ниже ловит попытку напечатать секрет после source — она остаётся под блоком.
SECRET_SOURCE = re.compile(
    r"(?:^|[;&|]|\s)\s*(?:\.|source)\s+['\"]?[^\s;&|'\"]*\.env\b['\"]?",
    re.IGNORECASE,
)

# Печать секрета в stdout: `echo $API_KEY`, `printenv`, голый `env`. Блокируется только вместе с .env
# в той же команде — то есть ровно тот сценарий, который открывает послабление SECRET_SOURCE.
SECRET_ECHO = re.compile(
    r"\becho\s+[^|;&\n]*\$\{?\w*(?:KEY|TOKEN|SECRET|PASSWORD|PASSWD|CREDS?)\w*"
    r"|\bprintenv\b"
    # `env` только как САМОСТОЯТЕЛЬНАЯ команда: без якоря `\benv` ловило слово внутри самого
    # `.env` и роняло `cp .env.example .env` (поймано smoke-тестом 09.09.2026).
    r"|(?:^|[;&|]\s*)env\s*(?:[|;&]|$)",
    re.IGNORECASE,
)

# Тело heredoc (`<<EOF … EOF` / `<<'EOF' … EOF`) — это ВСТРОЕННЫЙ ТЕКСТ (сообщение git commit / тело PR /
# скрипт), а НЕ чтение файла. Упоминание .env/ключа внутри тела, собираемого через `$(cat <<'EOF' … EOF)`,
# ложно ловилось как «cat + .env» (поймано 07.07.2026 на коммитах про PROAI_MAX_TPM). Вырезаем тело heredoc
# перед reader/target-сканом. Реальное чтение файла (`cat /x/.env`, без heredoc) остаётся под блоком.
HEREDOC_BODY = re.compile(r"<<-?\s*(['\"]?)([A-Za-z_]\w*)\1[\s\S]*?\n[ \t]*\2\b")

# Загрузка `.env` В ОКРУЖЕНИЕ из inline-кода: `python3 -c "... open('/opt/app/.env') ... os.environ ..."`,
# `load_dotenv()`, `dotenv.config()`. Значение уходит в окружение процесса, а НЕ в stdout/контекст LLM —
# это код-эквивалент уже разрешённого `set -a; . .env; set +a`. Без этого послабления любой запуск
# служебного скрипта, который сам поднимает окружение сервиса, ложно блокировался как «чтение секрета»
# (поймано 09.09.2026 на отправке инструкции менеджерам MPZORRO).
# КОМПЕНСАЦИЯ: ENV_PRINT_CODE ниже ловит попытку напечатать секрет из того же кода.
ENV_TO_ENVIRON = re.compile(
    r"load_dotenv\s*\([^)]*\)"
    r"|\.config\s*\([^)]*\.env[^)]*\)"
    r"|open\s*\([^)]*\.env[^)]*\)",
    re.IGNORECASE,
)
# Послабление действует только когда прочитанное кладут в окружение, а не просто читают файл.
ENV_ENVIRON_USE = re.compile(r"os\.environ|process\.env|load_dotenv|\bdotenv\b", re.IGNORECASE)

# Печать секрета ИЗ КОДА: `print(open(".env").read())`, `console.log(process.env.KEY)`.
# Это ровно тот сценарий, который открывает послабление ENV_TO_ENVIRON, поэтому проверяем до вырезания.
ENV_PRINT_CODE = re.compile(
    r"(?:print|pprint|console\.log|console\.error"
    r"|sys\.stdout\.write|process\.stdout\.write)\s*\("
    r"[^)]*(?:\.read\s*\(|readFileSync|os\.environ|process\.env|getenv)",
    re.IGNORECASE,
)

# Правка `.env` НА МЕСТЕ: `sed -i '' 's/A=1/A=2/' /opt/app/.env`. Результат уходит в файл, в stdout ничего
# не попадает — редактировать конфиг сервиса можно. Без флага `-i` sed печатает содержимое и остаётся
# под блоком (sed есть в списке SECRET_READERS).
SED_INPLACE_ENV = re.compile(
    # флаги (среди них -i), затем скрипт — в кавычках (внутри допустимы `;`, `|`, `&`) или голым словом,
    # затем аргументы до самого .env-файла (14.09.2026: `sed -i -E "s/a//; s/b//" …/.env` ложно блокировался)
    r"\bsed\s+(?:-[A-Za-z]+\s+)*-[A-Za-z]*i[A-Za-z]*\S*\s+(?:-[A-Za-z]+\s+)*"
    r"(?:'[^']*'|\"[^\"]*\"|[^\s|;&]+)\s+[^|;&\n]*?\.env\b[^|;&\n]*",
    re.IGNORECASE,
)

# ЗАКАВЫЧЕННЫЙ ПАТТЕРН поиска у grep/rg — это строка запроса, а не файл: `grep -n "git add ..." README.md`
# инспектирует README, а не секрет. Вырезаем паттерн только когда после него идёт ещё аргумент (значит это
# точно паттерн, а следом цель). Если целью остаётся сам секретный файл, он уцелеет в остатке и блок
# сработает (поймано 09.09.2026 на чтении README хуков).
GREP_PATTERN = re.compile(
    r"\b(?:grep|egrep|fgrep|rg)\b(?:\s+-{1,2}[\w-]+)*\s+(['\"])(?:(?!\1).)*\1(?=\s+\S)"
)

# РЕЗЕРВНАЯ КОПИЯ .env рядом с ним: `cp /opt/app/.env /opt/app/.env.bak-0914` — файл остаётся на том же
# хосте, в stdout ничего не уходит. Нужна перед `sed -i` по конфигу сервиса (14.09.2026, MPZORRO).
ENV_BACKUP_COPY = re.compile(
    r"\bcp\s+(?:-[a-z]+\s+)?(['\"]?)(\S*?\.env)\1\s+\1\2\.[\w.-]+\1(?=\s|$|[;&|])",
    re.IGNORECASE,
)
# grep БЕЗ ВЫВОДА СОДЕРЖИМОГО по .env: `grep -q "ID" …/.env` / `grep -c …` / `grep -l …` — наружу уходит
# только «есть/нет» или число совпадений, не значения. Паттерн должен быть закавычен (14.09.2026).
GREP_NO_CONTENT_ENV = re.compile(
    r"\b(?:grep|egrep|fgrep|rg)\s+(?:-[A-Za-z]+\s+)*-[A-Za-z]*[cqlL][A-Za-z]*\s+(?:-[A-Za-z]+\s+)*(['\"])(?:(?!\1).)*\1\s+\S*\.env\b\S*",
)

GIT_ADD_ENV = re.compile(
    r"\bgit\s+add\b[^|;&\n]*[\s/'\"]\.env(?!\.(?:example|sample|template|dist)\b)(?:\.[\w.-]+)?\b"
)

BROAD_SCAN = re.compile(r"\b(?:find\s+(?:/|~)|ls\s+-r\s+(?:/|~))(?=['\"]?(?:\s|$))", re.IGNORECASE)
# Команда целиком уходит на удалённый хост (ssh/scp): скан выполняется там, контекст/рантайм Мака не страдает.
REMOTE_SHELL = re.compile(r"^\s*(?:[A-Za-z_][A-Za-z0-9_]*=\S*\s+)*(?:ssh|autossh)\b")

# Имена .js, легальные в TS-проекте: тулинг-конфиги и скрипты.
JS_CONFIG_OK = re.compile(r"(?:^|/)(?:[\w.-]*\.config\.js|\.[\w.-]+)$")


def tool_name(payload: dict) -> str:
    return str(payload.get("tool_name") or payload.get("preToolUse", {}).get("tool") or "")


def tool_input(payload: dict) -> dict:
    value = payload.get("tool_input")
    if isinstance(value, dict):
        return value
    legacy = payload.get("preToolUse", {}).get("parameters")
    return legacy if isinstance(legacy, dict) else {}


def command_from_input(params: dict) -> str:
    for key in ("command", "cmd"):
        if isinstance(params.get(key), str):
            return params[key]
    return ""


def writes_js_in_ts_project(params: dict, workspace: Path) -> bool:
    """Новый .js/.jsx в TS-проекте — deny, кроме конфигов тулинга,
    dot-файлов и каталога scripts/."""
    if not (workspace / "tsconfig.json").exists():
        return False
    target = params.get("file_path") or params.get("path") or ""
    if not isinstance(target, str) or not (target.endswith(".js") or target.endswith(".jsx")):
        return False
    if JS_CONFIG_OK.search(target):
        return False
    if "scripts" in Path(target).parts:
        return False
    return True


def main() -> int:
    payload = read_payload()
    name = tool_name(payload)
    params = tool_input(payload)
    workspace = workspace_from_payload(payload)
    cmd = command_from_input(params)

    if name in {"Bash", "execute_command", "shell"}:
        # Текст БЕЗ тела heredoc: содержимое <<EOF … EOF — данные (сообщение коммита, тело скрипта-документа),
        # а не исполняемая строка. Все deny-правила ниже смотрят только на этот остаток.
        # Ограничение: `bash <<EOF` с деструктивом в теле хук не увидит — известный trade-off HEREDOC_BODY.
        cmd_no_heredoc = GREP_PATTERN.sub(" grep ", HEREDOC_BODY.sub(" ", cmd))
        if DANGEROUS_RM.search(cmd_no_heredoc):
            return emit_json(deny_pre_tool("Blocked by ZCode hook: destructive rm against a system/root/home path."))
        if re.search(r"(^|[;&|]\s*)sudo\b", cmd_no_heredoc):
            return emit_json(deny_pre_tool("Blocked by ZCode hook: sudo requires explicit user approval outside hooks."))
        # Вырезаем перед reader-проверкой: identity-аргументы ssh/scp и присваивание пути-ключа в переменную
        # (не чтение) И безопасные записи в .env (значение идёт в файл, не в контекст). Чтение .env / литерала
        # приватного ключа в stdout при этом остаётся под блоком.
        cmd_secret_scan = SECRET_SOURCE.sub(" ", SECRET_WRITE.sub(" ", SSH_KEY_ASSIGN.sub(" ", SSH_IDENTITY_ARG.sub("", cmd_no_heredoc))))
        # Закавыченный паттерн grep вырезаем и здесь: `grep -n "git add ..." README.md` —
        # это поиск по README, а не команда git и не чтение секрета.
        if SECRET_ECHO.search(cmd_no_heredoc) and SECRET_TARGET.search(cmd_no_heredoc):
            return emit_json(deny_pre_tool(
                "Blocked by ZCode hook: printing a secret to stdout. Source the .env and use $VAR directly."
            ))
        if ENV_PRINT_CODE.search(cmd_no_heredoc) and SECRET_TARGET.search(cmd_no_heredoc):
            return emit_json(deny_pre_tool(
                "Blocked by ZCode hook: printing a secret from code. "
                "Load it into os.environ and use the variable, do not print it."
            ))
        # Правка .env на месте и загрузка .env в окружение из кода — не чтение в контекст.
        cmd_secret_scan = GREP_NO_CONTENT_ENV.sub(" grep ", cmd_secret_scan)
        cmd_secret_scan = ENV_BACKUP_COPY.sub(" ", cmd_secret_scan)
        cmd_secret_scan = GREP_PATTERN.sub(" grep ", cmd_secret_scan)
        cmd_secret_scan = SED_INPLACE_ENV.sub(" ", cmd_secret_scan)
        if ENV_ENVIRON_USE.search(cmd_secret_scan):
            cmd_secret_scan = ENV_TO_ENVIRON.sub(" ", cmd_secret_scan)
        if (SECRET_READERS.search(cmd_secret_scan) or INLINE_EVAL.search(cmd_secret_scan)) and SECRET_TARGET.search(cmd_secret_scan):
            return emit_json(deny_pre_tool(
                "Blocked by ZCode hook: reading secret files (.env / private keys / .pem) into context is not allowed. "
                "Use placeholders like <stored in secrets> or ask Pavel explicitly."
            ))
        # Тоже по тексту без heredoc: упоминание команды в теле документа или скрипта — данные.
        if GIT_ADD_ENV.search(cmd_no_heredoc):
            return emit_json(deny_pre_tool("Blocked by ZCode hook: .env files must not be added to git (.env.example is fine)."))
        # BROAD_SCAN тоже по тексту без heredoc: `find /` внутри тела загружаемого скрипта/документа — данные,
        # не выполняемая команда (симметрично GIT_ADD_ENV выше; поймано 25.09.2026 на питон-хередоке со сканом скиллов).
        if BROAD_SCAN.search(cmd_no_heredoc) and not REMOTE_SHELL.search(cmd):
            return emit_json(deny_pre_tool("Blocked by ZCode hook: broad recursive scan over root/home is too risky for context and runtime."))

    if name in {"Write", "Edit", "MultiEdit"}:
        if writes_js_in_ts_project(params, workspace):
            return emit_json(deny_pre_tool("This project has tsconfig.json. Use .ts/.tsx instead of .js/.jsx (tooling configs like *.config.js are allowed)."))

    return emit_json({"continue": True, "suppressOutput": True})


if __name__ == "__main__":
    raise SystemExit(main())
