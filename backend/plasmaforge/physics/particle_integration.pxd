# particle_integration.pxd
#
# Declares the fused particle-integration step so it could be cimported
# by other Cython modules later (e.g. a GPU-dispatch shim that still
# wants the CPU fallback signature to match).

cdef void integrate_particles(double[:, :] positions, double[:, :] velocities,
                               double[:] charges, double[:] masses,
                               double dt,
                               double[:] source_x, double[:] source_y,
                               double[:] source_z, double[:] source_q,
                               Py_ssize_t n_particles, Py_ssize_t n_sources,
                               double globe_radius) noexcept nogil
