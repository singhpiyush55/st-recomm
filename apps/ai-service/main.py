"""
Stock Recommender — AI Service (FastAPI).
Entry point: uvicorn main:app --reload --port 8000
"""

import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.health import router as health_router
from routers.pipeline import router as pipeline_router

# ── Environment ─────────────────────────────────────────────────────
load_dotenv()

# ── Logging ─────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
)

# ── App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Stock Recommender AI Service",
    version="0.1.0",
    description="Multi-agent pipeline for stock analysis and recommendations.",
)

# CORS — allow the Express API (port 4000) and Next.js dev (port 3000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:4000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ─────────────────────────────────────────────────────────
app.include_router(health_router, tags=["health"])
app.include_router(pipeline_router, prefix="/pipeline", tags=["pipeline"])


# ── Startup / Shutdown ──────────────────────────────────────────────
@app.on_event("startup")
async def on_startup():
    logging.getLogger(__name__).info("AI Service started")


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
