#!/bin/bash
# Ejecutar pruebas E2E con Playwright

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           PRUEBAS E2E CON PLAYWRIGHT                       ║"
echo "╚════════════════════════════════════════════════════════════╝"

cd "$PROJECT_ROOT/playwright-tests"

# Verificar que playwright está instalado
if ! command -v npx &> /dev/null; then
    echo "❌ Error: npx no está instalado"
    exit 1
fi

# Ejecutar pruebas
npx playwright test --reporter=list "$@"
