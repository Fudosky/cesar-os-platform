"""Config del Monitor de Inversiones. Reusa secretos/rutas de maestro_briefing."""
import sys
sys.path.insert(0, "/opt/data/pylibs")   # pypdf vendorizado
sys.path.insert(0, "/opt/data/ops")
from maestro_briefing import config as base   # LITELLM_*, TELEGRAM_*, VAULT, BRIEFING_MODEL


def _secret(name):
    import os
    return os.environ.get(name, "").strip()


VAULT = base.VAULT
LITELLM_BASE = base.LITELLM_BASE
LITELLM_KEY = base.LITELLM_KEY
MODEL = base.BRIEFING_MODEL
TELEGRAM_TOKEN = base.TELEGRAM_TOKEN
TELEGRAM_CHAT = base.TELEGRAM_CHAT

# 🔒 Modo privacidad: True = TODO LOCAL (Anthropic no ve NADA financiero; análisis por reglas).
# Cambiar a False solo cuando el ZDR de Anthropic esté confirmado (para el análisis matizado de Opus).
LOCAL_ONLY = True
DROP_ALARM_PCT = 3.0   # caída >3% vs valor anterior dispara alarma (modo local)
NOISE_PATTERNS = ("protocolo cisa", "aviso del mercado", "aviso de abono", "cisa")

INV_DIR = "01 - Inversiones"
TRACKER_NOTE = INV_DIR + "/📈 Tracker de Inversiones — Valores en el Tiempo.md"
PENDIENTES_NOTE = "00 - Sistema/📌 Pendientes y TODOs.md"
LOG_PATH = "/opt/data/logs/investment_tracker.log"

# Cada fuente: match por remitente/asunto; bitácora propia; forecast textual (para el juicio de Opus).
INVESTMENT_SOURCES = [
    {"key": "bbva_ch", "label": "🇨🇭 BBVA Suiza",
     "from_endswith": "@bbva.ch", "subject_has": None,
     "bitacora": INV_DIR + "/📋 BBVA Suiza — Bitácora de Análisis de Correos.md",
     "forecast": "cartera moderada USD 100K, retorno esperado ~5%/año"},
    {"key": "bbva_co", "label": "🇨🇴 BBVA Colombia",
     "from_equals": "extractos@extractos.bbva.com.co", "subject_has": None,
     "pdf_password_env": "BBVA_CO_PDF_PW",  # extracto CIFRADO (cédula) — Task 1 gate
     "bitacora": INV_DIR + "/📋 BBVA Colombia — Bitácora de Extractos.md",
     "forecast": "extractos de cuenta; vigilar saldo y movimientos"},
    {"key": "azimut", "label": "🇲🇽 Azimut",
     "from_equals": "catylopezh@me.com", "subject_has": "azimut",
     "bitacora": INV_DIR + "/📋 Azimut — Bitácora (vía Caterine).md",
     "forecast": "portafolio Caterine (cuenta 129908) ~87% deuda gob + 13% RV; retorno proy ~13.5-16%/año"},
]
