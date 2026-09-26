#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import stat
from datetime import datetime
from pathlib import Path

KIT = Path(__file__).resolve().parent
HOME = Path.home()
DEST = HOME / ".hardcoding-agent-kit"

RUNTIMES = {
    "zcode": {"detect": HOME / ".zcode","config": HOME / ".zcode" / "cli" / "config.json","adapter": KIT / "adapters" / "zcode" / "config-snippet.json","instruction": HOME / ".zcode" / "AGENTS.md","skill_dir": HOME / ".zcode" / "skills","hooks_key": ("hooks", "events")},
    "claude": {"detect": HOME / ".claude","config": HOME / ".claude" / "settings.json","adapter": KIT / "adapters" / "claude" / "settings-snippet.json","instruction": HOME / ".claude" / "CLAUDE.md","skill_dir": HOME / ".claude" / "skills","hooks_key": ("hooks", None)},
    "codex": {"detect": HOME / ".codex","config": HOME / ".codex" / "hooks.json","adapter": KIT / "adapters" / "codex" / "hooks.json","instruction": HOME / ".codex" / "AGENTS.md","skill_dir": HOME / ".codex" / "skills","hooks_key": ("hooks", None)},
}

def detect_runtime() -> str:
    found=[name for name,cfg in RUNTIMES.items() if cfg["detect"].exists()]
    if len(found)==1:return found[0]
    if not found: raise SystemExit("Не найден ZCode, Claude Code или Codex. Укажи --runtime вручную после установки рантайма.")
    raise SystemExit("Найдено несколько рантаймов: "+", ".join(found)+". Запусти с --runtime <имя>.")

def backup(path: Path) -> Path|None:
    if not path.exists(): return None
    target=path.with_name(path.name+f".bak-{datetime.now().strftime('%Y%m%d-%H%M%S')}"); shutil.copy2(path,target); return target

def read_json(path: Path)->dict:
    if not path.exists(): return {}
    try:data=json.loads(path.read_text())
    except Exception as exc: raise SystemExit(f"Конфиг {path} невалидный JSON. Ничего не меняю: {exc}")
    if not isinstance(data,dict): raise SystemExit(f"Конфиг {path} должен быть JSON-объектом. Ничего не меняю.")
    return data

def merge_groups(existing:list,incoming:list)->list:
    out=list(existing);seen={json.dumps(x,ensure_ascii=False,sort_keys=True) for x in out}
    for item in incoming:
        key=json.dumps(item,ensure_ascii=False,sort_keys=True)
        if key not in seen: out.append(item);seen.add(key)
    return out

def merge_config(runtime:str):
    cfg=RUNTIMES[runtime];path=Path(cfg["config"]);base=read_json(path);adapter=json.loads(Path(cfg["adapter"]).read_text());old_backup=backup(path);path.parent.mkdir(parents=True,exist_ok=True)
    if runtime=="zcode":
        base_hooks=base.setdefault("hooks",{});base_hooks["enabled"]=True;events=base_hooks.setdefault("events",{})
        for event,groups in adapter["hooks"]["events"].items(): events[event]=merge_groups(events.get(event,[]),groups)
    else:
        hooks=base.setdefault("hooks",{})
        for event,groups in adapter["hooks"].items(): hooks[event]=merge_groups(hooks.get(event,[]),groups)
        if runtime=="codex" and adapter.get("description") and "description" not in base: base["description"]=adapter["description"]
    path.write_text(json.dumps(base,ensure_ascii=False,indent=2)+"\n");return path,old_backup

def copy_tree_with_backups(src:Path,dst:Path):
    dst.mkdir(parents=True,exist_ok=True);backups=[]
    for item in src.rglob("*"):
        rel=item.relative_to(src);target=dst/rel
        if item.is_dir(): target.mkdir(parents=True,exist_ok=True);continue
        target.parent.mkdir(parents=True,exist_ok=True)
        if target.exists() and target.read_bytes()!=item.read_bytes():
            b=backup(target)
            if b:backups.append(b)
        shutil.copy2(item,target)
    return backups

def main()->int:
    ap=argparse.ArgumentParser();ap.add_argument("--runtime",choices=["auto",*RUNTIMES],default="auto");args=ap.parse_args();runtime=detect_runtime() if args.runtime=="auto" else args.runtime;cfg=RUNTIMES[runtime]
    DEST.mkdir(parents=True,exist_ok=True);backups=copy_tree_with_backups(KIT/"hooks",DEST/"hooks")
    for f in ("configure_telegram.py","verify_install.py","PRACTICAL.md"): shutil.copy2(KIT/f,DEST/f)
    secret_dir=DEST/"secrets";secret_dir.mkdir(parents=True,exist_ok=True);secret=secret_dir/"telegram.env"
    if not secret.exists(): shutil.copy2(KIT/"secrets-template"/"telegram.env.example",secret);secret.chmod(stat.S_IRUSR|stat.S_IWUSR)
    skill_dst=Path(cfg["skill_dir"])/"hardcoding-verify-done";backups+=copy_tree_with_backups(KIT/"skills"/"hardcoding-verify-done",skill_dst)
    instruction=Path(cfg["instruction"]);instruction.parent.mkdir(parents=True,exist_ok=True)
    if not instruction.exists(): shutil.copy2(KIT/"AGENTS.md",instruction)
    config_path,config_backup=merge_config(runtime)
    if config_backup: backups.append(config_backup)
    print(f"PASS: runtime={runtime}");print(f"PASS: hooks={DEST/'hooks'}");print(f"PASS: skill={skill_dst}");print(f"PASS: config merged={config_path}");print(f"PASS: instruction={'created' if instruction.exists() else 'missing'} {instruction}")
    if backups:
        print("Backups:")
        for item in backups: print(" -",item)
    print("Следующий шаг: python3 ~/.hardcoding-agent-kit/hooks/smoke.py");print("Telegram: python3 ~/.hardcoding-agent-kit/configure_telegram.py");return 0
if __name__=="__main__": raise SystemExit(main())
