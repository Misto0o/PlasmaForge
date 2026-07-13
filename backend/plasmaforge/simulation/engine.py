"""
SimulationEngine: the core fixed-timestep loop that ties physics + a
SimulationMode + particle system together and produces SimulationState
snapshots. This is the one class server/websocket_handler.py talks to; it
has no idea a WebSocket exists.

Fixed timestep rationale: plasma filament timing (lifetimes measured in
tenths of a second) needs to look consistent regardless of render/network
framerate, so the engine steps physics at a fixed rate
(config.constants.FIXED_TIMESTEP_S) and accumulates leftover time across
calls to `advance()`, rather than stepping once per wall-clock frame.
"""

from __future__ import annotations

import numpy as np

from plasmaforge.config import constants
from plasmaforge.config.settings import settings
from plasmaforge.simulation.modes.base_mode import SimulationMode
from plasmaforge.simulation.modes.classic_mode import ClassicMode
from plasmaforge.simulation.particles.particle_system import ParticleSystem
from plasmaforge.simulation.state import FilamentSnapshot, SimulationState
from plasmaforge.utils.profiler import profiled_section

# Mode registry. Deliberately a plain dict, not a plugin/entry-point
# system — with a handful of modes, that indirection isn't earning its
# keep yet. Revisit if third-party/plugin modes become a real need.
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

        # The central electrode is the sole field source for now. As
        # filaments gain charge (once filament growth is field-driven),
        # their tips will be appended here each tick too.
        self._electrode_position = np.array([[0.0, 0.0, 0.0]], dtype=np.float64)
        self._electrode_charge = np.array([5.0], dtype=np.float64)

    def switch_mode(self, mode_name: str) -> None:
        """Swaps the active mode at runtime. Exists as a first-class
        operation because mode switching is expected to be a user-facing
        feature (a UI control), not just a startup-time choice."""
        mode_cls = _MODE_REGISTRY.get(mode_name)
        if mode_cls is None:
            raise ValueError(f"Unknown simulation mode: {mode_name!r}")
        self.mode.on_exit(self.particle_system)
        self.mode = mode_cls()
        self.mode.on_enter(self.particle_system)

    def set_touch_point(self, position: tuple[float, float, float]) -> None:
        """Called from the WebSocket control-message handler when the
        frontend reports a cursor/finger position on the glass (raycast
        result). Forwarded to the active mode, which decides how to react
        (ClassicMode pulls new filaments toward it) — the engine itself
        has no opinion on what "touch" means for a given mode."""
        self.mode.touch_target = position

    def clear_touch_point(self) -> None:
        """Called when the touch/cursor is released. Filaments already
        mid-flight toward the old touch point still finish their natural
        lifetime — this only affects newly spawned ones."""
        self.mode.touch_target = None

    def advance(self, wall_dt: float) -> SimulationState:
        """
        Advances the simulation by `wall_dt` seconds of wall-clock time,
        internally taking however many fixed `self.dt` substeps that
        represents (clamped by MAX_SUBSTEPS_PER_TICK to avoid runaway
        catch-up after a stall, e.g. a debugger breakpoint or GC pause).
        Returns the resulting state snapshot.
        """
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
        """
        Combines the fixed central electrode with whatever extra charge
        sources the active mode contributes this tick (e.g. filament tips
        — see SimulationMode.get_charge_sources). This is the one place
        "everything that pushes on particles" gets assembled, so adding a
        new kind of charge source later (a second electrode? a user's
        tracked hand, eventually) means implementing get_charge_sources
        somewhere, not touching this method's structure.
        """
        positions = [self._electrode_position[0]]
        charges = [self._electrode_charge[0]]
        for pos, charge in self.mode.get_charge_sources():
            positions.append(pos)
            charges.append(charge)
        return np.array(positions, dtype=np.float64), np.array(charges, dtype=np.float64)

    def _snapshot(self) -> SimulationState:
        filaments = []
        # ClassicMode-specific attribute access here is a known, temporary
        # layering shortcut — see TODO below.
        mode_filaments = getattr(self.mode, "filaments", [])
        for f in mode_filaments:
            points = []
            for seg in f.segments:
                points.append(seg.start)
                points.append(seg.end)
            filaments.append(FilamentSnapshot(points=points))

        return SimulationState(
            tick=self.tick,
            sim_time_s=self.sim_time_s,
            mode=self.mode.name,
            particle_positions=[tuple(p) for p in self.particle_system.positions],
            filaments=filaments,
        )

# TODO(architecture): `_snapshot` reaching into `self.mode.filaments` is a
# short-term shortcut — it assumes every mode exposes `.filaments`, which
# isn't part of the SimulationMode interface. Once a second mode without
# filaments exists, add a `mode.get_render_data()` hook to the base class
# instead of growing this getattr pattern.