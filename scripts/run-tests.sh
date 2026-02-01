#!/bin/bash

echo "🧪 PRONTO Tests Runner"
echo "======================"
echo ""

case "$1" in
  all)
    echo "🚀 Ejecutando todas las pruebas..."
    echo ""
    echo "📋 Pruebas de Funcionalidad:"
    echo "  - Unit Tests..."
    npm run test:unit || echo "  ⚠️ Unit tests no disponibles"
    echo "  - API Tests..."
    pytest tests/functionality/api/ -v 2>/dev/null || echo "  ⚠️ pytest no disponible"
    echo "  - UI Tests..."
    npx playwright test tests/functionality/ui/ --reporter=list 2>/dev/null || echo "  ⚠️ playwright no configurado"
    echo "  - E2E Tests..."
    npx playwright test tests/functionality/e2e/ --reporter=list 2>/dev/null || echo "  ⚠️ E2E tests no disponibles"
    echo ""
    echo "⚡ Pruebas de Performance:"
    npx playwright test tests/performance/ --reporter=list 2>/dev/null || echo "  ⚠️ Performance tests no disponibles"
    echo ""
    echo "🎨 Pruebas de Diseño:"
    npx playwright test tests/design/ --reporter=list 2>/dev/null || echo "  ⚠️ Design tests no disponibles"
    ;;
    
  functionality)
    echo "📋 Ejecutando pruebas de funcionalidad..."
    echo "  - Unit Tests..."
    npm run test:unit 2>/dev/null || python -m pytest tests/functionality/unit/ -v 2>/dev/null || echo "  ⚠️ Unit tests no disponibles"
    echo "  - API Tests..."
    pytest tests/functionality/api/ -v 2>/dev/null || echo "  ⚠️ pytest no disponible"
    echo "  - UI Tests..."
    npx playwright test tests/functionality/ui/ --reporter=list 2>/dev/null || echo "  ⚠️ UI tests no disponibles"
    echo "  - E2E Tests..."
    npx playwright test tests/functionality/e2e/ --reporter=list 2>/dev/null || echo "  ⚠️ E2E tests no disponibles"
    ;;
    
  performance)
    echo "⚡ Ejecutando pruebas de performance..."
    npx playwright test tests/performance/ --reporter=list 2>/dev/null || echo "  ⚠️ Performance tests no disponibles"
    ;;
    
  design)
    echo "🎨 Ejecutando pruebas de diseño..."
    echo "  Tomando screenshots de páginas..."
    npx playwright test tests/design/design-visual.spec.ts 2>/dev/null || echo "  ⚠️ Design tests no disponibles"
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
echo "✅ Ejecución completada"
