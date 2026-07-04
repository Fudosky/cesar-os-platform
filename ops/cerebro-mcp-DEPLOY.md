# Cerebro-MCP — el Maestro (Hermes) conectado al cerebro · 2026-07-03

Le da a Hermes la herramienta MCP **`buscar_cerebro`**: recupera fragmentos de los 30 años de
conocimiento de Cesar (Qdrant, colección **pública `vault`**). `vault_private` **NUNCA** se expone.

## Piezas (en este repo)
- `docker-compose.phase2.yml` → servicio **`cerebro-mcp`** (`image: cesar-os-bot:latest`, corre
  `cerebro_mcp.py`, FastMCP streamable-http en `:8090`, solo red interna, `restart: unless-stopped`).
- `ops/cerebro_mcp.py` → servidor FastMCP. En el VPS vive en `/root/bot/telegram-claude/cerebro_mcp.py`
  (bind-mounted). **Solo colección `vault`** (guarda dura por env + assert). Desactiva la protección
  anti-DNS-rebinding (`transport_security(enable_dns_rebinding_protection=False)`) porque es solo-interno.
- `ops/bot.Dockerfile` → Dockerfile del bot; agrega `RUN pip install "mcp[cli]"` (necesario para el
  servidor MCP). Construye `cesar-os-bot:latest`.

## Cableado en Hermes (config en `/root/.hermes`, NO en git — tiene secretos)
- `hermes mcp add cerebro --url http://cerebro-mcp:8090/mcp` (responder: no-auth, habilitar) → enabled.
- Modelo del Maestro: `model.default: opus` · `provider: custom:litellm` · fallback `sonnet`.
  custom_provider `litellm` (`base_url: http://litellm:4000/v1`, `key_env: LITELLM_MASTER_KEY`).
  `LITELLM_MASTER_KEY` en `/opt/data/.env` (leída de litellm).
- `terminal.cwd: /opt/data` (era `/root` → `PermissionError`: el agente corre como user `hermes`, no root).
- `SOUL.md`: instrucción de usar `buscar_cerebro` para temas del conocimiento de Cesar.

## Recuperar desde cero
1. `docker compose -f docker-compose.yml -f docker-compose.phase1.yml -f docker-compose.phase2.yml build telegram-bot` (imagen con `mcp`).
2. `... up -d cerebro-mcp`.
3. `hermes mcp add cerebro --url http://cerebro-mcp:8090/mcp` + `docker restart cesar-os-hermes-1`.
4. Verificar: `hermes mcp test cerebro`, y preguntar al Maestro por Telegram (`@Cesar_Maestro_bot`)
   algo de su conocimiento → debe llamar `buscar_cerebro` (ver log `[LLAMADA]` en `cesar-os-cerebro-mcp-1`).

## Monitoreo de gasto
El canario diario del laptop (`health_canary.py`, `check_anthropic_credit`) avisa 🔴 a Telegram si el
crédito Opus se agota. litellm sin DB de spend → no hay $ exacto (habilitarla sería otro paso).
