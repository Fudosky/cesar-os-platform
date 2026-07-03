import sys, os, time, json, urllib.request, urllib.parse
sys.path.insert(0, "/root/telegram-claude")
from conocimiento import manifest, config, store, summary, relate, brain_note

LOG = "/root/data/conocimiento/resumir_monitor.log"
DONE_MARK = "/root/data/conocimiento/resumir_monitor.DONE"
RATE = 0.029        # $/doc (empirico: 582 docs = ~$17)
CAP_USD = 80.0      # tope duro de seguridad (esperado ~$42)
SAVE_EVERY = 25
CHECK_OPUS_EVERY = 50


def log(msg):
    line = "%s | %s" % (time.strftime("%Y-%m-%dT%H:%M:%S"), msg)
    print(line, flush=True)
    try:
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _secret(name):
    try:
        for ln in open("/root/.secrets/.env"):
            ln = ln.strip()
            if ln.startswith(name + "="):
                return ln.split("=", 1)[1]
    except Exception:
        pass
    return ""


def notify(msg):
    tok = _secret("TELEGRAM_TOKEN")
    if not tok:
        return
    try:
        data = urllib.parse.urlencode({"chat_id": "8632566831", "text": msg}).encode()
        urllib.request.urlopen("https://api.telegram.org/bot%s/sendMessage" % tok, data=data, timeout=15)
    except Exception:
        pass


def opus_alive():
    key = os.environ.get("LITELLM_MASTER_KEY", "")
    try:
        req = urllib.request.Request(
            "http://litellm:4000/v1/chat/completions",
            data=json.dumps({"model": "opus", "messages": [{"role": "user", "content": "ok"}], "max_tokens": 3}).encode(),
            headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
        r = json.load(urllib.request.urlopen(req, timeout=25))
        m = (r.get("model") or "").lower()
        return ("opus" in m or "claude" in m), m
    except Exception as e:
        return False, str(e)[:80]


man = manifest.load(config.MANIFEST_PATH)
todo = [k for k, v in man.items() if v.get("chunks", 0) > 0 and "\U0001F3AF" not in (v.get("summary") or "")]
total = len(todo)
t0 = time.time()
log("INICIO: %d docs pendientes | tope $%.0f | guarda cada %d" % (total, CAP_USD, SAVE_EVERY))

ok, m = opus_alive()
if not ok:
    log("ABORTO: Opus NO disponible antes de empezar (%s). Cero gasto." % m)
    notify("Cerebro: NO arranque los resumenes, Opus no responde (%s). Cero gasto." % m)
    sys.exit(1)
log("Opus verificado (%s). Arrancando." % m)
notify("Cerebro: arranco resumenes expertos de %d docs (~$%.0f est.). Te aviso el avance." % (total, total * RATE))

done = errs = 0
aborted = False
for i, key in enumerate(todo, 1):
    if i % CHECK_OPUS_EVERY == 1 and i > 1:
        ok, m = opus_alive()
        if not ok:
            log("ABORTO en %d/%d: Opus cayo (%s). Guardo y salgo." % (i, total, m))
            manifest.save(config.MANIFEST_PATH, man)
            notify("Cerebro: PARE en %d/%d (~$%.2f) porque Opus cayo (credito?). Lo ya hecho quedo guardado, no se re-paga." % (i - 1, total, done * RATE, ))
            aborted = True
            break
    if done * RATE > CAP_USD:
        log("TOPE ~$%.2f > $%.0f en %d. Guardo y salgo." % (done * RATE, CAP_USD, i))
        manifest.save(config.MANIFEST_PATH, man)
        notify("Cerebro: PARE por tope de seguridad (~$%.0f) en %d/%d. Revisar." % (CAP_USD, i, total))
        aborted = True
        break
    meta = man.get(key)
    title = meta.get("title", "") if meta else ""
    try:
        text = "\n".join(t for t in store.texts_for_path(meta.get("path", key)) if t)[:8000]
        if not text:
            continue
        meta["summary"] = summary.summarize(text, title)
        meta["related"] = relate.related(text, title, meta.get("path", key))
        done += 1
    except Exception as e:
        errs += 1
        log("error %d (%s): %s" % (i, title[:40], str(e)[:90]))
    if i % SAVE_EVERY == 0:
        manifest.save(config.MANIFEST_PATH, man)
        pct = 100.0 * i / total
        log("PROGRESO %d/%d (%.0f%%) | hechos=%d errs=%d | ~$%.2f | %.0f min" % (i, total, pct, done, errs, done * RATE, (time.time() - t0) / 60))
    if i in (int(total * 0.25), int(total * 0.5), int(total * 0.75)):
        notify("Cerebro %d%%: %d/%d docs, ~$%.2f gastado, %.0f min." % (int(100.0 * i / total), i, total, done * RATE, (time.time() - t0) / 60))

manifest.save(config.MANIFEST_PATH, man)
brain_note.write(man)
open(DONE_MARK, "w").write("done=%d errs=%d total=%d\n" % (done, errs, total))
mins = (time.time() - t0) / 60
log("FIN: hechos=%d errs=%d de %d | ~$%.2f | %.0f min. Nota regenerada." % (done, errs, total, done * RATE, mins))
if not aborted:
    notify("Cerebro AL 100%%: %d resumenes expertos listos (errs=%d), ~$%.2f, %.0f min. DEXSON ya esta en tu nota Obsidian." % (done, errs, done * RATE, mins))
