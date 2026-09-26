#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any

HCAK_HOME = Path(os.environ.get("HCAK_HOME", "~/.hardcoding-agent-kit")).expanduser()
RUNTIME = os.environ.get("HCAK_RUNTIME", "unknown")
STATE_DIR = HCAK_HOME / "state" / RUNTIME
SECRETS_DIR = HCAK_HOME / "secrets"

def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {"_raw": raw}

def emit(data: dict[str, Any]) -> int:
    print(json.dumps(data, ensure_ascii=False))
    return 0

def allow() -> dict[str, Any]:
    return {"continue": True, "suppressOutput": True}

def additional_context(event: str, text: str) -> dict[str, Any]:
    if not text:
        return allow()
    return {
        "continue": True,
        "suppressOutput": True,
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": text,
        },
    }

def deny(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }

def workspace(payload: dict[str, Any]) -> Path:
    for key in ("cwd", "workspacePath", "workspace_path", "repo_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return Path(value).expanduser()
    return Path.cwd()

def limited(path: Path, max_chars: int = 3000) -> str:
    try:
        if not path.is_file():
            return ""
        text = path.read_text(errors="ignore")
        if len(text) > max_chars:
            text = text[:max_chars].rstrip() + "\n[…truncated…]"
        return text
    except Exception:
        return ""

def load_env(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    try:
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return out
