#!/usr/bin/env python3
"""Зеркало базы бота в Google Sheets — витрина для менеджеров, только чтение.

«Сводка» — KPI-плитки и таблица по менеджерам; «Очередь» — кому нужен ответ сейчас;
«Клиенты» — все карточки. Бот пушит данные при каждом изменении базы (≈10 с), таймер раз в 15 минут — страховка. Оформление идемпотентно:
зебра, условные правила и объединения снимаются перед новыми.
"""
import os, sys
from datetime import datetime, timezone
from pathlib import Path
sys.path.insert(0, "/opt/wb-refund-bot")
from wb_refund_bot.db import Store
from wb_refund_bot.crm import CRM_STATUS_LABELS
from google.oauth2 import service_account
from googleapiclient.discovery import build

_ENV = "/opt/wb-refund-bot/secrets/google.env"
if not os.getenv("MPZORRO_SHEET_ID") and os.path.exists(_ENV):
    for _l in open(_ENV, encoding="utf-8"):
        _l = _l.strip()
        if _l and not _l.startswith("#") and "=" in _l:
            _k, _v = _l.split("=", 1); os.environ.setdefault(_k.strip(), _v.strip().strip('"'))
SHEET_ID = os.getenv("MPZORRO_SHEET_ID", "1nNBNqkO9R6p_XCmqHpe9DgyNvbioKC-TRA6NPTPWsvI")
KEY = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "/opt/wb-refund-bot/secrets/google-sa.json")
DB = Path("/opt/wb-refund-bot/data/wb_refund_bot.sqlite3")
STAFF_NOISE = ("MPZORRO ", " деньги от WB", " WB Менеджер")

def team_usernames():
    """Сотрудники MPZORRO по списку Зорро (/opt/mpzorro-zorro/zorro/team.py) — их карточки в клиентские
    очереди не попадают, чтобы цифры таблицы и Зорро сходились. Если Зорро нет рядом — запасной список."""
    try:
        sys.path.insert(0, "/opt/mpzorro-zorro")
        from zorro.team import TEAM  # type: ignore
        names = {u for u, _n, _r in TEAM}
    except Exception:
        names = {"PavelDumbrao", "Vadimir_Isaev", "danilakovalev", "y_shira", "Savva32", "an_zhukoBa", "ddlgnd",
                 "MPZORRO_Manager_04", "semkhasanov", "strokover", "darinakrasnenko", "ZakirovaIl", "gskslS7"}
    names |= {"MPZORRO_Manager_01", "MPZORRO_Manager_02", "MPZORRO_Manager_03"}
    return sorted(n.lower() for n in names)
FONT = "Roboto"

# ---------- палитра ----------
def rgb(h):
    h = h.lstrip("#"); return {"red": int(h[0:2], 16)/255, "green": int(h[2:4], 16)/255, "blue": int(h[4:6], 16)/255}
INK, MUTED, LINE = rgb("111827"), rgb("6B7280"), rgb("E5E7EB")
HEAD_BG, HEAD_TXT = rgb("111827"), rgb("FFFFFF")
TILE_BG, ZEBRA = rgb("F3F4F6"), rgb("FAFAFA")
RED_BG, RED_TXT = rgb("FEE2E2"), rgb("B91C1C")
ORANGE_BG, ORANGE_TXT = rgb("FFEDD5"), rgb("C2410C")
GREEN_BG, GREEN_TXT = rgb("DCFCE7"), rgb("15803D")
WHITE = rgb("FFFFFF")

# ---------- колонки таблиц ----------
HEAD = ["№", "Имя", "Ник", "Диалог", "Этап", "Сигнал ИИ", "Менеджер", "Взял в работу", "Заявка", "Источник",
        "Проверка", "Предв. возврат, ₽", "Ждёт ответа", "Последнее сообщение", "Комментарий ИИ", "Кто писал",
        "Телефон", "Почта", "Кабинет",
        "мин", "этап№", "новый30", "ник", "продающий", "лежит_мин", "tg_id", "шевелится", "актив_мин", "сигнал№",
        "этап_сейчас№", "дней_на_этапе"]
WIDTHS = [52, 150, 150, 110, 165, 190, 110, 118, 92, 112, 105, 130, 110, 380, 300, 90, 130, 200, 170,
          40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40, 40]
TECH_COLS = ["мин", "этап№", "новый30", "ник", "продающий", "лежит_мин", "tg_id", "шевелится", "актив_мин", "сигнал№",
             "этап_сейчас№", "дней_на_этапе"]
STAGE_EVENTS = ("crm_status_changed", "manager_stage_changed", "manager_claimed", "manager_requested", "quiz_finished", "handover_done")
# Что ИИ понял о клиенте (users.ai_signal) — те же подписи, что в боте (messages.AI_SIGNAL_LABELS).
AI_SIGNAL_LABELS = {"ready": "🔥 готов начинать", "payment": "💳 готов оплатить", "manager": "🙋 просит менеджера",
                    "talking": "🤝 общается с менеджером", "complaint": "⚠️ жалоба", "later": "⏳ вернуться позже"}
AI_SIGNAL_RANK = {"complaint": 3, "ready": 2, "payment": 2, "manager": 2, "talking": 1, "later": 1}
AI_SIGNAL_FRESH_HOURS = 72  # старше — сигнал уже отработан или протух, наверх не поднимаем
def L(name: str) -> str:
    """Буква колонки листа «Клиенты» по имени — чтобы формулы не ломались при вставке колонок."""
    i = HEAD.index(name); s = ""
    while True:
        s = chr(ord("A") + i % 26) + s; i = i // 26 - 1
        if i < 0: return s
STAMP_CELL = "Z1"   # метка времени пуша: строка 1 — заголовок, правее A1 она свободна; сетка листа — 26 колонок
BOT_USERNAME = os.getenv("MPZORRO_BOT_USERNAME", "wb_refund_pavel_bot")
STAFF_DISPLAY = {6487233131: "Анастасия", 8804842855: "Самат"}  # кто реально сидит за рабочим аккаунтом
COL = {n: i for i, n in enumerate(HEAD)}
QUAL = {"qualified": "прошёл", "not_qualified": "не прошёл", "not_ready": "не готов",
        "bankruptcy_route": "юр. проверка", "legal_review": "юр. проверка", "": ""}
SOURCE = {"bot": "бот", "site": "сайт", "manual": "вручную", "excel": "Excel", "": ""}

def short(name):
    s = str(name or "")
    for n in STAFF_NOISE: s = s.replace(n, "")
    return s.strip() or "—"

def minutes_since(value):
    try:
        m = datetime.fromisoformat(str(value or "")[:19].replace(" ", "T")).replace(tzinfo=timezone.utc)
        return max(0, int((datetime.now(timezone.utc) - m).total_seconds() // 60))
    except Exception:
        return None

def human_wait(mins):
    if mins is None: return ""
    if mins >= 1440: return f"{mins // 1440} д {(mins % 1440) // 60} ч"
    return f"{mins // 60} ч {mins % 60} мин" if mins >= 60 else f"{mins} мин"

def fmt_date(created):
    s = str(created or "")
    return f"{s[8:10]}.{s[5:7]}.{s[2:4]}" if len(s) >= 10 else s

def link(nick, sep):
    return f'=HYPERLINK("https://t.me/{nick}"{sep}"@{nick}")' if nick else ""

# ---------- воронка ----------
FUNNEL_STAGES = [
    ("Открыли бота",               "bot"),                  # 0
    ("Прошли проверку",            "quiz_finished"),        # 1
    ("Запросили менеджера",        "manager_requested"),    # 2
    ("Менеджер взял в работу",     "manager_claimed_at"),   # 3
    ("Менеджер написал",           "manager_contacted_at"), # 4
    ("Клиент ответил",             "client_replied_at"),    # 5
    ("Договор отправлен",          "contract_sent_at"),     # 6
    ("Договор подписан",           "contract_signed_at"),   # 7
    ("Check-in выставлен",         "entry_fee"),            # 8  — сумма входного платежа назначена
    ("Check-in оплачен",           "payment_received"),     # 9  — входная оплата подтверждена
    ("Аудит / расчёт",             "calculation_ready"),    # 10
    ("Претензия подана",           "claim_submitted"),      # 11
    ("Ждём ответ WB",              "waiting_wb"),           # 12
    ("Ответ WB получен",           "wb_official_response"), # 13
    ("Соглашение о выплате",       "agreement_signature"),  # 14
    ("Деньги получены",            "payout_date"),          # 15
]
STATUS_STAGE = {  # текущий статус тоже свидетельство: до какого этапа человек точно дошёл
    "quiz_started": 0, "new_lead": 0, "qualified": 1, "nurture": 1, "manager_requested": 2, "manager_claimed": 3,
    "manager_contacted": 4, "client_replied": 5, "contract_sent": 6, "iu_template_sold": 6, "contract_signed": 7,
    "payment_received": 9, "audit_started": 10, "in_work": 10, "calculation_ready": 10, "claim_submitted": 11,
    "waiting_wb": 12, "wb_reply_overdue": 12, "wb_official_response": 13, "agreement_signature": 14,
    "paid": 15, "completed": 15,   # деньги получены (акт выполненных услуг)
}


def stage_index(r) -> int:
    """До какого этапа воронки клиент точно дошёл (0..9), по отметкам в карточке и статусу."""
    reached = 0
    if r["ev_fin"]: reached = max(reached, 1)
    if r["ev_req"]: reached = max(reached, 2)
    for idx, col in ((3, "manager_claimed_at"), (4, "manager_contacted_at"), (5, "client_replied_at"),
                     (6, "contract_sent_at"), (7, "contract_signed_at"), (15, "payout_date")):
        if str(r[col] or "").strip(): reached = max(reached, idx)
    if int(r["entry_fee"] or 0) > 0: reached = max(reached, 8)
    if str(r["claim_submitted"] or "").strip().lower() not in ("", "нет", "no", "0", "false", "none"): reached = max(reached, 11)  # в базе там дата подачи
    if str(r["wb_response_date"] or "").strip().lower() not in ("", "нет", "none"): reached = max(reached, 13)
    if str(r["agreement_sent"] or "").strip(): reached = max(reached, 14)
    return max(reached, STATUS_STAGE.get(str(r["crm_status"] or ""), 0))

def is_recent(created) -> bool:
    try:
        return datetime.fromisoformat(str(created)[:19]).replace(tzinfo=timezone.utc).timestamp() >= datetime.now(timezone.utc).timestamp() - 30 * 86400
    except Exception:
        return False

# Что делает сам клиент — тот же белый список, что у Зорро (zorro/crm.py CLIENT_EVENTS),
# чтобы «активны без ответа» в таблице сходилось с его отчётом в чате.
CLIENT_EVENTS = (
    "message", "callback", "faq_opened", "faq_topic_opened", "email_requested",
    "email_collected", "quiz_started", "quiz_step_completed", "quiz_finished",
    "contract_sample_opened", "iu_cta_clicked", "electrostal_cta_clicked",
    "warmup_intro_cta_clicked", "warmup_process_cta_clicked", "crm_advice_opened",
    "referral_materials_opened", "manager_link_attributed",
)
CLOSED_STATUSES = ("lost", "case_closed", "not_relevant", "completed", "paid")

def is_stirring(r):
    """Клиент сам что-то делал в боте после последнего касания менеджера, и ему не ответили.
    Один в один с hot_ignored у Зорро: касание = manager_contacted_at, иначе manager_assigned_at."""
    if not r["assigned_admin_id"] or str(r["crm_status"] or "") in CLOSED_STATUSES:
        return False
    active = str(r["client_active_at"] or "")
    if not active:
        return False
    touched = str(r["manager_contacted_at"] or r["manager_assigned_at"] or "")
    return not (touched and touched >= active)

def load_rows():
    staff = team_usernames()
    with Store(DB).managed_connection() as c:
        return c.execute("""
            select u.client_no, u.first_name, u.username, u.phone, u.email, u.cabinet_name,
                   u.crm_status, u.source, u.qualification, u.estimated_refund,
                   substr(u.created_at,1,16) created, u.assigned_admin_id, u.manager_claimed_at,
                   u.manager_assigned_at, m.first_name manager_name, m.role manager_role,
                   u.manager_contacted_at, u.client_replied_at, u.contract_sent_at, u.contract_signed_at, u.claim_submitted, u.payout_date,
                   u.entry_fee, u.wb_response_date, u.agreement_sent, u.telegram_id,
                   u.ai_signal, u.ai_signal_note, u.ai_signal_at,
                   (select max(e.created_at) from events e where e.telegram_id=u.telegram_id
                      and e.event_type in (""" + ",".join(f"'{e}'" for e in STAGE_EVENTS) + """)) stage_at,
                   exists(select 1 from events e where e.telegram_id=u.telegram_id and e.event_type='quiz_finished') ev_fin,
                   exists(select 1 from events e where e.telegram_id=u.telegram_id and e.event_type='manager_requested') ev_req,
                   (select text from dialog_messages d where d.client_id=u.telegram_id order by id desc limit 1) last_text,
                   (select direction from dialog_messages d where d.client_id=u.telegram_id order by id desc limit 1) last_dir,
                   (select created_at from dialog_messages d where d.client_id=u.telegram_id order by id desc limit 1) last_at,
                   (select max(e.created_at) from events e where e.telegram_id=u.telegram_id
                      and e.event_type in (""" + ",".join(f"'{e}'" for e in CLIENT_EVENTS) + """)) client_active_at
              from users u left join users m on m.telegram_id = u.assigned_admin_id
             where coalesce(u.role,'client') = 'client'
               and coalesce(u.source,'') not in ('test','merged_duplicate')
               and coalesce(u.crm_status,'') <> 'merged_duplicate'
               and u.telegram_id not in (select telegram_id from events where event_type='staff_offboarded')
               and lower(coalesce(u.username,'')) not in (%s)
             order by u.client_no""" % ",".join("?" * len(staff)), staff).fetchall()

def build_tables(rows, sep):
    clients, queue, summary = [], [], {}
    src_label = lambda s: SOURCE.get(str(s or "").lower(), str(s or ""))
    for r in rows:
        waited = minutes_since(r["last_at"]) if r["last_dir"] == "in" else None
        stirring = is_stirring(r)
        active_min = minutes_since(r["client_active_at"]) if stirring else None
        not_claimed = bool(str(r["crm_status"]) == "manager_requested" and r["assigned_admin_id"] and not r["manager_claimed_at"])
        stale_min = minutes_since(r["manager_assigned_at"]) if not_claimed else None
        mgr = STAFF_DISPLAY.get(int(r["assigned_admin_id"] or 0), short(r["manager_name"]))
        sig = str(r["ai_signal"] or "")
        sig_min = minutes_since(r["ai_signal_at"]) if sig else None
        sig_rank = AI_SIGNAL_RANK.get(sig, 0) if (sig_min is not None and sig_min <= AI_SIGNAL_FRESH_HOURS * 60) else 0
        tg = int(r["telegram_id"] or 0)
        dlg = f'=HYPERLINK("https://t.me/{BOT_USERNAME}?start=dlg_{tg}"{sep}"💬 в боте")' if tg > 0 else ""
        line = [
            r["client_no"] or "", str(r["first_name"] or "")[:40], link(r["username"], sep), dlg,
            CRM_STATUS_LABELS.get(str(r["crm_status"] or ""), str(r["crm_status"] or "")),
            AI_SIGNAL_LABELS.get(sig, sig) if sig else "",
            mgr, "нет" if not_claimed else ("да" if r["manager_claimed_at"] else "—"),
            fmt_date(r["created"]), src_label(r["source"]),
            QUAL.get(str(r["qualification"] or ""), str(r["qualification"] or "")),
            int(r["estimated_refund"] or 0) or "",
            human_wait(waited) if waited is not None else (f"⚡ {human_wait(active_min)}" if stirring else ""),
            str(r["last_text"] or "").replace("\n", " ")[:160],
            str(r["ai_signal_note"] or "").replace("\n", " ")[:200] if sig else "",
            {"in": "клиент", "ai": "ИИ", "out": "менеджер"}.get(str(r["last_dir"] or ""), ""),
            str(r["phone"] or ""), str(r["email"] or ""), str(r["cabinet_name"] or ""),
            waited if waited is not None else "",
            stage_index(r), 1 if is_recent(r["created"]) else 0,
            str(r["username"] or ""), 1 if str(r["manager_role"] or "") == "manager" else 0,
            stale_min if stale_min is not None else "",
            tg, 1 if stirring else 0, active_min if active_min is not None else "", sig_rank,
            STATUS_STAGE.get(str(r["crm_status"] or ""), 0), (minutes_since(r["stage_at"] or r["created"]) or 0) // 1440,
        ]
        clients.append(line)
        closed = str(r["crm_status"]) in ("lost", "case_closed", "not_relevant")
        is_selling = str(r["manager_role"] or "") == "manager"
        key = mgr if is_selling else "без менеджера"
        s = summary.setdefault(key, {"всего": 0, "не взял": 0, "ждут": 0, "в работе": 0})
        if not closed:
            s["всего"] += 1
        if not_claimed: s["не взял"] += 1
        if waited is not None: s["ждут"] += 1
        if r["manager_claimed_at"] and str(r["crm_status"]) not in ("lost", "case_closed", "not_relevant"): s["в работе"] += 1
        if stirring: s["активны"] = s.get("активны", 0) + 1
        if waited is not None or not_claimed or stirring or sig_rank >= 2:
            queue.append((sig_rank, waited if waited is not None else -1, active_min or 0, stale_min or 0, line))
    queue.sort(key=lambda t: (-t[0], -t[1], -t[2], -t[3]))
    return clients, [t[4] for t in queue], summary

# ---------- служебное ----------
def ensure_sheets(svc):
    meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    titles = {s["properties"]["title"]: s for s in meta["sheets"]}
    reqs = [{"addSheet": {"properties": {"title": t}}} for t in ("🔥 Работа", "Инструкция", "Сводка", "Воронка", "Клиенты") if t not in titles]
    if reqs:
        svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs}).execute()
        meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
        titles = {s["properties"]["title"]: s for s in meta["sheets"]}
    order = {"🔥 Работа": 0, "Инструкция": 1, "Сводка": 2, "Воронка": 3, "Клиенты": 4}
    reqs = []
    for t, s in titles.items():
        if t in order:
            reqs.append({"updateSheetProperties": {"properties": {"sheetId": s["properties"]["sheetId"], "index": order[t]}, "fields": "index"}})
        elif t == "Очередь" or len(titles) > 5:
            reqs.append({"deleteSheet": {"sheetId": s["properties"]["sheetId"]}})
    if reqs:
        svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs}).execute()
        meta = svc.spreadsheets().get(spreadsheetId=SHEET_ID).execute()
    return meta

def reset_requests(sheet):
    sid = sheet["properties"]["sheetId"]
    reqs = [{"deleteBanding": {"bandedRangeId": b["bandedRangeId"]}} for b in sheet.get("bandedRanges", [])]
    reqs += [{"deleteConditionalFormatRule": {"sheetId": sid, "index": 0}} for _ in sheet.get("conditionalFormats", [])]
    reqs.append({"unmergeCells": {"range": {"sheetId": sid}}})
    reqs += [{"deleteEmbeddedObject": {"objectId": ch["chartId"]}} for ch in sheet.get("charts", [])]
    # сброс формата всей области и показ всех колонок
    reqs.append({"repeatCell": {"range": {"sheetId": sid}, "cell": {"userEnteredFormat": {}}, "fields": "userEnteredFormat"}})
    reqs.append({"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": "COLUMNS", "startIndex": 0, "endIndex": 26},
                                               "properties": {"hiddenByUser": False}, "fields": "hiddenByUser"}})
    return reqs

def cell_fmt(sid, r0, r1, c0, c1, fmt, fields):
    return {"repeatCell": {"range": {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1, "startColumnIndex": c0, "endColumnIndex": c1},
                           "cell": {"userEnteredFormat": fmt}, "fields": fields}}

def dim(sid, kind, i0, i1, px=None, hidden=None):
    props, fields = {}, []
    if px is not None: props["pixelSize"] = px; fields.append("pixelSize")
    if hidden is not None: props["hiddenByUser"] = hidden; fields.append("hiddenByUser")
    return {"updateDimensionProperties": {"range": {"sheetId": sid, "dimension": kind, "startIndex": i0, "endIndex": i1},
                                          "properties": props, "fields": ",".join(fields)}}

def base_font(size=10, bold=False, color=INK, italic=False):
    return {"fontFamily": FONT, "fontSize": size, "bold": bold, "italic": italic, "foregroundColor": color}

def cond(sid, rng, formula, bg, fg=None, bold=False):
    fmt = {"backgroundColor": bg}
    if fg: fmt["textFormat"] = {"foregroundColor": fg, "bold": bold}
    return {"addConditionalFormatRule": {"rule": {"ranges": [rng], "booleanRule": {
        "condition": {"type": "CUSTOM_FORMULA", "values": [{"userEnteredValue": formula}]}, "format": fmt}}, "index": 0}}

# ---------- листы с таблицей ----------
def table_requests(sid, n_rows, sep, title, urgent_rows=False):
    last = n_rows + 2
    ncol = len(HEAD)
    reqs = [
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"columnCount": max(26, ncol + 1), "frozenRowCount": 2, "frozenColumnCount": 2, "hideGridlines": True}},
                                   "fields": "gridProperties(columnCount,frozenRowCount,frozenColumnCount,hideGridlines)"}},
        # строка 1 — заголовок листа и время
        cell_fmt(sid, 0, 1, 0, ncol, {"backgroundColor": WHITE, "verticalAlignment": "MIDDLE",
                                       "textFormat": base_font(12, True)}, "userEnteredFormat(backgroundColor,verticalAlignment,textFormat)"),
        dim(sid, "ROWS", 0, 1, px=40),
        # шапка
        cell_fmt(sid, 1, 2, 0, ncol, {"backgroundColor": HEAD_BG, "horizontalAlignment": "LEFT", "verticalAlignment": "MIDDLE",
                                       "wrapStrategy": "WRAP", "padding": {"left": 8, "right": 8},
                                       "textFormat": base_font(10, True, HEAD_TXT)},
                 "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,wrapStrategy,padding,textFormat)"),
        dim(sid, "ROWS", 1, 2, px=40),
        # тело
        cell_fmt(sid, 2, last, 0, ncol, {"backgroundColor": WHITE, "verticalAlignment": "MIDDLE", "wrapStrategy": "CLIP",
                                          "padding": {"left": 8, "right": 8}, "textFormat": base_font(10),
                                          "borders": {"bottom": {"style": "SOLID", "width": 1, "color": LINE}}},
                 "userEnteredFormat(backgroundColor,verticalAlignment,wrapStrategy,padding,textFormat,borders)"),
        dim(sid, "ROWS", 2, last, px=30),
        # выравнивания
        cell_fmt(sid, 2, last, COL["№"], COL["№"] + 1, {"horizontalAlignment": "CENTER", "textFormat": base_font(10, False, MUTED)}, "userEnteredFormat(horizontalAlignment,textFormat)"),
        cell_fmt(sid, 2, last, COL["Имя"], COL["Имя"] + 1, {"textFormat": base_font(10, True)}, "userEnteredFormat.textFormat"),
        cell_fmt(sid, 2, last, COL["Взял в работу"], COL["Взял в работу"] + 1, {"horizontalAlignment": "CENTER"}, "userEnteredFormat.horizontalAlignment"),
        cell_fmt(sid, 2, last, COL["Заявка"], COL["Заявка"] + 1, {"horizontalAlignment": "CENTER", "textFormat": base_font(10, False, MUTED),
                                                                    "numberFormat": {"type": "DATE", "pattern": "dd.MM.yy"}}, "userEnteredFormat(horizontalAlignment,textFormat,numberFormat)"),
        cell_fmt(sid, 2, last, COL["Предв. возврат, ₽"], COL["Предв. возврат, ₽"] + 1, {"horizontalAlignment": "RIGHT", "numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}, "userEnteredFormat(horizontalAlignment,numberFormat)"),
        cell_fmt(sid, 2, last, COL["Ждёт ответа"], COL["Ждёт ответа"] + 1, {"horizontalAlignment": "CENTER", "textFormat": base_font(10, True)}, "userEnteredFormat(horizontalAlignment,textFormat)"),
        cell_fmt(sid, 2, last, COL["Последнее сообщение"], COL["Последнее сообщение"] + 1, {"wrapStrategy": "CLIP", "textFormat": base_font(10, False, MUTED)}, "userEnteredFormat(wrapStrategy,textFormat)"),
        cell_fmt(sid, 2, last, COL["Кто писал"], COL["Кто писал"] + 1, {"horizontalAlignment": "CENTER", "textFormat": base_font(10, False, MUTED)}, "userEnteredFormat(horizontalAlignment,textFormat)"),
        {"addBanding": {"bandedRange": {"range": {"sheetId": sid, "startRowIndex": 2, "endRowIndex": last, "startColumnIndex": 0, "endColumnIndex": ncol},
                                        "rowProperties": {"firstBandColor": WHITE, "secondBandColor": ZEBRA}}}},
        {"setBasicFilter": {"filter": {"range": {"sheetId": sid, "startRowIndex": 1, "endRowIndex": last, "startColumnIndex": 0, "endColumnIndex": ncol}}}},
    ]
    for i, w in enumerate(WIDTHS):
        reqs.append(dim(sid, "COLUMNS", i, i + 1, px=w))
    reqs.append(dim(sid, "COLUMNS", COL["мин"], max(26, len(HEAD) + 1), hidden=True))
    # светофор — только на ячейке, не на строке
    mcol = chr(ord("A") + COL["мин"]); tcol = chr(ord("A") + COL["Взял в работу"])
    wait_rng = {"sheetId": sid, "startRowIndex": 2, "endRowIndex": last, "startColumnIndex": COL["Ждёт ответа"], "endColumnIndex": COL["Ждёт ответа"] + 1}
    took_rng = {"sheetId": sid, "startRowIndex": 2, "endRowIndex": last, "startColumnIndex": COL["Взял в работу"], "endColumnIndex": COL["Взял в работу"] + 1}
    if urgent_rows:
        row_rng = {"sheetId": sid, "startRowIndex": 2, "endRowIndex": last, "startColumnIndex": 0, "endColumnIndex": ncol - 1}
        reqs.append(cond(sid, row_rng, f'=AND(ISNUMBER(${mcol}3){sep}${mcol}3>=60)', rgb("FFF5F5")))
    reqs += [
        cond(sid, {"sheetId": sid, "startRowIndex": 2, "endRowIndex": last, "startColumnIndex": COL["Сигнал ИИ"], "endColumnIndex": COL["Сигнал ИИ"] + 1},
             f'=REGEXMATCH({L("Сигнал ИИ")}3{sep}"^⚠")', RED_BG, RED_TXT, True),
        cond(sid, {"sheetId": sid, "startRowIndex": 2, "endRowIndex": last, "startColumnIndex": COL["Сигнал ИИ"], "endColumnIndex": COL["Сигнал ИИ"] + 1},
             f'=REGEXMATCH({L("Сигнал ИИ")}3{sep}"^(🔥|💳|🙋)")', ORANGE_BG, ORANGE_TXT, True),
        cond(sid, wait_rng, f'=AND(ISNUMBER(${mcol}3){sep}${mcol}3<20)', GREEN_BG, GREEN_TXT, True),
        cond(sid, wait_rng, f'=AND(ISNUMBER(${mcol}3){sep}${mcol}3>=20{sep}${mcol}3<60)', ORANGE_BG, ORANGE_TXT, True),
        cond(sid, wait_rng, f'=AND(ISNUMBER(${mcol}3){sep}${mcol}3>=60)', RED_BG, RED_TXT, True),
        cond(sid, wait_rng, f'=LEFT({chr(ord("A") + COL["Ждёт ответа"])}3{sep}1)="⚡"', ORANGE_BG, ORANGE_TXT, False),
        cond(sid, took_rng, f'=${tcol}3="нет"', RED_BG, RED_TXT, True),
        cond(sid, took_rng, f'=${tcol}3="да"', GREEN_BG, GREEN_TXT, False),
    ]
    return reqs

# ---------- сводка ----------

def queue_values(sep):
    """«Очередь» — два QUERY с одинаковым where/order (колонка «Ник» между ними собирается отдельно, чтобы ссылки жили)."""
    last = L(HEAD[-1]); K = f"Клиенты!A3:{last}"
    m, took, stir, act, lie, sg = L("мин"), L("Взял в работу"), L("шевелится"), L("актив_мин"), L("лежит_мин"), L("сигнал№")
    where = f"where {sg} >= 2 or {m} >= 0 or {took} = 'нет' or {stir} = 1 order by {sg} desc, {m} desc, {act} desc, {lie} desc"
    rest = ",".join(L(h) for h in HEAD[4:])   # с колонки «Этап» до конца
    q1 = f'=IFERROR(QUERY({K};"select A,B {where}";0);"")'
    q2 = f'=IFERROR(QUERY({K};"select {rest} {where}";0);"")'
    n, tg = L("ник"), L("tg_id")
    nick = f'=ARRAYFORMULA(IF({n}3:{n}="";"";HYPERLINK("https://t.me/"&{n}3:{n};"@"&{n}3:{n})))'
    dlg = f'=ARRAYFORMULA(IF({tg}3:{tg}="";"";HYPERLINK("https://t.me/{BOT_USERNAME}?start=dlg_"&{tg}3:{tg};"💬 в боте")))'
    title = (f'="Работа · кому нужен ответ сейчас · обновлено "&Клиенты!{STAMP_CELL}&"   ·   сверху те, кто ждёт дольше · '
             'фильтр по себе — воронка в колонке «Менеджер» · «💬 в боте» открывает диалог с клиентом · как пользоваться — вкладка «Инструкция»"')
    return [[title], HEAD, [q1, "", nick, dlg, q2]]

def summary_values(sep, closed_labels, n_mgr_slots=6):
    """«Сводка» на формулах над «Клиентами». Буквы колонок берутся из HEAD."""
    K = "Клиенты!"
    e, f, q, st, u, m, d = (L("Менеджер"), L("Взял в работу"), L("мин"), L("шевелится"), L("продающий"), L("Этап"), L("Этап"))
    closed = "".join(f';{K}{m}3:{m};"<>{lbl}"' for lbl in closed_labels)
    rows = [
        ["", "MPZORRO · сводка для менеджеров"],
        ["", f'="Обновлено "&{K}{STAMP_CELL}&". Считается формулами из листа «Клиенты» — данные туда бот пушит при каждом изменении. Писать клиентам — из бота."'],
        [],
        ["", f'=COUNTIF({K}{L("сигнал№")}3:{L("сигнал№")};">=2")', "", f"=COUNT({K}{q}3:{q})", "", f'=COUNTIF({K}{f}3:{f};"нет")', "", f'=COUNTIF({K}{st}3:{st};1)'],
        ["", "🔥 прогреты ИИ — ждут менеджера", "", "написали в бот и ждут ответа", "", "не взяты в работу", "", "активны, а менеджер молчит"],
        [],
        ["", "По менеджерам"],
        ["", "Менеджер", "Всего карточек", "Не взял в работу", "Ждут ответа", "Активны", "В работе"],
    ]
    for i in range(n_mgr_slots):
        r = 9 + i
        name = f'=IFERROR(INDEX(SORT(UNIQUE(FILTER({K}{e}3:{e};{K}{u}3:{u}=1)));{i + 1});"")'
        rows.append(["", name,
                     f'=IF($B{r}="";"";COUNTIFS({K}{e}3:{e};$B{r}{closed}))',
                     f'=IF($B{r}="";"";COUNTIFS({K}{e}3:{e};$B{r};{K}{f}3:{f};"нет"))',
                     f'=IF($B{r}="";"";COUNTIFS({K}{e}3:{e};$B{r};{K}{q}3:{q};">=0"))',
                     f'=IF($B{r}="";"";COUNTIFS({K}{e}3:{e};$B{r};{K}{st}3:{st};1))',
                     f'=IF($B{r}="";"";COUNTIFS({K}{e}3:{e};$B{r};{K}{f}3:{f};"да"{closed}))'])
    rows += [[], ["", "Как читать таблицу"],
             ["", "Работа", "кому нужен ответ прямо сейчас: сигнал ИИ, написали в бот, активны без ответа, розданы и не взяты. Сверху — сигналы ИИ, потом кто ждёт дольше."],
             ["", "Сигнал ИИ", "что ИИ понял из переписки: 🔥 готов начинать · 💳 готов оплатить · 🙋 просит менеджера · ⚠️ жалоба · 🤝 уже общается с менеджером · ⏳ вернуться позже. Рядом — «Комментарий ИИ» для менеджера. Про 🔥💳🙋⚠️ бот пишет в чат «Огонь Менеджеры»."],
             ["", "Активны", "клиент сам что-то делал в боте (открыл, нажал, оставил почту) после последнего действия менеджера — и ему никто не ответил. Так считает и Зорро в чате."],
             ["", "Взял в работу", "«нет» — заявка раздана менеджеру, но кнопка «Взять» в боте не нажата. Такие надо брать первыми."],
             ["", "💬 в боте", "открывает диалог с клиентом прямо в боте — писать оттуда, не из личного аккаунта."]]
    return rows

def summary_requests(sid, n_mgr, n_rows, sep=","):
    hdr = 7  # индекс строки шапки таблицы менеджеров (0-based)
    mrows = (hdr + 1, hdr + 1 + n_mgr)
    legend0 = hdr + 1 + n_mgr + 1  # индекс строки «Как читать» (шапка + менеджеры + пустая)
    reqs = [
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"hideGridlines": True, "frozenRowCount": 0, "frozenColumnCount": 0}},
                                   "fields": "gridProperties(hideGridlines,frozenRowCount,frozenColumnCount)"}},
        cell_fmt(sid, 0, n_rows + 2, 0, 12, {"backgroundColor": WHITE, "textFormat": base_font(10), "verticalAlignment": "MIDDLE"}, "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)"),
        dim(sid, "COLUMNS", 0, 1, px=24),                       # левый отступ
        dim(sid, "COLUMNS", 1, 2, px=170),                      # B — имя менеджера / первая плитка
        dim(sid, "COLUMNS", 2, 9, px=112),                      # C..I — ровные колонки таблицы и плиток
        dim(sid, "COLUMNS", 9, 12, px=24),
        # заголовок и подзаголовок
        dim(sid, "ROWS", 0, 1, px=44),
        cell_fmt(sid, 0, 1, 1, 9, {"textFormat": base_font(18, True)}, "userEnteredFormat.textFormat"),
        {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
        cell_fmt(sid, 1, 2, 1, 9, {"textFormat": base_font(10, False, MUTED)}, "userEnteredFormat.textFormat"),
        {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 1, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
        dim(sid, "ROWS", 2, 3, px=18),
        # KPI-плитки: значение (строка 4) + подпись (строка 5), заливка на обеих
        dim(sid, "ROWS", 3, 4, px=56), dim(sid, "ROWS", 4, 5, px=30),
    ]
    tile_cols = [(1, 3), (3, 5), (5, 7), (7, 9)]
    accent = [INK, ORANGE_TXT, RED_TXT, INK]
    for (c0, c1), col in zip(tile_cols, accent):
        reqs += [
            {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 3, "endRowIndex": 4, "startColumnIndex": c0, "endColumnIndex": c1}, "mergeType": "MERGE_ALL"}},
            {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 4, "endRowIndex": 5, "startColumnIndex": c0, "endColumnIndex": c1}, "mergeType": "MERGE_ALL"}},
            cell_fmt(sid, 3, 4, c0, c1, {"backgroundColor": TILE_BG, "horizontalAlignment": "LEFT", "verticalAlignment": "BOTTOM",
                                          "padding": {"left": 14, "top": 8}, "textFormat": base_font(26, True, col),
                                          "numberFormat": {"type": "NUMBER", "pattern": "#,##0"},
                                          "borders": {"right": {"style": "SOLID", "width": 3, "color": WHITE}, "left": {"style": "SOLID", "width": 3, "color": WHITE}}},
                     "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,padding,textFormat,numberFormat,borders)"),
            cell_fmt(sid, 4, 5, c0, c1, {"backgroundColor": TILE_BG, "horizontalAlignment": "LEFT", "verticalAlignment": "TOP",
                                          "padding": {"left": 14, "bottom": 10}, "textFormat": base_font(9, False, MUTED),
                                          "borders": {"right": {"style": "SOLID", "width": 3, "color": WHITE}, "left": {"style": "SOLID", "width": 3, "color": WHITE}}},
                     "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,padding,textFormat,borders)"),
        ]
    reqs += [
        dim(sid, "ROWS", 5, 6, px=22),
        # секция «По менеджерам»
        cell_fmt(sid, 6, 7, 1, 8, {"textFormat": base_font(12, True)}, "userEnteredFormat.textFormat"),
        dim(sid, "ROWS", 6, 7, px=34),
        cell_fmt(sid, hdr, hdr + 1, 1, 9, {"backgroundColor": HEAD_BG, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE",
                                            "textFormat": base_font(10, True, HEAD_TXT), "padding": {"left": 8, "right": 8}},
                 "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,textFormat,padding)"),
        cell_fmt(sid, hdr, hdr + 1, 1, 2, {"horizontalAlignment": "LEFT"}, "userEnteredFormat.horizontalAlignment"),
        dim(sid, "ROWS", hdr, hdr + 1, px=36),
        cell_fmt(sid, mrows[0], mrows[1], 1, 7, {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "padding": {"left": 8, "right": 8},
                                                  "textFormat": base_font(11), "borders": {"bottom": {"style": "SOLID", "width": 1, "color": LINE}}},
                 "userEnteredFormat(horizontalAlignment,verticalAlignment,padding,textFormat,borders)"),
        cell_fmt(sid, mrows[0], mrows[1], 1, 2, {"horizontalAlignment": "LEFT", "textFormat": base_font(11, True)}, "userEnteredFormat(horizontalAlignment,textFormat)"),

        dim(sid, "ROWS", mrows[0], mrows[1], px=34),
        # подсветка только проблемных ячеек
        cond(sid, {"sheetId": sid, "startRowIndex": mrows[0], "endRowIndex": mrows[1], "startColumnIndex": 3, "endColumnIndex": 4}, ("=AND(ISNUMBER(D9);D9>0)" if sep == ";" else "=AND(ISNUMBER(D9),D9>0)"), RED_BG, RED_TXT, True),
        cond(sid, {"sheetId": sid, "startRowIndex": mrows[0], "endRowIndex": mrows[1], "startColumnIndex": 4, "endColumnIndex": 5}, ("=AND(ISNUMBER(E9);E9>0)" if sep == ";" else "=AND(ISNUMBER(E9),E9>0)"), ORANGE_BG, ORANGE_TXT, True),
        cond(sid, {"sheetId": sid, "startRowIndex": mrows[0], "endRowIndex": mrows[1], "startColumnIndex": 6, "endColumnIndex": 7}, ("=AND(ISNUMBER(F9);F9>0)" if sep == ";" else "=AND(ISNUMBER(F9),F9>0)"), ORANGE_BG, ORANGE_TXT, True),
        # легенда
        dim(sid, "ROWS", legend0 - 1, legend0, px=22),
        cell_fmt(sid, legend0, legend0 + 1, 1, 8, {"textFormat": base_font(12, True)}, "userEnteredFormat.textFormat"),
        dim(sid, "ROWS", legend0, legend0 + 1, px=34),
        cell_fmt(sid, legend0 + 1, n_rows, 1, 2, {"textFormat": base_font(10, True), "verticalAlignment": "TOP"}, "userEnteredFormat(textFormat,verticalAlignment)"),
        cell_fmt(sid, legend0 + 1, n_rows, 2, 9, {"textFormat": base_font(10, False, MUTED), "wrapStrategy": "WRAP", "verticalAlignment": "TOP"}, "userEnteredFormat(textFormat,wrapStrategy,verticalAlignment)"),
        dim(sid, "ROWS", legend0 + 1, n_rows, px=34),
    ]
    for r in range(legend0 + 1, n_rows):
        reqs.append({"mergeCells": {"range": {"sheetId": sid, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 2, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}})
    return reqs


# ---------- инструкция ----------
ACCENT_BG = rgb("EEF2FF"); ACCENT_TXT = rgb("3730A3")

def instruction_spec():
    """Строки инструкции: (тип, текст[, доп]). Типы: h1, sub, h2, step, text, color, warn, gap."""
    S = []
    S += [("h1", "Как пользоваться этой таблицей"),
          ("sub", f"Таблица — зеркало клиентского бота @{BOT_USERNAME}. Обновляется сама через несколько секунд после любого изменения в боте, время обновления — в первой строке каждого листа. "
                  "Здесь только смотрим и фильтруем. Работаем с клиентом — в боте."),
          ("gap", "")]
    S += [("h2", "1. Что здесь есть — пять вкладок внизу экрана"),
          ("step", "🔥 Работа", "Главная рабочая вкладка, открывается первой. Здесь только те, кому нужен ответ прямо сейчас: написали в бот, активны без ответа (⚡), или розданы и не взяты. Сверху — кто ждёт дольше всех."),
          ("step", "Сводка", "Цифры на сегодня: сколько клиентов всего, сколько ждут ответа, сколько раздали, но не взяли, сколько активны без ответа. И таблица по каждому менеджеру. Смотреть утром и вечером."),
          ("step", "Воронка", "Сколько клиентов дошли до каждого этапа — от «открыл бота» через check-in (входной платёж) до «деньги получены», с конверсией между этапами и графиком. Для руководителя и для понимания, где теряем людей."),
          ("step", "Клиенты", "Все карточки без исключения. Нужна, когда ищете конкретного человека или смотрите свой список целиком."),
          ("step", "Инструкция", "Эта страница."),
          ("gap", "")]
    S += [("h2", "2. Утро менеджера — пять действий по порядку"),
          ("step", "1", "Откройте вкладку «🔥 Работа»."),
          ("step", "2", "Оставьте только своих: в шапке нажмите воронку ▼ в колонке «Менеджер» → снимите «Выбрать все» → поставьте галочку на своём имени → «ОК». Чтобы снова видеть всех — та же воронка → «Выбрать все»."),
          ("step", "3", "Идите сверху вниз. Красные и оранжевые ячейки в «Ждёт ответа» — клиент уже написал и ждёт. Это первые."),
          ("step", "4", "Дальше строки, где «Взял в работу» = нет. Это заявки, которые раздали вам, но вы не нажали «Взять» в боте. Откройте бота → «📋 Все мои заявки» → найдите по номеру → «✅ Взять заявку»."),
          ("step", "5", "Пишите клиенту из бота: нажмите «💬 в боте» в строке клиента — откроется его диалог прямо в боте. Ник открывает личный чат — только если клиент не читает бота."),
          ("gap", "")]
    S += [("h2", "3. Что означают цвета"),
          ("color", GREEN_BG, GREEN_TXT, "Ждёт ответа — до 20 минут", "Свежее сообщение. Ответить сейчас — и клиент даже не заметит паузы."),
          ("color", ORANGE_BG, ORANGE_TXT, "Ждёт ответа — от 20 минут до часа", "Уже долго. Через 10 минут тишины в боте клиенту отвечает ИИ, через 15 — заявка уходит в общий пул."),
          ("step", "⚡ Активен без ответа", "Клиент сам что-то делал в боте (нажимал кнопки, открывал разделы, оставлял почту) после вашего последнего касания, а вы не ответили. В «Ждёт ответа» у таких стоит ⚡ и сколько времени прошло. Так же считает Зорро в чате менеджеров."),
          ("color", RED_BG, RED_TXT, "Ждёт ответа — больше часа", "Горит. Брать первым. Вся строка при этом подсвечена бледно-розовым, чтобы её было видно издалека."),
          ("color", RED_BG, RED_TXT, "Взял в работу — нет", "Заявка раздана вам, но кнопка «Взять» в боте не нажата. Бот считает такую заявку брошенной."),
          ("color", GREEN_BG, GREEN_TXT, "Взял в работу — да", "Всё в порядке, заявка в работе."),
          ("gap", "")]
    S += [("h2", "4. Колонки — что в них"),
          ("step", "№", "Постоянный номер клиента. По нему ищут в боте: просто напишите боту число, например 354. Тёзок много — номер один."),
          ("step", "Сигнал ИИ · Комментарий ИИ", "Что ИИ понял из переписки с клиентом: 🔥 готов начинать, 💳 готов оплатить, 🙋 просит менеджера, ⚠️ жалоба, 🤝 уже общается с менеджером напрямую, ⏳ просил вернуться позже. «Комментарий ИИ» — одна фраза для вас: что человек хочет и чего ждёт. Такие клиенты стоят в «🔥 Работе» первыми, а про 🔥💳🙋⚠️ бот сразу пишет в чат «Огонь Менеджеры» с вашим ником."),
          ("step", "Имя · Ник · Диалог", "Как клиент подписан в Telegram. Ник — личный чат. «💬 в боте» — переписка с ним внутри бота, туда и пишем."),
          ("step", "Этап", "На каком шаге сделка: «Ждёт менеджера», «Договор отправлен», «Ждём ответ WB» и так далее. То же, что в боте."),
          ("step", "Менеджер", "За кем закреплён клиент. «без менеджера» — ничей, взять может любой."),
          ("step", "Взял в работу", "да / нет / — . «Нет» — раздано, но не взято. «—» — статус не про это (уже в работе или закрыт)."),
          ("step", "Заявка", "Дата, когда клиент пришёл."),
          ("step", "Источник", "бот / сайт / Excel / вручную. У клиентов с сайта и из Excel нет чата с ботом — с ними связь по телефону и почте."),
          ("step", "Проверка", "Итог бесплатной проверки кабинета: прошёл / не прошёл / не готов / юр. проверка."),
          ("step", "Предв. возврат, ₽", "Сколько предварительно можем вернуть. Пусто — ещё не считали."),
          ("step", "Ждёт ответа", "Сколько времени последнее сообщение клиента висит без ответа. Пусто — клиент не писал или ему уже ответили."),
          ("step", "Последнее сообщение · Кто писал", "Последняя реплика в боте и кто её написал: клиент, ИИ или менеджер. Так видно, на чём остановились."),
          ("step", "Телефон · Почта · Кабинет", "Контакты и название кабинета, если есть."),
          ("gap", "")]
    S += [("h2", "5. Как искать и сортировать"),
          ("step", "Найти", "Ctrl+F (на Mac ⌘+F) → имя, ник или номер. Работает на любой вкладке."),
          ("step", "Фильтр", "Воронка ▼ в шапке любой колонки: галочками выберите нужные значения. Активный фильтр — воронка закрашена. Фильтр видит только вы, другим он не мешает."),
          ("step", "Сортировка", "В той же воронке: «Сортировать от А до Я» или «от Я до А». Работает на «Клиентах». На «🔥 Работе» сортировка не нужна и не сработает — она уже отсортирована формулой: сверху те, кто ждёт дольше."),
          ("step", "Сбросить всё", "Меню Данные → Удалить фильтр, либо просто обновите страницу — при следующем изменении в боте таблица всё равно перепишется."),
          ("gap", "")]
    S += [("h2", "6. Чего делать не надо"),
          ("warn", "Не редактировать ячейки. Таблица только для чтения: при следующем изменении в боте (это секунды) он перезапишет её целиком, и ваши правки исчезнут. Этапы и заметки меняются в боте."),
          ("warn", "Не писать клиенту из личного аккаунта, если он читает бота. Личные аккаунты блокируют за исходящие. Из бота — не блокируют."),
          ("warn", "Не копировать таблицу себе. Копия устареет через минуту, а здесь всегда свежее."),
          ("gap", "")]
    S += [("h2", "7. Если что-то не сходится"),
          ("text", "Источник истины — бот. Если в таблице одно, а в боте другое — верно в боте, таблица догонит за несколько секунд. "
                   "Если расхождение держится дольше часа или вкладка пустая — напишите Павлу или в чат «Огонь Менеджеры 🔥 MPZORRO»."),
          ("gap", "")]
    return S

def instruction_values(spec):
    rows = []
    for item in spec:
        kind = item[0]
        if kind in ("h1", "sub", "h2", "text", "warn"):
            rows.append(["", item[1]])
        elif kind == "step":
            rows.append(["", item[1], item[2]])
        elif kind == "color":
            rows.append(["", item[3], item[4]])
        else:
            rows.append([])
    return rows

def instruction_requests(sid, spec):
    n = len(spec)
    reqs = [
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"hideGridlines": True, "frozenRowCount": 0, "frozenColumnCount": 0}},
                                   "fields": "gridProperties(hideGridlines,frozenRowCount,frozenColumnCount)"}},
        cell_fmt(sid, 0, n + 2, 0, 6, {"backgroundColor": WHITE, "textFormat": base_font(11), "verticalAlignment": "TOP", "wrapStrategy": "WRAP",
                                        "padding": {"top": 6, "bottom": 6, "left": 8, "right": 8}},
                 "userEnteredFormat(backgroundColor,textFormat,verticalAlignment,wrapStrategy,padding)"),
        dim(sid, "COLUMNS", 0, 1, px=24), dim(sid, "COLUMNS", 1, 2, px=250), dim(sid, "COLUMNS", 2, 3, px=720), dim(sid, "COLUMNS", 3, 8, px=24),
    ]
    for i, item in enumerate(spec):
        kind = item[0]
        if kind == "h1":
            reqs += [cell_fmt(sid, i, i + 1, 1, 3, {"textFormat": base_font(20, True)}, "userEnteredFormat.textFormat"),
                     {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": i, "endRowIndex": i + 1, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
                     dim(sid, "ROWS", i, i + 1, px=48)]
        elif kind == "sub":
            reqs += [cell_fmt(sid, i, i + 1, 1, 3, {"textFormat": base_font(11, False, MUTED)}, "userEnteredFormat.textFormat"),
                     {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": i, "endRowIndex": i + 1, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
                     dim(sid, "ROWS", i, i + 1, px=48)]
        elif kind == "h2":
            reqs += [cell_fmt(sid, i, i + 1, 1, 3, {"backgroundColor": HEAD_BG, "textFormat": base_font(12, True, HEAD_TXT), "verticalAlignment": "MIDDLE"},
                              "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)"),
                     {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": i, "endRowIndex": i + 1, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}},
                     dim(sid, "ROWS", i, i + 1, px=38)]
        elif kind == "step":
            reqs += [cell_fmt(sid, i, i + 1, 1, 2, {"backgroundColor": ACCENT_BG, "textFormat": base_font(11, True, ACCENT_TXT),
                                                     "borders": {"bottom": {"style": "SOLID", "width": 2, "color": WHITE}}},
                              "userEnteredFormat(backgroundColor,textFormat,borders)"),
                     cell_fmt(sid, i, i + 1, 2, 3, {"borders": {"bottom": {"style": "SOLID", "width": 1, "color": LINE}}}, "userEnteredFormat.borders")]
        elif kind == "color":
            reqs += [cell_fmt(sid, i, i + 1, 1, 2, {"backgroundColor": item[1], "textFormat": base_font(11, True, item[2]),
                                                     "borders": {"bottom": {"style": "SOLID", "width": 2, "color": WHITE}}},
                              "userEnteredFormat(backgroundColor,textFormat,borders)"),
                     cell_fmt(sid, i, i + 1, 2, 3, {"borders": {"bottom": {"style": "SOLID", "width": 1, "color": LINE}}}, "userEnteredFormat.borders")]
        elif kind == "warn":
            reqs += [cell_fmt(sid, i, i + 1, 1, 3, {"backgroundColor": rgb("FFF7ED"), "textFormat": base_font(11, False, rgb("9A3412")),
                                                     "borders": {"left": {"style": "SOLID", "width": 3, "color": ORANGE_TXT}, "bottom": {"style": "SOLID", "width": 3, "color": WHITE}}},
                              "userEnteredFormat(backgroundColor,textFormat,borders)"),
                     {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": i, "endRowIndex": i + 1, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}}]
        elif kind == "text":
            reqs += [{"mergeCells": {"range": {"sheetId": sid, "startRowIndex": i, "endRowIndex": i + 1, "startColumnIndex": 1, "endColumnIndex": 3}, "mergeType": "MERGE_ALL"}}]
        elif kind == "gap":
            reqs.append(dim(sid, "ROWS", i, i + 1, px=18))
    # высоту строк с длинным текстом подобрать автоматически
    reqs.append({"autoResizeDimensions": {"dimensions": {"sheetId": sid, "dimension": "ROWS", "startIndex": 0, "endIndex": n}}})
    # после авто-подбора вернуть фиксированные высоты заголовкам и пробелам
    for i, item in enumerate(spec):
        if item[0] in ("h1", "sub"): reqs.append(dim(sid, "ROWS", i, i + 1, px=48))
        elif item[0] == "h2": reqs.append(dim(sid, "ROWS", i, i + 1, px=38))
        elif item[0] == "gap": reqs.append(dim(sid, "ROWS", i, i + 1, px=18))
    return reqs


def funnel_counts():
    """Сколько клиентов дошли до каждого этапа (накопительно) — всего и среди пришедших за 30 дней."""
    with Store(DB).managed_connection() as c:
        users = c.execute("""
            select u.telegram_id, u.crm_status, u.created_at, u.manager_claimed_at, u.manager_contacted_at,
                   u.client_replied_at, u.contract_sent_at, u.contract_signed_at, u.claim_submitted, u.payout_date,
                   u.source,
                   exists(select 1 from events e where e.telegram_id=u.telegram_id and e.event_type in ('bot_started','start_screen_viewed')) ev_bot,
                   exists(select 1 from events e where e.telegram_id=u.telegram_id and e.event_type='quiz_started') ev_quiz,
                   exists(select 1 from events e where e.telegram_id=u.telegram_id and e.event_type='quiz_finished') ev_fin,
                   exists(select 1 from events e where e.telegram_id=u.telegram_id and e.event_type='manager_requested') ev_req
              from users u
             where coalesce(u.role,'client')='client' and coalesce(u.source,'') not in ('test','merged_duplicate')
               and coalesce(u.crm_status,'') <> 'merged_duplicate'
               and u.telegram_id not in (select telegram_id from events where event_type='staff_offboarded')""").fetchall()
    total = [0] * len(FUNNEL_STAGES); recent = [0] * len(FUNNEL_STAGES)
    cutoff = (datetime.now(timezone.utc)).timestamp() - 30 * 86400
    for u in users:
        reached = -1
        if u["ev_bot"] or str(u["source"] or "bot") == "bot": reached = 0
        if u["ev_fin"]: reached = max(reached, 1)
        if u["ev_req"]: reached = max(reached, 2)
        for idx, col in ((3, "manager_claimed_at"), (4, "manager_contacted_at"), (5, "client_replied_at"),
                         (6, "contract_sent_at"), (7, "contract_signed_at"), (9, "payout_date")):
            if str(u[col] or "").strip(): reached = max(reached, idx)
        if str(u["claim_submitted"] or "").strip().lower() in ("да", "yes", "1", "true"): reached = max(reached, 8)
        reached = max(reached, STATUS_STAGE.get(str(u["crm_status"] or ""), -1))
        if reached < 0: continue
        try:
            is_recent = datetime.fromisoformat(str(u["created_at"])[:19]).replace(tzinfo=timezone.utc).timestamp() >= cutoff
        except Exception:
            is_recent = False
        for i in range(reached + 1):
            total[i] += 1
            if is_recent: recent[i] += 1
    return total, recent

def funnel_values(sep):
    K = "Клиенты!"
    rows = [["", "MPZORRO · воронка продаж"],
            ["", f'="Обновлено "&{K}{STAMP_CELL}&". Клиент засчитан на этапе, если дошёл до него или дальше. «Новые за 30 дней» — по дате первого обращения. Считается формулами."'],
            [],
            ["", "Этап", "Клиентов, всего", "От предыдущего", "От старта", "Новые за 30 дн.", "От предыдущего, 30 дн.",
             "Сейчас на этапе", "Из них > 7 дней"]]
    for i, (name, _) in enumerate(FUNNEL_STAGES):
        r = 5 + i
        st, nw, cur, dd = L("этап№"), L("новый30"), L("этап_сейчас№"), L("дней_на_этапе")
        rows.append(["", name,
                     f'=COUNTIF({K}{st}3:{st};">="&{i})',
                     "=1" if i == 0 else f"=IFERROR(C{r}/C{r - 1};0)",
                     f"=IFERROR(C{r}/$C$5;0)",
                     f'=COUNTIFS({K}{st}3:{st};">="&{i};{K}{nw}3:{nw};1)',
                     "=1" if i == 0 else f"=IFERROR(F{r}/F{r - 1};0)",
                     f'=COUNTIF({K}{cur}3:{cur};{i})',
                     f'=COUNTIFS({K}{cur}3:{cur};{i};{K}{dd}3:{dd};">7")'])
    rows += [[], ["", "Как читать"],
             ["", "От предыдущего", "какая доля людей с прошлого этапа дошла до этого. Самое маленькое число в столбце — самое узкое место воронки."],
             ["", "От старта", "какая доля всех, кто открыл бота, дошла до этапа."],
             ["", "Новые за 30 дней", "та же воронка, но только для тех, кто пришёл за последний месяц — показывает, как работает система сейчас, а не за всё время."],
             ["", "Сейчас на этапе", "сколько клиентов стоят ровно на этом этапе прямо сейчас (не дальше). «Из них > 7 дней» — сколько из них висят на этапе дольше недели: это и есть «где застряли»."]]
    return rows

def funnel_requests(sid, n_stages, n_rows):
    hdr = 3; r0, r1 = hdr + 1, hdr + 1 + n_stages
    legend0 = r1 + 1
    reqs = [
        {"updateSheetProperties": {"properties": {"sheetId": sid, "gridProperties": {"hideGridlines": True, "frozenRowCount": 0, "frozenColumnCount": 0}},
                                   "fields": "gridProperties(hideGridlines,frozenRowCount,frozenColumnCount)"}},
        cell_fmt(sid, 0, n_rows + 30, 0, 14, {"backgroundColor": WHITE, "textFormat": base_font(10), "verticalAlignment": "MIDDLE"}, "userEnteredFormat(backgroundColor,textFormat,verticalAlignment)"),
        dim(sid, "COLUMNS", 0, 1, px=24), dim(sid, "COLUMNS", 1, 2, px=220), dim(sid, "COLUMNS", 2, 9, px=124), dim(sid, "COLUMNS", 9, 10, px=30),
        dim(sid, "ROWS", 0, 1, px=44),
        cell_fmt(sid, 0, 1, 1, 9, {"textFormat": base_font(18, True)}, "userEnteredFormat.textFormat"),
        {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 0, "endRowIndex": 1, "startColumnIndex": 1, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
        cell_fmt(sid, 1, 2, 1, 9, {"textFormat": base_font(10, False, MUTED), "wrapStrategy": "WRAP"}, "userEnteredFormat(textFormat,wrapStrategy)"),
        {"mergeCells": {"range": {"sheetId": sid, "startRowIndex": 1, "endRowIndex": 2, "startColumnIndex": 1, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}},
        dim(sid, "ROWS", 1, 2, px=36), dim(sid, "ROWS", 2, 3, px=14),
        cell_fmt(sid, hdr, hdr + 1, 1, 7, {"backgroundColor": HEAD_BG, "horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "wrapStrategy": "WRAP",
                                            "textFormat": base_font(10, True, HEAD_TXT), "padding": {"left": 8, "right": 8}},
                 "userEnteredFormat(backgroundColor,horizontalAlignment,verticalAlignment,wrapStrategy,textFormat,padding)"),
        cell_fmt(sid, hdr, hdr + 1, 1, 2, {"horizontalAlignment": "LEFT"}, "userEnteredFormat.horizontalAlignment"),
        dim(sid, "ROWS", hdr, hdr + 1, px=48),
        cell_fmt(sid, r0, r1, 1, 9, {"horizontalAlignment": "CENTER", "verticalAlignment": "MIDDLE", "padding": {"left": 8, "right": 8}, "textFormat": base_font(11),
                                      "borders": {"bottom": {"style": "SOLID", "width": 1, "color": LINE}}},
                 "userEnteredFormat(horizontalAlignment,verticalAlignment,padding,textFormat,borders)"),
        cell_fmt(sid, r0, r1, 1, 2, {"horizontalAlignment": "LEFT", "textFormat": base_font(11, True)}, "userEnteredFormat(horizontalAlignment,textFormat)"),
        cell_fmt(sid, r0, r1, 2, 3, {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}, "textFormat": base_font(11, True)}, "userEnteredFormat(numberFormat,textFormat)"),
        cell_fmt(sid, r0, r1, 5, 6, {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}, "userEnteredFormat.numberFormat"),
        cell_fmt(sid, r0, r1, 3, 5, {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}, "userEnteredFormat.numberFormat"),
        cell_fmt(sid, r0, r1, 6, 7, {"numberFormat": {"type": "PERCENT", "pattern": "0%"}}, "userEnteredFormat.numberFormat"),
        cell_fmt(sid, r0, r1, 7, 9, {"numberFormat": {"type": "NUMBER", "pattern": "#,##0"}}, "userEnteredFormat.numberFormat"),
        cond(sid, {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1, "startColumnIndex": 8, "endColumnIndex": 9}, "=AND(ISNUMBER(I5);I5>=5)", RED_BG, RED_TXT, True),
        cond(sid, {"sheetId": sid, "startRowIndex": r0, "endRowIndex": r1, "startColumnIndex": 8, "endColumnIndex": 9}, "=AND(ISNUMBER(I5);I5>0;I5<5)", ORANGE_BG, ORANGE_TXT, False),
        dim(sid, "ROWS", r0, r1, px=32),
        # конверсия от предыдущего: шкала цветом — красное = узкое место
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid, "startRowIndex": r0 + 1, "endRowIndex": r1, "startColumnIndex": 3, "endColumnIndex": 4}],
            "gradientRule": {"minpoint": {"color": RED_BG, "type": "MIN"}, "midpoint": {"color": ORANGE_BG, "type": "PERCENTILE", "value": "50"}, "maxpoint": {"color": GREEN_BG, "type": "MAX"}}}, "index": 0}},
        {"addConditionalFormatRule": {"rule": {"ranges": [{"sheetId": sid, "startRowIndex": r0 + 1, "endRowIndex": r1, "startColumnIndex": 6, "endColumnIndex": 7}],
            "gradientRule": {"minpoint": {"color": RED_BG, "type": "MIN"}, "midpoint": {"color": ORANGE_BG, "type": "PERCENTILE", "value": "50"}, "maxpoint": {"color": GREEN_BG, "type": "MAX"}}}, "index": 0}},
        # легенда
        dim(sid, "ROWS", r1, r1 + 1, px=18),
        cell_fmt(sid, legend0, legend0 + 1, 1, 9, {"textFormat": base_font(12, True)}, "userEnteredFormat.textFormat"),
        cell_fmt(sid, legend0 + 1, n_rows, 1, 2, {"textFormat": base_font(10, True), "verticalAlignment": "TOP"}, "userEnteredFormat(textFormat,verticalAlignment)"),
        cell_fmt(sid, legend0 + 1, n_rows, 2, 9, {"textFormat": base_font(10, False, MUTED), "wrapStrategy": "WRAP", "verticalAlignment": "TOP"}, "userEnteredFormat(textFormat,wrapStrategy,verticalAlignment)"),
        dim(sid, "ROWS", legend0 + 1, n_rows, px=34),
    ]
    for r in range(legend0 + 1, n_rows):
        reqs.append({"mergeCells": {"range": {"sheetId": sid, "startRowIndex": r, "endRowIndex": r + 1, "startColumnIndex": 2, "endColumnIndex": 9}, "mergeType": "MERGE_ALL"}})
    # график: горизонтальные столбцы по этапам, справа от таблицы
    stage_rng = {"sheetId": sid, "startRowIndex": hdr, "endRowIndex": r1, "startColumnIndex": 1, "endColumnIndex": 2}
    total_rng = {"sheetId": sid, "startRowIndex": hdr, "endRowIndex": r1, "startColumnIndex": 2, "endColumnIndex": 3}
    recent_rng = {"sheetId": sid, "startRowIndex": hdr, "endRowIndex": r1, "startColumnIndex": 5, "endColumnIndex": 6}
    reqs.append({"addChart": {"chart": {
        "spec": {"title": "Воронка: сколько клиентов дошли до этапа", "titleTextFormat": {"fontFamily": FONT, "fontSize": 12, "bold": True},
                 "fontName": FONT, "backgroundColor": WHITE,
                 "basicChart": {"chartType": "BAR", "legendPosition": "BOTTOM_LEGEND", "headerCount": 1,
                                "axis": [{"position": "BOTTOM_AXIS", "title": "клиентов"}, {"position": "LEFT_AXIS"}],
                                "domains": [{"domain": {"sourceRange": {"sources": [stage_rng]}}, "reversed": True}],
                                "series": [{"series": {"sourceRange": {"sources": [total_rng]}}, "targetAxis": "BOTTOM_AXIS", "color": rgb("111827")},
                                           {"series": {"sourceRange": {"sources": [recent_rng]}}, "targetAxis": "BOTTOM_AXIS", "color": rgb("F59E0B")}]}},
        "position": {"overlayPosition": {"anchorCell": {"sheetId": sid, "rowIndex": n_rows + 1, "columnIndex": 1}, "widthPixels": 920, "heightPixels": 460}}}}})
    return reqs

def push_data(svc, sheets, stamp, clients):
    """Быстрый пуш: только строки «Клиентов» + метка времени. Формулы остальных листов пересчитаются сами."""
    title = "Все клиенты · фильтры в шапке: этап, менеджер, источник · как пользоваться — вкладка «Инструкция»"
    last = L(HEAD[-1])
    svc.spreadsheets().values().clear(spreadsheetId=SHEET_ID, range=f"'Клиенты'!A3:{last}").execute()
    svc.spreadsheets().values().batchUpdate(spreadsheetId=SHEET_ID, body={"valueInputOption": "USER_ENTERED", "data": [
        {"range": "'Клиенты'!A1", "values": [[title], HEAD] + clients},
        {"range": f"'Клиенты'!{STAMP_CELL}", "values": [[stamp]]},
    ]}).execute()

def main():
    data_only = "--data" in sys.argv
    creds = service_account.Credentials.from_service_account_file(KEY, scopes=["https://www.googleapis.com/auth/spreadsheets"])
    svc = build("sheets", "v4", credentials=creds, cache_discovery=False)
    meta = ensure_sheets(svc)
    locale = str(meta.get("properties", {}).get("locale") or "en")
    sep = ";" if locale.lower().startswith(("ru", "de", "fr", "es", "it", "pl", "tr", "uk")) else ","
    sheets = {s["properties"]["title"]: s for s in meta["sheets"]}
    stamp = datetime.now(timezone.utc).astimezone().strftime("%d.%m.%Y %H:%M") + " МСК"

    clients, queue, summary = build_tables(load_rows(), sep)
    if data_only:
        push_data(svc, sheets, stamp, clients)
        print(f"data: {len(clients)} строк, {stamp}")
        return

    closed_labels = [CRM_STATUS_LABELS.get(s, s) for s in ("lost", "case_closed", "not_relevant")]
    spec = instruction_spec()
    formula_sheets = {
        "Сводка": summary_values(sep, closed_labels, n_mgr_slots=4),
        "Воронка": funnel_values(sep),
        "🔥 Работа": queue_values(sep),
        "Инструкция": instruction_values(spec),
    }
    reqs = []
    for name in ("Инструкция", "Воронка", "🔥 Работа", "Клиенты", "Сводка"):
        reqs += reset_requests(sheets[name])
    svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs}).execute()
    for name in formula_sheets:
        svc.spreadsheets().values().clear(spreadsheetId=SHEET_ID, range=f"'{name}'!A:Z").execute()
    svc.spreadsheets().values().clear(spreadsheetId=SHEET_ID, range="'Клиенты'!A:Z").execute()
    push_data(svc, sheets, stamp, clients)
    for name, data in formula_sheets.items():
        svc.spreadsheets().values().update(spreadsheetId=SHEET_ID, range=f"'{name}'!A1", valueInputOption="USER_ENTERED", body={"values": data}).execute()
    reqs = []
    reqs += table_requests(sheets["🔥 Работа"]["properties"]["sheetId"], len(queue) + 60, sep, "🔥 Работа", urgent_rows=True)
    reqs += table_requests(sheets["Клиенты"]["properties"]["sheetId"], len(clients), sep, "Клиенты")
    reqs += summary_requests(sheets["Сводка"]["properties"]["sheetId"], 4, len(formula_sheets["Сводка"]), sep)
    reqs += instruction_requests(sheets["Инструкция"]["properties"]["sheetId"], spec)
    reqs += funnel_requests(sheets["Воронка"]["properties"]["sheetId"], len(FUNNEL_STAGES), len(formula_sheets["Воронка"]))
    svc.spreadsheets().batchUpdate(spreadsheetId=SHEET_ID, body={"requests": reqs}).execute()
    print(f"layout+data: клиентов {len(clients)}, в очереди {len(queue)}, {stamp}")

if __name__ == "__main__":
    main()
