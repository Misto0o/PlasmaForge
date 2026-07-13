"""
Application entrypoint: `python -m plasmaforge.server.app`

Wires together the FastAPI HTTP app (health/config endpoints), the
WebSocket state-broadcast server, and one long-lived SimulationEngine
instance. This is intentionally the only file in the project that starts
event loops / binds ports — everything it depends on (engine, handlers)
is plain, testable Python/asyncio with no process-startup side effects
of its own.
"""

from __future__ import annotations

import asyncio
import logging

import uvicorn
import websockets
from fastapi import FastAPI

from plasmaforge.config.settings import settings
from plasmaforge.server.api_routes import router as api_router
from plasmaforge.server.websocket_handler import bind_engine, broadcast_loop, handle_client
from plasmaforge.simulation.engine import SimulationEngine

logging.basicConfig(level=settings.log_level)
logger = logging.getLogger("plasmaforge.server.app")

app = FastAPI(title="PlasmaForge", version="0.1.0")
app.include_router(api_router)


async def _run_websocket_server(engine: SimulationEngine) -> None:
    async with websockets.serve(handle_client, settings.host, settings.port + 1):
        logger.info("WebSocket server listening on %s:%d", settings.host, settings.port + 1)
        await broadcast_loop(engine)


async def _run_http_server() -> None:
    config = uvicorn.Config(app, host=settings.host, port=settings.port,
                             log_level=settings.log_level.lower())
    server = uvicorn.Server(config)
    logger.info("HTTP server listening on %s:%d", settings.host, settings.port)
    await server.serve()


async def main() -> None:
    engine = SimulationEngine(mode_name=settings.default_mode)
    bind_engine(engine)  # so WebSocket control messages (touch, mode switch) can reach it
    # HTTP (health/config) and WebSocket (simulation stream) run as two
    # servers on adjacent ports rather than multiplexed on one, since that
    # keeps each protocol's library (uvicorn vs websockets) doing what
    # it's actually good at instead of forcing WS-over-ASGI complexity in
    # early development. Revisit if deployment wants a single port.
    await asyncio.gather(
        _run_http_server(),
        _run_websocket_server(engine),
    )


if __name__ == "__main__":
    asyncio.run(main())