# Cesar OS Platform — Fase 0 (Cimiento + Observabilidad)

Servidor 24/7 con HTTPS, **gateway de LLM (LiteLLM)** y **observabilidad de costo (Langfuse)**.
Construido por Claude. Tú solo: contratas VPS + dominio y corres los comandos.

---

## 🛒 Paso A — Lo que necesitas conseguir (una sola vez)

1. **VPS 8 GB** (~$15-25/mes). Recomendado:
   - **Hetzner** CCX13 (o CX42) — mejor relación precio/potencia, o
   - **Hostinger** KVM 2 — más fácil si quieres panel simple.
   - Sistema: **Ubuntu 24.04**. Apunta el acceso por SSH.
2. **Dominio** (~$12/año): Namecheap o Cloudflare. Ej. `cesaros.com` o un subdominio que ya tengas.
3. **Anthropic API key** (de pago, para los agentes expertos): https://console.anthropic.com → API Keys.
4. Ten a mano tus llaves ya existentes: **OpenRouter** y **Groq** (están en `~/.secrets/.env`).

### DNS (en tu proveedor de dominio)
Crea 3 registros **A** apuntando a la **IP de tu VPS**:
```
@        ->  IP_DEL_VPS
llm      ->  IP_DEL_VPS
observ   ->  IP_DEL_VPS
```

---

## ⚙️ Paso B — Instalar Docker en el VPS (una vez)
Conéctate por SSH y corre:
```bash
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER && newgrp docker
docker --version && docker compose version
```

## 📦 Paso C — Subir este proyecto al VPS
Opción simple (clonar desde tu GitHub privado):
```bash
git clone https://github.com/Fudosky/cesar-os-platform.git
cd cesar-os-platform
```
*(O cópialo por `scp`. Yo ya dejé el repo listo en tu PC: `C:\Users\Cesar\cesar-os-platform`.)*

## 🔐 Paso D — Configurar secretos
```bash
cp .env.example .env
nano .env          # rellena DOMAIN, las 3 llaves LLM, y genera los secretos:
# para cada XXXX de Langfuse y el master key:   openssl rand -hex 32
chmod +x postgres/init-databases.sh scripts/health-check.sh
```

## 🚀 Paso E — Arrancar (en 2 tiempos por las llaves de Langfuse)
```bash
# 1) Levanta todo
docker compose up -d

# 2) Abre Langfuse en el navegador:  https://observ.TU_DOMINIO
#    - crea tu cuenta (primer usuario = admin)
#    - crea un proyecto "cesar-os"
#    - Settings -> API Keys -> copia PUBLIC y SECRET
#    - pégalas en .env  (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY)

# 3) Reinicia litellm para que empiece a trazar a Langfuse
docker compose up -d litellm
```

## ✅ Paso F — Verificar
```bash
./scripts/health-check.sh
```
Prueba el gateway (debe responder y aparecer en Langfuse con su costo):
```bash
curl https://llm.TU_DOMINIO/v1/chat/completions \
  -H "Authorization: Bearer TU_LITELLM_MASTER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"haiku","messages":[{"role":"user","content":"hola"}]}'
```

**Fase 0 lista cuando:** la llamada responde Y aparece en `https://observ.TU_DOMINIO` con su costo. 🎉

---

## 💵 Costo de Fase 0
VPS ~$15-25/mes + dominio ~$12/año. El LLM solo se cobra cuando lo uses (en Fase 0 casi nada).
Langfuse y LiteLLM = software libre, $0.

## 🔜 Siguiente
Con el cimiento arriba → **Fase 1** (Open WebUI = tu iPhone hablando con tu vault).
Plan completo: vault → `09 - Plataforma Cesar OS/🛠️ Plan de Implementación por Fases`.

## 🛡️ Notas
- Presupuesto mensual duro: configúralo por llave en `https://llm.TU_DOMINIO/ui`.
- LiteLLM y Open WebUI (Fase 1) hablarán SOLO con este gateway.
- Secretos: en Fase 7 migramos a Infisical; por ahora `.env` (fuera de git).
