"""
Environment/deployment-dependent settings.

Unlike constants.py, everything here is allowed to be overridden by
environment variables. This is the file that changes between a laptop dev
run, CI, and (eventually) a deployed instance — physics constants should
never need to change based on where the code is running, but a port number
or log level absolutely does.
"""

import os
from dataclasses import dataclass


def _env_bool(name: str, default: bool) -> bool:
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


@dataclass(frozen=True)
class Settings:
    # --- Server ---
    host: str = os.environ.get("PLASMAFORGE_HOST", "0.0.0.0")
    port: int = int(os.environ.get("PLASMAFORGE_PORT", "8765"))
    debug: bool = _env_bool("PLASMAFORGE_DEBUG", False)

    # --- Simulation backend selection ---
    # "cython" today; reserved values "gpu_cupy" / "gpu_taichi" for later.
    # Keeping this as a string switch (rather than importing GPU code
    # unconditionally) means the GPU extra never has to be installed
    # unless someone actually opts into it.
    physics_backend: str = os.environ.get("PLASMAFORGE_PHYSICS_BACKEND", "cython")

    # --- Simulation mode ---
    default_mode: str = os.environ.get("PLASMAFORGE_DEFAULT_MODE", "classic")

    # --- Logging ---
    log_level: str = os.environ.get("PLASMAFORGE_LOG_LEVEL", "INFO")

    # --- Networking / streaming ---
    state_broadcast_hz: float = float(os.environ.get("PLASMAFORGE_BROADCAST_HZ", "35.0"))


# Single shared instance. Import this, don't re-instantiate Settings()
# elsewhere, so the whole process agrees on configuration.
settings = Settings()
