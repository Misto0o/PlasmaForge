// src/utils/mathUtils.js
//
// Small, generic math helpers for the frontend. Mirrors the existence of
// backend/plasmaforge/utils/math_helpers.py conceptually, but is not the
// same file — frontend and backend utils have no shared dependency, by
// design, to keep the two halves of the project independently buildable.

export function clamp(value, lo, hi) {
  return Math.max(lo, Math.min(hi, value));
}

export function lerp(a, b, t) {
  return a + (b - a) * t;
}

/** Random point uniformly distributed on the surface of a unit sphere,
 * scaled by `radius`. Useful for placeholder/demo filament endpoints
 * before real simulation data is flowing in. */
export function randomPointOnSphere(radius = 1) {
  const u = Math.random();
  const v = Math.random();
  const theta = 2 * Math.PI * u;
  const phi = Math.acos(2 * v - 1);
  return {
    x: radius * Math.sin(phi) * Math.cos(theta),
    y: radius * Math.sin(phi) * Math.sin(theta),
    z: radius * Math.cos(phi),
  };
}
