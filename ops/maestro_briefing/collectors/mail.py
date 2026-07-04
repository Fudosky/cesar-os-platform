"""Colector de correos: REUSA outlook_email.py (token Graph, refresh, Mail.Read).

Nombre `mail.py` (no `email.py`) para NO tapar el módulo stdlib `email`.
Corre el script probado como subproceso y parsea su JSON — no reimplementa Graph.
"""
import subprocess
import json
import traceback


def collect(max_items: int = 8):
    """Devuelve (nombre, bloque, ok). Resume no leídos."""
    try:
        out = subprocess.run(
            ["python", "/opt/data/scripts/outlook_email.py"],
            capture_output=True, text=True, timeout=45,
        )
        raw = (out.stdout or "").strip()
        if not raw:
            return ("Correos", "⚠️ Correos no disponible: sin salida (%s)" % (out.stderr or "")[:120], False)
        data = json.loads(raw)
        if data.get("error"):
            return ("Correos", "⚠️ Correos no disponible: %s" % data["error"], False)
        unread = data.get("unread", [])
        count = data.get("unread_count", len(unread))
        if not unread:
            return ("Correos", "Sin correos no leídos.", True)
        lines = []
        for m in unread[:max_items]:
            frm = m.get("from", "?")
            subj = m.get("subject", "(sin asunto)")
            prev = (m.get("preview", "") or "")[:140]
            lines.append("- **%s** — %s: %s" % (frm, subj, prev))
        return ("Correos", "%d no leídos:\n%s" % (count, "\n".join(lines)), True)
    except Exception as e:
        traceback.print_exc()
        return ("Correos", "⚠️ Correos no disponible: %s" % e, False)


if __name__ == "__main__":
    n, b, ok = collect()
    print("OK=%s\n%s" % (ok, b))
