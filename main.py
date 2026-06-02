from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")


@app.get("/wake")
def wake():
    """Ping endpoint to wake Render before sending notification."""
    return {"status": "awake"}


@app.post("/notify")
async def notify(request: Request):
    """Receive message from HF Spaces and forward to Telegram."""
    body = await request.json()
    message = body.get("message", "")

    if not message:
        return JSONResponse({"error": "no message"}, status_code=400)

    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    try:
        r = requests.post(
            url,
            json={
                "chat_id": CHAT_ID,
                "text": message,
                "parse_mode": "Markdown",
            },
            timeout=30,
        )
        return {"status": "sent", "telegram_status": r.status_code}
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
