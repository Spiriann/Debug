"""
Fix: bad_subject_keywords filter — comparación case-insensitive
"""

import requests
import json
from datetime import datetime, timezone

client_id = (GetVar("client_id") or "").strip()
tenant_id = (GetVar("tenant_id") or "").strip()
secret_id = (GetVar("secret_id") or "").strip()
mailbox = "asistente.contactcenter@alpina.com"

# ---- TOKEN ----
token_url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
token_data = {
    "client_id": client_id,
    "client_secret": secret_id,
    "scope": "https://graph.microsoft.com/.default",
    "grant_type": "client_credentials",
}
r = requests.post(token_url, data=token_data, timeout=30)
r.raise_for_status()
token = r.json()["access_token"]

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# ---- KEYWORDS A IGNORAR (DSN / BOUNCES) ----
bad_subject_keywords = [
    "error: la extraccion de datos no se pudo completar",
    "no se puede entregar:",
    "no se pudo entregar:",
    "[external] delivery status notification (failure)",
    "delivery status notification (failure)",
    "delivery status notification",
    "undeliverable",
    "mail delivery subsystem",
    "delivery has failed",
    "failure notice",
    "returned mail",
    "message not delivered",
    "couldn't be delivered",
    "non-delivery report",
    "nondelivery report",
    "mailbox unavailable",
    "recipient address rejected",
    "flow(s) have failed",
    "your flow(s) have failed",
    "a flow has failed",
    "flow has failed",
    "power automate",
    "powerapps",
    "embajador envió un mensaje",
    "envió un mensaje",
    "embajador",
]

# ---- FILTRO ANTI "CORREO RECIÉN NACIDO" ----
min_age_seconds = 120

# ---- LEER UNREAD ORDENADO VIEJO->NUEVO ----
url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/mailFolders/Inbox/messages"
params = {
    "$select": "id,subject,receivedDateTime",
    "$filter": "isRead eq false",
    "$orderby": "receivedDateTime asc",
    "$top": "50"
}

ids_ok = []

while True:
    resp = requests.get(url, headers=headers, params=params, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    for m in data.get("value", []):
        mid = m.get("id")
        subject = (m.get("subject") or "").strip()
        rdt = (m.get("receivedDateTime") or "").strip()

        if not mid:
            continue

        # ---- 1) Evitar procesar correos demasiado nuevos ----
        too_new = False
        if rdt:
            try:
                dt = datetime.fromisoformat(rdt.replace("Z", "+00:00"))
                age = (datetime.now(timezone.utc) - dt).total_seconds()
                if age < min_age_seconds:
                    too_new = True
            except:
                too_new = False

        if too_new:
            continue

        # ---- 2) Detectar si es correo "basura" (DSN/Undeliverable/etc.) ----
        subj_low = subject.lower()
        is_bad = any(kw in subj_low for kw in bad_subject_keywords)

        if is_bad:
            patch_url = f"https://graph.microsoft.com/v1.0/users/{mailbox}/messages/{mid}"
            patch_body = {"isRead": True}
            try:
                requests.patch(patch_url, headers=headers, data=json.dumps(patch_body), timeout=30)
            except:
                pass
            continue

        # ---- 3) Si pasa filtros, va al flujo normal ----
        ids_ok.append(mid)

    next_link = data.get("@odata.nextLink")
    if not next_link:
        break

    url = next_link
    params = None

SetVar("list_mails", ids_ok)
