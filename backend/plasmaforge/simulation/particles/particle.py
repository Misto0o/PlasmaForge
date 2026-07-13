"""
A single charged particle. Kept as a lightweight dataclass rather than a
full class hierarchy — particles don't have behavior of their own beyond
state; the *behavior* (integration, field response) lives in
particle_system.py so it can be vectorized/batched instead of calling a
method per-particle per-tick.
"""

from __future__ import annotations

from dataclasses import dataclass

from plasmaforge.config import constants


@dataclass
class Particle:
    x: float
    y: float
    z: float
    vx: float = 0.0
    vy: float = 0.0
    vz: float = 0.0
    charge: float = constants.PARTICLE_CHARGE
    mass: float = constants.PARTICLE_MASS
    age_s: float = 0.0
    alive: bool = True
