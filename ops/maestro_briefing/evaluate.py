"""Evaluador: valida el RESULTADO antes de enviar. Devuelve (ok, razon).

Filosofía: verificar el resultado real, no el status. Si algo huele mal, NO enviar
un briefing malo — fallar ruidoso (el orquestador avisa 🔴 a Telegram).
"""
BANNED = ["as an ai", "i cannot", "i'm sorry", "lorem ipsum", "todo:", "<placeholder", "tbd"]
ACTION_HINTS = ["acción", "acciones", "top 3", "top3", "🎯"]


def evaluate(briefing: str, model: str):
    t = (briefing or "").strip()
    low = t.lower()
    if len(t) < 120:
        return False, "briefing demasiado corto (%d chars)" % len(t)
    if "claude" not in (model or "").lower() and "opus" not in (model or "").lower():
        return False, "modelo inesperado (%s) — posible fallback silencioso a Groq" % model
    if not any(k in low for k in ACTION_HINTS):
        return False, "sin sección de acciones (Top 3)"
    for b in BANNED:
        if b in low:
            return False, "contiene texto prohibido: %s" % b
    return True, "ok"


if __name__ == "__main__":
    good = "🌅 Briefing\n1) resumen...\n🎯 TOP 3 ACCIONES\n1. hacer X\n2. hacer Y\n3. hacer Z\n⚠️ alertas..."
    print("caso bueno:", evaluate(good, "claude-opus-4-8"))
    print("caso corto:", evaluate("muy corto", "claude-opus-4-8"))
    print("caso fallback:", evaluate("largo con acciones 🎯 top 3 " * 20, "llama-3.3-70b-versatile"))
    print("caso sin acciones:", evaluate("un resumen largo sin nada accionable " * 10, "claude-opus-4-8"))
