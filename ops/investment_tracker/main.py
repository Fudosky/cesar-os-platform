"""Orquestador del Monitor de Inversiones. CLI: --dry-run, --source KEY."""
import sys
import os
import re
import datetime
import traceback
sys.path.insert(0, "/opt/data/ops")
from investment_tracker import config as c, fetch, extract, analyze, record, alarm


def _series(src, subject):
    """Nombre de serie por cuenta: usa el Ref del extracto si está (evita mezclar cuentas)."""
    m = re.search(r"Ref[:\s]*([0-9]{6,})", subject or "")
    return "%s ·%s" % (src["label"], m.group(1)[-6:]) if m else src["label"]


def _log(msg):
    try:
        os.makedirs(os.path.dirname(c.LOG_PATH), exist_ok=True)
        open(c.LOG_PATH, "a", encoding="utf-8").write(
            "%s  %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), msg))
    except Exception:
        pass
    print(msg)


def process_source(src, dry_run=False):
    msgs, token = fetch.recent_for_source(src, top=120)
    pw = os.environ.get(src.get("pdf_password_env", ""), "")
    nuevos = 0
    for m in msgs:
        key = "%s | %s" % (m.get("receivedDateTime", "")[:16].replace("T", " "), m.get("subject", ""))
        if record.already_seen(src, key):
            continue
        cand = []
        if m.get("hasAttachments"):
            raw = fetch.pdf_bytes(m["id"], token)   # PDF local, no sale del VPS
            if raw:
                try:
                    cand = extract.candidate_lines(extract.pdf_text(raw, pw))
                except Exception as e:
                    cand = ["(no se pudo leer el PDF: %s)" % e]
        subject = m.get("subject", "") or ""
        # --- análisis: LOCAL (sin LLM) o Opus, según config ---
        if c.LOCAL_ONLY:
            res = analyze.analyze_local(src, subject, cand)
        else:
            res, _model = analyze.analyze(src, subject, cand, m.get("bodyPreview", ""))
        series = _series(src, subject)
        valor = res.get("valor")
        prev = record.last_value(series)   # valor anterior de ESTA cuenta
        caida = (prev is not None and valor is not None and valor < prev * (1 - c.DROP_ALARM_PCT / 100.0))
        if dry_run:
            print("\n== %s [%s] | %s\n   tipo=%s valor=%s %s | prev=%s caida=%s\n   %s" %
                  (src["label"], series.split("·")[-1], subject[:45], res.get("tipo"),
                   valor, res.get("moneda"), prev, caida, res.get("resumen")))
            nuevos += 1
            continue
        if res.get("tipo") == "ruido":
            record.bitacora_row(src, key, "ruido", res.get("resumen", ""), False)
        else:
            tend = record.tracker_row(src, valor, res.get("moneda"), series=series)
            tend_baja = bool(tend and "↘️" in tend)
            accion = caida or tend_baja
            record.bitacora_row(src, key, "sustantivo", res.get("resumen", ""), accion)
            if accion:
                motivo = ("caída >%.0f%% vs anterior" % c.DROP_ALARM_PCT) if caida else "tendencia a la baja"
                alarm.raise_alarm(src, res.get("resumen", ""), motivo)
        nuevos += 1
    _log("%s: %d nuevos%s" % (src["key"], nuevos, " (dry-run)" if dry_run else ""))
    return nuevos


def run(dry_run=False, only=None):
    for src in c.INVESTMENT_SOURCES:
        if only and src["key"] != only:
            continue
        try:
            process_source(src, dry_run)
        except Exception as e:
            traceback.print_exc()
            _log("ERROR %s: %s" % (src["key"], e))
            if not dry_run:
                try:
                    alarm.deliver.to_telegram("🔴 Monitor inversiones ERROR (%s): %s" % (src["key"], e))
                except Exception:
                    pass


if __name__ == "__main__":
    args = sys.argv[1:]
    only = args[args.index("--source") + 1] if "--source" in args else None
    run(dry_run="--dry-run" in args, only=only)
