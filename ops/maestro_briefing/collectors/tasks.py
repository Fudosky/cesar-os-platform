"""Colector de tareas del día: pendientes de Obsidian + agenda del día (Graph calendarView).

La agenda usa el token Graph con scope Calendars.Read (requiere re-login 1 vez con
outlook_auth.py ampliado). Si el permiso no está → degrada a "⚠️ no disponible".
"""
import os
import re
import json
import datetime
import urllib.request
import urllib.parse
from maestro_briefing import config as c

_CLIENT_ID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"  # Graph CLI público (mismo que la migración)
_AUTHORITY = "https://login.microsoftonline.com/consumers"
_TOKEN = "/opt/data/outlook_token.json"


def _pendientes(max_items: int = 15):
    path = os.path.join(c.VAULT, c.PENDIENTES_NOTE)
    try:
        lines = open(path, encoding="utf-8").read().splitlines()
    except FileNotFoundError:
        return "⚠️ Pendientes no disponible: nota no encontrada", False
    section = ""
    groups = {}
    count = 0
    for line in lines:
        h = re.match(r"^#{2,}\s+(.*)$", line)
        if h:
            section = h.group(1).strip()
            continue
        m = re.match(r"^\s*[-*]\s*\[ \]\s*(.+)$", line)
        if m and count < max_items:
            item = re.sub(r"\*\*|\[\[|\]\]", "", m.group(1)).strip()
            groups.setdefault(section or "General", []).append(item)
            count += 1
    total_open = sum(1 for l in lines if re.match(r"^\s*[-*]\s*\[ \]", l))
    if not groups:
        return "Sin pendientes abiertos.", True
    out = ["%s:\n%s" % (sec, "\n".join("- " + i for i in items)) for sec, items in groups.items()]
    body = "\n\n".join(out)
    if total_open > count:
        body += "\n(+%d pendientes más)" % (total_open - count)
    return body, True


def _agenda(max_items: int = 12):
    from msal import PublicClientApplication
    try:
        tok = json.load(open(_TOKEN))
        app = PublicClientApplication(_CLIENT_ID, authority=_AUTHORITY)
        res = app.acquire_token_by_refresh_token(tok.get("refresh_token", ""), scopes=["Calendars.Read"])
        if "access_token" not in res:
            return "⚠️ Agenda no disponible: falta permiso de calendario (re-login pendiente)", False
        today = datetime.date.today().isoformat()
        params = urllib.parse.urlencode({
            "startDateTime": today + "T00:00:00",
            "endDateTime": today + "T23:59:59",
            "$select": "subject,start,end,location",
            "$orderby": "start/dateTime",
            "$top": str(max_items),
        })
        url = "https://graph.microsoft.com/v1.0/me/calendarView?" + params
        req = urllib.request.Request(url, headers={
            "Authorization": "Bearer " + res["access_token"],
            "Prefer": 'outlook.timezone="Central Standard Time (Mexico)"',
        })
        with urllib.request.urlopen(req, timeout=20) as r:
            evs = json.loads(r.read().decode("utf-8")).get("value", [])
        if not evs:
            return "Agenda de hoy: sin eventos.", True
        lines = []
        for e in evs:
            t = (e.get("start", {}).get("dateTime", "") or "")[11:16]
            lines.append("- %s — %s" % (t, e.get("subject", "(sin título)")))
        return "Agenda de hoy:\n" + "\n".join(lines), True
    except Exception as ex:
        return "⚠️ Agenda no disponible: %s" % ex, False


def collect():
    pend, ok1 = _pendientes()
    ag, ok2 = _agenda()
    return ("Tareas", pend + "\n\n" + ag, ok1 or ok2)


if __name__ == "__main__":
    n, b, ok = collect()
    print("OK=%s\n%s" % (ok, b))
