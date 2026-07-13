"""
Tests for ParticleSystem: the Cython-backed integration kernel
(physics.particle_integration) and the despawn-by-age behavior added
alongside it.
"""

import numpy as np

from plasmaforge.config import constants
from plasmaforge.simulation.particles.particle_system import ParticleSystem


def test_particle_moves_under_field_from_source():
    """A particle should accelerate away from a positive source charge —
    basic sanity check that the Cython integration kernel is actually
    applying a force, not just moving in a straight line."""
    system = ParticleSystem()
    system.spawn(position=(0.1, 0.0, 0.0), velocity=(0.0, 0.0, 0.0))

    source_positions = np.array([[0.0, 0.0, 0.0]])
    source_charges = np.array([5.0])

    initial_x = system.positions[0, 0]
    for _ in range(10):
        system.step(dt=1.0 / 120.0, source_charge_positions=source_positions,
                    source_charge_values=source_charges)

    # Repelled by the positive source at the origin, so it should have
    # moved further out along +x than where it started.
    assert system.positions[0, 0] > initial_x


def test_particles_despawn_after_max_age():
    system = ParticleSystem()
    system.spawn(position=(0.1, 0.0, 0.0))
    assert system.count == 1

    source_positions = np.array([[0.0, 0.0, 0.0]])
    source_charges = np.array([1.0])

    # Step well past PARTICLE_MAX_AGE_S in fixed increments.
    dt = 0.5
    steps = int(constants.PARTICLE_MAX_AGE_S / dt) + 5
    for _ in range(steps):
        system.step(dt=dt, source_charge_positions=source_positions,
                    source_charge_values=source_charges)

    assert system.count == 0


def test_particles_stay_contained_within_globe_radius():
    system = ParticleSystem()
    # Spawn with a large outward velocity so containment is actually
    # exercised within a handful of steps.
    system.spawn(position=(0.5, 0.0, 0.0), velocity=(5.0, 0.0, 0.0))

    source_positions = np.array([[0.0, 0.0, 0.0]])
    source_charges = np.array([1.0])

    for _ in range(30):
        system.step(dt=1.0 / 120.0, source_charge_positions=source_positions,
                    source_charge_values=source_charges)
        if system.count == 0:
            break  # could have aged out; not the point of this test

    if system.count > 0:
        radius = np.linalg.norm(system.positions[0])
        assert radius <= constants.GLOBE_RADIUS + 1e-6