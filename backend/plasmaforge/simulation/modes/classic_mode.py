from __future__ import annotations
import random
from plasmaforge.config import constants
from plasmaforge.physics.filament import Filament, spawn_filament
from plasmaforge.simulation.modes.base_mode import SimulationMode
from plasmaforge.simulation.particles.particle_system import ParticleSystem

PARTICLE_SPAWN_INTERVAL_S = 0.15
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
        use_touch = self.touch_target is not None and self.rng.random() < TOUCH_BIAS_PROBABILITY
        # Origin is now a random point on the ELECTRODE's surface, not
        # always the exact center (0,0,0). At high filament counts,
        # every arc starting from one identical point made them braid
        # together into a dense tangle right at the middle — spreading
        # origins across the electrode surface is what a real plasma
        # ball's arcs actually do (they emerge from around the
        # electrode, not from one infinitesimal point), and untangles
        # that central mess.
        origin = tuple(c * constants.ELECTRODE_RADIUS for c in _random_unit_vector(self.rng))
        return spawn_filament(
            origin=origin,
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
        self.filaments = [f for f in self.filaments if f.alive]
        while len(self.filaments) < constants.DEFAULT_FILAMENT_COUNT:
            self.filaments.append(self._spawn_filament())
        self._spawn_ambient_particles(dt, particle_system)

    def _spawn_ambient_particles(self, dt: float, particle_system: ParticleSystem) -> None:
        self._time_since_last_particle_spawn += dt
        if self._time_since_last_particle_spawn < PARTICLE_SPAWN_INTERVAL_S:
            return
        self._time_since_last_particle_spawn = 0.0
        if particle_system.count >= particle_system.max_particles:
            return
        radius = constants.ELECTRODE_RADIUS * 1.5
        direction = _random_unit_vector(self.rng)
        position = tuple(c * radius for c in direction)
        speed = self.rng.uniform(0.05, 0.15)
        velocity = tuple(c * speed for c in direction)
        particle_system.spawn(position=position, velocity=velocity,
                               charge=constants.PARTICLE_CHARGE * 0.2)

    def get_charge_sources(self) -> list[tuple[tuple[float, float, float], float]]:
        return [(f.tip, constants.PARTICLE_CHARGE * 0.5) for f in self.filaments if f.alive]

def _random_unit_vector(rng: random.Random) -> tuple[float, float, float]:
    x, y, z = rng.gauss(0, 1), rng.gauss(0, 1), rng.gauss(0, 1)
    norm = max((x * x + y * y + z * z) ** 0.5, 1e-9)
    return (x / norm, y / norm, z / norm)