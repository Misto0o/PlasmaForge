"""
Physics package: pure math, no simulation state, no I/O, no networking.

This package intentionally has no knowledge of "particles" as simulation
objects, WebSocket clients, or rendering. Everything here operates on plain
numbers/arrays in, numbers/arrays out. That constraint is what makes it
possible to:

  1. Unit test against known analytical solutions.
  2. Benchmark in isolation (see /backend/benchmarks).
  3. Swap the implementation (Cython today, GPU later) behind the same
     function signatures without touching simulation/ code.

Compiled Cython modules (electric_field, vector_math) are imported here so
the rest of the codebase can do `from plasmaforge.physics import electric_field`
without knowing whether it's talking to compiled or pure-Python fallback code.
"""
