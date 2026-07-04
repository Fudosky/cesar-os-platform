"""Dedup + escritura de bitácora por fuente + tracker de valores (con tendencia)."""
import os
import datetime
from investment_tracker import config as c


def _read(path):
    full = os.path.join(c.VAULT, path)
    return open(full, encoding="utf-8").read() if os.path.exists(full) else ""


def _append(path, text):
    full = os.path.join(c.VAULT, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "a", encoding="utf-8") as f:
        f.write(text)


def _safe_key(key):
    return key.replace("|", "/").replace("\n", " ")


def already_seen(source, key):
    """key = 'YYYY-MM-DD HH:MM | asunto'. Dedup contra la bitácora (misma sanitización que al escribir)."""
    return _safe_key(key) in _read(source["bitacora"])


def bitacora_row(source, key, tipo, resumen, accion):
    if not _read(source["bitacora"]):   # crear con cabecera si no existe
        _append(source["bitacora"],
                "---\ntipo: seguimiento-correos\nproyecto: Inversiones\n---\n\n# %s — Bitácora\n\n"
                "> Automatizada por el Monitor de Inversiones. Vinculada a [[🏦 Index - Inversiones]] "
                "y [[📈 Tracker de Inversiones — Valores en el Tiempo]].\n\n"
                "| Fecha+hora | Asunto/clave | Tipo | Resumen | ¿Acción? |\n|---|---|---|---|---|\n"
                % source["label"])
    _append(source["bitacora"], "| %s | %s | %s | %s |\n" %
            (_safe_key(key), tipo, resumen.replace("|", "/").replace("\n", " "),
             "Sí" if accion else "No"))


def _prev_values(series):
    """Valores históricos de UNA serie (cuenta) — evita mezclar cuentas distintas."""
    vals = []
    for l in _read(c.TRACKER_NOTE).splitlines():
        if not l.startswith("|"):
            continue
        cols = [x.strip() for x in l.split("|")]
        if len(cols) < 5 or cols[2] != series:
            continue
        try:
            vals.append(float(cols[3].replace(",", "")))
        except ValueError:
            pass
    return vals


def last_value(series):
    """Último valor registrado de una serie (o None) — para detectar caídas localmente."""
    vals = _prev_values(series)
    return vals[-1] if vals else None


def _trend(values):
    if len(values) < 2:
        return "➡️ (base)"
    return "↗️" if values[-1] > values[-2] else ("↘️" if values[-1] < values[-2] else "➡️")


def tracker_row(source, valor, moneda, series=None):
    """Registra el valor en el tracker por SERIE (cuenta). Devuelve la tendencia."""
    if valor is None:
        return None
    series = series or source["label"]
    if not _read(c.TRACKER_NOTE):
        _append(c.TRACKER_NOTE,
                "---\ntipo: tracker\nproyecto: Inversiones\n---\n\n"
                "# 📈 Tracker de Inversiones — Valores en el Tiempo\n\n"
                "> Registro de largo plazo (valor + tendencia) POR CUENTA. Vinculado a [[🏦 Index - Inversiones]].\n\n"
                "| Fecha | Cuenta | Valor | Moneda | Δ vs anterior | Tendencia |\n|---|---|---|---|---|---|\n")
    prev = _prev_values(series)
    delta = ("{:+,.2f}".format(valor - prev[-1])) if prev else "—"
    tend = _trend(prev + [valor])
    _append(c.TRACKER_NOTE, "| %s | %s | %s | %s | %s | %s |\n" %
            (datetime.date.today().isoformat(), series,
             "{:,.2f}".format(valor), moneda or "", delta, tend))
    return tend


if __name__ == "__main__":
    print("record.py — dedup + bitácora + tracker")
