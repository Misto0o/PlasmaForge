# vector_math.pxd — Cython declaration file.
#
# Why this file exists separately from vector_math.pyx:
# A .pxd file declares C-level signatures (cdef functions, struct-like
# types) so OTHER .pyx modules (like electric_field.pyx) can cimport this
# module and call these functions at C speed, with no Python call overhead.
# Without this file, electric_field.pyx could still `import vector_math`,
# but every call would pay full Python function-call overhead — defeating
# the point of writing this in Cython at all.

cdef double vec3_distance(double x1, double y1, double z1,
                           double x2, double y2, double z2) noexcept nogil

cdef double vec3_distance_sq(double x1, double y1, double z1,
                              double x2, double y2, double z2) noexcept nogil

cdef void vec3_normalize(double x, double y, double z,
                          double* out_x, double* out_y, double* out_z) noexcept nogil
