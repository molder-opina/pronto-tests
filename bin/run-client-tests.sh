#!/bin/bash
# Ejecutar pruebas E2E de clientes con Playwright

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║        PRUEBAS E2E - CLIENTES (PLAYWRIGHT)                ║"
echo "╚════════════════════════════════════════════════════════════╝"

cd "$PROJECT_ROOT/playwright-tests/clients"

npx playwright test --reporter=list "$@"
