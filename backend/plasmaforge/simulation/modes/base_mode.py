"""
SimulationMode: the interface every simulation mode (classic, storm, calm,
future audio-reactive, etc.) implements.

This exists so `simulation/engine.py` can hold a single `self.mode:
SimulationMode` and call generic hooks, instead of branching on a mode
enum throughout the engine. To add a new mode: implement this interface,
register it in modes/__init__.py's registry (added once that's needed),
and select it via config.settings.default_mode. The engine itself does
not change.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from plasmaforge.simulation.particles.particle_system import ParticleSystem


class SimulationMode(ABC):
    """Base class for all simulation modes."""

    name: str = "base"

    def __init__(self) -> None:
        # Set externally by the engine (see SimulationEngine.set_touch_point)
        # whenever the frontend reports a cursor/finger position on the
        # glass. None means "no active touch" — modes should fall back to
        # their normal behavior. This lives on the base class so every
        # mode gets touch support for free without repeating the
        # attribute, even if a given mode chooses to ignore it.
        self.touch_target: tuple[float, float, float] | None = None

    @abstractmethod
    def on_enter(self, particle_system: ParticleSystem) -> None:
        """Called once when this mode becomes active. Use this to set up
        initial filament/particle configuration for the mode."""
        raise NotImplementedError

    @abstractmethod
    def step(self, dt: float, particle_system: ParticleSystem) -> None:
        """Called every fixed timestep. Should perform mode-specific
        behavior (e.g. filament spawn rate, particle emission patterns)
        beyond the baseline physics integration the engine already does."""
        raise NotImplementedError

    def on_exit(self, particle_system: ParticleSystem) -> None:
        """Called once when switching away from this mode. Default no-op;
        override if a mode needs cleanup (most won't)."""
        return None

    def get_charge_sources(self) -> list[tuple[tuple[float, float, float], float]]:
        """
        Returns extra (position, charge) pairs this mode contributes to
        the field particles feel this tick — e.g. filament tips acting as
        small charges, so particles visibly swirl around active arcs
        instead of only feeling the central electrode.

        Default: no extra sources. The engine always includes the central
        electrode itself; this is purely additive. Override in a mode
        that has its own charge-bearing objects (see ClassicMode).
        """
        return []