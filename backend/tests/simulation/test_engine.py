import math
from plasmaforge.simulation.engine import SimulationEngine


def test_engine_advances_without_nan_or_explosion():
    engine = SimulationEngine(mode_name="classic")
    engine.particle_system.spawn(position=(0.1, 0.0, 0.0), velocity=(0.0, 0.05, 0.0))
    for _ in range(120):
        state = engine.advance(wall_dt=1.0 / 60.0)
    for pos in state.particle_positions:
        assert all(math.isfinite(c) for c in pos)
        radius = math.sqrt(sum(c * c for c in pos))
        assert radius <= 1.05


def test_mode_switch_resets_filaments():
    engine = SimulationEngine(mode_name="classic")
    engine.advance(wall_dt=0.1)
    assert len(engine.mode.filaments) > 0
    engine.switch_mode("classic")
    from plasmaforge.config import constants

    assert len(engine.mode.filaments) == constants.DEFAULT_FILAMENT_COUNT


def test_snapshot_produces_valid_main_and_branch_points():
    """New: confirms the split main/branch snapshot format actually
    produces well-formed data for the frontend to consume."""
    engine = SimulationEngine(mode_name="classic")
    state = engine.advance(wall_dt=0.05)
    assert len(state.filaments) > 0
    for f in state.filaments:
        assert len(f.main_points) >= 2  # at least a start and an end
        assert len(f.branch_points) % 2 == 0
