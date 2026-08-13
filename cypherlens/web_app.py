"""
CypherLens Web Radar Backend (FastAPI + Static Dashboard)
"""

import os
import uvicorn
from fastapi import FastAPI, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from cypherlens.engines.orchestrator import CypherOrchestrator

app = FastAPI(
    title="CypherLens Web Radar",
    description="Real-Time Web Search Simplifier & Price Radar",
    version="1.0.0"
)

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Mount static folder
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def get_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


@app.get("/api/search")
async def search_endpoint(
    q: str = Query(..., description="Search prompt"),
    category: str = Query("auto", description="Intelligence lens: auto, amazon, flight, tech, general"),
    max_results: int = Query(8, description="Maximum results count")
):
    try:
        response = CypherOrchestrator.scout(q, category=category, max_results=max_results)
        return JSONResponse(content=response.model_dump())
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e), "message": "Failed to scout web results."})


@app.get("/api/health")
async def health_check():
    return {"status": "online", "system": "CypherLens Radar Matrix", "version": "1.0.0"}


def start_server(host: str = "127.0.0.1", port: int = 8000):
    """Starts the Uvicorn web server."""
    uvicorn.run(app, host=host, port=port, log_level="info")
