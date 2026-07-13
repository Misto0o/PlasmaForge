"""
Unit tests for the Cython vector_math module, exercised through its
Python wrappers (py_distance, py_normalize). These are correctness tests
against known analytical results — the kind of test that would catch a
sign error or an off-by-one introduced during a "harmless" refactor of
the .pyx file.
"""

import math

from plasmaforge.physics import vector_math


def test_distance_between_identical_points_is_zero():
    assert vector_math.py_distance(0, 0, 0, 0, 0, 0) == 0.0


def test_distance_matches_known_3_4_5_triangle():
    # A 3-4-12 right-triangle-in-3D case with a clean integer answer,
    # chosen specifically so this test doesn't need an epsilon comparison.
    assert vector_math.py_distance(0, 0, 0, 3, 4, 12) == 13.0


def test_normalize_returns_unit_length_vector():
    x, y, z = vector_math.py_normalize(3, 4, 0)
    length = math.sqrt(x * x + y * y + z * z)
    assert math.isclose(length, 1.0, abs_tol=1e-9)


def test_normalize_zero_vector_does_not_explode():
    # Degenerate input should return a safe zero vector, not NaN/inf —
    # this guards the epsilon check inside vec3_normalize.
    x, y, z = vector_math.py_normalize(0, 0, 0)
    assert (x, y, z) == (0.0, 0.0, 0.0)
