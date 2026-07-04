"""Extracción LOCAL: pypdf (con descifrado) -> texto -> líneas-candidato. El PDF NO sale del VPS."""
import io
import re
import sys
sys.path.insert(0, "/opt/data/pylibs")
import pypdf

# montos: 26,994,985.88  /  29.700.000,00  /  USD 1,234.56
_MONEY = re.compile(r"\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{2})?|(?:USD|COP|MXN|EUR|\$)\s?[\d.,]{3,}", re.IGNORECASE)
_KEYS = ("saldo", "total", "valor de cartera", "valor cartera", "net asset",
         "posición", "posicion", "disponible", "patrimonio", "cupo", "abono", "cargo")


def pdf_text(raw: bytes, password: str = "") -> str:
    reader = pypdf.PdfReader(io.BytesIO(raw))
    if reader.is_encrypted:   # extractos BBVA CO vienen cifrados (cédula)
        if not password or reader.decrypt(password) == 0:
            raise RuntimeError("PDF cifrado: contraseña ausente o incorrecta")
    return "\n".join((p.extract_text() or "") for p in reader.pages)


def candidate_lines(text: str, max_lines: int = 20):
    """Solo las líneas con montos o keywords -> lo MÍNIMO que verá el LLM."""
    out = []
    for line in text.splitlines():
        L = line.strip()
        if not L:
            continue
        if _MONEY.search(L) or any(k in L.lower() for k in _KEYS):
            out.append(L[:120])
        if len(out) >= max_lines:
            break
    return out


if __name__ == "__main__":
    print("extract.py — helper de extracción local (pypdf)")
