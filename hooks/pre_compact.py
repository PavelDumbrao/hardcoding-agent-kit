#!/usr/bin/env python3
from __future__ import annotations
from common import (
    COMPACTION_DIR,
    CONTEXT_GUARD_DIR,
    TASK_MARKER_DIR,
    emit_json,
    ensure_dirs,
    extra_context,
    now_iso,
    project_identity,
    read_json_file,
    safe_name,
    turn_or_task_id,
    workspace_from_payload,
    write_json_file,
    read_payload,
)


def main() -> int:
    ensure_dirs()
    payload = read_payload()
    workspace = workspace_from_payload(payload)
    ident = project_identity(workspace)
    task_id = safe_name(turn_or_task_id(payload))
    state = read_json_file(CONTEXT_GUARD_DIR / task_id / "state.json")
    timestamp = now_iso()
    summary_dir = CONTEXT_GUARD_DIR / task_id / "recovery"
    summary_dir.mkdir(parents=True, exist_ok=True)
    prefix = ident.get("projectSlug") or "workspace"
    summary_path = summary_dir / f"zcode-{prefix}__precompact-{timestamp.replace(':', '').replace('-', '')}.md"
    summary = (
        "# Claude Context Guard Recovery Bundle\n\n"
        f"- Generated at: {timestamp}\n"
        f"- Session/task ID: {task_id}\n"
        f"- Project: {ident.get('projectLabel', '')}\n"
        f"- Risk level: {state.get('riskLevel', 'low')}\n"
        f"- Tool calls: {state.get('toolCalls', 0)}\n"
        f"- Cumulative chars: {state.get('cumulativeChars', 0)}\n"
        f"- Cumulative estimated tokens: {state.get('cumulativeEstimatedTokens', 0)}\n"
        f"- Last tool: {state.get('lastTool', '')}\n"
        f"- Last oversized artifact: {state.get('lastOversizedArtifact', '')}\n\n"
        "## Recovery guidance\n"
        "- Continue from the latest project continuity below.\n"
        "- Use preview-first / chunked reads for large files or outputs.\n"
        "- If context grows again, avoid full reads and preserve raw outputs as artifacts.\n"
    )
    summary_path.write_text(summary)

    marker = {
        "timestamp": timestamp,
        "taskId": task_id,
        "userId": payload.get("userId") or payload.get("user_id") or "",
        "workspace": str(workspace),
        "workspaceRealpath": ident.get("workspaceRealpath", ""),
        "projectLabel": ident.get("projectLabel", ""),
        "projectSlug": ident.get("projectSlug", ""),
        "projectIdentitySource": ident.get("projectIdentitySource", ""),
        "riskLevel": state.get("riskLevel", "low"),
        "recoverySummaryPath": str(summary_path),
    }
    write_json_file(TASK_MARKER_DIR / f"{task_id}.json", marker)
    with (COMPACTION_DIR / "compaction.log").open("a") as fh:
        fh.write(f"{timestamp} | PreCompact | task:{task_id} | workspace:{ident.get('workspaceRealpath')} | project:{ident.get('projectLabel')} | risk:{marker['riskLevel']}\n")

    # PreCompact не умеет additionalContext: длинные простыни уходили юзеру как
    # systemMessage и не попадали в модель. Реальное восстановление делает маркер
    # + SessionStart(source=compact), поэтому сообщение — одна строка.
    has_continuity = any(
        (workspace / rel).exists()
        for rel in ("implementation_plan.md", "codex_docs/project-state.md", "codex_docs/handoff-summary.md")
    )
    label = ident.get("projectLabel") or "unknown"
    if ident.get("isBroadRoot"):
        tail = "Broad workspace root — after compaction continue only from explicit project context."
    elif has_continuity:
        tail = "Continuity files will be re-injected automatically after compaction."
    else:
        tail = "No continuity files found — after compaction ask for status or create codex_docs/project-state.md."
    context = (
        f"🚨 ZCODE PRE-COMPACT CHECKPOINT saved (project: {label}, risk: {marker['riskLevel']}). "
        f"Recovery bundle: {summary_path}. {tail}"
    )
    return emit_json(extra_context("PreCompact", context))


if __name__ == "__main__":
    raise SystemExit(main())
