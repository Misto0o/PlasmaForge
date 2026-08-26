"""
Application entrypoint: `python -m plasmaforge.server.app`

Single-port design: the WebSocket route lives on the SAME FastAPI app as
the HTTP endpoints (health/config), both served by one uvicorn process on
one port. This replaced an earlier two-port design (separate `websockets`
server on its own port) specifically so this deploys cleanly on
platforms like Render/Railway that only expose one external port per
service — see websocket_handler.py's module docstring for the full
rationale.
"""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, WebSocket

from plasmaforge.config.settings import settings
from plasmaforge.server.api_routes import router as api_router
from plasmaforge.server.websocket_handler import bind_engine, broadcast_loop, handle_client
from plasmaforge.simulation.engine import SimulationEngine

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("plasmaforge.server.app")

_engine = SimulationEngine(mode_name=settings.default_mode)
bind_engine(_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Starts the simulation broadcast loop as a background task when
    the app starts, and cancels it cleanly on shutdown. This is
    FastAPI's recommended replacement for the older startup/shutdown
    event decorators."""
    task = asyncio.create_task(broadcast_loop(_engine))
    logger.info("Simulation broadcast loop started")
    yield
    task.cancel()


app = FastAPI(title="PlasmaForge", version="0.1.0", lifespan=lifespan)
app.include_router(api_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """The single WebSocket route simulation state streams over, and
    control messages (touch point, mode switch) arrive on. Frontend
    should connect to wss://your-host/ws in production, ws://localhost:PORT/ws
    locally — see frontend/src/config/constants.js's WS_URL."""
    await handle_client(websocket)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level=settings.log_level.lower(),
    )