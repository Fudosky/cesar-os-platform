#!/usr/bin/env python3
# Cerebro-MCP: expone la busqueda del cerebro PUBLICO de Cesar al Maestro (Hermes) via MCP.
# PROTECCION MAXIMA: solo la coleccion "vault" (publica). NUNCA vault_private.
import os
# Forzar coleccion publica ANTES de importar conocimiento.config
os.environ["CONOCIMIENTO_COLLECTION"] = "vault"
import sys
sys.path.insert(0, "/root/telegram-claude")
from conocimiento import search, config  # noqa: E402
from mcp.server.fastmcp import FastMCP  # noqa: E402
from mcp.server.transport_security import TransportSecuritySettings  # noqa: E402

# Guarda dura de arranque: si por lo que sea no es la publica, no levantar.
assert config.COLLECTION == "vault", "Cerebro-MCP DEBE usar solo la coleccion publica 'vault'"

# Servicio solo-red-interna (no expuesto a internet) -> la proteccion anti-DNS-rebinding
# (que solo permite localhost) sobra y bloquea a Hermes. La desactivamos.
mcp = FastMCP("cerebro", transport_security=TransportSecuritySettings(
    enable_dns_rebinding_protection=False))
mcp.settings.host = "0.0.0.0"
mcp.settings.port = int(os.environ.get("CEREBRO_MCP_PORT", "8090"))


@mcp.tool()
def buscar_cerebro(pregunta: str, top_k: int = 5, carpeta: str = "") -> list:
    """Busca en el cerebro de conocimiento de Cesar: 30 anios de documentos profesionales
    (calidad, comercial, six sigma, normas electricas, MBA, DEXSON, etc.), coleccion PUBLICA.
    Devuelve fragmentos relevantes con su fuente para responder fundamentado y citando.
    Usar cuando la pregunta se beneficie del conocimiento/experiencia de Cesar.

    Args:
        pregunta: la consulta en lenguaje natural.
        top_k: cuantos fragmentos traer (default 5).
        carpeta: opcional, limitar a un dominio (ej. 'Gestion de Calidad', 'MBA', 'RETIE').
    """
    # Log de prueba: cada llamada del Maestro queda registrada (query + resultados).
    print("[LLAMADA] buscar_cerebro pregunta=%r carpeta=%r top_k=%d" % (pregunta, carpeta, top_k), flush=True)
    # Guarda dura en cada llamada: jamas la coleccion privada.
    if config.COLLECTION != "vault":
        raise RuntimeError("Cerebro-MCP: coleccion no publica -> abortado por seguridad")
    try:
        hits = search.buscar(pregunta, top_k=top_k, folder=(carpeta or None))
    except Exception as e:  # fallar ruidoso, nunca datos inventados
        raise RuntimeError("Cerebro no disponible: %s" % str(e)[:150])
    print("[RESULTADO] %d fragmentos | top: %s" % (len(hits), (hits[0].get("source", "-") if hits else "ninguno")), flush=True)
    return [
        {"fuente": h.get("source", ""), "carpeta": h.get("folder", ""),
         "score": round(h.get("score", 0.0), 3), "texto": (h.get("text", "") or "")[:1200]}
        for h in hits
    ]


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
