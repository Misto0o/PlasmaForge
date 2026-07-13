"""
ClassicMode: the standard, always-on plasma globe behavior — a handful of
filaments continuously arcing from the central electrode to the glass,
with a light ambient particle drift. This is the mode the project should
default to and the one worth polishing first; other modes are variations
layered on top of this baseline once it feels right.
"""

from __future__ import annotations

import random

from plasmaforge.config import constants
from plasmaforge.physics.filament import Filament, spawn_filament
from plasmaforge.simulation.modes.base_mode import SimulationMode
from plasmaforge.simulation.particles.particle_system import ParticleSystem

# How often (in seconds) ClassicMode spawns one new ambient particle,
# while under the pool's max_particles cap. Kept slow and steady rather
# than bursty — a light drift, not a snowstorm.
PARTICLE_SPAWN_INTERVAL_S = 0.01

# Fraction of newly-spawned filaments that get pulled toward an active
# touch point, rather than ALL of them. A real plasma ball still has
# some flicker near the electrode even while you're touching the glass —
# it doesn't go fully dark elsewhere. 1.0 would mean "every new filament
# always targets the touch point"; this keeps some organic randomness.
TOUCH_BIAS_PROBABILITY = 0.7


class ClassicMode(SimulationMode):
    name = "classic"

    def __init__(self, rng: random.Random | None = None):
        super().__init__()
        self.rng = rng or random.Random()
        self.filaments: list[Filament] = []
        self._time_since_last_particle_spawn = 0.0

    def _spawn_filament(self) -> Filament:
        other_tips = [f.tip for f in self.filaments if f.alive]
        # Only bias THIS filament toward the touch point some of the
        # time (see TOUCH_BIAS_PROBABILITY) — keeps some arcs near the
        # electrode active even while the user is touching the glass,
        # instead of every single filament abandoning the center.
        use_touch = self.touch_target is not None and self.rng.random() < TOUCH_BIAS_PROBABILITY
        return spawn_filament(
            origin=(0.0, 0.0, 0.0),
            target_radius=constants.GLOBE_RADIUS * 0.95,
            other_tips=other_tips,
            touch_target=self.touch_target if use_touch else None,
            rng=self.rng,
        )

    def on_enter(self, particle_system: ParticleSystem) -> None:
        self.filaments = [self._spawn_filament() for _ in range(constants.DEFAULT_FILAMENT_COUNT)]
        self._time_since_last_particle_spawn = 0.0

    def step(self, dt: float, particle_system: ParticleSystem) -> None:
        for f in self.filaments:
            f.step(dt)

        # Replace any filaments that died of old age, keeping the count
        # roughly constant — this is what produces the classic "restless
        # flicker" look of a real plasma globe. Each replacement is aware
        # of the OTHER currently-alive tips, so it grows away from them.
        self.filaments = [f for f in self.filaments if f.alive]
        while len(self.filaments) < constants.DEFAULT_FILAMENT_COUNT:
            self.filaments.append(self._spawn_filament())

        self._spawn_ambient_particles(dt, particle_system)

    def _spawn_ambient_particles(self, dt: float, particle_system: ParticleSystem) -> None:
        """Trickles a slow, steady stream of low-charge particles in from
        near the electrode, giving the globe drifting motes in addition
        to the filament arcs — real plasma globes have both."""
        self._time_since_last_particle_spawn += dt
        if self._time_since_last_particle_spawn < PARTICLE_SPAWN_INTERVAL_S:
            return
        self._time_since_last_particle_spawn = 0.0

        if particle_system.count >= particle_system.max_particles:
            return

        # Spawn just outside the electrode with a small outward + tangential
        # velocity, so particles drift outward and curl rather than shooting
        # straight out — visually distinct from the filament arcs.
        radius = constants.ELECTRODE_RADIUS * 1.5
        direction = _random_unit_vector(self.rng)
        position = tuple(c * radius for c in direction)
        speed = self.rng.uniform(0.05, 0.15)
        velocity = tuple(c * speed for c in direction)
        particle_system.spawn(position=position, velocity=velocity,
                               charge=constants.PARTICLE_CHARGE * 0.2)

    def get_charge_sources(self) -> list[tuple[tuple[float, float, float], float]]:
        """
        Exposes each active filament's tip as a small repelling charge
        that the particle system's field calculation includes alongside
        the central electrode. This is what makes ambient particles
        visibly curl away from active arcs instead of drifting in a
        perfectly uniform radial field — the filaments and particles now
        share one real field, computed by the same Cython kernel.
        """
        return [(f.tip, constants.PARTICLE_CHARGE * 0.5) for f in self.filaments if f.alive]


def _random_unit_vector(rng: random.Random) -> tuple[float, float, float]:
    x, y, z = rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)
    norm = max((x * x + y * y + z * z) ** 0.5, 1e-9)
    return (x / norm, y / norm, z / norm)