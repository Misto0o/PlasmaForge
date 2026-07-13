"""
Placeholder for offline frame/video export (e.g. "record 10 seconds of
this simulation as an mp4/gif"). Not wired up yet — exists so the
intended location is obvious rather than this being bolted onto
server/ later.
"""

from plasmaforge.simulation.state import SimulationState


def export_frame_placeholder(state: SimulationState) -> None:
    """No-op placeholder. Real implementation will likely serialize
    `state` plus camera parameters to a queue consumed by a separate
    rendering process (e.g. headless Three.js via Puppeteer, or a
    server-side renderer) — deliberately not decided yet."""
    raise NotImplementedError("Frame export is not implemented yet.")
