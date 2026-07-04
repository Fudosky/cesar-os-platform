"""Config del Briefing Maestro: rutas, feeds RSS, secretos (SOLO desde entorno)."""
import os
import sys

# feedparser se instala en /opt/data/pylibs (Task 5); disponible para todo el paquete.
sys.path.insert(0, "/opt/data/pylibs")


def _load_env(path="/opt/data/.env"):
    """Carga el .env del contenedor en os.environ (el cron NO hereda el env del gateway).

    Usa setdefault: si la variable ya viene del entorno (gateway), no la pisa.
    """
    try:
        with open(path) as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
    except FileNotFoundError:
        pass


_load_env()


def _secret(name: str) -> str:
    """Lee un secreto SOLO del entorno. Nada hardcoded."""
    return os.environ.get(name, "").strip()


# --- Rutas ---
VAULT = "/root/Dropbox/OBSIDIAN"
SCRIPTS = "/opt/data/scripts"
LOG_PATH = "/opt/data/logs/maestro_briefing.log"

# --- LLM (gateway litellm) ---
LITELLM_BASE = os.environ.get("LITELLM_BASE_URL", "http://litellm:4000/v1")
LITELLM_KEY = _secret("LITELLM_MASTER_KEY")
BRIEFING_MODEL = os.environ.get("BRIEFING_MODEL", "opus")
MAX_TOKENS = int(os.environ.get("BRIEFING_MAX_TOKENS", "1500"))

# --- Telegram ---
TELEGRAM_TOKEN = _secret("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.environ.get("BRIEFING_CHAT_ID", "8632566831")

# --- Cerebro MCP ---
CEREBRO_MCP = os.environ.get("CEREBRO_MCP_URL", "http://cerebro-mcp:8090/mcp")

# --- Notas del vault (relativas a VAULT) ---
PENDIENTES_NOTE = "00 - Sistema/📌 Pendientes y TODOs.md"
RADAR_DIR = "08 - Carrera"
BRIEFINGS_DIR = "00 - Sistema/Briefings"

# --- Noticias RSS (semilla; Cesar cura/ajusta) — sector DC/energía/IA/QC ---
RSS_FEEDS = [
    "https://www.datacenterdynamics.com/en/rss/",
    "https://www.datacenterfrontier.com/feed/",
    "https://www.utilitydive.com/feeds/news/",
    "https://thequantuminsider.com/feed/",
]

# --- Cuentas de correo (multi-cuenta) ---
# provider: "microsoft" (Graph via outlook_email.py) o "gmail_imap" (IMAP + App Password).
# La App Password de cada Gmail se guarda en /opt/data/.env con el nombre de pw_env.
# Cuentas gmail_imap sin App Password configurada se SALTAN (no rompen el briefing).
EMAIL_ACCOUNTS = [
    {"label": "📧 Hotmail", "email": "cabrerc1@hotmail.com", "provider": "microsoft"},
    {"label": "📨 Gmail", "email": "cukly17@gmail.com", "provider": "gmail_imap", "pw_env": "GMAIL_CUKLY17_APP_PW"},
    {"label": "🔺 C2J", "email": "c2jtycheventures@gmail.com", "provider": "gmail_imap", "pw_env": "GMAIL_C2J_APP_PW"},
    {"label": "🎓 Edron", "email": "cabrera.lopez@edron.edu.mx", "provider": "gmail_imap", "pw_env": "GMAIL_EDRON_APP_PW"},
]
