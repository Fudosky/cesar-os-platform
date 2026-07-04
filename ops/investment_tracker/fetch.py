"""Lee Hotmail vía Graph: mensajes que casan una fuente + descarga de adjuntos PDF."""
import json
import base64
import urllib.request
from msal import PublicClientApplication

_CID = "14d82eec-204b-4c2f-b7e8-296a70dab67e"
_AUTH = "https://login.microsoftonline.com/consumers"
_TOKEN = "/opt/data/outlook_token.json"
_GRAPH = "https://graph.microsoft.com/v1.0"


def _token():
    tok = json.load(open(_TOKEN))
    app = PublicClientApplication(_CID, authority=_AUTH)
    res = app.acquire_token_by_refresh_token(tok["refresh_token"], scopes=["Mail.Read"])
    if "access_token" not in res:
        raise RuntimeError("token Graph inválido (re-auth)")
    return res["access_token"]


def _get(path, token):
    req = urllib.request.Request(_GRAPH + path, headers={"Authorization": "Bearer " + token})
    return json.loads(urllib.request.urlopen(req, timeout=25).read())


def _matches(msg, src):
    frm = (msg.get("from", {}).get("emailAddress", {}) or {}).get("address", "").lower()
    subj = (msg.get("subject", "") or "").lower()
    if src.get("from_endswith") and not frm.endswith(src["from_endswith"]):
        return False
    if src.get("from_equals") and frm != src["from_equals"]:
        return False
    if src.get("subject_has") and src["subject_has"] not in subj:
        return False
    return True


def recent_for_source(src, top=60):
    """Devuelve (lista de msgs que casan, token)."""
    token = _token()
    q = ("/me/messages?%24top=" + str(top) +
         "&%24select=id,subject,from,receivedDateTime,hasAttachments,bodyPreview"
         "&%24orderby=receivedDateTime%20desc")
    msgs = _get(q, token).get("value", [])
    return [m for m in msgs if _matches(m, src)], token


def pdf_bytes(msg_id, token):
    """Descarga el primer adjunto PDF del mensaje (bytes) o None."""
    at = _get("/me/messages/%s/attachments" % msg_id, token).get("value", [])
    for a in at:
        if a.get("contentType") == "application/pdf" or (a.get("name", "").lower().endswith(".pdf")):
            if a.get("contentBytes"):
                return base64.b64decode(a["contentBytes"])
    return None
