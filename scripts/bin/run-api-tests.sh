#!/bin/bash
# Ejecutar pruebas de API

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║              PRUEBAS DE API                                ║"
echo "╚════════════════════════════════════════════════════════════╝"

cd "$PROJECT_ROOT/api-tests"

python -m pytest -v --tb=short "$@"
