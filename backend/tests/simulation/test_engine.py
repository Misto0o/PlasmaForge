"""
Integration-style test for SimulationEngine: does advancing the
simulation over many ticks produce sane, non-exploding, non-NaN state.
This is intentionally coarse-grained compared to the physics unit tests —
it's a smoke test for "does the whole pipeline hang together", not a
correctness proof for any individual piece.
"""

import math

from plasmaforge.simulation.engine import SimulationEngine


def test_engine_advances_without_nan_or_explosion():
    engine = SimulationEngine(mode_name="classic")
    engine.particle_system.spawn(position=(0.1, 0.0, 0.0), velocity=(0.0, 0.05, 0.0))

    for _ in range(120):  # ~1 second of sim time at the default rate
        state = engine.advance(wall_dt=1.0 / 60.0)

    for pos in state.particle_positions:
        assert all(math.isfinite(c) for c in pos)
        # Particles should stay contained within (a small margin around)
        # the globe radius thanks to _contain_within_globe().
        radius = math.sqrt(sum(c * c for c in pos))
        assert radius <= 1.05


def test_mode_switch_resets_filaments():
    engine = SimulationEngine(mode_name="classic")
    engine.advance(wall_dt=0.1)
    assert len(engine.mode.filaments) > 0
    engine.switch_mode("classic")
    # After a fresh on_enter(), filament count should be back to the
    # configured default rather than accumulating across switches.
    from plasmaforge.config import constants
    assert len(engine.mode.filaments) == constants.DEFAULT_FILAMENT_COUNT
