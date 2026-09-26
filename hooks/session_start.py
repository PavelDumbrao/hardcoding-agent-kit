#!/usr/bin/env python3
from __future__ import annotations
import time
from pathlib import Path
from common import (
    COMPACTION_DIR,
    TASK_MARKER_DIR,
    cleanup_state,
    emit_json,
    ensure_dirs,
    extra_context,
    project_identity,
    read_json_file,
    read_limited,
    resolve_realpath,
    turn_or_task_id,
    workspace_from_payload,
    read_payload,
)
from second_brain import central_vault_block, is_central_vault

TTL_SECONDS = 43200  # 12h


def cleanup_markers() -> None:
    now = time.time()
    for path in TASK_MARKER_DIR.glob("*.json"):
        try:
            if now - path.stat().st_mtime > TTL_SECONDS:
                path.unlink(missing_ok=True)
        except Exception:
            pass


def marker_matches(data: dict, payload: dict, workspace_real: str) -> bool:
    marker_real = data.get("workspaceRealpath") or data.get("workspace") or ""
    if marker_real and workspace_real and resolve_realpath(marker_real) != workspace_real:
        return False
    marker_user = data.get("userId") or ""
    payload_user = payload.get("userId") or payload.get("user_id") or ""
    if marker_user and payload_user and marker_user != payload_user:
        return False
    return True


def select_marker(payload: dict, workspace_real: str) -> tuple[str, Path | None, str]:
    turn_id = turn_or_task_id(payload)
    candidates: list[Path] = []
    for path in TASK_MARKER_DIR.glob("*.json"):
        data = read_json_file(path)
        if marker_matches(data, payload, workspace_real):
            candidates.append(path)
    exact = [p for p in candidates if read_json_file(p).get("taskId") == turn_id]
    if exact:
        return "exact", sorted(exact, key=lambda p: p.stat().st_mtime, reverse=True)[0], "turn-id-match"
    if len(candidates) == 1:
        return "workspace-single", candidates[0], "single-workspace-candidate"
    if len(candidates) > 1:
        return "ambiguous", None, "multiple-candidates-for-workspace"
    return "none", None, "no-matching-marker"


def project_block(workspace: Path, ident: dict) -> str:
    if ident.get("isBroadRoot"):
        return ""
    parts: list[str] = []
    mapping = [
        ("implementation_plan.md", workspace / "implementation_plan.md", 16000),
        ("codex_docs/project-state.md", workspace / "codex_docs" / "project-state.md", 16000),
        ("codex_docs/handoff-summary.md", workspace / "codex_docs" / "handoff-summary.md", 12000),
        ("memory-bank/activeContext.md", workspace / "memory-bank" / "activeContext.md", 12000),
        ("memory-bank/progress.md", workspace / "memory-bank" / "progress.md", 12000),
    ]
    label = ident.get("projectLabel") or workspace.name
    for title, path, limit in mapping:
        text = read_limited(path, limit)
        if text:
            parts.append(f"### {label} / {title}\n{text}")
    return "\n\n".join(parts)


def vault_block(workspace: Path) -> str:
    hot = read_limited(workspace / "wiki" / "hot.md", 6000)
    focus = read_limited(workspace / "wiki" / "meta" / "current-focus.md", 3000)
    parts = []
    if hot:
        parts.append(f"### wiki/hot.md\n{hot}")
    if focus:
        parts.append(f"### wiki/meta/current-focus.md\n{focus}")
    return "\n\n".join(parts)


def main() -> int:
    ensure_dirs()
    cleanup_state()
    payload = read_payload()
    workspace = workspace_from_payload(payload)
    ident = project_identity(workspace)
    workspace_real = ident.get("workspaceRealpath") or resolve_realpath(str(workspace))
    cleanup_markers()
    status, marker, reason = select_marker(payload, workspace_real)

    pblock = project_block(workspace, ident)
    vblock = "" if is_central_vault(workspace) else vault_block(workspace)
    cblock = central_vault_block()
    focus = ""
    if ident.get("projectLabel") and not ident.get("isBroadRoot"):
        if ident.get("projectIdentitySource") == "workspace-basename-fallback":
            focus = f"Текущий проект (fallback): `{ident['projectLabel']}`. Зафиксируй `Проект:` в AGENTS.md или codex_docs/*.md."
        else:
            focus = f"Текущий проект: `{ident['projectLabel']}`."

    context = ""
    if marker and marker.exists():
        data = read_json_file(marker)
        summary = read_limited(Path(data.get("recoverySummaryPath") or ""), 12000)
        marker.unlink(missing_ok=True)
        context = (
            "🔄 ZCODE RESTORE AFTER COMPACTION\n\n"
            f"Previous compaction: {data.get('timestamp', 'unknown')}, risk: {data.get('riskLevel', 'unknown')}."
        )
        if summary:
            context += f"\n\n### Recovery bundle\n{summary}"
        if pblock:
            context += f"\n\n### Актуальное состояние проекта\n{pblock}"
        if vblock:
            context += f"\n\n### Vault continuity\n{vblock}"
        if cblock:
            context += f"\n\n{cblock}"
    elif pblock:
        context = f"📋 ZCODE PROJECT CONTINUITY\n\n{pblock}"
        if status == "ambiguous":
            amb_log = COMPACTION_DIR / "context-guard-ambiguous.log"
            amb_log.parent.mkdir(parents=True, exist_ok=True)
            amb_log.write_text((amb_log.read_text(errors="ignore") if amb_log.exists() else "") + f"{time.time()} | {workspace_real} | {reason}\n")
            context = "⚠️ Multiple compaction markers matched this workspace; unsafe restore skipped.\n\n" + context
        if vblock:
            context += f"\n\n### Vault continuity\n{vblock}"
        if cblock:
            context += f"\n\n{cblock}"
    elif vblock:
        context = f"🧠 ZCODE VAULT CONTINUITY\n\n{vblock}"
        if cblock:
            context += f"\n\n{cblock}"
    elif cblock:
        context = f"🧠 ZCODE VAULT CONTINUITY\n\n{cblock}"

    if focus and context:
        context = f"🎯 PROJECT FOCUS\n{focus}\n\n{context}"
    if not context:
        return emit_json({"continue": True, "suppressOutput": True})
    return emit_json(extra_context("SessionStart", context))


if __name__ == "__main__":
    raise SystemExit(main())
