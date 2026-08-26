"""
Physics and simulation constants.

These are values that describe the *model*, not the deployment: units,
default physical parameters, and tunables that a physicist/tuner would want
grouped together and untouched by devops-style config changes.

Keep this file free of anything environment-dependent (no os.environ reads
here — that belongs in settings.py).
"""

# --- Units -------------------------------------------------------------
# We simulate in a normalized, dimensionless unit system rather than SI,
# because the visual plasma globe effect is tuned for "looks right", not
# physical accuracy. Documenting the mapping here means future contributors
# don't have to reverse-engineer it from magic numbers scattered in physics/.
COULOMB_CONSTANT = 1.0          # normalized k in F = k * q1 * q2 / r^2
VACUUM_PERMITTIVITY = 1.0       # normalized

# --- Globe geometry ------------------------------------------------------
GLOBE_RADIUS = 1.0              # simulation-space radius of the glass globe
ELECTRODE_RADIUS = 0.10         # radius of the central electrode sphere

# --- Filament defaults -----------------------------------------------
DEFAULT_FILAMENT_COUNT = 65
FILAMENT_MIN_LIFETIME_S = 0.03   # Lowered: Rapid, frantic twitching/flicker
FILAMENT_MAX_LIFETIME_S = 0.4    # Lowered: Arcs cycle out quicker, keeping it dynamic
FILAMENT_BRANCH_PROBABILITY = 0.12
FILAMENT_PATH_SEGMENTS = 15      # jagged segments per main filament path
FILAMENT_JITTER = 0.12         # perpendicular displacement scale for jaggedness

# --- Particle system defaults ------------------------------------------
DEFAULT_MAX_PARTICLES = 4000
PARTICLE_CHARGE = 1.0
PARTICLE_MASS = 1.0
PARTICLE_MAX_AGE_S = 4.0  # particles despawn after this long, so the
                          # globe doesn't accumulate into a static "starfield"

# --- Simulation stepping -------------------------------------------------
FIXED_TIMESTEP_S = 1.0 / 120.0  # physics steps at 120Hz regardless of render/network rate
MAX_SUBSTEPS_PER_TICK = 8        # clamp to avoid the "spiral of death" under load

# --- Numerical safety ------------------------------------------------
MIN_DISTANCE_EPSILON = 1e-6      # prevents divide-by-zero in inverse-square law