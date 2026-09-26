#!/usr/bin/env python3
"""Тест Telegram-уведомления для Hard Coding Agent Kit.

Читает ~/.zcode/secrets/telegram.env сам (токен не попадает в чат и argv)
и отправляет короткое проверочное сообщение. Выход: 0 = отправлено, 1 = нет.
"""
from __future__ import annotations
import json
import sys
import urllib.parse
import urllib.request
from pathlib import Path

SECRETS = Path.home() / ".zcode" / "secrets" / "telegram.env"


def load_creds() -> tuple[str, str]:
    token = chat_id = ""
    if SECRETS.is_file():
        for line in SECRETS.read_text().splitlines():
            line = line.strip()
            if line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            value = value.strip().strip('"').strip("'")
            if key == "TELEGRAM_BOT_TOKEN":
                token = value
            elif key == "TELEGRAM_CHAT_ID":
                chat_id = value
    return token, chat_id


def send(token: str, chat_id: str, text: str) -> bool:
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    body = urllib.parse.urlencode({"chat_id": chat_id, "text": text, "disable_web_page_preview": "true"}).encode()
    req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"})
    try:
        ctx = ssl_context()
        resp = json.loads(urllib.request.urlopen(req, timeout=10, context=ctx).read().decode())
        return bool(resp.get("ok"))
    except Exception as e:
        print(f"send failed: {type(e).__name__}: {str(e)[:120]}", file=sys.stderr)
        return False


def ssl_context():
    import ssl
    try:
        return ssl.create_default_context(cafile="/etc/ssl/cert.pem")
    except Exception:
        return ssl.create_default_context()


def main() -> int:
    token, chat_id = load_creds()
    if not token or not chat_id:
        print(f"нет кредов в {SECRETS} — заполни TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID")
        return 1
    text = "✅ Hard Coding Agent Kit: охрана установлена, Telegram-звонок работает."
    ok = send(token, chat_id, text)
    print("отправлено" if ok else "не отправлено (проверь токен/chat_id и интернет)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
