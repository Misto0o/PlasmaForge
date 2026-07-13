# filament_growth.pxd
#
# Declares the candidate-scoring function so it can be cimported at C
# speed by other Cython modules later (e.g. if branching filament growth
# moves here too).

cdef Py_ssize_t select_best_candidate(double[:, :] candidates,
                                       double[:] tip_x, double[:] tip_y,
                                       double[:] tip_z, double[:] tip_charges,
                                       Py_ssize_t n_candidates,
                                       Py_ssize_t n_tips) except -1 nogil
