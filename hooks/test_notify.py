#!/usr/bin/env python3
from __future__ import annotations

import json
import urllib.parse
import urllib.request

from common import SECRETS_DIR, load_env

def main() -> int:
    cfg = load_env(SECRETS_DIR / "telegram.env")
    token = cfg.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = cfg.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        print(f"Нет кредов в {SECRETS_DIR / 'telegram.env'}")
        return 1
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat_id,"text":"✅ Hard Coding Agent Kit: Telegram E2E работает."}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type":"application/x-www-form-urlencoded"})
    try:
        data = json.loads(urllib.request.urlopen(req, timeout=10).read().decode())
        ok = bool(data.get("ok"))
    except Exception as exc:
        print(f"Не отправлено: {type(exc).__name__}")
        return 1
    print("PASS: сообщение отправлено" if ok else "FAIL: Telegram вернул ok=false")
    return 0 if ok else 1

if __name__ == "__main__":
    raise SystemExit(main())
