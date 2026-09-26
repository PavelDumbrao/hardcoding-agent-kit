#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT / "practical" / "index.html").read_text()
checks = {"exactly 9 WebP visuals":HTML.count("data:image/webp;base64,")==9,"all visuals have alt":len(re.findall(r"<img\s+alt=",HTML))==9,"copy label":"Скопировать промпт" in HTML,"interactive DoD":HTML.count('type="checkbox"')>=10 and "localStorage" in HTML,"mobile viewport":'name="viewport"' in HTML,"no external script":"<script src=" not in HTML.lower(),"no external stylesheet":"<link " not in HTML.lower(),"no send-token-in-chat path":"пришлю токен в чат" not in HTML.lower(),"Practical placement":"HARDCODING PRO · PRACTICALS" in HTML}
failed=[k for k,v in checks.items() if not v]
for k,v in checks.items(): print(("PASS" if v else "FAIL")+":",k)
print(f"TOTAL: {len(checks)-len(failed)}/{len(checks)} PASS")
raise SystemExit(1 if failed else 0)
