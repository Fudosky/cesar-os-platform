# Cesar OS — Bot de Telegram 24/7 (núcleo + career-radar + mem0)
# El código se monta como volumen desde el host; la imagen solo trae dependencias.
FROM python:3.13-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8 \
    HOME=/root \
    TZ=America/Mexico_City \
    HF_HOME=/root/.cache/huggingface

WORKDIR /root/telegram-claude

RUN apt-get update \
 && apt-get install -y --no-install-recommends tzdata ca-certificates build-essential \
 && rm -rf /var/lib/apt/lists/*

# Torch CPU-only primero (evita descargar CUDA, ~700MB en vez de ~2.5GB)
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

COPY requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt

# Pre-baja el modelo de embeddings para que /recuerda no espere en la 1ª llamada
RUN python3 -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Outlook (Microsoft Graph) — lectura de correo headless via refresh token (/email)
RUN pip install --no-cache-dir msal

# Hermes Agent (/hermes) — agente LLM via OpenRouter + MCP LinkedIn (Composio cloud)
RUN pip install --no-cache-dir hermes-agent

# rclone (Cerebro v2.1, /nutrir) — leer carpetas curadas de Dropbox desde la nube
RUN apt-get update && apt-get install -y --no-install-recommends curl unzip \
 && curl -fsSL https://downloads.rclone.org/rclone-current-linux-amd64.zip -o /tmp/rc.zip \
 && unzip -j /tmp/rc.zip "*/rclone" -d /usr/local/bin/ \
 && chmod +x /usr/local/bin/rclone \
 && rm -rf /tmp/rc.zip /var/lib/apt/lists/*

# Legacy: LibreOffice (.ppt, lento) + antiword (.doc, rápido). .xls via xlrd (pip).
RUN apt-get update && apt-get install -y --no-install-recommends \
    libreoffice-impress libreoffice-writer libreoffice-calc antiword \
 && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir "mcp[cli]"
CMD ["python3", "bot.py"]
