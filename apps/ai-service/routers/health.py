"""
Health check endpoint — GET /health.
No auth required. Used by the Node API to verify the Python service is running.
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    return {"status": "ok"}
