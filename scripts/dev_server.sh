#!/usr/bin/env bash
# scripts/dev_server.sh
#
# Starts the backend simulation server and frontend dev server together
# for local development. Kills both on exit (Ctrl+C) so you don't end up
# with an orphaned background process holding a port. This is a
# convenience script, not a production launcher — see docs/development.md
# for the manual two-terminal workflow this replaces.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cleanup() {
  echo "Shutting down..."
  kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true
}
trap cleanup EXIT

cd "$REPO_ROOT/backend"
python -m plasmaforge.server.app &
BACKEND_PID=$!

cd "$REPO_ROOT/frontend"
npm run dev &
FRONTEND_PID=$!

echo "Backend PID $BACKEND_PID, Frontend PID $FRONTEND_PID. Ctrl+C to stop both."
wait
