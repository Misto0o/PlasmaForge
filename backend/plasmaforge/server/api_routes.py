"""
HTTP API routes: health check and read-only config info.
"""

from __future__ import annotations

from fastapi import APIRouter

from plasmaforge import __version__
from plasmaforge.config.settings import settings

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {"status": "ok", "version": __version__}


@router.get("/config")
async def get_config() -> dict:
    return {
        "default_mode": settings.default_mode,
        "physics_backend": settings.physics_backend,
        "state_broadcast_hz": settings.state_broadcast_hz,
    }