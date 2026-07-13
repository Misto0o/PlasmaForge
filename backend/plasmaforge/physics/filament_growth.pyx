# filament_growth.pyx — picks which candidate growth direction a new
# filament should take, entirely in one tight Cython loop.
#
# WHY THIS MODULE EXISTS SEPARATELY FROM electric_field.pyx: the previous
# approach called electric_field.compute_field_grid() — which allocates a
# fresh numpy output array — then did the "pick the direction with
# weakest field" argmin back in Python with numpy.linalg.norm over that
# array. That's several boundary crossings (Cython -> Python -> numpy ->
# Python) for scoring a handful of candidate points. This module fuses
# candidate scoring into a single loop that stays in C for the actual
# math, called once from Python per filament spawn instead of once per
# candidate. For a project this size (12 candidates, single-digit
# filaments) the perf difference is not the point yet — it's the correct
# shape for when filament/candidate counts grow, and it's a second real
# accelerated module rather than everything routing through
# electric_field.
#
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libc.math cimport sqrt

from plasmaforge.physics.electric_field cimport field_at_point


cdef Py_ssize_t select_best_candidate(double[:, :] candidates,
                                       double[:] tip_x, double[:] tip_y,
                                       double[:] tip_z, double[:] tip_charges,
                                       Py_ssize_t n_candidates,
                                       Py_ssize_t n_tips) except -1 nogil:
    """
    For each row in `candidates` (shape (n_candidates, 3)), computes the
    field magnitude produced by the given tip charges, then returns the
    index of the candidate with the SMALLEST magnitude — i.e. the
    direction furthest from existing plasma, which is where a new
    filament should grow.

    Runs entirely nogil: no Python objects are touched inside the loop,
    so this can later be parallelized with cython.parallel.prange across
    candidates if candidate counts ever grow large enough to matter.
    """
    cdef Py_ssize_t best_idx = 0
    cdef double best_magnitude = 1e300  # effectively +inf, avoids a first-iteration branch
    cdef double ex, ey, ez, magnitude
    cdef Py_ssize_t i

    for i in range(n_candidates):
        field_at_point(candidates[i, 0], candidates[i, 1], candidates[i, 2],
                        tip_x, tip_y, tip_z, tip_charges, n_tips,
                        &ex, &ey, &ez)
        magnitude = sqrt(ex * ex + ey * ey + ez * ez)
        if magnitude < best_magnitude:
            best_magnitude = magnitude
            best_idx = i

    return best_idx


def select_best_candidate_py(candidates, tips):
    """
    Python-callable entry point used by physics/filament.py. Takes numpy
    arrays `candidates` (n_candidates, 3) and `tips` (n_tips, 3, treated
    as unit-charge repellers), returns the integer index of the best
    candidate. Returns 0 if `tips` is empty — nothing to repel from, so
    the caller should treat that as "pick randomly among candidates"
    rather than this function making that choice silently.
    """
    cdef Py_ssize_t n_tips = tips.shape[0]
    if n_tips == 0:
        return 0

    cdef double[:, :] c = candidates
    cdef double[:] tx = tips[:, 0].copy()
    cdef double[:] ty = tips[:, 1].copy()
    cdef double[:] tz = tips[:, 2].copy()
    import numpy as np
    cdef double[:] charges = np.ones(n_tips, dtype=np.float64)

    return select_best_candidate(c, tx, ty, tz, charges, c.shape[0], n_tips)
