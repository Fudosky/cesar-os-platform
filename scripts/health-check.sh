#!/usr/bin/env bash
# Verifica que los servicios de Fase 0 respondan. Correr en el VPS.
set -u
source ./.env 2>/dev/null || true
DOM="${DOMAIN:-localhost}"
echo "=== Cesar OS — Health check (Fase 0) ==="
echo "--- Contenedores ---"
docker compose ps
echo ""
echo "--- LiteLLM (interno) ---"
docker compose exec -T litellm sh -c 'wget -qO- http://localhost:4000/health/readiness || echo "litellm NO responde"' 2>/dev/null
echo ""
echo "--- Langfuse (interno) ---"
docker compose exec -T langfuse sh -c 'wget -qO- http://localhost:3000/api/public/health || echo "langfuse NO responde"' 2>/dev/null
echo ""
echo "--- HTTPS público (Caddy) ---"
for sub in "" "llm." "observ."; do
  url="https://${sub}${DOM}"
  code=$(curl -s -o /dev/null -w "%{http_code}" --max-time 10 "$url" || echo "ERR")
  echo "  $url -> $code"
done
echo ""
echo "Si los 3 dan 200/302/401, el cimiento está arriba. ✅"
