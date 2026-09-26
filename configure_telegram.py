#!/usr/bin/env python3
from __future__ import annotations

import getpass
import os
from pathlib import Path

ROOT = Path.home() / ".hardcoding-agent-kit"
TARGET = ROOT / "secrets" / "telegram.env"

def main() -> int:
    print("Hard Coding Agent Kit · локальная настройка Telegram")
    print("Секреты вводятся в терминале и не должны попадать в чат.")
    token = getpass.getpass("Bot token (ввод скрыт): ").strip()
    chat_id = input("Chat ID: ").strip()
    if not token or not chat_id:
        print("Отмена: оба значения обязательны.")
        return 1
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(f"TELEGRAM_BOT_TOKEN={token}\nTELEGRAM_CHAT_ID={chat_id}\n")
    os.chmod(TARGET, 0o600)
    print(f"Готово: {TARGET} создан с правами 600.")
    print("Теперь запусти: python3 ~/.hardcoding-agent-kit/hooks/test_notify.py")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
