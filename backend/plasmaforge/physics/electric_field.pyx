# electric_field.pyx — Coulomb's-law-style electric field summation.
#
# This is the single most performance-critical module in the project: it's
# an O(n_points * n_charges) sum, called every simulation tick. Everything
# here is written to allow `nogil` execution so that, later, the outer
# per-particle loop in simulation/ can be parallelized with
# `cython.parallel.prange` without a rewrite.
#
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libc.math cimport sqrt
cimport numpy as cnp
import numpy as np

from plasmaforge.physics.vector_math cimport vec3_distance_sq

# Kept in sync with config/constants.py by convention; duplicated here
# (rather than imported) because pure-Python imports inside a nogil-heavy
# .pyx hot path are avoided — see docs/architecture.md for the tradeoff.
cdef double MIN_DISTANCE_EPSILON_SQ = 1e-12
cdef double COULOMB_CONSTANT = 1.0


cdef void field_at_point(double px, double py, double pz,
                          double[:] charge_x, double[:] charge_y,
                          double[:] charge_z, double[:] charge_q,
                          Py_ssize_t n_charges,
                          double* out_ex, double* out_ey, double* out_ez) noexcept nogil:
    """
    Sums the electric field contribution of every charge in
    (charge_x, charge_y, charge_z, charge_q) at point (px, py, pz).

    Writes result into out_ex/out_ey/out_ez rather than returning, to stay
    allocation-free on the hot path (no Python object creation at all).
    """
    cdef Py_ssize_t i
    cdef double dx, dy, dz, dist_sq, dist, inv_dist3, scale
    cdef double ex = 0.0
    cdef double ey = 0.0
    cdef double ez = 0.0

    for i in range(n_charges):
        dx = px - charge_x[i]
        dy = py - charge_y[i]
        dz = pz - charge_z[i]
        dist_sq = dx * dx + dy * dy + dz * dz
        if dist_sq < MIN_DISTANCE_EPSILON_SQ:
            continue  # avoid self-interaction / singularity blowup
        dist = sqrt(dist_sq)
        inv_dist3 = 1.0 / (dist_sq * dist)
        scale = COULOMB_CONSTANT * charge_q[i] * inv_dist3
        ex += dx * scale
        ey += dy * scale
        ez += dz * scale

    out_ex[0] = ex
    out_ey[0] = ey
    out_ez[0] = ez


def compute_field_grid(cnp.ndarray[cnp.double_t, ndim=2] points,
                        cnp.ndarray[cnp.double_t, ndim=1] charge_x,
                        cnp.ndarray[cnp.double_t, ndim=1] charge_y,
                        cnp.ndarray[cnp.double_t, ndim=1] charge_z,
                        cnp.ndarray[cnp.double_t, ndim=1] charge_q):
    """
    Python-callable entry point: computes the field at every row of `points`
    (shape (N, 3)) produced by the given charges. This is what
    simulation/engine.py actually calls — it's the boundary between
    "Python orchestration" and "Cython number crunching".

    Returns an (N, 3) numpy array of field vectors.
    """
    cdef Py_ssize_t n_points = points.shape[0]
    cdef Py_ssize_t n_charges = charge_x.shape[0]
    cdef cnp.ndarray[cnp.double_t, ndim=2] result = np.zeros((n_points, 3), dtype=np.float64)

    cdef double[:] cx = charge_x
    cdef double[:] cy = charge_y
    cdef double[:] cz = charge_z
    cdef double[:] cq = charge_q

    cdef Py_ssize_t i
    cdef double ex, ey, ez
    for i in range(n_points):
        field_at_point(points[i, 0], points[i, 1], points[i, 2],
                        cx, cy, cz, cq, n_charges,
                        &ex, &ey, &ez)
        result[i, 0] = ex
        result[i, 1] = ey
        result[i, 2] = ez

    return result
