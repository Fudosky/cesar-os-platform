"""Entrega: Telegram sendMessage (texto plano) + nota Obsidian. Verifica el resultado real.

Texto plano a propósito: el output de Opus trae **negritas**/[links] que romperían el
Markdown de Telegram (HTTP 400). Plano con emojis se lee bien y nunca falla por formato.
"""
import os
import json
import datetime
import urllib.request
import urllib.parse
from maestro_briefing import config as c


def _tg_send(text):
    url = "https://api.telegram.org/bot%s/sendMessage" % c.TELEGRAM_TOKEN
    data = urllib.parse.urlencode({
        "chat_id": c.TELEGRAM_CHAT,
        "text": text,
        "disable_web_page_preview": "true",
    }).encode("utf-8")
    with urllib.request.urlopen(urllib.request.Request(url, data=data), timeout=25) as r:
        res = json.loads(r.read().decode("utf-8"))
    if not res.get("ok"):
        raise RuntimeError("Telegram no ok: %s" % res)
    return res["result"]["message_id"]


def to_telegram(text):
    """Envía; parte en trozos de <=4000 chars si hace falta. Falla ruidoso si no ok."""
    text = text or ""
    mids = []
    for i in range(0, max(len(text), 1), 3900):
        mids.append(_tg_send(text[i:i + 3900]))
    return mids[0] if mids else None


def to_obsidian(text):
    day = datetime.date.today().isoformat()
    d = os.path.join(c.VAULT, c.BRIEFINGS_DIR)
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, "%s — Briefing Maestro.md" % day)
    with open(path, "w", encoding="utf-8") as f:
        f.write("---\ntipo: briefing\nfecha: %s\n---\n\n# 🌅 Briefing Maestro — %s\n\n%s\n" % (day, day, text))
    return path


def deliver(text):
    mid = to_telegram(text)      # falla ruidoso si Telegram no ok
    path = to_obsidian(text)
    return mid, path
