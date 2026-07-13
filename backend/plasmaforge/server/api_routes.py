"""
HTTP API routes: currently just a health check and a couple of read-only
config endpoints. This exists as a separate file from app.py so route
definitions don't clutter the app bootstrap/wiring code, and so this can
grow (e.g. REST endpoints for recorded sessions) without app.py growing
with it.
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
    """Read-only view of non-sensitive runtime settings, useful for the
    frontend to confirm what mode/backend it's talking to on connect."""
    return {
        "default_mode": settings.default_mode,
        "physics_backend": settings.physics_backend,
        "state_broadcast_hz": settings.state_broadcast_hz,
    }
