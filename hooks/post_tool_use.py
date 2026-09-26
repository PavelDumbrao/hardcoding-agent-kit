#!/usr/bin/env python3
from __future__ import annotations

import json
import time
from common import STATE_DIR, allow, emit, read_payload

def main() -> int:
    payload = read_payload()
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        name = str(payload.get("tool_name") or payload.get("toolName") or "unknown")
        row = {"ts": int(time.time()), "tool": name}
        with (STATE_DIR / "tool-usage.jsonl").open("a") as fh:
            fh.write(json.dumps(row, ensure_ascii=False) + "\n")
    except Exception:
        pass
    return emit(allow())

if __name__ == "__main__":
    raise SystemExit(main())
