# electric_field.pxd — declarations so other Cython modules (e.g. a future
# filament-growth accelerator) can cimport these functions at C speed.

cdef void field_at_point(double px, double py, double pz,
                          double[:] charge_x, double[:] charge_y,
                          double[:] charge_z, double[:] charge_q,
                          Py_ssize_t n_charges,
                          double* out_ex, double* out_ey, double* out_ez) noexcept nogil
