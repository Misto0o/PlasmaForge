#!/usr/bin/env bash
# scripts/build_cython.sh
#
# Convenience wrapper around `python setup.py build_ext --inplace`, run
# from the repo root regardless of the caller's current directory. Exists
# so build instructions in README/CI don't need to remember to `cd backend`
# first, and so the exact build invocation lives in one place.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT/backend"
echo "Building Cython extensions in backend/plasmaforge/physics ..."
python setup.py build_ext --inplace
echo "Done."
