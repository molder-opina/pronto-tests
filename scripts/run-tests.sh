#!/bin/bash

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR/.."

set -euo pipefail

fail=0

have_cmd() { command -v "$1" >/dev/null 2>&1; }

run_step() {
  local name="$1"
  shift
  echo "==> $name"
  if "$@"; then
    return 0
  fi
  echo "FAIL: $name" >&2
  fail=1
  return 0
}

require_cmd() {
  local c="$1"
  if have_cmd "$c"; then
    return 0
  fi
  echo "MISSING: $c" >&2
  fail=1
  return 1
}

echo "PRONTO Tests Runner"
echo "======================"
echo ""

case "$1" in
  all)
    echo "🚀 Ejecutando todas las pruebas..."
    echo ""
    echo "📋 Pruebas de Funcionalidad:"
    echo "  - Unit Tests..."
    if have_cmd npm; then
      run_step "unit (npm)" npm run test:unit
    elif have_cmd python; then
      run_step "unit (pytest)" python -m pytest tests/functionality/unit/ -v
    else
      echo "MISSING: npm/python (unit tests)" >&2
      fail=1
    fi
    echo "  - API Tests..."
    VENV_PATH="$SCRIPT_DIR/../.venv-test"
    if [[ -x "$VENV_PATH/bin/pytest" ]]; then
      run_step "api (pytest)" "$VENV_PATH/bin/pytest" tests/functionality/api/ -v
    elif have_cmd pytest; then
      run_step "api (pytest)" pytest tests/functionality/api/ -v
    else
      echo "MISSING: pytest (api tests)" >&2
      fail=1
    fi
    echo "  - UI Tests..."
    if have_cmd npx; then
      run_step "ui (playwright)" npx playwright test tests/functionality/ui/ --reporter=list
    else
      echo "MISSING: npx (playwright ui tests)" >&2
      fail=1
    fi
    echo "  - E2E Tests..."
    if have_cmd npx; then
      run_step "e2e (playwright)" npx playwright test tests/functionality/e2e/ --reporter=list
    else
      echo "MISSING: npx (playwright e2e tests)" >&2
      fail=1
    fi
    echo ""
    echo "⚡ Pruebas de Performance:"
    if have_cmd npx; then
      run_step "performance (playwright)" npx playwright test tests/performance/ --reporter=list
    else
      echo "MISSING: npx (playwright performance tests)" >&2
      fail=1
    fi
    echo ""
    echo "🎨 Pruebas de Diseño:"
    if have_cmd npx; then
      run_step "design (playwright)" npx playwright test tests/design/ --reporter=list
    else
      echo "MISSING: npx (playwright design tests)" >&2
      fail=1
    fi
    ;;
    
  functionality)
    echo "📋 Ejecutando pruebas de funcionalidad..."
    echo "  - Unit Tests..."
    if have_cmd npm; then
      run_step "unit (npm)" npm run test:unit
    elif have_cmd python; then
      run_step "unit (pytest)" python -m pytest tests/functionality/unit/ -v
    else
      echo "MISSING: npm/python (unit tests)" >&2
      fail=1
    fi
    echo "  - API Tests..."
    VENV_PATH="$SCRIPT_DIR/../.venv-test"
    if [[ -x "$VENV_PATH/bin/pytest" ]]; then
      run_step "api (pytest)" "$VENV_PATH/bin/pytest" tests/functionality/api/ -v
    elif have_cmd pytest; then
      run_step "api (pytest)" pytest tests/functionality/api/ -v
    else
      echo "MISSING: pytest (api tests)" >&2
      fail=1
    fi
    echo "  - UI Tests..."
    if have_cmd npx; then
      run_step "ui (playwright)" npx playwright test tests/functionality/ui/ --reporter=list
    else
      echo "MISSING: npx (playwright ui tests)" >&2
      fail=1
    fi
    echo "  - E2E Tests..."
    if have_cmd npx; then
      run_step "e2e (playwright)" npx playwright test tests/functionality/e2e/ --reporter=list
    else
      echo "MISSING: npx (playwright e2e tests)" >&2
      fail=1
    fi
    ;;
    
  performance)
    echo "⚡ Ejecutando pruebas de performance..."
    if have_cmd npx; then
      run_step "performance (playwright)" npx playwright test tests/performance/ --reporter=list
    else
      echo "MISSING: npx (playwright performance tests)" >&2
      fail=1
    fi
    ;;
    
  design)
    echo "🎨 Ejecutando pruebas de diseño..."
    echo "  Tomando screenshots de páginas..."
    if have_cmd npx; then
      run_step "design (playwright)" npx playwright test tests/design/design-visual.spec.ts
    else
      echo "MISSING: npx (playwright design tests)" >&2
      fail=1
    fi
    echo ""
    echo "  Analizando con OpenCode AI..."
    if command -v opencode &> /dev/null; then
      for screenshot in tests/design/screenshots/*.png; do
        if [ -f "$screenshot" ]; then
          echo "    Analizando: $(basename $screenshot)"
          opencode run --analyze-design --image "$screenshot" 2>/dev/null || true
        fi
      done
    fi
    echo ""
    if [ -f "tests/design/reports/design-report.md" ]; then
      echo "📄 Reporte generado: tests/design/reports/design-report.md"
    fi
    ;;
    
  *)
    echo "Uso: $0 {all|functionality|performance|design}"
    echo ""
    echo "Comandos disponibles:"
    echo "  all           - Ejecutar todas las pruebas"
    echo "  functionality - Ejecutar pruebas de funcionalidad"
    echo "  performance   - Ejecutar pruebas de performance"
    echo "  design        - Ejecutar pruebas de diseño (screenshots + análisis)"
    ;;
esac

echo ""
if [[ "$fail" == "0" ]]; then
  echo "OK: Ejecución completada"
  exit 0
fi
echo "FAIL: Ejecución completada con errores" >&2
exit 1
