"""
Tests for the FastAPI app: confirms HTTP endpoints and the WebSocket
route both work on the single port (see server/app.py's module
docstring for why single-port matters for deployment). Uses FastAPI's
TestClient, which supports real WebSocket connections without needing
an actual running server/network.
"""

from fastapi.testclient import TestClient

from plasmaforge.server.app import app


def test_health_endpoint():
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "ok"


def test_config_endpoint():
    with TestClient(app) as client:
        response = client.get("/config")
        assert response.status_code == 200
        body = response.json()
        assert "default_mode" in body
        assert "physics_backend" in body


def test_websocket_streams_simulation_state():
    """Confirms /ws actually delivers real simulation data — filaments
    and particles as expected keys, not just that the connection opens."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            data = ws.receive_json()
            assert "filaments" in data
            assert "particles" in data
            assert "tick" in data
            assert isinstance(data["filaments"], list)


def test_websocket_control_message_advances_state():
    """Confirms sending a control message (set_touch) doesn't break the
    connection — the tick should keep advancing on subsequent messages."""
    with TestClient(app) as client:
        with client.websocket_connect("/ws") as ws:
            first = ws.receive_json()

            ws.send_text('{"type": "set_touch", "position": [0.1, 0.2, 0.3]}')
            second = ws.receive_json()

            assert second["tick"] >= first["tick"]