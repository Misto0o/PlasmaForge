"""
Interaction package — RESERVED FOR FUTURE WORK. Do not build this out yet.

This will eventually house MediaPipe-based hand tracking: detecting a
hand near the physical/webcam view of the globe and translating that into
a "disturbance" the simulation reacts to (e.g. filaments bending toward
the hand, like a real plasma globe).

It exists as an empty-but-present package now, rather than being added
later, so that:

  1. The intended integration seam is documented in docs/architecture.md
     and visible in the tree from day one — contributors designing
     simulation/engine.py's public interface today can keep "a future
     external disturbance input" in mind.
  2. When this work starts, it's additive (new files in an existing,
     already-wired-up package) rather than requiring a restructure.

When this is actually implemented, the expected shape is:
  - `hand_tracker.py`: wraps MediaPipe, emits normalized hand position
    events.
  - `disturbance.py`: translates hand events into a simulation-facing
    interface (e.g. an extra charge source, or a repulsion field) that
    `simulation/engine.py` consumes through a small, explicit hook —
    NOT by importing MediaPipe types into simulation/.
"""
