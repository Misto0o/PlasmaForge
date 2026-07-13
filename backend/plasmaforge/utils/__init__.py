"""
Utils package: small, dependency-free helpers used across the codebase
(logging setup, profiling, generic math helpers that don't belong in
physics/ because they aren't simulation math — e.g. easing functions for
the frontend-facing JSON, or array reshaping helpers).

Rule of thumb for what belongs here: if a function doesn't know anything
about plasma, particles, or fields, it can live in utils/. The moment it
encodes a physics concept, it belongs in physics/ instead.
"""
