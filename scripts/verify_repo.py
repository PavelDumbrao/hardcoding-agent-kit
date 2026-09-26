#!/usr/bin/env python3
from pathlib import Path
import json,re
ROOT=Path(__file__).resolve().parents[1]
problems=[]
for p in ROOT.rglob("*"):
    if not p.is_file() or ".git" in p.parts: continue
    if "__pycache__" in p.parts or p.suffix==".pyc": problems.append(f"compiled artifact tracked: {p.relative_to(ROOT)}")
text_paths=[p for p in ROOT.rglob("*") if p.is_file() and p.suffix in {".md",".py",".sh",".json",".html",".example"}]
combined="\n".join(p.read_text(errors="ignore") for p in text_paths)
secret_patterns={"Telegram token":r"\b\d{8,12}:[A-Za-z0-9_-]{30,}\b","private key":r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----","OpenAI-like key":r"\bsk-[A-Za-z0-9_-]{20,}\b","GitHub PAT":r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"}
for label,pattern in secret_patterns.items():
    if re.search(pattern,combined): problems.append("possible secret: "+label)
for rel in ("adapters/zcode/config-snippet.json","adapters/claude/settings-snippet.json","adapters/codex/hooks.json","config-examples/config-zcode.json"):
    try: json.loads((ROOT/rel).read_text())
    except Exception as exc: problems.append(f"invalid JSON {rel}: {exc}")
for p in (ROOT/"hooks").glob("*.py"): compile(p.read_text(),str(p),"exec")
for rel in ["skills/hardcoding-verify-done/SKILL.md","install.py","configure_telegram.py","verify_install.py","PROMPT.md","PRACTICAL.md","practical/index.html"]:
    if not (ROOT/rel).is_file(): problems.append("missing: "+rel)
if problems:
    [print("FAIL:",x) for x in problems]; raise SystemExit(1)
print("PASS: repo structure, JSON, Python syntax and bounded secret scan")
