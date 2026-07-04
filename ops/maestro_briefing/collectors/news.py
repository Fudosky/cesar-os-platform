"""Colector de noticias: RSS/Atom del sector, ítems recientes. SOLO stdlib (sin feedparser).

Parsea RSS 2.0 y Atom con xml.etree; fechas RFC822 (RSS) o ISO8601 (Atom).
Tolerante a fallos: un feed caído se salta; nunca rompe el briefing.
"""
import urllib.request
import datetime
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from maestro_briefing import config as c


def _local(tag):
    return tag.split("}")[-1].lower()


def _child_text(elem, *names):
    for ch in elem:
        if _local(ch.tag) in names:
            return (ch.text or "").strip()
    return ""


def _parse_date(raw):
    if not raw:
        return None
    try:
        return parsedate_to_datetime(raw)          # RFC822 (RSS)
    except Exception:
        pass
    try:
        return datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))  # ISO (Atom)
    except Exception:
        return None


def _feed_items(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (MaestroBriefing)"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        xml_bytes = r.read()
    root = ET.fromstring(xml_bytes)
    src = ""
    for el in root.iter():
        if _local(el.tag) == "title":
            src = (el.text or "").strip()[:40]
            break
    items = []
    for el in root.iter():
        if _local(el.tag) in ("item", "entry"):
            title = _child_text(el, "title")
            raw = _child_text(el, "pubdate", "published", "updated", "date")
            if title:
                items.append((title, _parse_date(raw)))
    return src, items


def collect(max_per_feed=3, hours=48):
    if not c.RSS_FEEDS:
        return ("Noticias", "⚠️ Noticias no disponible: feeds no configurados", False)
    cutoff = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=hours)
    out = []
    for url in c.RSS_FEEDS:
        try:
            src, items = _feed_items(url)
            n = 0
            for title, dt in items:
                if dt is not None:
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.timezone.utc)
                    if dt < cutoff:
                        continue
                out.append("- [%s] %s" % (src, title))
                n += 1
                if n >= max_per_feed:
                    break
        except Exception:
            continue
    if not out:
        return ("Noticias", "Sin titulares recientes del sector.", True)
    return ("Noticias", "\n".join(out[:15]), True)


if __name__ == "__main__":
    n, b, ok = collect()
    print("OK=%s\n%s" % (ok, b))
