"""Colector de radar: resume la nota 'Radar Diario' más reciente del vault.

Notas en: 08 - Carrera/Radar/YYYY-MM-DD — Radar Diario.md
"""
import os
import glob
import re
from maestro_briefing import config as c


def collect(max_chars: int = 1500):
    d = os.path.join(c.VAULT, c.RADAR_DIR, "Radar")
    files = sorted(glob.glob(os.path.join(d, "*Radar Diario*.md")))
    if not files:  # fallback recursivo por si cambia la estructura
        files = sorted(glob.glob(
            os.path.join(c.VAULT, c.RADAR_DIR, "**", "*Radar*Diario*.md"), recursive=True))
    if not files:
        return ("Radar", "⚠️ Radar no disponible: sin nota de radar", False)
    latest = files[-1]
    try:
        text = open(latest, encoding="utf-8").read()
    except Exception as e:
        return ("Radar", "⚠️ Radar no disponible: %s" % e, False)
    body = re.sub(r"^---.*?---\s*", "", text, flags=re.DOTALL)[:max_chars]
    fecha = os.path.basename(latest).replace(".md", "")
    return ("Radar", "(%s)\n%s" % (fecha, body.strip()), True)


if __name__ == "__main__":
    n, b, ok = collect()
    print("OK=%s\n%s" % (ok, b))
