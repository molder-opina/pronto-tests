#!/bin/bash
# Script principal para ejecutar todas las pruebas del proyecto

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

echo "╔════════════════════════════════════════════════════════════╗"
echo "║           EJECUTANDO TODAS LAS PRUEBAS                    ║"
echo "╚════════════════════════════════════════════════════════════╝"

# Colores para la salida
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Función para ejecutar pruebas
run_tests() {
    local test_type=$1
    local test_command=$2
    local test_name=$3

    echo -e "\n${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}  $test_name${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

    if eval "$test_command"; then
        echo -e "${GREEN}✓ $test_name completadas exitosamente${NC}"
        return 0
    else
        echo -e "${RED}✗ $test_name fallaron${NC}"
        return 1
    fi
}

# Array para almacenar resultados
RESULTS=()

# 1. Pruebas Unitarias
echo -e "\n${YELLOW}>>> FASE 1: PRUEBAS UNITARIAS${NC}"
if run_tests "unit" "cd '$PROJECT_ROOT/unit-tests' && python -m pytest -v --tb=short 2>&1 | head -100" "Pruebas Unitarias"; then
    RESULTS+=("unit:OK")
else
    RESULTS+=("unit:FAIL")
fi

# 2. Pruebas de API
echo -e "\n${YELLOW}>>> FASE 2: PRUEBAS DE API${NC}"
if run_tests "api" "cd '$PROJECT_ROOT/api-tests' && python -m pytest -v --tb=short 2>&1 | head -100" "Pruebas de API"; then
    RESULTS+=("api:OK")
else
    RESULTS+=("api:FAIL")
fi

# 3. Pruebas E2E con Playwright
echo -e "\n${YELLOW}>>> FASE 3: PRUEBAS E2E (PLAYWRIGHT)${NC}"
if [ -d "$PROJECT_ROOT/playwright-tests" ]; then
    if run_tests "playwright" "cd '$PROJECT_ROOT/playwright-tests' && npx playwright test --reporter=list 2>&1 | head -100" "Pruebas Playwright"; then
        RESULTS+=("playwright:OK")
    else
        RESULTS+=("playwright:FAIL")
    fi
else
    echo -e "${YELLOW}⚠ Carpeta playwright-tests no encontrada, saltando...${NC}"
    RESULTS+=("playwright:SKIP")
fi

# Resumen final
echo -e "\n╔════════════════════════════════════════════════════════════╗"
echo -e "║                    RESUMEN FINAL                           ║"
echo -e "╚════════════════════════════════════════════════════════════╝"

for result in "${RESULTS[@]}"; do
    IFS=':' read -r type status <<< "$result"
    if [ "$status" = "OK" ]; then
        echo -e "  ${GREEN}✓ $type: PASSED${NC}"
    elif [ "$status" = "FAIL" ]; then
        echo -e "  ${RED}✗ $type: FAILED${NC}"
    else
        echo -e "  ${YELLOW}○ $status: SKIPPED${NC}"
    fi
done

# Verificar si todas las pruebas pasaron
if [[ " ${RESULTS[*]} " =~ "FAIL" ]]; then
    echo -e "\n${RED}❌ Algunas pruebas fallaron${NC}"
    exit 1
else
    echo -e "\n${GREEN}✅ Todas las pruebas pasaron${NC}"
    exit 0
fi
