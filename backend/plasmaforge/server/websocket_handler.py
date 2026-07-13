"""
WebSocket handler: streams SimulationState snapshots to connected browser
clients at settings.state_broadcast_hz, and receives control messages
(mode switches, reset, etc.) from clients.

Uses the `websockets` library directly rather than a full framework,
since the server's job is narrow (stream state, accept a few control
commands) — see requirements.txt for why FastAPI is used for HTTP
endpoints instead, keeping the two concerns on separate, well-understood
libraries rather than forcing everything through one.
"""

from __future__ import annotations

import asyncio
import json
import logging

import websockets

from plasmaforge.config.settings import settings
from plasmaforge.simulation.engine import SimulationEngine

logger = logging.getLogger("plasmaforge.server.websocket")

_CONNECTED_CLIENTS: set[websockets.WebSocketServerProtocol] = set()

# Set once at server startup (see server/app.py). Kept as module state
# rather than threaded through every function call because there is
# exactly one engine per server process — see docs/architecture.md's note
# that server/ owns a single long-lived engine.
_engine: SimulationEngine | None = None


def bind_engine(engine: SimulationEngine) -> None:
    """Called once from app.py at startup so control messages (touch
    point, mode switches) have something to act on."""
    global _engine
    _engine = engine


async def handle_client(websocket: websockets.WebSocketServerProtocol) -> None:
    """Registers a client for broadcast and listens for control messages
    (e.g. {"type": "set_mode", "mode": "storm"}) until it disconnects."""
    _CONNECTED_CLIENTS.add(websocket)
    logger.info("Client connected (%d total)", len(_CONNECTED_CLIENTS))
    try:
        async for raw_message in websocket:
            await _handle_control_message(raw_message)
    except websockets.ConnectionClosed:
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
    at a fixed rate, forever. Runs as one of the server's background
    tasks — see app.py."""
    interval = 1.0 / settings.state_broadcast_hz
    while True:
        state = engine.advance(interval)
        if _CONNECTED_CLIENTS:
            payload = json.dumps(state.to_dict())
            await asyncio.gather(
                *(client.send(payload) for client in list(_CONNECTED_CLIENTS)),
                return_exceptions=True,
            )
        await asyncio.sleep(interval)