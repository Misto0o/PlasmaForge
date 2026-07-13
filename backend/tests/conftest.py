"""
Shared pytest fixtures. Currently minimal — exists as the designated
location for fixtures once tests need shared setup (e.g. a seeded RNG
fixture for deterministic filament tests, or a pre-built ParticleSystem).
Adding fixtures here rather than duplicating setup in each test file is
the convention to follow as the test suite grows.
"""

import random

import pytest


@pytest.fixture
def seeded_rng() -> random.Random:
    """Deterministic RNG for tests that touch filament/particle spawning,
    so test failures are reproducible instead of flaky."""
    return random.Random(1234)
