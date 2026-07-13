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
// environment settings once the backend is deployed somewhere (Railway,
// Render, Fly.io, etc.). Falls back to localhost for local development.
export const WS_URL = import.meta.env.VITE_WS_URL || "ws://localhost:8766";

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
  filament: 0x9b30ff,
  filamentCore: 0xffffff,
  ambientLight: 0x223344,
};