"""Orquestador del Briefing Maestro.

CLI:
  (sin args)   corre el briefing diario y lo ENVÍA (Telegram + Obsidian)
  --no-send    dry-run: corre todo e imprime, NO envía
  --pipeline   pipeline Vertiv on-demand (fuera del briefing diario)
"""
import os
import sys
import datetime
import traceback

sys.path.insert(0, "/opt/data/ops")
from maestro_briefing import config as c
from maestro_briefing.collectors import mail, tasks, news, radar, cerebro
from maestro_briefing import synthesize, evaluate, deliver

COLLECTORS = [mail, tasks, news, radar, cerebro]


def _log(msg):
    try:
        os.makedirs(os.path.dirname(c.LOG_PATH), exist_ok=True)
        with open(c.LOG_PATH, "a", encoding="utf-8") as f:
            f.write("%s  %s\n" % (datetime.datetime.now().isoformat(timespec="seconds"), msg))
    except Exception:
        pass
    print(msg)


def gather():
    parts = []
    for mod in COLLECTORS:
        try:
            name, block, ok = mod.collect()
        except Exception as e:
            name = mod.__name__.split(".")[-1]
            block, ok = "⚠️ %s error: %s" % (name, e), False
        _log("colector %-8s ok=%s" % (name, ok))
        parts.append("### %s\n%s" % (name, block))
    return "\n\n".join(parts)


def run(no_send=False):
    bundle = gather()
    text, model = synthesize.synthesize(bundle)
    ok, reason = evaluate.evaluate(text, model)
    if not ok:
        alert = "🔴 Briefing Maestro NO enviado: %s" % reason
        _log(alert)
        if not no_send:
            try:
                deliver.to_telegram(alert)   # fallo ruidoso a Telegram
            except Exception:
                pass
        return 2
    if no_send:
        print("\n===== DRY-RUN (no enviado) =====\n" + text)
        _log("dry-run ok (%d chars, model=%s)" % (len(text), model))
        return 0
    mid, path = deliver.deliver(text)
    _log("ENVIADO mid=%s nota=%s" % (mid, path))
    return 0


def pipeline_ondemand(no_send=False):
    """Pipeline Vertiv on-demand (fuera del briefing diario)."""
    notes = ["02 - Vertiv/Pipeline y Cuentas.md", "02 - Vertiv/Equipo Hunter y Pipeline 2026.md"]
    raw = []
    for n in notes:
        p = os.path.join(c.VAULT, n)
        try:
            raw.append("## %s\n%s" % (n, open(p, encoding="utf-8").read()[:4000]))
        except Exception as e:
            raw.append("⚠️ %s no disponible: %s" % (n, e))
    text, model = synthesize.synthesize(
        "PIPELINE VERTIV (resume estado, prioridades y próximos pasos comerciales):\n" + "\n\n".join(raw))
    if no_send:
        print(text)
        return 0
    deliver.to_telegram("📊 Pipeline Vertiv\n\n" + text)
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    no_send = "--no-send" in args
    try:
        if "--pipeline" in args:
            sys.exit(pipeline_ondemand(no_send))
        sys.exit(run(no_send))
    except Exception as e:
        traceback.print_exc()
        try:
            deliver.to_telegram("🔴 Briefing Maestro CRASH: %s" % e)
        except Exception:
            pass
        sys.exit(1)
