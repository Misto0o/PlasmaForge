"""
WebSocket handler: streams SimulationState snapshots to connected browser
clients at settings.state_broadcast_hz, and receives control messages
(mode switches, touch point, etc.) from clients.

Rewritten to use FastAPI/Starlette's BUILT-IN WebSocket support (a route
on the same app as the HTTP endpoints) instead of a standalone
`websockets.serve()` server on its own port. Why this matters: most
simple deployment platforms (Render, Railway, and similar) only expose
ONE external port per service. Binding HTTP and WebSocket to two
separate ports works fine locally but makes the WebSocket half
unreachable once deployed to one of those platforms — this rewrite
avoids that entirely by putting everything behind the single port
uvicorn already serves.
"""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from plasmaforge.config.settings import settings
from plasmaforge.simulation.engine import SimulationEngine

logger = logging.getLogger("plasmaforge.server.websocket")

_CONNECTED_CLIENTS: set[WebSocket] = set()

# Set once at server startup (see server/app.py). Kept as module state
# rather than threaded through every function call because there is
# exactly one engine per server process.
_engine: SimulationEngine | None = None


def bind_engine(engine: SimulationEngine) -> None:
    """Called once from app.py at startup so control messages (touch
    point, mode switches) have something to act on."""
    global _engine
    _engine = engine


async def handle_client(websocket: WebSocket) -> None:
    """Accepts one client connection, registers it for broadcast, and
    listens for control messages (e.g. {"type": "set_touch", ...}) until
    it disconnects."""
    await websocket.accept()
    _CONNECTED_CLIENTS.add(websocket)
    logger.info("Client connected (%d total)", len(_CONNECTED_CLIENTS))
    try:
        while True:
            raw_message = await websocket.receive_text()
            await _handle_control_message(raw_message)
    except WebSocketDisconnect:
        pass
    finally:
        _CONNECTED_CLIENTS.discard(websocket)
        logger.info("Client disconnected (%d total)", len(_CONNECTED_CLIENTS))


async def _handle_control_message(raw_message: str) -> None:
    """Parses and applies a control message from a client. Kept as its
    own function (rather than inline in handle_client) so unit tests can
    exercise message handling without a real socket."""
    try:
        message = json.loads(raw_message)
    except json.JSONDecodeError:
        logger.warning("Ignoring malformed control message: %r", raw_message)
        return

    if _engine is None:
        logger.warning("Received control message before engine was bound: %r", message)
        return

    msg_type = message.get("type")
    if msg_type == "set_touch":
        position = message.get("position")
        if isinstance(position, list) and len(position) == 3:
            _engine.set_touch_point(tuple(float(c) for c in position))
        else:
            logger.warning("Malformed set_touch message: %r", message)
    elif msg_type == "clear_touch":
        _engine.clear_touch_point()
    elif msg_type == "set_mode":
        mode = message.get("mode")
        try:
            _engine.switch_mode(mode)
        except ValueError:
            logger.warning("Unknown mode requested: %r", mode)
    else:
        logger.debug("Ignoring unrecognized control message type: %r", msg_type)


async def broadcast_loop(engine: SimulationEngine) -> None:
    """Steps the simulation and broadcasts state to all connected clients
    at a fixed rate, forever. Runs as a background asyncio task started
    at app startup — see server/app.py."""
    interval = 1.0 / settings.state_broadcast_hz
    while True:
        state = engine.advance(interval)
        if _CONNECTED_CLIENTS:
            payload = json.dumps(state.to_dict())
            # send_text can raise if a client disconnected between the
            # `if _CONNECTED_CLIENTS` check and now — gather with
            # return_exceptions so one dead connection doesn't crash the
            # whole broadcast loop for everyone else.
            await asyncio.gather(
                *(client.send_text(payload) for client in list(_CONNECTED_CLIENTS)),
                return_exceptions=True,
            )
        await asyncio.sleep(interval)