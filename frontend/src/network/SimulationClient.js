// src/network/SimulationClient.js
//
// Thin WebSocket wrapper around the backend's state broadcast
// (plasmaforge/server/websocket_handler.py). This is the ONLY file in
// the frontend allowed to know about the wire protocol (JSON shape of
// SimulationState.to_dict()) — scene code should only ever see the
// parsed callback payload, never raw WebSocket frames.
//
// Not connected by default from main.js yet (see the comment there) —
// the globe runs fully standalone on its placeholder animation until a
// backend is actually running. Flip the flag in main.js when you want
// to test against a live server.

import { WS_URL } from "../config/constants.js";

export class SimulationClient {
  constructor({ url = WS_URL, onState, onConnect, onDisconnect } = {}) {
    this.url = url;
    this.onState = onState || (() => {});
    this.onConnect = onConnect || (() => {});
    this.onDisconnect = onDisconnect || (() => {});
    this._socket = null;
    this._reconnectDelayMs = 1000;
    this._shouldReconnect = true;
  }

  connect() {
    this._socket = new WebSocket(this.url);

    this._socket.addEventListener("open", () => {
      this._reconnectDelayMs = 1000; // reset backoff on successful connect
      this.onConnect();
    });

    this._socket.addEventListener("message", (event) => {
      try {
        const state = JSON.parse(event.data);
        this.onState(state);
      } catch (err) {
        console.error("[SimulationClient] Failed to parse state message:", err);
      }
    });

    this._socket.addEventListener("close", () => {
      this.onDisconnect();
      if (this._shouldReconnect) this._scheduleReconnect();
    });

    this._socket.addEventListener("error", () => {
      // The 'close' event fires right after 'error' for WebSocket, so
      // reconnect logic lives solely in the close handler to avoid
      // double-scheduling reconnects.
      console.warn("[SimulationClient] WebSocket error");
    });
  }

  _scheduleReconnect() {
    setTimeout(() => {
      if (this._shouldReconnect) this.connect();
    }, this._reconnectDelayMs);
    // Exponential backoff, capped at 10s, so a persistently-down backend
    // doesn't spam reconnect attempts.
    this._reconnectDelayMs = Math.min(this._reconnectDelayMs * 1.5, 10000);
  }

  /** Sends a control message to the backend, e.g. a mode switch:
   * client.send({ type: "set_mode", mode: "storm" }) */
  send(message) {
    if (this._socket && this._socket.readyState === WebSocket.OPEN) {
      this._socket.send(JSON.stringify(message));
    }
  }

  disconnect() {
    this._shouldReconnect = false;
    this._socket?.close();
  }
}
