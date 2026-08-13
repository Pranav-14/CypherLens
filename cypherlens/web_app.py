"""
CypherLens Web Radar Backend 2.0 (FastAPI + Conversational Chat API + Multi-Currency + BYOK Auth)
"""

import os
import uvicorn
from typing import Dict, Any, Optional
from fastapi import FastAPI, Query, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from cypherlens.engines.chat_session import CypherChatSession
from cypherlens.engines.currency import CurrencyConverter
from cypherlens.engines.geo_resolver import GeoResolver
from cypherlens.engines.ai_provider import AIProviderManager

app = FastAPI(
    title="CypherLens Conversational Web Radar",
    description="Conversational Web Intelligence, Cross-Border Price Radar & Transit Hub",
    version="2.0.0"
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Active chat sessions in memory
SESSIONS: Dict[str, CypherChatSession] = {}

app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def get_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.post("/api/chat")
async def chat_endpoint(payload: Dict[str, Any] = Body(...)):
    """
    Multi-turn conversational chat endpoint.
    Payload: { "message": "...", "session_id": "...", "region": "de", "currency": "EUR" }
    """
    message = payload.get("message", "").strip()
    session_id = payload.get("session_id", "default_session")
    region = payload.get("region", "de")
    currency = payload.get("currency", "EUR")

    if not message:
        return JSONResponse(status_code=400, content={"error": "Message cannot be empty."})

    # Get or create session
    if session_id not in SESSIONS:
        SESSIONS[session_id] = CypherChatSession(session_id=session_id, region=region, currency=currency)

    session = SESSIONS[session_id]
    session.set_region(region)
    session.set_currency(currency)

    try:
        response = session.process_message(message)
        return JSONResponse(content=response)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "message": "Chat operation interrupted."})


@app.post("/api/chat/reset")
async def reset_chat_endpoint(payload: Dict[str, Any] = Body(...)):
    session_id = payload.get("session_id", "default_session")
    if session_id in SESSIONS:
        SESSIONS[session_id].reset()
    return {"status": "ok", "message": "Session reset."}


@app.get("/api/currencies")
async def get_currencies():
    """Returns supported currencies and exchange rates."""
    return CurrencyConverter.get_supported_currencies()


@app.get("/api/config")
async def get_config():
    """Loads local AI provider configuration."""
    cfg = AIProviderManager.load_config()
    # Mask API key for security
    key = cfg.get("api_key", "")
    masked_key = f"{key[:4]}...{key[-4:]}" if len(key) > 8 else ("Set" if key else "")
    return {
        "provider": cfg.get("provider", "zero_key"),
        "has_api_key": bool(key),
        "masked_key": masked_key,
        "model": cfg.get("model", "gemini-1.5-flash"),
        "default_currency": cfg.get("default_currency", "EUR"),
        "default_region": cfg.get("default_region", "de")
    }


@app.post("/api/config")
async def save_config_endpoint(payload: Dict[str, Any] = Body(...)):
    """Saves user BYOK API key and settings."""
    provider = payload.get("provider", "gemini")
    api_key = payload.get("api_key", "")
    model = payload.get("model", "gemini-1.5-flash")
    currency = payload.get("default_currency", "EUR")
    region = payload.get("default_region", "de")

    saved = AIProviderManager.save_config(
        provider=provider,
        api_key=api_key,
        model=model,
        default_currency=currency,
        default_region=region
    )
    return {"status": "ok", "message": "Configuration saved successfully.", "provider": saved["provider"]}


@app.get("/api/health")
async def health_check():
    return {"status": "online", "system": "CypherLens 2.0 Conversational Matrix", "version": "2.0.0"}


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Starts the Uvicorn web server."""
    uvicorn.run(app, host=host, port=port, log_level="info")
