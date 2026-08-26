"""
SimulationState: a lightweight, serialization-friendly snapshot of "what
the frontend needs to render right now".
"""

from __future__ import annotations

from dataclasses import dataclass, field


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
            "sim_time_s": self.sim_time_s,
            "mode": self.mode,
            "particles": self.particle_positions,
            "filaments": [
                {"main": f.main_points, "branches": f.branch_points} for f in self.filaments
            ],
        }
