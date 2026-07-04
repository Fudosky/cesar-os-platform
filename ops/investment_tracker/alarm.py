"""Alarmas: Telegram inmediato + fila en Pendientes. Reusa maestro_briefing.deliver."""
import os
from investment_tracker import config as c
from maestro_briefing import deliver


def raise_alarm(source, resumen, motivo):
    msg = ("🚨 Inversión — %s\n%s\nMotivo: %s\n"
           "(verifica por el canal oficial del banco, nunca desde el enlace del correo)"
           % (source["label"], resumen, motivo))
    deliver.to_telegram(msg)   # texto plano; falla ruidoso si Telegram no ok
    full = os.path.join(c.VAULT, c.PENDIENTES_NOTE)
    try:
        with open(full, "a", encoding="utf-8") as f:
            f.write("\n- [ ] 🚨 Inversión %s: %s (%s)" % (source["label"], resumen[:80], motivo[:60]))
    except Exception:
        pass


if __name__ == "__main__":
    print("alarm.py — Telegram + Pendientes")
