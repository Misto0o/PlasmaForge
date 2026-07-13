"""
PlasmaForge backend package.

This file exists to (a) mark `plasmaforge` as an importable package and
(b) expose a single, stable version string that setup.py, the server's
/health endpoint, and logs can all reference without duplicating it.
"""

__version__ = "0.1.0"
