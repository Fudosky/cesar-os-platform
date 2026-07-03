#!/usr/bin/env python3
# Reconcilia el manifest para DEXSON desde Qdrant (verdad de lo ya ingerido) + size/mtime
# de stage/DEXSON. NO re-embebe, NO re-resume, NO paga. Idempotente.
# DRY=1 -> solo reporta. Sin DRY -> aplica (con backup del manifest).
import os
import sys
import json
import shutil
import datetime
import requests

sys.path.insert(0, "/root/telegram-claude")
from conocimiento import config, manifest  # noqa: E402

FOLDER = "DEXSON"
DRY = os.environ.get("DRY", "0") == "1"


def qdrant_dexson_paths():
    url = f"{config.QDRANT_URL}/collections/{config.COLLECTION}/points/scroll"
    paths = {}
    offset = None
    while True:
        body = {"filter": {"must": [{"key": "folder", "match": {"value": FOLDER}}]},
                "with_payload": ["path", "title", "folder"], "limit": 1000}
        if offset is not None:
            body["offset"] = offset
        r = requests.post(url, json=body, timeout=120)
        r.raise_for_status()
        res = r.json()["result"]
        for p in res.get("points", []):
            pl = p.get("payload", {})
            pa = pl.get("path")
            if not pa:
                continue
            d = paths.setdefault(pa, {"chunks": 0, "title": pl.get("title", "")})
            d["chunks"] += 1
        offset = res.get("next_page_offset")
        if offset is None:
            break
    return paths


qp = qdrant_dexson_paths()
fragments = sum(v["chunks"] for v in qp.values())
man = manifest.load(config.MANIFEST_PATH)
today = datetime.date.today().isoformat()

added = already = no_stage = 0
for pa, meta in qp.items():
    if pa in man:
        already += 1
        continue
    staged = os.path.join(config.STAGE_DIR, pa)
    if not os.path.exists(staged):
        no_stage += 1
        continue
    st = os.stat(staged)
    if not DRY:
        man[pa] = {"folder": FOLDER,
                   "title": meta["title"] or os.path.basename(pa),
                   "path": pa, "indexed_at": today,
                   "size": st.st_size, "mtime": int(st.st_mtime),
                   "chunks": meta["chunks"],
                   "summary": "(reconciliado 2026-07-02 desde Qdrant - pendiente de resumen experto)"}
    added += 1

report = {"dexson_paths_en_qdrant": len(qp), "fragmentos": fragments,
          "ya_en_manifest": already, "a_agregar": added, "sin_staged": no_stage,
          "dry_run": DRY, "manifest_total_resultante": len(man)}
print(json.dumps(report, ensure_ascii=False))

if not DRY:
    bak = config.MANIFEST_PATH + ".bak-reconcile-" + datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    shutil.copy2(config.MANIFEST_PATH, bak)
    manifest.save(config.MANIFEST_PATH, man)
    print("APLICADO. backup:", bak)
