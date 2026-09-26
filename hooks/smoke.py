#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent

def load_pre():
    spec = importlib.util.spec_from_file_location("pre_tool_use", HERE / "pre_tool_use.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def is_deny(data):
    return data.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"

def is_allow(data):
    return data.get("continue") is True

def main() -> int:
    pre = load_pre()
    tests = []

    def check(label, payload, denied):
        out = pre.evaluate(payload)
        ok = is_deny(out) if denied else is_allow(out)
        if not ok:
            raise AssertionError(f"{label}: {json.dumps(out, ensure_ascii=False)}")
        tests.append(label)

    check("deny rm root", {"tool_name":"Bash","tool_input":{"command":"rm -rf /"}}, True)
    check("deny sudo", {"tool_name":"Bash","tool_input":{"command":"sudo systemctl restart x"}}, True)
    check("deny find root", {"tool_name":"Bash","tool_input":{"command":"find / -name x"}}, True)
    check("deny shell .env read", {"tool_name":"Bash","tool_input":{"command":"cat .env"}}, True)
    check("deny Read .env", {"tool_name":"Read","tool_input":{"file_path":"/tmp/app/.env"}}, True)
    check("allow Read .env.example", {"tool_name":"Read","tool_input":{"file_path":"/tmp/app/.env.example"}}, False)
    check("deny git add .env", {"tool_name":"Bash","tool_input":{"command":"git add .env"}}, True)
    check("allow normal command", {"tool_name":"Bash","tool_input":{"command":"git status --short"}}, False)

    print("# Hard Coding Agent Kit smoke")
    for item in tests:
        print("PASS:", item)
    print(f"TOTAL: {len(tests)}/{len(tests)} PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
