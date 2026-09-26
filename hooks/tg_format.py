#!/usr/bin/env python3
"""LLM-форматтер Telegram-уведомлений: текст → Telegram HTML + разбивка ≤4096.

Порт n8n-пайплайна Павла (нода «LLM HTML» + нода «CleanText»):
модель приводит произвольный текст/Markdown к Telegram-HTML, локальный код
санитизирует теги, чинит баланс и режет на чанки с переносом открытых тегов.
Любая ошибка сети/провайдера — исключение наверх, вызывающий код обязан
падать обратно на plain-текст (уведомление не должно теряться).
"""
from __future__ import annotations

import json
import os
import re
import ssl
import urllib.error
import urllib.request

ALLOWED_TAGS = ("b", "strong", "i", "em", "u", "s", "code", "pre", "a", "tg-spoiler", "blockquote")
TAG_RE = re.compile(r"<(/?)([a-zA-Z0-9-]+)((?:\s[^>]*)?)>")

SYSTEM_PROMPT = """You are an HTML formatting device for Telegram messages.
Convert the input text into Telegram-compatible HTML. Output ONLY the final HTML text — no explanations, no Markdown fences.

Allowed tags (no others): <b> <strong> <i> <em> <u> <s> <code> <pre> <tg-spoiler> <a href="..."> <blockquote>

Rules:
- Preserve the original words and their order. You MAY change layout ONLY where a construct is unsupported by Telegram (tables — see below); otherwise keep spacing and paragraph structure.
- **text** -> <b>text</b>; *text* / _text_ -> <i>text</i>; ~~text~~ -> <s>text</s>; `code` -> <code>code</code>; fenced code blocks -> <pre><code>...</code></pre>.
- Markdown headers (# / ## / ### at line start): remove the symbols, wrap the whole line in <b>...</b>.
- Keep list markers (•, -, *) as-is; add at least one emphasis tag elsewhere in the line.
- @username -> <a href="https://t.me/username">@username</a> (never wrap in <code>).
- Bare URLs -> <a href="URL">domain</a> without altering the URL.
- Markdown links [text](url) -> <a href="url">text</a>.
- Explicit quotations -> <blockquote>...</blockquote>; hidden/sensitive fragments -> <tg-spoiler>...</tg-spoiler>.
- Content inside <code>/<pre> must stay byte-identical; never nest other tags there.
- Outside of tags escape: & -> &amp;   < -> &lt;   > -> &gt;
- Literal \\n sequences become real line breaks; preserve empty lines.
- Every non-empty line should carry at least one tag; if unsure, use <i>.

CRITICAL — NO TABLES. Telegram HTML has no table support. NEVER output pipe/dash tables (no `|`, no `---` separator rows). Convert any Markdown/ASCII table into a compact vertical list:
- Two columns (key → value): one line per row as `• <b>Key</b>: value`. Drop the header row.
- Three+ columns: one block per row — first cell bold as a mini-title, remaining cells as `<i>Header:</i> value` separated by " · " (middle dot), each row separated by a blank line.
- Never leave raw `|` characters or `|---|` separator lines in the output.

Example 1 (table -> vertical list):
INPUT:
| Метрика | Значение |
|---|---|
| Ниже рынка | 38 из 69 |
| Недополучаем | ~260 000 ₽ |
OUTPUT:
• <b>Метрика</b>: —
• <b>Ниже рынка</b>: 38 из 69
• <b>Недополучаем</b>: ~260 000 ₽

Example 2 (inline formatting):
INPUT:
## Итог
Встреча с @Founderbrain в 10:00. Код: print('test')
OUTPUT:
<b>Итог</b>
Встреча с <a href="https://t.me/Founderbrain">@Founderbrain</a> в <b>10:00</b>. Код: <code>print('test')</code>"""


def _ssl_context() -> ssl.SSLContext | None:
    """Системный python3 на macOS без CA-бандла — берём /etc/ssl/cert.pem."""
    for cafile in ("/etc/ssl/cert.pem", "/private/etc/ssl/cert.pem"):
        if os.path.exists(cafile):
            return ssl.create_default_context(cafile=cafile)
    try:
        import certifi  # noqa: F401
        return ssl.create_default_context(cafile=certifi.where())
    except Exception:
        return None


def llm_format(text: str, base_url: str, api_key: str, model: str = "gpt-5.4-mini",
               timeout: int = 25, reasoning_effort: str = "low") -> str:
    """OpenAI-совместимый /chat/completions. Возвращает HTML-текст модели."""
    url = base_url.rstrip("/")
    if not url.endswith("/chat/completions"):
        url += "/chat/completions"
    body: dict = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
    }
    if reasoning_effort:
        body["reasoning_effort"] = reasoning_effort
    ctx = _ssl_context()

    def _call(payload: dict) -> dict:
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
        )
        return json.loads(urllib.request.urlopen(req, timeout=timeout, context=ctx).read().decode("utf-8"))

    try:
        data = _call(body)
    except urllib.error.HTTPError as e:
        # провайдер может не знать reasoning_effort — пробуем без него
        if body.pop("reasoning_effort", None) is not None and 400 <= e.code < 500:
            data = _call(body)
        else:
            raise
    out = ((data.get("choices") or [{}])[0].get("message") or {}).get("content") or ""
    out = out.strip()
    if out.startswith("```"):
        out = re.sub(r"^```[a-zA-Z]*\n?", "", out)
        out = re.sub(r"\n?```\s*$", "", out).strip()
    return out


_TABLE_SEP_RE = re.compile(r"^\s*\|?\s*:?-{2,}:?\s*(\|\s*:?-{2,}:?\s*)*\|?\s*$")


def detable(text: str) -> str:
    """Markdown/ASCII-таблицы → вертикальные буллеты. Страховка на случай,
    если LLM проигнорил правило или сработал plain-фолбэк: сырые `|`/`---`
    в Telegram выглядят мусором. Работает построчно, не-таблицы не трогает."""
    lines = text.split("\n")
    out: list[str] = []
    i = 0
    n = len(lines)

    def cells(line: str) -> list[str]:
        s = line.strip()
        if s.startswith("|"):
            s = s[1:]
        if s.endswith("|"):
            s = s[:-1]
        return [c.strip() for c in s.split("|")]

    while i < n:
        line = lines[i]
        # табличная строка: >=2 '|' и это не просто текст с одной трубой
        is_row = line.count("|") >= 2
        nxt = lines[i + 1] if i + 1 < n else ""
        if is_row and (_TABLE_SEP_RE.match(nxt) or _TABLE_SEP_RE.match(line)):
            # собираем блок таблицы
            block = []
            while i < n and lines[i].count("|") >= 2:
                block.append(lines[i])
                i += 1
            rows = [cells(b) for b in block if not _TABLE_SEP_RE.match(b)]
            if not rows:
                continue
            header = rows[0]
            body = rows[1:] if len(rows) > 1 else rows
            for r in body:
                r = [c for c in r if c != ""]
                if not r:
                    continue
                if len(r) == 1:
                    out.append(f"• {r[0]}")
                elif len(r) == 2:
                    out.append(f"• **{r[0]}**: {r[1]}")
                else:
                    tail = " · ".join(
                        f"{header[j]}: {r[j]}" if j < len(header) and header[j] else r[j]
                        for j in range(1, len(r))
                    )
                    out.append(f"• **{r[0]}** — {tail}")
            out.append("")
        else:
            out.append(line)
            i += 1
    return "\n".join(out)


def strip_table_seps(html_text: str) -> str:
    """Финальная зачистка: убрать оставшиеся separator-строки таблиц (|---|)."""
    return "\n".join(l for l in html_text.split("\n") if not _TABLE_SEP_RE.match(l))


def sanitize(html_text: str) -> str:
    """Только разрешённые Telegram-теги; у <a> — только https?://-href."""
    html_text = strip_table_seps(html_text)
    # <li> в буллеты ДО общего фильтра тегов (иначе маркеры теряются)
    html_text = re.sub(r"<li[^>]*>\s*", "• ", html_text, flags=re.I)
    html_text = re.sub(r"</li\s*>", "\n", html_text, flags=re.I)

    def repl(m: re.Match) -> str:
        slash, tag, attrs = m.group(1), m.group(2).lower(), m.group(3) or ""
        if tag not in ALLOWED_TAGS:
            return ""
        if slash:
            return f"</{tag}>"
        if tag == "a":
            hm = re.search(r"href\s*=\s*\"([^\"]+)\"", attrs) or re.search(r"href\s*=\s*'([^']+)'", attrs)
            href = (hm.group(1).strip() if hm else "")
            if not re.match(r"^https?://", href, re.I):
                return ""  # плохой href: opener выкидываем, остаток добьёт balance()
            return f'<a href="{href}">'
        return f"<{tag}>"

    out = TAG_RE.sub(repl, html_text)
    out = re.sub(r"[ \t]+\n", "\n", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def balance(html_text: str) -> str:
    """Гарантирует валидную вложенность: лишние закрывашки — вон, незакрытое — закрыть."""
    out: list[str] = []
    stack: list[tuple[str, str]] = []  # (tag, полный открывающий тег)
    pos = 0
    for m in TAG_RE.finditer(html_text):
        out.append(html_text[pos:m.start()])
        pos = m.end()
        slash, tag = m.group(1), m.group(2).lower()
        if tag not in ALLOWED_TAGS:
            continue
        if not slash:
            out.append(m.group(0))
            stack.append((tag, m.group(0)))
        else:
            if any(t == tag for t, _ in stack):
                while stack:
                    t, _ = stack.pop()
                    out.append(f"</{t}>")
                    if t == tag:
                        break
            # stray closer без открывашки — молча выкидываем
    out.append(html_text[pos:])
    while stack:
        t, _ = stack.pop()
        out.append(f"</{t}>")
    return "".join(out)


def md_to_html_basic(text: str) -> str:
    """Локальная Markdown→Telegram-HTML конвертация без LLM (порт n8n «CleanText»).
    Используется в фолбэке: даже без LLM уведомление получит теги, а не сырые
    звёздочки. Не идеальна (может тронуть ** внутри code), но balance() чинит
    вложенность, а это лишь аварийный путь."""
    text = detable(text)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    text = re.sub(r"```[a-zA-Z]*\n?([\s\S]*?)```",
                  lambda m: "<pre><code>" + m.group(1).rstrip() + "</code></pre>", text)
    text = re.sub(r"`([^`\n]+)`", r"<code>\1</code>", text)
    text = re.sub(r"(?m)^\s{0,3}#{1,6}\s+(.+?)\s*$", r"<b>\1</b>", text)
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', text)
    text = re.sub(r"\*\*([^\n*]+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!_)__([^\n_]+?)__(?!_)", r"<b>\1</b>", text)
    text = re.sub(r"~~([^\n~]+?)~~", r"<s>\1</s>", text)
    text = re.sub(r"(?<![*\w])\*([^\n*]+?)\*(?![*\w])", r"<i>\1</i>", text)
    text = re.sub(r"(?m)^(\s*)[*\-]\s+", r"\1• ", text)
    return text


def strip_tags(html_text: str) -> str:
    return re.sub(r"<[^>]+>", "", html_text)


def is_balanced(html_text: str) -> bool:
    stack: list[str] = []
    for m in TAG_RE.finditer(html_text):
        slash, tag = m.group(1), m.group(2).lower()
        if tag not in ALLOWED_TAGS:
            return False
        if not slash:
            stack.append(tag)
        else:
            if not stack or stack.pop() != tag:
                return False
    return not stack


def split_telegram_html(html_text: str, max_len: int = 3900, max_chunks: int = 3) -> list[str]:
    """Режет HTML на чанки ≤max_len, перенося открытые теги между чанками.

    Лимит Telegram (4096) считается по тексту ПОСЛЕ разбора тегов, так что
    порог по «сырой» длине с тегами — консервативно-безопасный.
    """
    parts = [p for p in re.split(r"(\n\n|</blockquote>|</pre>|</code>)", html_text) if p]
    chunks: list[str] = []
    stack: list[tuple[str, str]] = []
    cur = ""
    cur_has_content = False

    def closing() -> str:
        return "".join(f"</{t}>" for t, _ in reversed(stack))

    def flush() -> None:
        nonlocal cur, cur_has_content
        if cur_has_content and strip_tags(cur).strip():
            chunks.append((cur + closing()).strip())
        cur = "".join(o for _, o in stack)  # переоткрываем теги в новом чанке
        cur_has_content = False

    def feed(segment: str) -> None:
        for m in TAG_RE.finditer(segment):
            slash, tag = m.group(1), m.group(2).lower()
            if tag not in ALLOWED_TAGS:
                continue
            if not slash:
                stack.append((tag, m.group(0)))
            else:
                for i in range(len(stack) - 1, -1, -1):
                    if stack[i][0] == tag:
                        del stack[i]
                        break

    def safe_cut(segment: str, room: int) -> str:
        take = segment[:max(room, 100)]
        lt = take.rfind("<")
        if lt != -1 and ">" not in take[lt:]:
            take = take[:lt]
        amp = take.rfind("&")
        if amp != -1 and ";" not in take[amp:] and len(take) - amp < 10:
            take = take[:amp]
        return take if take else segment[:100]

    for part in parts:
        if len(cur) + len(part) + len(closing()) + 32 > max_len and cur_has_content:
            flush()
        if len(cur) + len(part) + len(closing()) + 32 > max_len:
            seg = part
            while seg:
                room = max_len - len(cur) - len(closing()) - 32
                take = safe_cut(seg, room)
                cur += take
                cur_has_content = cur_has_content or bool(strip_tags(take).strip())
                feed(take)
                seg = seg[len(take):]
                if seg:
                    flush()
        else:
            cur += part
            cur_has_content = cur_has_content or bool(strip_tags(part).strip())
            feed(part)
    flush()

    if len(chunks) > max_chunks:
        chunks = chunks[:max_chunks]
        chunks[-1] = chunks[-1].rstrip() + "\n<i>… (обрезано)</i>"
    # страховка: жёсткий предел Telegram
    return [c if len(c) <= 4096 else c[:4090] + " …" for c in chunks] or [""]
