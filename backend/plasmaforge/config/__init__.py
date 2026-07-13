"""
Configuration package.

Why config is its own package rather than a single settings.py at the repo
root: as the project grows (multiple sim modes, GPU backends, deployment
configs), settings need structure. Splitting `constants.py` (physics/units,
things that rarely change and are not environment-dependent) from
`settings.py` (things that DO vary per-environment: ports, debug flags,
which physics backend to use) avoids the common anti-pattern of one giant
settings file mixing physics constants with deployment config.
"""
