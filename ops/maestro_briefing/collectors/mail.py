"""Colector de correos MULTI-CUENTA (etiquetado por cuenta).

- provider "microsoft": reusa outlook_email.py (Graph, Mail.Read) — Hotmail.
- provider "gmail_imap": imaplib + App Password (SSL). readonly + BODY.PEEK →
  NUNCA marca como leído ni envía nada (Fase 1 = solo lectura).

Cuentas gmail sin App Password configurada se SALTAN (no rompen el briefing).
Archivo `mail.py` (no `email.py`) para no tapar el módulo stdlib `email`.
"""
import os
import json
import datetime
import subprocess
import imaplib
import email as emaillib
from email.header import decode_header
from maestro_briefing import config as c

_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def _decode(s):
    if not s:
        return ""
    out = []
    for text, enc in decode_header(s):
        if isinstance(text, bytes):
            try:
                out.append(text.decode(enc or "utf-8", "replace"))
            except Exception:
                out.append(text.decode("utf-8", "replace"))
        else:
            out.append(text)
    return "".join(out).replace("\n", " ").strip()


def _microsoft_block(acc, label, max_items):
    out = subprocess.run(["python", "/opt/data/scripts/outlook_email.py"],
                         capture_output=True, text=True, timeout=45)
    data = json.loads((out.stdout or "").strip() or "{}")
    if data.get("error"):
        raise RuntimeError(data["error"])
    unread = data.get("unread", [])
    count = data.get("unread_count", len(unread))
    if not unread:
        return "%s: sin no leídos." % label
    lines = ["  - %s: %s" % (m.get("from", "?"), (m.get("subject", "") or "")[:80])
             for m in unread[:max_items]]
    return "%s (%d no leídos):\n%s" % (label, count, "\n".join(lines))


def _gmail_block(acc, label, max_items):
    pw = os.environ.get(acc.get("pw_env", ""), "").strip()
    if not pw:
        return None  # cuenta aún no configurada -> skip silencioso
    recent_days = acc.get("recent_days")
    note = ""
    M = imaplib.IMAP4_SSL("imap.gmail.com", 993)
    try:
        M.login(acc["email"], pw)
        M.select("INBOX", readonly=True)   # readonly = jamás marca leído
        if recent_days:
            d = datetime.date.today() - datetime.timedelta(days=recent_days)
            since = "%02d-%s-%d" % (d.day, _MONTHS[d.month - 1], d.year)
            typ, data = M.search(None, "UNSEEN", "SINCE", since)
            note = " · últimas ~%dh" % (recent_days * 24)
        else:
            typ, data = M.search(None, "UNSEEN")
        ids = data[0].split() if (data and data[0]) else []
        if not ids:
            return "%s: sin no leídos%s." % (label, note)
        lines = []
        for i in reversed(ids[-max_items:]):
            typ, md = M.fetch(i, "(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])")
            raw = md[0][1] if (md and md[0] and len(md[0]) > 1) else b""
            msg = emaillib.message_from_bytes(raw)
            frm = _decode(msg.get("From", ""))[:40]
            subj = _decode(msg.get("Subject", "(sin asunto)"))[:80]
            lines.append("  - %s: %s" % (frm, subj))
        return "%s (%d no leídos%s):\n%s" % (label, len(ids), note, "\n".join(lines))
    finally:
        try:
            M.logout()
        except Exception:
            pass


def collect(max_items: int = 5):
    blocks = []
    ok_any = False
    for acc in c.EMAIL_ACCOUNTS:
        label = acc.get("label", acc["email"])
        try:
            if acc["provider"] == "microsoft":
                blk = _microsoft_block(acc, label, max_items)
            elif acc["provider"] == "gmail_imap":
                blk = _gmail_block(acc, label, max_items)
            else:
                blk = None
            if blk is None:
                continue  # cuenta no configurada aún
            blocks.append(blk)
            ok_any = True
        except Exception as e:
            blocks.append("%s: ⚠️ no disponible (%s)" % (label, str(e)[:80]))
    if not blocks:
        return ("Correos", "Sin cuentas de correo configuradas.", False)
    return ("Correos", "\n\n".join(blocks), ok_any)


if __name__ == "__main__":
    n, b, ok = collect()
    print("OK=%s\n%s" % (ok, b))
