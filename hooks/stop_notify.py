#!/usr/bin/env python3
from __future__ import annotations
import html
import json
import os
import re
import urllib.parse
import urllib.request
from pathlib import Path
from common import SECRETS_DIR, emit_json, load_env_file, project_identity, read_payload, workspace_from_payload
import tg_format

MAX_INPUT = 7000   # сколько символов ответа берём в уведомление (до форматирования)
MAX_CHUNKS = 3     # максимум сообщений в Telegram на одно уведомление


def credentials() -> tuple[str, str]:
    """Env первичен; фолбэк — chmod-600 файл ~/.zcode/secrets/telegram.env."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        data = load_env_file(SECRETS_DIR / "telegram.env")
        token = token or data.get("TELEGRAM_BOT_TOKEN", "")
        chat_id = chat_id or data.get("TELEGRAM_CHAT_ID", "")
    return token, chat_id


def send_telegram(token: str, chat_id: str, message: str) -> bool:
    """True только при ok:true от Bot API.

    urllib вместо curl: quoted-значения curl-конфига не переживают многострочный
    текст (ловили ok=False на любом сообщении с \n). Токен живёт только в памяти
    процесса, в argv/ps не попадает.
    """
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML",
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        resp = json.loads(urllib.request.urlopen(req, timeout=10, context=tg_format._ssl_context()).read().decode("utf-8"))
        return bool(resp.get("ok"))
    except Exception:
        return False


def last_assistant_from_transcript(path_value: str) -> str:
    """Claude Code does not pass the assistant text in the Stop payload; it gives
    transcript_path (JSONL). Walk it backwards for the last assistant text."""
    try:
        path = Path(path_value).expanduser()
        if not path.is_file():
            return ""
        lines = path.read_text(errors="ignore").splitlines()
        for line in reversed(lines):
            line = line.strip()
            if not line:
                continue
            try:
                rec = json.loads(line)
            except Exception:
                continue
            msg = rec.get("message") if isinstance(rec, dict) else None
            if isinstance(msg, dict) and msg.get("role") == "assistant":
                content = msg.get("content")
                if isinstance(content, str) and content.strip():
                    return content
                if isinstance(content, list):
                    texts = [c.get("text", "") for c in content if isinstance(c, dict) and c.get("type") == "text"]
                    joined = " ".join(t for t in texts if t).strip()
                    if joined:
                        return joined
    except Exception:
        pass
    return ""


def build_chunks(raw: str, cfg: dict) -> list[str]:
    """LLM-форматирование (порт n8n «LLM HTML»+«CleanText»); при сбое — plain."""
    api_key = cfg.get("LLM_FORMAT_API_KEY", "")
    base_url = cfg.get("LLM_FORMAT_BASE_URL", "")
    force_fallback = bool(os.environ.get("ZCODE_TG_FORCE_FALLBACK"))  # для теста фолбэка
    # детаблер ДО LLM: таблицы уходят в буллеты независимо от послушности модели
    raw = tg_format.detable(raw)
    # короткий «сырой» текст без разметки не гоняем через LLM — незачем
    rich = len(raw) >= 200 or bool(re.search(r"[`*#<>|]|https?://|\n", raw))
    if api_key and base_url and rich and not force_fallback:
        try:
            formatted = tg_format.llm_format(
                raw, base_url, api_key,
                model=cfg.get("LLM_FORMAT_MODEL", "gpt-5.4-mini"),
                timeout=int(cfg.get("LLM_FORMAT_TIMEOUT", "45")),
                reasoning_effort=cfg.get("LLM_FORMAT_REASONING", "low"),
            )
            if formatted and tg_format.strip_tags(formatted).strip():
                safe = tg_format.balance(tg_format.sanitize(formatted))
                chunks = tg_format.split_telegram_html(safe, max_len=3900, max_chunks=MAX_CHUNKS)
                if chunks and chunks[0]:
                    return chunks
        except Exception as e:
            print(f"tg_format fallback: {type(e).__name__}: {str(e)[:120]}", flush=True, file=__import__("sys").stderr)
    # фолбэк без LLM: локальная Markdown→HTML + детаблер, а не сырые звёздочки
    safe = tg_format.balance(tg_format.sanitize(tg_format.md_to_html_basic(raw)))
    return tg_format.split_telegram_html(safe, max_len=3900, max_chunks=MAX_CHUNKS) or [html.escape(raw)[:3500]]


def main() -> int:
    payload = read_payload()
    if os.environ.get("ZCODE_TG_NOTIFY_DISABLE"):
        return emit_json({"continue": True, "suppressOutput": True})
    token, chat_id = credentials()
    if not token or not chat_id:
        # без кредов не тратимся на парсинг транскрипта
        return emit_json({"continue": True, "suppressOutput": True})

    workspace = workspace_from_payload(payload)
    ident = project_identity(workspace)
    last = payload.get("last_assistant_message")
    if not last:
        last = last_assistant_from_transcript(payload.get("transcript_path", "")) or "ZCode response completed."
    raw = str(last).strip()[:MAX_INPUT]
    project = ident.get("projectLabel") or workspace.name
    header = f"<b>🤖 ZCode finished</b> — <i>{html.escape(str(project)[:120])}</i>"

    cfg = load_env_file(SECRETS_DIR / "telegram.env")
    chunks = build_chunks(raw, cfg)
    chunks[0] = header + "\n" + chunks[0]

    debug = os.environ.get("ZCODE_TG_NOTIFY_DEBUG")
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        prefix = f"<i>[{i + 1}/{total}]</i>\n" if total > 1 and i > 0 else ""
        ok = send_telegram(token, chat_id, prefix + chunk)
        if not ok:
            # HTML не прошёл валидацию Telegram — шлём этот чанк плоским текстом
            plain = html.escape(tg_format.strip_tags(prefix + chunk))[:3900]
            ok = send_telegram(token, chat_id, plain)
        if debug:
            print(f"chunk {i + 1}/{total} sent ok={ok} len={len(chunk)}", flush=True, file=__import__("sys").stderr)
    return emit_json({"continue": True, "suppressOutput": True})


if __name__ == "__main__":
    raise SystemExit(main())
