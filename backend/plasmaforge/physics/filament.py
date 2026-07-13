"""
Plasma filament generation.

Filament growth direction is now driven by real field math: each new
filament's outward direction is biased away from the tips of currently
active filaments, computed via physics.electric_field.compute_field_grid
treating each active tip as a small repelling charge. This is what makes
filaments visually spread apart around the globe instead of clustering
randomly — the same behavior a real plasma globe shows, where an existing
arc "claims" its region and pushes new streamers elsewhere.

Deliberately still plain Python (not Cython) at the orchestration level:
this module calls into the Cython electric_field kernel for the actual
field sum, but filament-level bookkeeping (spawning, aging, branching)
runs at a scale (single digits of filaments) far below where Cython
would earn its complexity cost. See docs/development.md.
"""

from __future__ import annotations

import random

import numpy as np
from dataclasses import dataclass, field

from plasmaforge.config import constants
from plasmaforge.physics import filament_growth


@dataclass
class FilamentSegment:
    """One straight segment of a branching filament."""
    start: tuple[float, float, float]
    end: tuple[float, float, float]
    age_s: float = 0.0
    lifetime_s: float = constants.FILAMENT_MIN_LIFETIME_S


@dataclass
class Filament:
    """A single plasma streamer: a chain of segments from the electrode
    outward toward the globe's inner surface, with occasional branches."""
    segments: list[FilamentSegment] = field(default_factory=list)
    alive: bool = True
    # The main path's intended endpoint, set once at spawn time. Kept
    # separate from "segments[-1].end" because branch segments can be
    # appended after the main path segments in the list — relying on
    # list order to find the tip would occasionally return a branch's
    # endpoint instead of the actual filament tip.
    target: tuple[float, float, float] = (0.0, 0.0, 0.0)

    def step(self, dt: float) -> None:
        """Ages every segment and kills any that exceed their lifetime.
        This is what gives filaments their flickering, restless look."""
        for seg in self.segments:
            seg.age_s += dt
        self.segments = [s for s in self.segments if s.age_s < s.lifetime_s]
        if not self.segments:
            self.alive = False

    @property
    def tip(self) -> tuple[float, float, float]:
        """The outermost point of this filament's main path — used as a
        repelling charge source when computing where the NEXT filament
        should grow."""
        return self.target


def _repulsion_biased_direction(candidate_directions: np.ndarray,
                                 other_tips: list[tuple[float, float, float]],
                                 rng: random.Random) -> np.ndarray:
    """
    Given several candidate outward directions (points on the target
    sphere), picks the one furthest from where plasma is already active,
    using physics.filament_growth.select_best_candidate_py — a Cython
    function that scores every candidate against every existing filament
    tip's field contribution in one fused C loop, rather than allocating
    a full field-vector array and doing the argmin back in Python/numpy.
    """
    if not other_tips:
        # No other filaments active yet — nothing to repel from, pick
        # uniformly at random among the candidates.
        idx = rng.randrange(len(candidate_directions))
        return candidate_directions[idx]

    tips = np.array(other_tips, dtype=np.float64)
    best_idx = filament_growth.select_best_candidate_py(candidate_directions, tips)
    return candidate_directions[best_idx]


def spawn_filament(origin: tuple[float, float, float],
                    target_radius: float,
                    other_tips: list[tuple[float, float, float]] | None = None,
                    touch_target: tuple[float, float, float] | None = None,
                    rng: random.Random | None = None,
                    n_candidates: int = 12) -> Filament:
    """
    Creates a new filament starting at `origin` (typically the electrode
    surface) and growing outward toward `target_radius` (the inner globe
    wall), as a JAGGED multi-segment path with occasional short branches
    (see `_build_jagged_path`) rather than a single straight line — this
    is what makes filaments read as lightning instead of laser beams.

    If `touch_target` is set (a point on/near the glass surface, reported
    by the frontend from where the user is pointing/touching), the
    filament's overall endpoint is the touch point instead of a
    repulsion-chosen direction — this is the real-plasma-ball behavior
    where touching the glass visibly draws the arc to your finger. The
    touch point dominates completely while active, matching how a real
    device behaves: one arc locks onto the touch point rather than
    competing with repulsion from other filaments. The jaggedness/branch
    logic is identical either way — only the target point differs.

    Without an active touch, the endpoint is chosen from `n_candidates`
    random points on the target sphere, biased away from `other_tips` via
    real field repulsion (see `_repulsion_biased_direction`).
    """
    rng = rng or random.Random()
    other_tips = other_tips or []

    if touch_target is not None:
        tx, ty, tz = touch_target
        norm = max((tx * tx + ty * ty + tz * tz) ** 0.5, 1e-9)
        # Small per-filament jitter so multiple simultaneous filaments
        # converge near the touch point without perfectly overlapping —
        # a real plasma ball's arc has some visible width/wobble even
        # when locked onto a finger, not a single infinitely thin line.
        jitter = 0.03
        end = (
            tx / norm * target_radius + rng.uniform(-jitter, jitter),
            ty / norm * target_radius + rng.uniform(-jitter, jitter),
            tz / norm * target_radius + rng.uniform(-jitter, jitter),
        )
    else:
        # Sample several candidate outward directions on the sphere, then
        # let the field math pick the one furthest from existing plasma.
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
    """
    Builds a jagged multi-segment path from `start` to `end` using the
    standard fractal-midpoint-displacement technique real lightning
    renderers use: walk from start to end in `n_segments` steps, and at
    each intermediate point add a random offset that shrinks as it
    approaches the target (so the path visibly converges on `end` rather
    than wandering indefinitely). At a few intermediate points, a short
    branch segment is added that doesn't reach the target — a small
    offshoot, matching how real electrical streamers fork.

    All segments share the same `lifetime` (and start at age 0) since the
    whole path is generated instantaneously at spawn time rather than
    animated growing over multiple ticks — a deliberate simplification;
    see docs/architecture.md's note on this being a placeholder-grade
    growth model, not a true dielectric-breakdown simulation.
    """
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
        # Jitter shrinks as t -> 1 so the path actually reaches `end`
        # instead of overshooting near the target.
        scale = jitter * (1.0 - t)
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
                                         lifetime_s=lifetime))
        # Branches only make sense from interior points (not the very
        # first or last), and are shorter-lived so they read as a quick
        # spark rather than a full second arc.
        is_interior_point = 0 < i < len(points) - 2
        if is_interior_point and rng.random() < branch_probability:
            branch_point = points[i + 1]
            branch_offset = (
                branch_point[0] + rng.uniform(-jitter * 2, jitter * 2),
                branch_point[1] + rng.uniform(-jitter * 2, jitter * 2),
                branch_point[2] + rng.uniform(-jitter * 2, jitter * 2),
            )
            segments.append(FilamentSegment(start=branch_point, end=branch_offset,
                                             lifetime_s=lifetime * 0.5))

    return segments


def _random_point_on_sphere(radius: float, rng: random.Random) -> tuple[float, float, float]:
    """Uniform random point on a sphere surface (not a cube-projected
    approximation) — using the standard normalized-Gaussian method avoids
    the pole-clustering bias naive lat/long sampling would introduce."""
    x, y, z = rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)
    norm = max((x * x + y * y + z * z) ** 0.5, 1e-9)
    return (x / norm * radius, y / norm * radius, z / norm * radius)