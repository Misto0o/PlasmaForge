// src/config/constants.js
//
// Frontend-side constants: rendering/visual tuning values that mirror
// (but are intentionally separate from) backend/plasmaforge/config/constants.py.
// They're not shared/imported across the Python/JS boundary because the
// two languages tune for different things — the backend's GLOBE_RADIUS
// is a simulation-space unit, this file's GLOBE_RADIUS is a Three.js
// world-space unit. Keeping them as separate, clearly-named constants
// avoids a fragile cross-language import mechanism for two numbers that
// happen to currently match.

export const GLOBE_RADIUS = 1.0;
export const ELECTRODE_RADIUS = 0.08;

// WebSocket URL for the simulation server. Reads from a Vite env
// variable (VITE_WS_URL) so production deploys can point at a real
// backend host instead of localhost — set this in Netlify's build
// environment settings once the backend is deployed (Render, Railway,
// Fly.io, etc.). Falls back to localhost for local development.
//
// Note the path: the backend now serves HTTP and WebSocket on the SAME
// port, with the WebSocket route at /ws (see backend/plasmaforge/server/app.py).
// An earlier version used a separate port (8766) with no path — that
// design doesn't work on most deployment platforms, which only expose
// one external port per service, so both the port and the /ws path
// changed together.
export const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8765/ws";

export const CAMERA = {
  fov: 45,
  near: 0.1,
  far: 100,
  initialDistance: 3.2,
};

export const COLORS = {
  background: 0x05060a,
  globeGlass: 0x88ccff,
  electrode: 0xffffff,
  // A more saturated/deeper purple than before — the previous shade
  // (0x9b30ff) washed toward pale pink/white once additively blended
  // with itself and bloom; this one has more "purple" to lose before it
  // reads as white.
  filament: 0x7a1fd6,
  filamentCore: 0xffffff,
  ambientLight: 0x223344,
};