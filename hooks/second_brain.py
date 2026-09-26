from __future__ import annotations

import os
import re
from pathlib import Path

from common import read_limited, resolve_realpath

DEFAULT_VAULT = Path.home() / "Documents" / "second-brain-vault"

QUERY_PATTERNS = [
    r"\bobsidian\b",
    # bare "vault" false-positives on HashiCorp/Ansible vault; require context
    r"obsidian\s+vault\b",
    r"(?:в|из)\s+vault\b",
    r"vault\s+знаний",
    r"\bsecond brain\b",
    r"втор(ой|ого)\s+мозг",
    r"баз[ауы]\s+знани",
    # "по базе данных" — обычный SQL-промпт, не второй мозг
    r"по\s+базе(?!\s+данных)",
    r"вспомни",
    r"что\s+мы\s+знаем",
    r"по\s+моим\s+заметкам",
]

SAVE_PATTERNS = [
    r"сохрани",
    r"добавь\s+в\s+баз",
    r"запиши\s+в\s+(vault|wiki|баз)",
    r"запомни\s+это",
    r"\bsave-?back\b",
    r"добавь\s+в\s+(brain|wiki|vault)",
]

INGEST_PATTERNS = [
    r"\bingest\b",
    r"ингест",
    # bare "импорт" ловил обычные кодовые промпты («ошибка импорта модуля»)
    r"импорт\w*[^\n.!?]{0,40}\b(?:в\s+баз|в\s+vault|в\s+wiki|в\s+raw|источник)",
    r"обработай\s+источник",
    r"разложи\s+.*\s+по\s+vault",
    r"\braw/inbox\b",
    r"нов(ый|ые)\s+источник",
]


def central_vault_path() -> Path:
    env = os.environ.get("ZCODE_SECOND_BRAIN_VAULT") or os.environ.get("CLAUDE_SECOND_BRAIN_VAULT") or os.environ.get("CODEX_SECOND_BRAIN_VAULT")
    return Path(env or DEFAULT_VAULT).expanduser()


def is_central_vault(path: Path) -> bool:
    return resolve_realpath(str(path)) == resolve_realpath(str(central_vault_path()))


def read_limited_note(relative_path: str, max_chars: int = 6000) -> str:
    rel = Path(relative_path)
    if rel.is_absolute() or ".." in rel.parts:
        return ""
    return read_limited(central_vault_path() / rel, max_chars)


def central_vault_block(max_chars: int = 6000) -> str:
    """Trimmed preview: full hot.md dumps cost thousands of tokens per session."""
    vault = central_vault_path()
    if not vault.exists():
        return ""

    hot = read_limited(vault / "wiki" / "hot.md", min(4000, max_chars))
    remaining = max(1000, max_chars - len(hot))
    focus = read_limited(vault / "wiki" / "meta" / "current-focus.md", min(2000, remaining))

    parts: list[str] = []
    if hot:
        parts.append(f"#### wiki/hot.md (превью)\n{hot}")
    if focus:
        parts.append(f"#### wiki/meta/current-focus.md (превью)\n{focus}")
    if not parts:
        return ""

    text = "\n\n".join(parts)
    if len(text) > max_chars:
        text = text[:max_chars].rstrip() + "\n\n[... truncated for central second brain preview ...]"
    return (
        "### Central Second Brain Continuity\n" + text
        + f"\n\nПолные файлы при необходимости: `{vault}/wiki/hot.md`, `{vault}/wiki/meta/current-focus.md`."
    )


def _matches(patterns: list[str], text: str) -> bool:
    return any(re.search(pattern, text, re.IGNORECASE) for pattern in patterns)


def detect_second_brain_intent(prompt: str) -> str:
    text = prompt or ""
    if _matches(SAVE_PATTERNS, text):
        return "save"
    if _matches(INGEST_PATTERNS, text):
        return "ingest"
    if _matches(QUERY_PATTERNS, text):
        return "query"
    return ""
