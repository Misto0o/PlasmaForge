"""
ParticleSystem: owns and updates a pool of Particle objects as batched
numpy arrays rather than a Python list of objects on the hot path.

Why numpy arrays instead of iterating Particle dataclasses: the
integration kernel (physics.particle_integration) expects contiguous
(N, 3) arrays it can mutate in place. Converting a list of dataclasses to
that layout every tick would itself become the bottleneck at particle
counts in the thousands. So the "source of truth" position/velocity/age
data lives in numpy arrays here; Particle objects (if needed for
non-hot-path code, e.g. inspection/debugging) can be materialized from
them on demand — see `to_particles()`.
"""

from __future__ import annotations

import numpy as np

from plasmaforge.config import constants
from plasmaforge.physics import particle_integration
from plasmaforge.simulation.particles.particle import Particle


class ParticleSystem:
    def __init__(self, max_particles: int = constants.DEFAULT_MAX_PARTICLES):
        self.max_particles = max_particles
        self.positions = np.zeros((0, 3), dtype=np.float64)
        self.velocities = np.zeros((0, 3), dtype=np.float64)
        self.charges = np.zeros((0,), dtype=np.float64)
        self.masses = np.zeros((0,), dtype=np.float64)
        self.ages = np.zeros((0,), dtype=np.float64)

    @property
    def count(self) -> int:
        return self.positions.shape[0]

    def spawn(
        self,
        position: tuple[float, float, float],
        velocity: tuple[float, float, float] = (0.0, 0.0, 0.0),
        charge: float = constants.PARTICLE_CHARGE,
        mass: float = constants.PARTICLE_MASS,
    ) -> None:
        """Adds one particle. Called infrequently relative to `step()`, so
        the per-call array concatenation cost here is acceptable; if spawn
        rate ever becomes hot, switch to a preallocated ring buffer."""
        if self.count >= self.max_particles:
            return
        self.positions = np.vstack([self.positions, np.array(position, dtype=np.float64)])
        self.velocities = np.vstack([self.velocities, np.array(velocity, dtype=np.float64)])
        self.charges = np.append(self.charges, charge)
        self.masses = np.append(self.masses, mass)
        self.ages = np.append(self.ages, 0.0)

    def step(
        self, dt: float, source_charge_positions: np.ndarray, source_charge_values: np.ndarray
    ) -> None:
        """
        Advances every particle by one timestep under the field produced by
        `source_charge_positions`/`source_charge_values` (e.g. the central
        electrode and any active filament tips), then despawns anything
        past PARTICLE_MAX_AGE_S. The actual field+integration+containment
        math is a single fused Cython call (physics.particle_integration)
        that mutates positions/velocities in place — this method is just
        the bookkeeping around that call (aging, despawn).
        """
        if self.count == 0:
            return

        # Ensure contiguous C-order float64 arrays — the Cython kernel
        # takes raw memoryviews over these buffers and mutates them
        # directly, so non-contiguous views (e.g. from fancy indexing
        # elsewhere) would silently corrupt state. np.ascontiguousarray
        # is a no-op (no copy) when already contiguous, which is the
        # common case here.
        self.positions = np.ascontiguousarray(self.positions, dtype=np.float64)
        self.velocities = np.ascontiguousarray(self.velocities, dtype=np.float64)

        particle_integration.integrate_particles_py(
            self.positions,
            self.velocities,
            self.charges,
            self.masses,
            dt,
            source_charge_positions,
            source_charge_values,
            constants.GLOBE_RADIUS,
        )

        self.ages += dt
        self._despawn_expired()

    def _despawn_expired(self) -> None:
        """Removes any particle past PARTICLE_MAX_AGE_S. Without this,
        the ambient spawn trickle in ClassicMode would accumulate forever
        (up to max_particles) into a static-looking shell of dots rather
        than a lively, continuously-refreshing drift."""
        alive_mask = self.ages < constants.PARTICLE_MAX_AGE_S
        if np.all(alive_mask):
            return
        self.positions = self.positions[alive_mask]
        self.velocities = self.velocities[alive_mask]
        self.charges = self.charges[alive_mask]
        self.masses = self.masses[alive_mask]
        self.ages = self.ages[alive_mask]

    def to_particles(self) -> list[Particle]:
        """Materializes Particle objects for inspection/testing/debug
        tooling. Not used on the hot path."""
        return [
            Particle(x=p[0], y=p[1], z=p[2], vx=v[0], vy=v[1], vz=v[2], charge=q, mass=m)
            for p, v, q, m in zip(self.positions, self.velocities, self.charges, self.masses)
        ]
