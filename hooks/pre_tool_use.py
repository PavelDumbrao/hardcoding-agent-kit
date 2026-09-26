#!/usr/bin/env python3
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from common import allow, deny, emit, read_payload

SECRET_NAMES = re.compile(
    r"(?i)(^|/)(\.env(?:\.[^/]+)?|id_(?:rsa|ed25519|ecdsa)|[^/]+\.(?:pem|key|p12|pfx))$"
)
SAFE_SECRET_TEMPLATES = re.compile(r"(?i)(\.env\.(?:example|sample|template)|example\.env)$")
READ_WORDS = re.compile(r"(?i)\b(cat|head|tail|less|more|grep|rg|awk|sed\s+-n|strings)\b")
DANGEROUS_RM = re.compile(
    r"(?i)\brm\s+(?:-[a-zA-Z]*r[a-zA-Z]*f[a-zA-Z]*|--recursive\s+--force|-[a-zA-Z]*f[a-zA-Z]*r[a-zA-Z]*)\s+"
    r"(?:/|~|\$HOME)(?:\s|$|/etc(?:/|\s|$)|/usr(?:/|\s|$)|/System(?:/|\s|$))"
)
BROAD_SCAN = re.compile(r"(?i)(?:^|[;&|]\s*)find\s+/\s")
GIT_ADD_SECRET = re.compile(r"(?i)\bgit\s+add\b[^\n;&|]*(?:\.env(?:\.[^\s]+)?|id_(?:rsa|ed25519)|\.pem\b|\.key\b)")

def sensitive_path(value: str) -> bool:
    value = value.strip().strip("'\"")
    if SAFE_SECRET_TEMPLATES.search(value):
        return False
    return bool(SECRET_NAMES.search(value))

def extract_tool(payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    name = str(payload.get("tool_name") or payload.get("toolName") or "")
    inp = payload.get("tool_input") or payload.get("toolInput") or {}
    if not isinstance(inp, dict):
        inp = {}
    return name, inp

def evaluate(payload: dict[str, Any]) -> dict[str, Any]:
    name, inp = extract_tool(payload)
    lname = name.lower()

    if lname == "read":
        path = str(inp.get("file_path") or inp.get("path") or "")
        if sensitive_path(path):
            return deny(
                "Hard Coding guard: secret-файл нельзя читать в контекст агента. "
                "Используй локальный helper/окружение без вывода значения в чат."
            )
        return allow()

    if lname == "bash" or "shell" in lname:
        command = str(inp.get("command") or inp.get("cmd") or "")
        if re.search(r"(?i)(^|[;&|]\s*)sudo(?:\s|$)", command):
            return deny("Hard Coding guard: sudo требует отдельного явного решения пользователя.")
        if DANGEROUS_RM.search(command):
            return deny("Hard Coding guard: заблокировано разрушительное удаление системного/домашнего корня.")
        if BROAD_SCAN.search(command):
            return deny("Hard Coding guard: широкий локальный scan `find /` заблокирован.")
        if GIT_ADD_SECRET.search(command):
            return deny("Hard Coding guard: secret-файл нельзя добавлять в git.")

        candidates = re.findall(r"(?:^|\s)([~/$A-Za-z0-9_.-]+(?:/[^ \t\n;&|]+)*)", command)
        if READ_WORDS.search(command) and any(sensitive_path(x) for x in candidates):
            return deny("Hard Coding guard: чтение secret-файла в stdout/контекст заблокировано.")

        if re.search(r"(?i)(open|read_text|readFileSync)\s*\([^)]*(?:\.env|id_ed25519|id_rsa|\.pem|\.key)", command):
            if re.search(r"(?i)(print|console\.log|stdout|sys\.stdout)", command):
                return deny("Hard Coding guard: попытка вывести содержимое secret-файла в контекст заблокирована.")
        return allow()

    return allow()

def main() -> int:
    return emit(evaluate(read_payload()))

if __name__ == "__main__":
    raise SystemExit(main())
