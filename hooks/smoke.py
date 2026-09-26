#!/usr/bin/env python3
"""Direct stdin smoke test for the ZCode hook scripts.

Runs each hook the same way Claude Code would (JSON on stdin), asserting the
output schema. Does not require a live Claude Code session.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

HOOK_DIR = Path.home() / ".zcode" / "hooks"


def run(script: str, payload: dict, cwd: Path, env: dict | None = None) -> tuple[int, dict, str, str]:
    proc = subprocess.run(
        ["python3", str(HOOK_DIR / script)],
        input=json.dumps(payload),
        text=True,
        capture_output=True,
        cwd=str(cwd),
        timeout=20,
        env=env,
    )
    data = {}
    if proc.stdout.strip():
        data = json.loads(proc.stdout)
    return proc.returncode, data, proc.stdout, proc.stderr


def injected(data: dict) -> str:
    hso = data.get("hookSpecificOutput") or {}
    return hso.get("additionalContext") or data.get("systemMessage") or ""


def assert_true(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def is_deny(data: dict) -> bool:
    return data.get("hookSpecificOutput", {}).get("permissionDecision") == "deny"


def is_pass(data: dict) -> bool:
    return data.get("continue") is True and "hookSpecificOutput" not in data


def make_workspace(root: Path) -> Path:
    ws = root / "zcode-hook-smoke-project"
    (ws / "codex_docs").mkdir(parents=True)
    (ws / "memory-bank").mkdir()
    (ws / "wiki" / "meta").mkdir(parents=True)
    (ws / "AGENTS.md").write_text("Проект: zcode-hook-smoke.md\nЗавершённость: [████░░░░░░] 40% — smoke\n")
    (ws / "implementation_plan.md").write_text("Проект: zcode-hook-smoke.md\n\n# Plan\nNext: smoke.\n")
    (ws / "codex_docs" / "project-state.md").write_text("Проект: zcode-hook-smoke.md\n\n# State\nNext exact step: continue smoke.\n")
    (ws / "codex_docs" / "handoff-summary.md").write_text("Проект: zcode-hook-smoke.md\n\n# Handoff\nResume smoke.\n")
    (ws / "memory-bank" / "activeContext.md").write_text("# Active\nSmoke context.\n")
    (ws / "memory-bank" / "progress.md").write_text("# Progress\nSmoke progress.\n")
    (ws / "wiki" / "hot.md").write_text("# Hot\nSmoke hot.\n")
    (ws / "wiki" / "meta" / "current-focus.md").write_text("# Focus\nSmoke focus.\n")
    (ws / "tsconfig.json").write_text("{}\n")
    return ws


def bash(cmd: str, sid: str) -> dict:
    return {"session_id": sid, "tool_name": "Bash", "tool_input": {"command": cmd}}


def main() -> int:
    tmp = Path(tempfile.mkdtemp(prefix="zcode-hooks-smoke-"))
    try:
        ws = make_workspace(tmp)
        results: list[str] = []

        rc, data, _, err = run("session_start.py", {"cwd": str(ws), "source": "startup", "session_id": "smoke-session"}, ws)
        assert_true(rc == 0 and "zcode-hook-smoke.md" in injected(data), f"SessionStart continuity failed: {err}")
        assert_true(data.get("hookSpecificOutput", {}).get("hookEventName") == "SessionStart", "SessionStart additionalContext channel missing")
        results.append("SessionStart continuity (additionalContext)")

        # --- PreToolUse: destructive rm ---
        deny_cmds = [
            ("rm -rf /", "rm -rf / (bare root)"),
            ("rm -rf /etc/nginx", "rm -rf /etc/*"),
            ("rm -rf ~", "rm -rf ~ (entire home)"),
            ("rm --recursive --force /", "rm --recursive --force /"),
            ("rm -fr $HOME", "rm -fr $HOME"),
            ("rm -rf /Users/<you>", "rm -rf /Users/<you> (entire home)"),
        ]
        for cmd, label in deny_cmds:
            rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash(cmd, f"smoke-{abs(hash(cmd)) % 9999}")}, ws)
            assert_true(rc == 0 and is_deny(data), f"PreToolUse rm deny failed for {label}: {err}")
        results.append("PreToolUse destructive rm blocks (6 variants)")

        allow_cmds = [
            ("rm -rf /tmp/build-cache", "rm -rf /tmp/x"),
            ("rm -rf /private/tmp/claude-501/scratch", "rm -rf scratchpad"),
            ("rm -rf node_modules", "rm -rf relative"),
            ("rm -rf /Users/<you>/Downloads/proj/dist", "rm -rf deep in home"),
            ("rm -rf /var/folders/xx/tmp123", "rm -rf /var/folders (mac temp)"),
        ]
        for cmd, label in allow_cmds:
            rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash(cmd, f"smoke-{abs(hash(cmd)) % 9999}")}, ws)
            assert_true(rc == 0 and is_pass(data), f"PreToolUse rm false positive for {label}: {err} {data}")
        results.append("PreToolUse legit rm passthrough (5 variants)")

        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("sudo rm x", "smoke-sudo")}, ws)
        assert_true(rc == 0 and is_deny(data), f"PreToolUse sudo block failed: {err}")
        results.append("PreToolUse sudo block")

        # --- PreToolUse: secret reads ---
        secret_denies = [
            "cat .env",
            "grep -v '^#' .env.production",
            "head -5 ~/proj/.env.local",
            "cat ~/.ssh/id_ed25519",
            "python3 -c \"print(open('.env').read())\"",
            "node -e \"console.log(require('fs').readFileSync('.env','utf8'))\"",
            # ЧТЕНИЕ .env остаётся блоком даже когда рядом есть redirect в ДРУГОЙ файл (санитайзер записи
            # вырезает только «.env как цель записи», читаемый .env-аргумент уцелевает и ловится).
            "cat /opt/app/.env >> /tmp/out.txt",
            # присваивание пути-ключа в переменную вырезается, но ЛИТЕРАЛЬНОЕ чтение ключа рядом — всё ещё блок.
            "KEY=/x/id_ed25519; cat /home/u/.ssh/id_ed25519",
        ]
        for cmd in secret_denies:
            rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash(cmd, f"smoke-{abs(hash(cmd)) % 9999}")}, ws)
            assert_true(rc == 0 and is_deny(data), f"PreToolUse secret-read deny failed for `{cmd}`: {err} {data}")
        results.append("PreToolUse secret-read blocks (8 variants)")

        secret_allows = [
            "cat .env.example",
            "cp .env.example .env",
            "docker compose --env-file .env up -d",
            "ssh -i ~/.ssh/id_ed25519 root@example-vps.test uptime",
            # -i = identity-аргумент, ключ не читается: grep/cat ВНУТРИ удалённой команды — не чтение ключа (ложняк 02.07)
            "ssh -i /Users/x/.ssh/id_ed25519 root@example-vps.test 'docker exec c nginx -T | grep gzip'",
            "scp -i ~/.ssh/id_ed25519 a.conf root@h:/tmp/x && ssh -i ~/.ssh/id_ed25519 root@h 'cat /tmp/x'",
            "cat ~/.ssh/config",
            "python3 script.py",
            "grep TODO src/env.ts",
            # ЗАПИСЬ секрета в .env (значение идёт в файл, не в контекст) — Павел кладёт ключи в .env на VPS.
            "echo 'X=1' >> /opt/app/.env",
            "F=/opt/app/.env; echo 'X=1' >> \"$F\"",
            "tee -a /opt/app/.env <<< 'X=1'",
            "ssh -i ~/.ssh/id_ed25519 root@example-vps.test 'cat >> /opt/proai-stack/.env'",
            # KEY=/…/id_ed25519 + ssh -i "$KEY" — путь-ключа в переменную (не чтение); reader/eval рядом
            # больше не ложняк (06.07): grep / tail / node -e внутри удалённой команды не блокируются.
            "KEY=/Users/x/.ssh/id_ed25519\nssh -i \"$KEY\" root@h 'docker ps | grep proai'",
            "KEY=/Users/x/.ssh/id_ed25519; ssh -i \"$KEY\" root@h 'tail -5 /var/log/app.log'",
            "KEY=/Users/x/.ssh/id_ed25519\nssh -i \"$KEY\" root@h 'docker exec c node --input-type=module -e \"console.log(1)\"'",
        ]
        for cmd in secret_allows:
            rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash(cmd, f"smoke-{abs(hash(cmd)) % 9999}")}, ws)
            assert_true(rc == 0 and is_pass(data), f"PreToolUse secret-read false positive for `{cmd}`: {err} {data}")
        results.append("PreToolUse secret-read passthrough (16 variants: reads + VPS ssh + .env writes + key-path vars)")

        # --- PreToolUse: .env как окружение и правка на месте (09.09.2026) ---
        # Служебные скрипты сами поднимают окружение сервиса, а конфиг иногда надо править —
        # это не утечка в контекст. Печать секрета из того же кода остаётся под блоком.
        env_runtime_allows = [
            'python3 -c "import os\nfor l in open(\'/opt/app/.env\'):\n    k,v=l.split(\'=\',1); os.environ[k]=v"',
            'python3 -c "from dotenv import load_dotenv; load_dotenv(\'/opt/app/.env\')"',
            'node -e "require(\'dotenv\').config({path:\'/opt/app/.env\'}); console.log(1)"',
            "sed -i '' 's/^MANAGER_CHAT_IDS=.*/MANAGER_CHAT_IDS=1,2/' /opt/app/.env",
            "sed -i.bak 's/A=1/A=2/' /opt/app/.env",
            "ssh -i ~/.ssh/id_ed25519 root@h \"sed -i 's/A=1/A=2/' /opt/app/.env\"",
            'grep -n "git add .env" README.md',
            'rg "dotenv" docs/setup.md',
        ]
        for cmd in env_runtime_allows:
            rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash(cmd, f"smoke-envrt-{abs(hash(cmd)) % 9999}")}, ws)
            assert_true(rc == 0 and is_pass(data), f"PreToolUse env-runtime false positive for `{cmd}`: {err} {data}")
        env_leak_denies = [
            'python3 -c "print(open(\'/opt/app/.env\').read())"',
            'node -e "console.log(process.env.API_KEY)"; cat /opt/app/.env',
            'python3 -c "import os; print(os.environ[\'TOKEN\'])" ; ls /opt/app/.env',
            "sed -n '1,5p' /opt/app/.env",
            'grep "KEY" /opt/app/.env',
        ]
        for cmd in env_leak_denies:
            rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash(cmd, f"smoke-envleak-{abs(hash(cmd)) % 9999}")}, ws)
            assert_true(rc == 0 and is_deny(data), f"PreToolUse env leak must deny `{cmd}`: {err} {data}")
        results.append("PreToolUse env-runtime (allow load-to-environ + sed -i / deny printing secrets)")

        # --- PreToolUse: git add .env ---
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("git add .env", "smoke-ga1")}, ws)
        assert_true(rc == 0 and is_deny(data), f"git add .env deny failed: {err}")
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("git add .env.example src/app.ts", "smoke-ga2")}, ws)
        assert_true(rc == 0 and is_pass(data), f"git add .env.example false positive: {err} {data}")
        results.append("PreToolUse git-add-env (deny .env / allow .env.example)")

        # --- PreToolUse: broad scans ---
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("find / -name x", "smoke-f1")}, ws)
        assert_true(rc == 0 and is_deny(data), f"find / deny failed: {err}")
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("find /tmp -name x", "smoke-f2")}, ws)
        assert_true(rc == 0 and is_pass(data), f"find /tmp false positive: {err} {data}")
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("ssh -i ~/.ssh/id_ed25519 root@example-vps.test 'find / -xdev -name pyvenv.cfg'", "smoke-f3")}, ws)
        assert_true(rc == 0 and is_pass(data), f"remote ssh find / must pass: {err} {data}")
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("echo x; find / -name y", "smoke-f4")}, ws)
        assert_true(rc == 0 and is_deny(data), f"local find / after other cmd must deny: {err}")
        results.append("PreToolUse broad-scan (deny find / / allow find /tmp)")

        # --- PreToolUse: упоминание в теле heredoc — данные, не команда (фикс 25.09.2026) ---
        heredoc_doc = "cat > /tmp/notes.md <<'EOF'\nrun: find / -name x; git add .env\nEOF"
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash(heredoc_doc, "smoke-heredoc-doc")}, ws)
        assert_true(rc == 0 and is_pass(data), f"heredoc-embedded mention must pass: {err} {data}")
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("find / -name y", "smoke-f5")}, ws)
        assert_true(rc == 0 and is_deny(data), f"real find / must still deny after heredoc fix: {err}")
        results.append("PreToolUse heredoc-mention passthrough (broad-scan + git-add rules)")

        # --- PreToolUse: rm/sudo в теле heredoc — данные (фикс 25.09.2026: все deny-правила heredoc-aware) ---
        heredoc_doc2 = "cat > /tmp/notes2.md <<'EOF'\ndocs: rm -rf / , sudo systemctl restart x\nEOF"
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash(heredoc_doc2, "smoke-heredoc-doc2")}, ws)
        assert_true(rc == 0 and is_pass(data), f"rm/sudo inside heredoc body must pass: {err} {data}")
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("rm -rf /etc/nginx", "smoke-rm2")}, ws)
        assert_true(rc == 0 and is_deny(data), f"real rm -rf must still deny after heredoc fix: {err}")
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("sudo apt install x", "smoke-sudo2")}, ws)
        assert_true(rc == 0 and is_deny(data), f"real sudo must still deny after heredoc fix: {err}")
        results.append("PreToolUse heredoc passthrough for rm/sudo (real commands still denied)")

        # --- PreToolUse: JS in TS project ---
        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), "session_id": "smoke-js", "tool_name": "Write", "tool_input": {"file_path": "app.js", "content": "console.log(1)"}}, ws)
        assert_true(rc == 0 and is_deny(data), f"PreToolUse JS-in-TS block failed: {err}")
        for ok_path in ("next.config.js", ".eslintrc.js", "scripts/build.js"):
            rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), "session_id": "smoke-jsok", "tool_name": "Write", "tool_input": {"file_path": ok_path, "content": "x"}}, ws)
            assert_true(rc == 0 and is_pass(data), f"JS-in-TS false positive for {ok_path}: {err} {data}")
        results.append("PreToolUse JS-in-TS (deny app.js / allow configs+scripts)")

        rc, data, _, err = run("pre_tool_use.py", {"cwd": str(ws), **bash("ls -la", "smoke-ok")}, ws)
        assert_true(rc == 0 and is_pass(data), f"PreToolUse safe passthrough failed: {err}")
        results.append("PreToolUse safe passthrough")

        # --- PostToolUse ---
        rc, data, _, err = run("post_tool_use.py", {"cwd": str(ws), "session_id": "smoke-post", "tool_name": "Bash", "tool_response": "ok"}, ws)
        assert_true(rc == 0 and data.get("continue") is True, f"PostToolUse log failed: {err}")
        rc, data, _, err = run("post_tool_use.py", {"cwd": str(ws), "session_id": "smoke-post", "tool_name": "Bash", "tool_response": "ok2"}, ws)
        assert_true(rc == 0 and data.get("continue") is True, f"PostToolUse cached-identity call failed: {err}")
        results.append("PostToolUse telemetry (incl. cached project identity)")

        large = "x" * 85000
        rc, data, _, err = run("post_tool_use.py", {"cwd": str(ws), "session_id": "smoke-large", "tool_name": "WebFetch", "tool_response": large}, ws)
        assert_true(rc == 0 and "large output" in injected(data), f"PostToolUse large output warning failed: {err}")
        results.append("PostToolUse large output artifact")

        # --- PreCompact -> SessionStart restore ---
        rc, data, _, err = run("pre_compact.py", {"cwd": str(ws), "session_id": "smoke-compact", "trigger": "manual"}, ws)
        assert_true(rc == 0 and "PRE-COMPACT" in injected(data), f"PreCompact checkpoint failed: {err}")
        assert_true(len(injected(data)) < 1200, f"PreCompact message not short: {len(injected(data))} chars")
        results.append("PreCompact checkpoint + marker (short systemMessage)")

        rc, data, _, err = run("session_start.py", {"cwd": str(ws), "source": "compact", "session_id": "smoke-compact"}, ws)
        assert_true(rc == 0 and "RESTORE AFTER COMPACTION" in injected(data), f"SessionStart compact restore failed: {err}")
        results.append("SessionStart compact restore (marker)")

        # --- UserPromptSubmit intents ---
        rc, data, _, err = run("user_prompt_submit.py", {"cwd": str(ws), "session_id": "smoke-up", "prompt": "сохрани это в базу знаний"}, ws)
        assert_true(rc == 0 and "obsidian-second-brain-save" in injected(data), f"UserPromptSubmit save routing failed: {err}")
        rc, data, _, err = run("user_prompt_submit.py", {"cwd": str(ws), "session_id": "smoke-up1", "prompt": "вспомни, что мы решали про LiteLLM"}, ws)
        assert_true(rc == 0 and "obsidian-second-brain-query" in injected(data), f"UserPromptSubmit query routing failed: {err}")
        rc, data, _, err = run("user_prompt_submit.py", {"cwd": str(ws), "session_id": "smoke-up2", "prompt": "импортируй эти статьи в базу знаний"}, ws)
        assert_true(rc == 0 and "obsidian-second-brain-ingest" in injected(data), f"UserPromptSubmit ingest routing failed: {err}")
        results.append("UserPromptSubmit second-brain routing (save/query/ingest)")

        false_positive_prompts = [
            "почини ошибку импорта модуля в python",
            "оптимизируй запрос по базе данных пользователей",
            "настрой hashicorp vault для секретов",
            "обычный вопрос про код",
        ]
        for prompt in false_positive_prompts:
            rc, data, _, err = run("user_prompt_submit.py", {"cwd": str(ws), "session_id": "smoke-up3", "prompt": prompt}, ws)
            assert_true(rc == 0 and is_pass(data), f"UserPromptSubmit false positive for `{prompt}`: {err} {data}")
        results.append("UserPromptSubmit non-intent passthrough (4 variants)")

        # --- Stop notify (kill-switch: secrets-файл может держать РЕАЛЬНЫЕ креды,
        #     без выключателя smoke слал бы живые сообщения в TG) ---
        env = os.environ.copy()
        env.pop("TELEGRAM_BOT_TOKEN", None)
        env.pop("TELEGRAM_CHAT_ID", None)
        env["ZCODE_TG_NOTIFY_DISABLE"] = "1"
        rc, data, _, err = run("stop_notify.py", {"cwd": str(ws), "session_id": "smoke-stop", "last_assistant_message": "done"}, ws, env=env)
        assert_true(rc == 0 and data.get("continue") is True, f"Stop notify failed: {err}")
        results.append("Stop notify (kill-switch, no live send)")

        # --- tg_format: sanitize / balance / split ---
        import sys
        sys.path.insert(0, str(HOOK_DIR))
        import tg_format
        dirty = '<script>x</script><div><b>ok</b> <a href="javascript:e()">bad</a> <a href="https://a.io">a</a></div>'
        clean = tg_format.balance(tg_format.sanitize(dirty))
        assert_true("<script" not in clean and "javascript:" not in clean and '<a href="https://a.io">' in clean,
                    f"tg_format sanitize failed: {clean}")
        assert_true(tg_format.is_balanced(clean), f"tg_format balance failed: {clean}")
        long_html = "<b>Заголовок</b>\n\n" + ("<i>строка проверки разбивки с <b>вложенным</b> тегом</i> и хвост абзаца\n\n" * 140)
        parts = tg_format.split_telegram_html(long_html, max_len=3900, max_chunks=10)
        assert_true(len(parts) >= 2, f"tg_format split produced {len(parts)} chunk(s)")
        for p in parts:
            assert_true(len(p) <= 4096, f"tg_format chunk too long: {len(p)}")
            assert_true(tg_format.is_balanced(p), f"tg_format unbalanced chunk: {p[:120]}")
        results.append("tg_format sanitize/split/balance")

        # --- tg_format: детаблер (таблицы Telegram не умеет) ---
        table2 = "| Метрика | Значение |\n|---|---|\n| Ниже рынка | 38 из 69 |\n| Недополучаем | ~260 000 ₽ |"
        d2 = tg_format.detable(table2)
        assert_true("|---|" not in d2 and "| Метрика |" not in d2, f"detable left raw table: {d2}")
        assert_true("•" in d2 and "38 из 69" in d2, f"detable lost data: {d2}")
        table3 = "| Округ | Спрос | Остаток |\n|---|---|---|\n| ЦФО | 100 | 20 |\n| СЗФО | 50 | 5 |"
        d3 = tg_format.detable(table3)
        assert_true("|---|" not in d3 and "•" in d3 and "ЦФО" in d3 and "100" in d3, f"detable 3-col failed: {d3}")
        # полный fallback-путь на таблице: НИ ОДНОГО сырого разделителя/трубы-строки
        fb = tg_format.balance(tg_format.sanitize(tg_format.md_to_html_basic(table2)))
        assert_true("|---|" not in fb and "<b>" in fb and tg_format.is_balanced(fb),
                    f"fallback table render failed: {fb}")
        for line in fb.split("\n"):
            assert_true(not tg_format._TABLE_SEP_RE.match(line), f"separator row survived: {line}")
        results.append("tg_format detable (2-col + 3-col + fallback, no raw pipes)")

        # --- tg_format: локальная Markdown→HTML в фолбэке ---
        md = "## Итог\n**жирный** и *курсив* и ~~зачёркнутый~~\n`код` и [ссылка](https://a.io)\n* пункт"
        h = tg_format.md_to_html_basic(md)
        assert_true("<b>Итог</b>" in h and "<b>жирный</b>" in h and "<i>курсив</i>" in h
                    and "<s>зачёркнутый</s>" in h and "<code>код</code>" in h
                    and '<a href="https://a.io">ссылка</a>' in h and "•" in h
                    and "**" not in h and "##" not in h, f"md_to_html_basic failed: {h}")
        results.append("tg_format md_to_html_basic (no raw markdown)")

        # --- cleanup_state must not raise ---
        import sys
        sys.path.insert(0, str(HOOK_DIR))
        from common import cleanup_state
        cleanup_state()
        results.append("cleanup_state sanity")

        print("# ZCode hooks smoke test")
        for item in results:
            print(f"PASS: {item}")
        print(f"TOTAL: {len(results)}/{len(results)} PASS")

        # tidy up smoke-* state so the guard dir stays clean
        from common import CONTEXT_GUARD_DIR, TASK_MARKER_DIR
        for d in CONTEXT_GUARD_DIR.glob("smoke-*"):
            shutil.rmtree(d, ignore_errors=True)
        for m in TASK_MARKER_DIR.glob("smoke-*.json"):
            m.unlink(missing_ok=True)
        return 0
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
