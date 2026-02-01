#!/bin/bash
# Ejecutar pruebas unitarias

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              PRUEBAS UNITARIAS                             ║"
echo "╚════════════════════════════════════════════════════════════╝"

cd "$PROJECT_ROOT/unit-tests"

python -m pytest -v --tb=short "$@"
