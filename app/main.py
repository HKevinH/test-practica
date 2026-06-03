from typing import Any

from fastapi import Body, FastAPI


app = FastAPI(title="Chat Alert API", version="1.0.0")

ALERT_KEYWORDS = ("urgente", "error", "ayuda")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/webhook")
def webhook(payload: dict[str, Any] = Body(...)):
    candidate: Any = payload

    for key in ("body", "data", "json", "input"):
        if isinstance(candidate, dict) and key in candidate and isinstance(candidate[key], dict):
            candidate = candidate[key]

    message = str(candidate.get("message", "")).lower()
    alert = any(keyword in message for keyword in ALERT_KEYWORDS)
    return {"alert": alert}
