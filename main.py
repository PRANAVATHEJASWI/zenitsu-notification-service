from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import requests
import os
import threading
import time
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

RENDER_URL = "https://zenitsu-notification-service.onrender.com"


# ─── Keep-Alive Background Thread ──────────────────────────────────────

def keep_alive_loop():
    """Ping self every 5 minutes to prevent Render sleep."""
    while True:
        try:
            response = requests.get(f"{RENDER_URL}/health", timeout=5)
            print(f"[keep-alive] Ping successful: {response.status_code}")
        except Exception as e:
            print(f"[keep-alive] Ping failed: {e}")
        time.sleep(300)  # 5 minutes


# Start keep-alive thread on startup
keep_alive_thread = threading.Thread(target=keep_alive_loop, daemon=True)
keep_alive_thread.start()
print("[startup] Keep-alive thread started")


# ─── Endpoints ─────────────────────────────────────────────────────────

@app.get("/health")
def health():
    """Health check endpoint. Ping this to keep Render awake."""
    return {"status": "healthy", "timestamp": time.time()}


@app.get("/wake")
def wake():
    """Ping endpoint to wake Render before sending notification."""
    return {"status": "awake", "timestamp": time.time()}


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
        print(f"[notify] Message sent: {r.status_code}")
        return {"status": "sent", "telegram_status": r.status_code}
    except Exception as e:
        print(f"[notify] Error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.get("/")
def root():
    """Root endpoint for UptimeRobot monitoring."""
    return {
        "service": "zenitsu-notification-service",
        "status": "running",
        "endpoints": ["/health", "/wake", "/notify"]
    }

@app.head("/")
async def health_head():
    return Response(status_code=200)
    
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=10000)
