#!/usr/bin/env python3
from __future__ import annotations
import argparse,json,os
from pathlib import Path
HOME=Path.home(); ROOT=HOME/".hardcoding-agent-kit"
def main()->int:
    ap=argparse.ArgumentParser(); ap.add_argument("--runtime",choices=["zcode","claude","codex"],required=True); args=ap.parse_args()
    configs={"zcode":HOME/".zcode"/"cli"/"config.json","claude":HOME/".claude"/"settings.json","codex":HOME/".codex"/"hooks.json"}
    skills={r:HOME/f".{r}"/"skills"/"hardcoding-verify-done"/"SKILL.md" for r in ("zcode","claude","codex")}
    checks=[]
    def add(label,ok): checks.append((label,bool(ok)))
    add("shared hooks exist",(ROOT/"hooks"/"pre_tool_use.py").is_file()); add("skill installed",skills[args.runtime].is_file())
    path=configs[args.runtime]
    try:
        cfg=json.loads(path.read_text()); add("config valid JSON",isinstance(cfg,dict)); hooks=cfg.get("hooks",{}); events=hooks.get("events",{}) if args.runtime=="zcode" else hooks; add("SessionStart wired",bool(events.get("SessionStart"))); add("PreToolUse wired",bool(events.get("PreToolUse"))); add("Stop wired",bool(events.get("Stop")))
    except Exception: add("config valid JSON",False)
    secret=ROOT/"secrets"/"telegram.env"; add("secret file exists",secret.is_file())
    if secret.exists():
        if os.name=="nt": add("secret file in user profile (Windows: права NTFS)",str(secret).startswith(str(HOME)))
        else: add("secret permissions private",(secret.stat().st_mode&0o077)==0)
    if os.name=="nt":
        try:
            raw=path.read_text(); add("hook commands Windows-ready","HCAK_RUNTIME=" not in raw and "python3 ~/" not in raw)
        except Exception: add("hook commands Windows-ready",False)
    failed=[label for label,ok in checks if not ok]
    for label,ok in checks: print(("PASS" if ok else "FAIL")+":",label)
    print(f"TOTAL: {len(checks)-len(failed)}/{len(checks)} PASS"); return 1 if failed else 0
if __name__=="__main__": raise SystemExit(main())
