#!/usr/bin/env python3
from __future__ import annotations

import html
import json
import urllib.parse
import urllib.request

from common import SECRETS_DIR, allow, emit, load_env, read_payload

def send(token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id":chat_id,"text":text,"parse_mode":"HTML","disable_web_page_preview":"true"}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
        return bool(data.get("ok"))
    except Exception:
        return False

def main() -> int:
    cfg = load_env(SECRETS_DIR / "telegram.env")
    token = cfg.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = cfg.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return emit(allow())
    payload = read_payload()
    raw = str(payload.get("last_assistant_message") or payload.get("lastAssistantMessage") or "AI coding agent завершил текущий ответ.").strip()[:3200]
    send(token, chat_id, "<b>🤖 Hard Coding Agent Kit</b>\n" + html.escape(raw))
    return emit(allow())

if __name__ == "__main__":
    raise SystemExit(main())
