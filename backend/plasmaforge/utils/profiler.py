"""
Lightweight profiling utilities: a context manager for timing named
sections of code and accumulating stats, without pulling in a heavyweight
APM/tracing dependency.

This is deliberately simple. For deep investigation, prefer external
tools (py-spy for sampling, line_profiler for line-level detail in
.pyx files) as described in docs/development.md — this module is for
"is this section of code taking 2ms or 20ms, in a way I can log or
assert on in CI", not full profiling.
"""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import contextmanager

_SECTION_TOTALS_S: dict[str, float] = defaultdict(float)
_SECTION_COUNTS: dict[str, int] = defaultdict(int)


@contextmanager
def profiled_section(name: str):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        _SECTION_TOTALS_S[name] += elapsed
        _SECTION_COUNTS[name] += 1


def get_stats() -> dict[str, dict[str, float]]:
    """Returns {section_name: {total_s, count, avg_ms}} for everything
    profiled so far in this process. Useful for a debug endpoint or a
    periodic log line during development."""
    stats = {}
    for name, total in _SECTION_TOTALS_S.items():
        count = _SECTION_COUNTS[name]
        stats[name] = {
            "total_s": total,
            "count": count,
            "avg_ms": (total / count * 1000.0) if count else 0.0,
        }
    return stats


def reset_stats() -> None:
    _SECTION_TOTALS_S.clear()
    _SECTION_COUNTS.clear()
