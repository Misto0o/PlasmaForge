"""
Manual benchmark for physics.electric_field.compute_field_grid.

Not part of the pytest suite (see docs/development.md — benchmarks are
run deliberately, not on every commit, because they're slow and their
absolute numbers are machine-dependent). Run directly:

    python benchmarks/bench_electric_field.py

Use this to answer "did my change make field computation faster or
slower" with real numbers instead of guessing, especially before/after
touching electric_field.pyx or vector_math.pyx.
"""

import time

import numpy as np

from plasmaforge.physics import electric_field


def run(n_points: int, n_charges: int, n_iterations: int = 50) -> None:
    rng = np.random.default_rng(0)
    points = rng.uniform(-1, 1, size=(n_points, 3))
    charge_positions = rng.uniform(-0.5, 0.5, size=(n_charges, 3))
    charge_values = rng.uniform(0.5, 2.0, size=(n_charges,))

    # Warm-up call, excluded from timing, to avoid measuring one-time
    # costs unrelated to the kernel itself (e.g. first-touch page faults).
    electric_field.compute_field_grid(
        points,
        charge_positions[:, 0].copy(), charge_positions[:, 1].copy(),
        charge_positions[:, 2].copy(), charge_values,
    )

    start = time.perf_counter()
    for _ in range(n_iterations):
        electric_field.compute_field_grid(
            points,
            charge_positions[:, 0].copy(), charge_positions[:, 1].copy(),
            charge_positions[:, 2].copy(), charge_values,
        )
    elapsed = time.perf_counter() - start

    per_call_ms = (elapsed / n_iterations) * 1000.0
    print(f"points={n_points:>6} charges={n_charges:>4}  "
          f"avg {per_call_ms:8.3f} ms/call over {n_iterations} calls")


if __name__ == "__main__":
    print("compute_field_grid benchmark")
    print("-" * 60)
    for n_points in (100, 1_000, 4_000):
        for n_charges in (1, 8, 32):
            run(n_points, n_charges)
