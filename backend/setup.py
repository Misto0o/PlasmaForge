"""
Build script for the Cython extensions in plasmaforge.physics.

Usage:
    python setup.py build_ext --inplace

This compiles physics/*.pyx into .so/.pyd files placed next to their
source, so `import plasmaforge.physics.electric_field` works exactly like
importing a normal Python module — nothing else in the codebase needs to
know these modules are compiled.

Why setup.py and not exclusively pyproject.toml build-backend config:
Cython's `cythonize()` + `Extension` glob pattern is still the most
direct, well-documented way to compile multiple .pyx files with shared
compiler directives. pyproject.toml (see pyproject.toml) handles metadata
and dependency declarations; this file handles the actual extension
build, which is what `pip install -e .` invokes under the hood via
setuptools.
"""

from __future__ import annotations

import numpy
from Cython.Build import cythonize
from setuptools import Extension, find_packages, setup

# Every .pyx module in physics/ gets its own Extension entry. As more
# accelerated modules are added (e.g. a future filament-growth kernel),
# add them here explicitly rather than globbing — explicit extension
# lists make build errors traceable to a specific module immediately.
extensions = [
    Extension(
        "plasmaforge.physics.vector_math",
        ["plasmaforge/physics/vector_math.pyx"],
        include_dirs=[numpy.get_include()],
    ),
    Extension(
        "plasmaforge.physics.electric_field",
        ["plasmaforge/physics/electric_field.pyx"],
        include_dirs=[numpy.get_include()],
    ),
    Extension(
        "plasmaforge.physics.filament_growth",
        ["plasmaforge/physics/filament_growth.pyx"],
        include_dirs=[numpy.get_include()],
    ),
    Extension(
        "plasmaforge.physics.particle_integration",
        ["plasmaforge/physics/particle_integration.pyx"],
        include_dirs=[numpy.get_include()],
    ),
]

setup(
    name="plasmaforge",
    version="0.1.0",
    packages=find_packages(exclude=("tests", "tests.*", "benchmarks")),
    ext_modules=cythonize(
        extensions,
        compiler_directives={
            "language_level": "3",
            "boundscheck": False,
            "wraparound": False,
            "cdivision": True,
        },
        annotate=True,  # generates .html files showing Python-interaction
                        # "heat" per line — invaluable when optimizing;
                        # see docs/development.md profiling section.
    ),
    zip_safe=False,
)