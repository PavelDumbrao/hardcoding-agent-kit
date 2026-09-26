#!/usr/bin/env python3
from __future__ import annotations

import json
from typing import Any

from common import emit_json, extra_context, read_payload
from second_brain import central_vault_path, detect_second_brain_intent


PROMPT_KEYS = (
    "prompt",
    "userPrompt",
    "user_prompt",
    "message",
    "text",
    "input",
    "last_user_message",
)


def extract_prompt(payload: dict[str, Any]) -> str:
    for key in PROMPT_KEYS:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value

    for nested_key in ("userPromptSubmit", "user_prompt_submit", "hookSpecificInput"):
        nested = payload.get(nested_key)
        if isinstance(nested, dict):
            nested_prompt = extract_prompt(nested)
            if nested_prompt:
                return nested_prompt

    raw = payload.get("_raw")
    if isinstance(raw, str):
        return raw
    return json.dumps(payload, ensure_ascii=False, default=str)


def routing_context(intent: str) -> str:
    vault = central_vault_path()
    if intent == "save":
        return (
            "Second brain routing: use `obsidian-second-brain-save`.\n"
            f"Central vault: `{vault}`.\n"
            "- Save only reusable, specific, linked knowledge artifacts.\n"
            "- Do not save raw transcript noise.\n"
            "- Prefer updating existing pages over duplicates.\n"
            "- After live wiki writes, update `wiki/index.md`, append `wiki/log.md`, and refresh `wiki/hot.md`.\n"
            "- Update `wiki/meta/current-focus.md` only if the user's active knowledge priorities truly changed."
        )
    if intent == "ingest":
        return (
            "Second brain routing: use `obsidian-second-brain-ingest`.\n"
            f"Central vault: `{vault}`.\n"
            "- Treat `raw/` as source of truth and do not rewrite raw source content.\n"
            "- Prefer new sources in `raw/inbox/`.\n"
            "- Create/update source, entity, concept, question, or comparison pages as appropriate.\n"
            "- Add `[[wikilinks]]`, update `wiki/index.md`, append `wiki/log.md`, and refresh `wiki/hot.md`."
        )
    if intent == "query":
        return (
            "Second brain routing: use `obsidian-second-brain-query`.\n"
            f"Central vault: `{vault}`.\n"
            "- Read `wiki/hot.md`, then `wiki/index.md`, then targeted pages.\n"
            "- Use MCP `search_notes` for filename discovery only; use targeted file reads for content-level search.\n"
            "- Answer with `[[wikilinks]]` to supporting pages.\n"
            "- If the result is reusable, offer a save-back instead of writing silently."
        )
    return ""


def main() -> int:
    payload = read_payload()
    prompt = extract_prompt(payload)
    intent = detect_second_brain_intent(prompt)
    if not intent:
        return emit_json({"continue": True, "suppressOutput": True})

    return emit_json(extra_context("UserPromptSubmit", routing_context(intent)))


if __name__ == "__main__":
    raise SystemExit(main())
