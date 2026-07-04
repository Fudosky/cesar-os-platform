"""Colector de cerebro: contexto/recordatorios vía buscar_cerebro (cerebro-mcp).

Usa el cliente MCP oficial (streamable-http). SOLO la colección PÚBLICA `vault`
(la guarda dura vive en cerebro-mcp; este colector nunca puede tocar vault_private).
"""
import asyncio
import json
from maestro_briefing import config as c

QUERIES = [
    "prioridades estratégicas y proyecto de vida de Cesar",
    "recordatorios o compromisos importantes de Cesar",
]


async def _query(pregunta, top_k):
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client
    async with streamablehttp_client(c.CEREBRO_MCP) as (r, w, _):
        async with ClientSession(r, w) as s:
            await s.initialize()
            res = await s.call_tool("buscar_cerebro", {"pregunta": pregunta, "top_k": top_k})
            hits = []
            for ci in (res.content or []):
                t = getattr(ci, "text", "") or ""
                try:
                    hits.append(json.loads(t))
                except Exception:
                    pass
            return hits


def collect(top: int = 2):
    try:
        blocks = []
        for q in QUERIES:
            hits = asyncio.run(_query(q, top))
            if hits:
                fuentes = ", ".join(sorted({h.get("fuente", "?") for h in hits})[:3])
                snippet = (hits[0].get("texto", "") or "").strip().replace("\n", " ")[:180]
                blocks.append("• %s → %s (fuentes: %s)" % (q, snippet, fuentes))
        if not blocks:
            return ("Cerebro", "Sin contexto relevante hoy.", True)
        return ("Cerebro", "\n".join(blocks), True)
    except Exception as e:
        return ("Cerebro", "⚠️ Cerebro no disponible: %s" % e, False)


if __name__ == "__main__":
    n, b, ok = collect()
    print("OK=%s\n%s" % (ok, b))
