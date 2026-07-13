"""
Unit tests for electric field computation, checked against Coulomb's law
computed independently in plain Python. This dual-implementation
comparison is the primary safety net for the Cython hot path: if
electric_field.pyx is ever "optimized" incorrectly, this test catches it
even though it doesn't know anything about Cython internals.
"""

import numpy as np

from plasmaforge.physics import electric_field


def _reference_field_at_point(point, charge_positions, charge_values):
    """Slow, obviously-correct pure-Python Coulomb's law sum — the ground
    truth this test compares the Cython implementation against."""
    ex = ey = ez = 0.0
    for pos, q in zip(charge_positions, charge_values):
        d = point - pos
        dist = np.linalg.norm(d)
        if dist < 1e-6:
            continue
        scale = q / dist**3
        ex += d[0] * scale
        ey += d[1] * scale
        ez += d[2] * scale
    return np.array([ex, ey, ez])


def test_field_matches_reference_implementation():
    rng = np.random.default_rng(42)
    points = rng.uniform(-1, 1, size=(5, 3))
    charge_positions = rng.uniform(-0.5, 0.5, size=(3, 3))
    charge_values = rng.uniform(0.5, 2.0, size=(3,))

    result = electric_field.compute_field_grid(
        points,
        charge_positions[:, 0].copy(),
        charge_positions[:, 1].copy(),
        charge_positions[:, 2].copy(),
        charge_values,
    )

    for i, point in enumerate(points):
        expected = _reference_field_at_point(point, charge_positions, charge_values)
        assert np.allclose(result[i], expected, atol=1e-8)


def test_field_at_single_positive_charge_points_outward():
    # A single positive charge at the origin: the field at (1, 0, 0)
    # should point in the +x direction — a basic sanity/direction check.
    points = np.array([[1.0, 0.0, 0.0]])
    charge_positions = np.array([0.0]), np.array([0.0]), np.array([0.0])
    result = electric_field.compute_field_grid(
        points, *charge_positions, np.array([1.0])
    )
    assert result[0, 0] > 0
    assert abs(result[0, 1]) < 1e-9
    assert abs(result[0, 2]) < 1e-9
