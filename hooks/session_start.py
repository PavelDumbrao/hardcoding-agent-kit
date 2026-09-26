#!/usr/bin/env python3
from __future__ import annotations

from common import additional_context, emit, limited, read_payload, workspace

CANDIDATES = (
    ("AGENTS.md", 2200),
    ("CLAUDE.md", 2200),
    ("implementation_plan.md", 3000),
    ("codex_docs/project-state.md", 3000),
    ("codex_docs/handoff-summary.md", 2200),
    ("memory-bank/activeContext.md", 2200),
)

def build_context() -> str:
    payload = read_payload()
    root = workspace(payload)
    parts: list[str] = []
    total = 0
    for rel, limit in CANDIDATES:
        text = limited(root / rel, limit)
        if not text:
            continue
        block = f"### {rel}\n{text}"
        if total + len(block) > 8000:
            break
        parts.append(block)
        total += len(block)
    if not parts:
        return emit({"continue": True, "suppressOutput": True})
    text = (
        "📋 HARD CODING CONTINUITY\n"
        "Используй это как ориентир по текущему проекту. Не выдумывай состояние, которого здесь нет.\n\n"
        + "\n\n".join(parts)
    )
    return emit(additional_context("SessionStart", text))

if __name__ == "__main__":
    raise SystemExit(build_context())
