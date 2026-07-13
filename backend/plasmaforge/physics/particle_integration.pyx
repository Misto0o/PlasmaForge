# particle_integration.pyx — fuses field calculation, semi-implicit Euler
# integration, and glass-containment into ONE nogil loop over particles.
#
# WHY THIS REPLACES THE OLD numpy-BASED ParticleSystem.step(): the
# previous version called electric_field.compute_field_grid() (allocates
# an (N,3) output array), then did velocity/position updates and
# containment as several separate numpy expressions — each one a full
# pass over the particle arrays plus a temporary array allocation. For
# thousands of particles at 120Hz, that's a lot of allocator churn for
# work that's fundamentally "loop over particles once, do some math per
# particle." This module does exactly that: one pass, no temporaries, no
# numpy calls in the loop body.
#
# cython: language_level=3
# cython: boundscheck=False
# cython: wraparound=False
# cython: cdivision=True

from libc.math cimport sqrt

from plasmaforge.physics.electric_field cimport field_at_point

cdef double MIN_DISTANCE_EPSILON_SQ = 1e-12


cdef void integrate_particles(double[:, :] positions, double[:, :] velocities,
                               double[:] charges, double[:] masses,
                               double dt,
                               double[:] source_x, double[:] source_y,
                               double[:] source_z, double[:] source_q,
                               Py_ssize_t n_particles, Py_ssize_t n_sources,
                               double globe_radius) noexcept nogil:
    """
    Mutates `positions` and `velocities` IN PLACE for every particle:
      1. Sum the field from all sources (electrode + filament tips) at
         the particle's current position.
      2. F = qE, a = F/m, semi-implicit Euler: v += a*dt, x += v*dt.
      3. Contain within the glass: if the particle ends up outside
         `globe_radius`, clamp it to the surface and reflect the outward
         velocity component (soft bounce), matching the previous numpy
         implementation's behavior exactly.

    No return value — this is the whole point: the caller's numpy arrays
    (backed by contiguous memory the memoryviews point into) are updated
    directly, no new array is allocated per tick.
    """
    cdef Py_ssize_t i
    cdef double ex, ey, ez
    cdef double ax, ay, az
    cdef double radius, nx, ny, nz, v_dot_n

    for i in range(n_particles):
        field_at_point(positions[i, 0], positions[i, 1], positions[i, 2],
                        source_x, source_y, source_z, source_q, n_sources,
                        &ex, &ey, &ez)

        ax = (charges[i] * ex) / masses[i]
        ay = (charges[i] * ey) / masses[i]
        az = (charges[i] * ez) / masses[i]

        velocities[i, 0] += ax * dt
        velocities[i, 1] += ay * dt
        velocities[i, 2] += az * dt

        positions[i, 0] += velocities[i, 0] * dt
        positions[i, 1] += velocities[i, 1] * dt
        positions[i, 2] += velocities[i, 2] * dt

        radius = sqrt(positions[i, 0] * positions[i, 0]
                       + positions[i, 1] * positions[i, 1]
                       + positions[i, 2] * positions[i, 2])
        if radius > globe_radius and radius > 1e-9:
            nx = positions[i, 0] / radius
            ny = positions[i, 1] / radius
            nz = positions[i, 2] / radius
            positions[i, 0] = nx * globe_radius
            positions[i, 1] = ny * globe_radius
            positions[i, 2] = nz * globe_radius

            v_dot_n = (velocities[i, 0] * nx + velocities[i, 1] * ny
                       + velocities[i, 2] * nz)
            velocities[i, 0] -= 1.5 * v_dot_n * nx
            velocities[i, 1] -= 1.5 * v_dot_n * ny
            velocities[i, 2] -= 1.5 * v_dot_n * nz


def integrate_particles_py(positions, velocities, charges, masses, dt,
                            source_positions, source_charges, globe_radius):
    """
    Python-callable entry point used by simulation/particles/particle_system.py.
    `positions`/`velocities` are mutated in place — this function has no
    return value on purpose, matching integrate_particles' contract.
    """
    cdef double[:, :] pos = positions
    cdef double[:, :] vel = velocities
    cdef double[:] q = charges
    cdef double[:] m = masses
    cdef double[:] sx = source_positions[:, 0].copy()
    cdef double[:] sy = source_positions[:, 1].copy()
    cdef double[:] sz = source_positions[:, 2].copy()
    cdef double[:] sq = source_charges

    integrate_particles(pos, vel, q, m, dt, sx, sy, sz, sq,
                         pos.shape[0], sq.shape[0], globe_radius)
