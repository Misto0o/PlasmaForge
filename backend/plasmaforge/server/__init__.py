"""
Server package: the boundary between the simulation and the outside world.

Everything network-related (WebSocket streaming of simulation state, any
future HTTP API for configuration/health checks) lives here. This package
is allowed to import from `simulation/` and `rendering/`; nothing outside
this package should import from `server/` — that would be a layering
violation (see docs/architecture.md).
"""
