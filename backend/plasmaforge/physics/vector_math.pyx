# vector_math.pyx — small, hot-path 3D vector operations.
#
# Why Cython instead of NumPy here: for per-particle, per-pair operations
# called millions of times a second (N-body-ish electric field sums), the
# Python/NumPy call overhead per operation dominates. Dropping to `cdef`
# functions with `nogil` and C doubles lets these run at near-C speed and,
# down the line, lets the outer loops release the GIL for multithreading.
#
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True
#
# The directives above are deliberate, not defaults:
#   - boundscheck/wraparound off: these functions don't touch Python
#     buffers directly, so the safety checks would be dead weight anyway.
#   - cdivision=True: we do our own zero-distance guarding in
#     electric_field.pyx via MIN_DISTANCE_EPSILON, so we don't need
#     Python's div-by-zero exception machinery here.

from libc.math cimport sqrt


cdef double vec3_distance(double x1, double y1, double z1,
                           double x2, double y2, double z2) noexcept nogil:
    """Euclidean distance between two points. Hot path: called O(n^2) times
    per tick in naive field calculations, so this stays branch-free."""
    cdef double dx = x2 - x1
    cdef double dy = y2 - y1
    cdef double dz = z2 - z1
    return sqrt(dx * dx + dy * dy + dz * dz)


cdef double vec3_distance_sq(double x1, double y1, double z1,
                              double x2, double y2, double z2) noexcept nogil:
    """Squared distance — prefer this over vec3_distance when you don't
    need the actual distance (e.g., nearest-neighbor comparisons), since
    it skips the sqrt."""
    cdef double dx = x2 - x1
    cdef double dy = y2 - y1
    cdef double dz = z2 - z1
    return dx * dx + dy * dy + dz * dz


cdef void vec3_normalize(double x, double y, double z,
                          double* out_x, double* out_y, double* out_z) noexcept nogil:
    """Writes a unit vector into out_x/out_y/out_z. Takes pointers (rather
    than returning a tuple) specifically to avoid Python tuple boxing on
    a function that may be called per-particle, per-tick."""
    cdef double length = sqrt(x * x + y * y + z * z)
    if length < 1e-12:
        out_x[0] = 0.0
        out_y[0] = 0.0
        out_z[0] = 0.0
        return
    out_x[0] = x / length
    out_y[0] = y / length
    out_z[0] = z / length


# --- Python-visible wrappers -------------------------------------------
# The cdef functions above are invisible to plain Python/pytest. These
# thin `def` wrappers exist purely so tests and non-hot-path Python code
# can call into the same logic without duplicating it.

def py_distance(x1, y1, z1, x2, y2, z2):
    """Python-callable wrapper around vec3_distance, for unit tests."""
    return vec3_distance(x1, y1, z1, x2, y2, z2)


def py_normalize(x, y, z):
    """Python-callable wrapper around vec3_normalize, for unit tests."""
    cdef double ox, oy, oz
    vec3_normalize(x, y, z, &ox, &oy, &oz)
    return (ox, oy, oz)
