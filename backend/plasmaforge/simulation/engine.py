from __future__ import annotations

import numpy as np

from plasmaforge.config import constants
from plasmaforge.config.settings import settings
from plasmaforge.simulation.modes.base_mode import SimulationMode
from plasmaforge.simulation.modes.classic_mode import ClassicMode
from plasmaforge.simulation.particles.particle_system import ParticleSystem
from plasmaforge.simulation.state import FilamentSnapshot, SimulationState
from plasmaforge.utils.profiler import profiled_section

_MODE_REGISTRY: dict[str, type[SimulationMode]] = {
    "classic": ClassicMode,
}


class SimulationEngine:
    def __init__(self, mode_name: str | None = None):
        self.dt = constants.FIXED_TIMESTEP_S
        self._accumulated_time = 0.0
        self.tick = 0
        self.sim_time_s = 0.0

        self.particle_system = ParticleSystem()

        mode_name = mode_name or settings.default_mode
        mode_cls = _MODE_REGISTRY.get(mode_name, ClassicMode)
        self.mode: SimulationMode = mode_cls()
        self.mode.on_enter(self.particle_system)

        self._electrode_position = np.array([[0.0, 0.0, 0.0]], dtype=np.float64)
        self._electrode_charge = np.array([5.0], dtype=np.float64)

    def switch_mode(self, mode_name: str) -> None:
        mode_cls = _MODE_REGISTRY.get(mode_name)
        if mode_cls is None:
            raise ValueError(f"Unknown simulation mode: {mode_name!r}")
        self.mode.on_exit(self.particle_system)
        self.mode = mode_cls()
        self.mode.on_enter(self.particle_system)

    def set_touch_point(self, position: tuple[float, float, float]) -> None:
        self.mode.touch_target = position

    def clear_touch_point(self) -> None:
        self.mode.touch_target = None

    def advance(self, wall_dt: float) -> SimulationState:
        self._accumulated_time += wall_dt
        substeps = 0
        with profiled_section("engine.advance"):
            while self._accumulated_time >= self.dt and substeps < constants.MAX_SUBSTEPS_PER_TICK:
                self._step_once()
                self._accumulated_time -= self.dt
                substeps += 1

        return self._snapshot()

    def _step_once(self) -> None:
        self.mode.step(self.dt, self.particle_system)
        positions, charges = self._current_field_sources()
        self.particle_system.step(self.dt, positions, charges)
        self.tick += 1
        self.sim_time_s += self.dt

    def _current_field_sources(self) -> tuple[np.ndarray, np.ndarray]:
        positions = [self._electrode_position[0]]
        charges = [self._electrode_charge[0]]
        for pos, charge in self.mode.get_charge_sources():
            positions.append(pos)
            charges.append(charge)
        return np.array(positions, dtype=np.float64), np.array(charges, dtype=np.float64)

    def _snapshot(self) -> SimulationState:
        filaments = []
        mode_filaments = getattr(self.mode, "filaments", [])
        for f in mode_filaments:
            # main_path_points/branch_segment_pairs — see filament.py.
            # Sending the main path as an ORDERED chain (not flat pairs)
            # is what lets the frontend spline-smooth it into a wavy
            # curve instead of a jagged straight-segment polyline.
            filaments.append(
                FilamentSnapshot(
                    main_points=f.main_path_points,
                    branch_points=f.branch_segment_pairs,
                )
            )

        return SimulationState(
            tick=self.tick,
            sim_time_s=self.sim_time_s,
            mode=self.mode.name,
            particle_positions=[tuple(p) for p in self.particle_system.positions],
            filaments=filaments,
        )
