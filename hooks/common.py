#!/usr/bin/env python3
"""Shared helpers for ZCode lifecycle hooks.

Ported from the Codex hook system but fully isolated:
- scripts live in ~/.zcode/hooks/ (Claude uses ~/.claude/hooks/, Codex uses ~/.codex/hooks/)
- mutable state lives under ~/.zcode/state/hooks/ (Claude uses ~/.claude/state/hooks/, Codex uses ~/.codex/logs/)
so the two systems (and Cline) never overwrite each other's files.
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# --- Claude-owned roots (isolated namespace) ---------------------------------
ZCODE_HOME = Path.home() / ".zcode"
HOOK_DIR = ZCODE_HOME / "hooks"
STATE_ROOT = ZCODE_HOME / "state" / "hooks"
LOG_DIR = STATE_ROOT / "logs"
CONTEXT_GUARD_DIR = STATE_ROOT / "context-guard"
COMPACTION_DIR = STATE_ROOT / "compaction"
TASK_MARKER_DIR = COMPACTION_DIR / "by-task"

# Branded marker prefix so any written file is unambiguously "ours".
NS = "zcode"

PROJECT_RE = re.compile(r"^\s*Проект:\s*(.+?)\s*$")
PROGRESS_RE = re.compile(r"^\s*Заверш[её]нность:\s*(.+?)\s*$")
BROAD_ROOTS = {str(Path.home().resolve()), str((Path.home() / "Desktop").resolve()), "/"}
SENSITIVE_RE = re.compile(r"(?i)(api[_-]?key|token|secret|password|authorization|bearer|chat_id)\s*[:=]\s*([^\s,'\"}]+)")


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_payload() -> dict[str, Any]:
    raw = sys.stdin.read()
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {"_raw": raw}


def emit_json(data: dict[str, Any]) -> int:
    print(json.dumps(data, ensure_ascii=False))
    return 0


def extra_context(event: str, text: str, *, suppress: bool = True) -> dict[str, Any]:
    """Inject text into the model context.

    Claude Code consumes context injection via hookSpecificOutput.additionalContext
    for SessionStart / UserPromptSubmit / PostToolUse (and SubagentStart). For
    events that do not support additionalContext (PreCompact), fall back to
    systemMessage, which is surfaced to the user as a notice.
    """
    payload: dict[str, Any] = {"continue": True, "suppressOutput": suppress}
    if not text:
        return payload
    if event in {"UserPromptSubmit", "PostToolUse", "SessionStart", "SubagentStart"}:
        payload["hookSpecificOutput"] = {
            "hookEventName": event,
            "additionalContext": text,
        }
    else:
        payload["systemMessage"] = text
    return payload


def deny_pre_tool(reason: str) -> dict[str, Any]:
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }


def redacted(text: Any) -> str:
    value = text if isinstance(text, str) else json.dumps(text, ensure_ascii=False, default=str)
    value = SENSITIVE_RE.sub(lambda m: f"{m.group(1)}=<redacted>", value)
    value = re.sub(r"(?i)(Bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1<redacted>", value)
    value = re.sub(r"https://api\.telegram\.org/bot[^/\s]+", "https://api.telegram.org/bot<redacted>", value)
    return value


def resolve_realpath(path_value: str | None) -> str:
    if not path_value:
        return ""
    p = Path(path_value).expanduser()
    try:
        return str(p.resolve()) if p.exists() else str(p.absolute())
    except Exception:
        return os.path.abspath(os.path.expanduser(str(path_value)))


def workspace_from_payload(payload: dict[str, Any]) -> Path:
    for key in ("cwd", "workspacePath", "workspace_path", "repo_path"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return Path(value).expanduser()
    env_pwd = os.environ.get("PWD")
    return Path(env_pwd or os.getcwd()).expanduser()


def is_broad_root(path: Path) -> bool:
    real = resolve_realpath(str(path))
    return real in BROAD_ROOTS


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "_", value or "unknown").strip("._-")
    return cleaned or "unknown"


def clean_label(value: str) -> str:
    text = (value or "").strip()
    if text.startswith("`") and text.endswith("`") and len(text) >= 2:
        text = text[1:-1].strip()
    return text


def slugify(value: str) -> str:
    text = clean_label(value)
    if text.endswith(".md"):
        text = text[:-3]
    safe = []
    previous_dash = False
    for char in text.lower():
        if char.isalnum():
            safe.append(char)
            previous_dash = False
        elif not previous_dash:
            safe.append("-")
            previous_dash = True
    return "".join(safe).strip("-") or "workspace"


def extract_project_header(path: Path) -> tuple[str, str]:
    try:
        for line in path.read_text(errors="ignore").splitlines():
            project = PROJECT_RE.match(line)
            if project:
                return clean_label(project.group(1)), ""
    except Exception:
        pass
    return "", ""


def project_identity(workspace: Path) -> dict[str, Any]:
    workspace_real = resolve_realpath(str(workspace))
    result: dict[str, Any] = {
        "workspace": str(workspace),
        "workspaceRealpath": workspace_real,
        "isBroadRoot": is_broad_root(workspace),
        "projectLabel": "",
        "projectSlug": "",
        "projectIdentitySource": "",
        "projectIdentityPath": "",
        "foundExplicitHeader": False,
    }

    # AGENTS.md (ZCode convention) first, then Claude/CLAUDE.md, then shared cross-tool continuity files.
    candidates = [
        ("agents-header", workspace / "AGENTS.md"),
        ("claude-md-header", workspace / "CLAUDE.md"),
        ("claude-local-header", workspace / "CLAUDE.local.md"),
        ("implementation-plan-header", workspace / "implementation_plan.md"),
        ("project-state-header", workspace / "codex_docs" / "project-state.md"),
        ("handoff-header", workspace / "codex_docs" / "handoff-summary.md"),
    ]
    for source, path in candidates:
        label, _ = extract_project_header(path)
        if label:
            result.update({
                "projectLabel": label,
                "projectSlug": slugify(label),
                "projectIdentitySource": source,
                "projectIdentityPath": str(path),
                "foundExplicitHeader": True,
            })
            return result

    fallback = Path(workspace_real).name if workspace_real else workspace.name
    fallback = fallback or "workspace"
    result.update({
        "projectLabel": fallback,
        "projectSlug": slugify(fallback),
        "projectIdentitySource": "workspace-basename-fallback",
        "projectIdentityPath": workspace_real or str(workspace),
    })
    return result


def read_limited(path: Path, max_chars: int = 16000) -> str:
    if not path.exists() or not path.is_file():
        return ""
    text = path.read_text(errors="ignore")
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n\n[... truncated for ZCode continuity preview ...]"
    return text


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, len(text) // 4)


def ensure_dirs() -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    CONTEXT_GUARD_DIR.mkdir(parents=True, exist_ok=True)
    COMPACTION_DIR.mkdir(parents=True, exist_ok=True)
    TASK_MARKER_DIR.mkdir(parents=True, exist_ok=True)


ARTIFACT_TTL_SECONDS = 7 * 24 * 3600  # context-guard state/artifacts live 7 days
LOG_ROTATE_BYTES = 5 * 1024 * 1024

SECRETS_DIR = ZCODE_HOME / "secrets"


def _last_activity(entry: Path) -> float:
    # dir mtime does not change on in-place file rewrites; check state.json too
    latest = entry.stat().st_mtime
    state = entry / "state.json"
    try:
        if state.exists():
            latest = max(latest, state.stat().st_mtime)
    except Exception:
        pass
    return latest


def cleanup_state(now: float | None = None) -> None:
    """Prune stale context-guard task dirs and rotate the tool-usage log.

    Called once per session from SessionStart; must never raise.
    """
    import shutil

    ts = now or time.time()
    try:
        for entry in CONTEXT_GUARD_DIR.iterdir():
            try:
                if entry.is_dir() and ts - _last_activity(entry) > ARTIFACT_TTL_SECONDS:
                    shutil.rmtree(entry, ignore_errors=True)
            except Exception:
                pass
    except Exception:
        pass
    log_path = LOG_DIR / "tool-usage.log"
    try:
        if log_path.exists() and log_path.stat().st_size > LOG_ROTATE_BYTES:
            rotated = log_path.with_name("tool-usage.log.1")
            rotated.unlink(missing_ok=True)
            log_path.rename(rotated)
    except Exception:
        pass


def load_env_file(path: Path) -> dict[str, str]:
    """Read KEY=VALUE lines from a chmod-600 secrets file; values never logged."""
    data: dict[str, str] = {}
    try:
        if path.is_file():
            for line in path.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                data[key.strip()] = value.strip().strip('"').strip("'")
    except Exception:
        pass
    return data


def turn_or_task_id(payload: dict[str, Any]) -> str:
    for key in ("session_id", "turn_id", "taskId", "conversation_id"):
        value = payload.get(key)
        if isinstance(value, str) and value:
            return value
    return "unknown"


def read_json_file(path: Path) -> dict[str, Any]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def write_json_file(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
