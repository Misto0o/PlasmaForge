"""
SimulationState: a lightweight, serialization-friendly snapshot of "what
the frontend needs to render right now". This is deliberately decoupled
from the engine's internal representation (numpy arrays, Filament objects
with dataclass segments) — the engine's internals are optimized for
computation, this is optimized for "cheap to turn into JSON and send over
a WebSocket 60 times a second".

Keeping this separate means the engine's internal data structures can
change (e.g. switching particle storage to a different layout for GPU
compatibility) without touching the wire format, and vice versa.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class FilamentSnapshot:
    points: list[tuple[float, float, float]]


@dataclass
class SimulationState:
    tick: int
    sim_time_s: float
    mode: str
    particle_positions: list[tuple[float, float, float]] = field(default_factory=list)
    filaments: list[FilamentSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Plain-dict form for JSON serialization in the WebSocket handler.
        Kept as an explicit method (rather than relying on dataclasses.asdict
        everywhere) so the wire format can diverge intentionally from the
        Python structure later (e.g. flattening arrays for binary transport)."""
        return {
            "tick": self.tick,
            "sim_time_s": self.sim_time_s,
            "mode": self.mode,
            "particles": self.particle_positions,
            "filaments": [f.points for f in self.filaments],
        }
