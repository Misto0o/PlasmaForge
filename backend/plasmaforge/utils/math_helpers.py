"""
Generic math helpers that are not simulation-physics-specific (contrast
with physics/vector_math.pyx, which IS simulation-specific and
performance-critical). Things like easing/interpolation for smoothing
values sent to the frontend belong here.
"""

from __future__ import annotations


def clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    """Classic smoothstep, useful for fading effects (e.g. globe glow
    intensity ramping) without linear-interpolation harshness."""
    t = clamp((x - edge0) / (edge1 - edge0 + 1e-12), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)
