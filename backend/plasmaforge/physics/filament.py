"""
Plasma filament generation.

Filament growth direction is driven by real field math: each new
filament's outward direction is biased away from the tips of currently
active filaments, computed via physics.filament_growth — a fused Cython
loop that scores candidate directions against every other active
filament's field contribution.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

import numpy as np

from plasmaforge.config import constants
from plasmaforge.physics import filament_growth


@dataclass
class FilamentSegment:
    """One straight segment of a branching filament."""
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    age_s: float = 0.0
    lifetime_s: float = constants.FILAMENT_MIN_LIFETIME_S
    # True for short offshoot sparks that don't continue the main path
    # toward the target — see _build_jagged_path. The frontend uses this
    # to render the main path as a smooth curve and branches as sharp
    # little sparks, rather than treating everything identically.
    is_branch: bool = False


@dataclass
class Filament:
    """A single plasma streamer: a chain of segments from the electrode
    outward toward the globe's inner surface, with occasional branches."""
    segments: list[FilamentSegment] = field(default_factory=list)
    alive: bool = True
    target: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def step(self, dt: float) -> None:
        for seg in self.segments:
            seg.age_s += dt
        self.segments = [s for s in self.segments if s.age_s < s.lifetime_s]
        if not self.segments:
            self.alive = False

    @property
    def tip(self) -> tuple[float, float, float]:
        return self.target

    @property
    def main_path_points(self) -> list[tuple[float, float, float]]:
        """
        The continuous chain of points forming the main path (excludes
        branch segments), in order from origin to current endpoint. This
        is what the frontend spline-smooths into a wavy curve — sending
        it as an ordered point chain (rather than flat segment pairs)
        is what makes that possible; a flat pairs list loses the
        "these are consecutive" information a spline needs.
        """
        main_segments = [s for s in self.segments if not s.is_branch]
        if not main_segments:
            return []
        points = [main_segments[0].start]
        points.extend(s.end for s in main_segments)
        return points

    @property
    def branch_segment_pairs(self) -> list[tuple[float, float, float]]:
        """Flat [start, end, start, end, ...] pairs for branch segments
        only — rendered as sharp little sparks on the frontend, not
        smoothed (they're short and meant to look like abrupt offshoots,
        not part of the main wavy arc)."""
        points: list[tuple[float, float, float]] = []
        for s in self.segments:
            if s.is_branch:
                points.append(s.start)
                points.append(s.end)
        return points


def spawn_filament(origin: tuple[float, float, float],
                    target_radius: float,
                    other_tips: list[tuple[float, float, float]] | None = None,
                    touch_target: tuple[float, float, float] | None = None,
                    rng: random.Random | None = None,
                    n_candidates: int = 12) -> Filament:
    rng = rng or random.Random()
    other_tips = other_tips or []

    if touch_target is not None:
        tx, ty, tz = touch_target
        norm = max((tx * tx + ty * ty + tz * tz) ** 0.5, 1e-9)
        jitter = 0.03
        end = (
            tx / norm * target_radius + rng.uniform(-jitter, jitter),
            ty / norm * target_radius + rng.uniform(-jitter, jitter),
            tz / norm * target_radius + rng.uniform(-jitter, jitter),
        )
    else:
        candidates = np.array([
            _random_point_on_sphere(target_radius, rng) for _ in range(n_candidates)
        ])
        chosen = _repulsion_biased_direction(candidates, other_tips, rng)
        end = (float(chosen[0]), float(chosen[1]), float(chosen[2]))

    lifetime = rng.uniform(constants.FILAMENT_MIN_LIFETIME_S,
                            constants.FILAMENT_MAX_LIFETIME_S)
    segments = _build_jagged_path(origin, end, rng, lifetime)
    return Filament(segments=segments, target=end)


def _build_jagged_path(start: tuple[float, float, float],
                        end: tuple[float, float, float],
                        rng: random.Random,
                        lifetime: float,
                        n_segments: int = constants.FILAMENT_PATH_SEGMENTS,
                        jitter: float = constants.FILAMENT_JITTER,
                        branch_probability: float = constants.FILAMENT_BRANCH_PROBABILITY
                        ) -> list[FilamentSegment]:
    sx, sy, sz = start
    ex, ey, ez = end

    points: list[tuple[float, float, float]] = [start]
    for i in range(1, n_segments):
        t = i / n_segments
        base = (
            sx + (ex - sx) * t,
            sy + (ey - sy) * t,
            sz + (ez - sz) * t,
        )
        # Symmetric taper: zero right at the start (t=0) AND zero right
        # at the end (t=1), peaking in the middle (t=0.5). The previous
        # version was `jitter * (1.0 - t)` — maximal at the START and
        # shrinking toward the end. That meant every single filament's
        # chaotic zigzag was concentrated exactly at the electrode
        # (where every arc originates), which is what was producing a
        # dense tangled knot right at the center no matter how spread
        # out the origin points on the electrode surface were — the
        # jitter itself was doing the tangling, not the shared origin.
        # 4*t*(1-t) is a simple parabola: 0 at t=0, 1.0 at t=0.5, 0 at
        # t=1 — the chaos now happens along the MIDDLE of each arc's
        # length, where there's much more room for arcs to spread apart
        # visually, instead of all bunching where they start.
        scale = jitter * 4.0 * t * (1.0 - t)
        jittered = (
            base[0] + rng.uniform(-scale, scale),
            base[1] + rng.uniform(-scale, scale),
            base[2] + rng.uniform(-scale, scale),
        )
        points.append(jittered)
    points.append(end)

    segments: list[FilamentSegment] = []
    for i in range(len(points) - 1):
        segments.append(FilamentSegment(start=points[i], end=points[i + 1],
                                         lifetime_s=lifetime, is_branch=False))
        is_interior_point = 0 < i < len(points) - 2
        if is_interior_point and rng.random() < branch_probability:
            branch_point = points[i + 1]
            branch_offset = (
                branch_point[0] + rng.uniform(-jitter * 2, jitter * 2),
                branch_point[1] + rng.uniform(-jitter * 2, jitter * 2),
                branch_point[2] + rng.uniform(-jitter * 2, jitter * 2),
            )
            segments.append(FilamentSegment(start=branch_point, end=branch_offset,
                                             lifetime_s=lifetime * 0.5, is_branch=True))

    return segments


def _repulsion_biased_direction(candidate_directions: np.ndarray,
                                 other_tips: list[tuple[float, float, float]],
                                 rng: random.Random) -> np.ndarray:
    if not other_tips:
        idx = rng.randrange(len(candidate_directions))
        return candidate_directions[idx]

    tips = np.array(other_tips, dtype=np.float64)
    best_idx = filament_growth.select_best_candidate_py(candidate_directions, tips)
    return candidate_directions[best_idx]


def _random_point_on_sphere(radius: float, rng: random.Random) -> tuple[float, float, float]:
    x, y, z = rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)
    norm = max((x * x + y * y + z * z) ** 0.5, 1e-9)
    return (x / norm * radius, y / norm * radius, z / norm * radius)