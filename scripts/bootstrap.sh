#!/usr/bin/env bash
# Bootstrap de Fase 0 en el VPS: instala Docker + genera secretos en .env.
# Correr desde la raíz del repo:   bash scripts/bootstrap.sh
set -euo pipefail
cd "$(dirname "$0")/.."

echo "=== Cesar OS — Bootstrap Fase 0 ==="

# [1/3] Docker
if ! command -v docker >/dev/null 2>&1; then
  echo "[1/3] Instalando Docker..."
  curl -fsSL https://get.docker.com | sh
  sudo usermod -aG docker "$USER" 2>/dev/null || true
  echo "   (si te pide re-login para el grupo docker, cierra y reabre SSH)"
else
  echo "[1/3] Docker ya instalado: $(docker --version)"
fi

# [2/3] .env con secretos auto-generados
if [ ! -f .env ]; then
  echo "[2/3] Generando .env con secretos seguros..."
  cp .env.example .env
  gen() { openssl rand -hex 32; }
  sed -i "s|^LITELLM_MASTER_KEY=.*|LITELLM_MASTER_KEY=sk-litellm-$(gen)|" .env
  sed -i "s|^POSTGRES_PASSWORD=.*|POSTGRES_PASSWORD=$(gen)|" .env
  sed -i "s|^NEXTAUTH_SECRET=.*|NEXTAUTH_SECRET=$(gen)|" .env
  sed -i "s|^LANGFUSE_SALT=.*|LANGFUSE_SALT=$(gen)|" .env
  sed -i "s|^LANGFUSE_ENCRYPTION_KEY=.*|LANGFUSE_ENCRYPTION_KEY=$(gen)|" .env
  echo "   ✔ Secretos generados automáticamente."
else
  echo "[2/3] .env ya existe — no lo toco."
fi

# [3/3] permisos de scripts
chmod +x postgres/init-databases.sh scripts/*.sh 2>/dev/null || true
echo "[3/3] Permisos listos."

echo ""
echo "================ FALTA SOLO ESTO (tú) ================"
echo "1) Edita .env:        nano .env"
echo "   - DOMAIN=tu.dominio.com"
echo "   - ANTHROPIC_API_KEY, OPENROUTER_API_KEY, GROQ_API_KEY"
echo "2) Levanta todo:      docker compose up -d"
echo "3) Abre Langfuse:     https://observ.TU_DOMINIO  (crea cuenta + proyecto + API keys)"
echo "   pega LANGFUSE_PUBLIC_KEY/SECRET_KEY en .env y:  docker compose up -d litellm"
echo "4) Verifica:          ./scripts/health-check.sh"
echo "====================================================="
