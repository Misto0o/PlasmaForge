import os
from dataclasses import dataclass

def _env_bool(name, default):
    val = os.environ.get(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")

@dataclass(frozen=True)
class Settings:
    host: str = os.environ.get("PLASMAFORGE_HOST", "0.0.0.0")
    # Reads the platform-provided PORT env var first (Render, Railway,
    # Fly, Heroku, etc. all set this automatically to tell your app
    # which single port is externally reachable) — falls back to
    # PLASMAFORGE_PORT for local dev, then a hardcoded default.
    port: int = int(os.environ.get("PORT", os.environ.get("PLASMAFORGE_PORT", "8765")))
    debug: bool = _env_bool("PLASMAFORGE_DEBUG", False)
    physics_backend: str = os.environ.get("PLASMAFORGE_PHYSICS_BACKEND", "cython")
    default_mode: str = os.environ.get("PLASMAFORGE_DEFAULT_MODE", "classic")
    log_level: str = os.environ.get("PLASMAFORGE_LOG_LEVEL", "INFO")
    # Lowered from 60 — this is how often state gets SENT over the
    # network, completely separate from FIXED_TIMESTEP_S (the physics
    # still runs at 120Hz internally regardless of this number). Sending
    # the full filament/particle state 60x/second to every connected
    # browser is what actually burned through Render's free bandwidth
    # tier in about a day. Lightning doesn't visually need 20 updates a
    # second to look smooth — this cuts outbound bandwidth by roughly
    # 3x with minimal perceptible difference.
    state_broadcast_hz: float = float(os.environ.get("PLASMAFORGE_BROADCAST_HZ", "20"))

settings = Settings()