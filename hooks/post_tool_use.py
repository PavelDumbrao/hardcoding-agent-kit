#!/usr/bin/env python3
from __future__ import annotations
import json
import time
from pathlib import Path
from common import (
    CONTEXT_GUARD_DIR,
    LOG_DIR,
    emit_json,
    ensure_dirs,
    estimate_tokens,
    extra_context,
    now_iso,
    project_identity,
    read_json_file,
    redacted,
    safe_name,
    turn_or_task_id,
    workspace_from_payload,
    write_json_file,
    read_payload,
)

THRESHOLDS = [(20000, "early"), (50000, "medium"), (100000, "high")]


def tool_name(payload: dict) -> str:
    return str(payload.get("tool_name") or payload.get("postToolUse", {}).get("tool") or payload.get("postToolUse", {}).get("toolName") or "unknown")


def response_text(payload: dict) -> str:
    value = payload.get("tool_response")
    if value is None:
        value = payload.get("postToolUse", {}).get("result")
    if isinstance(value, str):
        return value
    return json.dumps(value, ensure_ascii=False, default=str)


def risk_level(total_tokens: int) -> str:
    if total_tokens >= 100000:
        return "critical"
    if total_tokens >= 50000:
        return "high"
    if total_tokens >= 20000:
        return "medium"
    return "low"


def main() -> int:
    ensure_dirs()
    payload = read_payload()
    workspace = workspace_from_payload(payload)
    task_id = safe_name(turn_or_task_id(payload))
    name = tool_name(payload)
    text = response_text(payload)
    chars = len(text)
    tokens = estimate_tokens(text)

    with (LOG_DIR / "tool-usage.log").open("a") as fh:
        fh.write(f"{now_iso()} | turn:{task_id} | tool:{name} | chars:{chars} | est_tokens:{tokens}\n")

    state_path = CONTEXT_GUARD_DIR / task_id / "state.json"
    state = read_json_file(state_path)
    # project_identity читает до 6 файлов — кэшируем в state, хук бежит на каждый tool call
    if state.get("workspace") == str(workspace) and state.get("projectLabel"):
        label = str(state.get("projectLabel", ""))
        slug = str(state.get("projectSlug", "")) or "workspace"
    else:
        ident = project_identity(workspace)
        label = ident.get("projectLabel", "")
        slug = ident.get("projectSlug", "")
    state["updatedAt"] = now_iso()
    state["workspace"] = str(workspace)
    state["projectLabel"] = label
    state["projectSlug"] = slug
    state["toolCalls"] = int(state.get("toolCalls", 0)) + 1
    state["cumulativeChars"] = int(state.get("cumulativeChars", 0)) + chars
    state["cumulativeEstimatedTokens"] = int(state.get("cumulativeEstimatedTokens", 0)) + tokens
    state["lastTool"] = name
    state["riskLevel"] = risk_level(int(state["cumulativeEstimatedTokens"]))
    crossed = set(state.get("thresholdsCrossed", []))
    for threshold, label in THRESHOLDS:
        if int(state["cumulativeEstimatedTokens"]) >= threshold:
            crossed.add(label)
    state["thresholdsCrossed"] = sorted(crossed)

    warning = ""
    if chars >= 80000 or tokens >= 20000:
        raw_dir = CONTEXT_GUARD_DIR / task_id / "artifacts"
        raw_dir.mkdir(parents=True, exist_ok=True)
        prefix = slug or "workspace"
        raw_path = raw_dir / f"zcode-{prefix}__{safe_name(name)}__{int(time.time())}.txt"
        preview_path = raw_dir / f"{raw_path.stem}.preview.txt"
        raw_path.write_text(redacted(text))
        preview_path.write_text(redacted(text[:4000]))
        state["lastOversizedArtifact"] = str(raw_path)
        warning = f"⚠️ ZCode hook: {name} returned a large output. Raw output was saved to {raw_path}; use preview-first and avoid re-reading the full output."

    write_json_file(state_path, state)
    if warning:
        return emit_json(extra_context("PostToolUse", warning))
    return emit_json({"continue": True, "suppressOutput": True})


if __name__ == "__main__":
    raise SystemExit(main())
