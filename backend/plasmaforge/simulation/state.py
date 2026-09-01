"""
SimulationState: a lightweight, serialization-friendly snapshot of "what
the frontend needs to render right now".
"""

from __future__ import annotations

from dataclasses import dataclass, field

# The simulation runs in a normalized unit sphere of radius ~1.0 (see
# backend/plasmaforge/config/constants.py's GLOBE_RADIUS). At that
# scale, 3 decimal places of precision (millimeter-equivalent detail)
# is already far beyond what's visually distinguishable on screen — but
# a raw Python float serializes to JSON with up to ~17 significant
# digits by default. Rounding before sending cuts the bytes-per-number
# roughly in half with zero visible difference, which matters a lot
# when this gets sent for every point of every filament, many times a
# second, to every connected browser — see settings.py's
# state_broadcast_hz comment for the other half of this bandwidth fix.
_COORD_PRECISION = 3


def _round_point(point: tuple[float, float, float]) -> list[float]:
    return [round(c, _COORD_PRECISION) for c in point]


@dataclass
class FilamentSnapshot:
    # Ordered chain of points for the main path — the frontend spline-
    # smooths this into a wavy curve, which is why it needs to stay an
    # ORDERED chain rather than flat unordered pairs.
    main_points: list[tuple[float, float, float]]
    # Flat [start, end, start, end, ...] pairs for branch sparks, kept
    # separate and unsmoothed since they're meant to look like abrupt
    # little offshoots, not part of the main wavy arc.
    branch_points: list[tuple[float, float, float]]


@dataclass
class SimulationState:
    tick: int
    sim_time_s: float
    mode: str
    particle_positions: list[tuple[float, float, float]] = field(default_factory=list)
    filaments: list[FilamentSnapshot] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "tick": self.tick,
            "sim_time_s": round(self.sim_time_s, _COORD_PRECISION),
            "mode": self.mode,
            "particles": [_round_point(p) for p in self.particle_positions],
            "filaments": [
                {
                    "main": [_round_point(p) for p in f.main_points],
                    "branches": [_round_point(p) for p in f.branch_points],
                }
                for f in self.filaments
            ],
        }