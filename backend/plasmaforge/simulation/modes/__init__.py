"""
Simulation mode registry.

A "mode" (classic globe, storm, calm/idle, future audio-reactive, etc.)
is a class implementing the SimulationMode interface in base_mode.py.
engine.py holds exactly one active mode and calls its lifecycle hooks;
it has no if/elif chain of mode-specific behavior. This is the extension
point mentioned in docs/architecture.md for "multiple simulation modes".
"""
