# Estructura del Proyecto de Pruebas PRONTO

```
pronto-tests/
├── scripts/
│   └── run-tests.sh          # Script principal para ejecutar pruebas
├── tests/
│   ├── functionality/
│   │   ├── api/              # Pruebas de API (Pytest)
│   │   │   ├── test_auth_api.py
│   │   │   ├── test_jwt_*.py
│   │   │   └── ...
│   │   ├── ui/               # Pruebas de UI (Playwright)
│   │   │   ├── clients/
│   │   │   ├── employees/
│   │   │   └── *.spec.ts
│   │   ├── e2e/              # Pruebas End-to-End
│   │   │   ├── test_e2e_*.py
│   │   │   └── *.cjs
│   │   ├── unit/             # Pruebas Unitarias
│   │   │   └── test_*.py
│   │   └── integration/      # Pruebas de Integración
│   │       └── test_*.py
│   ├── performance/          # Pruebas de Performance
│   │   ├── performance.spec.ts
│   │   ├── benchmarks.spec.ts
│   │   └── performance-report.md
│   └── design/               # Pruebas de Diseño
│       ├── design-visual.spec.ts
│       ├── accessibility.spec.ts
│       ├── screenshots/      # Screenshots capturados
│       │   └── *.png
│       └── reports/          # Reportes de análisis
│           ├── design-report.md
│           └── accessibility-report.md
├── bin/                      # Scripts legacy
├── playwright.config.ts      # Configuración de Playwright
└── README.md
```

## Uso

### Ejecutar todas las pruebas
```bash
./scripts/run-tests.sh all
```

### Solo funcionalidad
```bash
./scripts/run-tests.sh functionality
```

### Solo performance
```bash
./scripts/run-tests.sh performance
```

### Solo diseño (con screenshots)
```bash
./scripts/run-tests.sh design
```

## Pruebas de Diseño

Las pruebas de diseño toman screenshots de las pantallas y los analizan con OpenCode AI:

1. **Screenshots capturados**: `tests/design/screenshots/`
2. **Reporte generado**: `tests/design/reports/design-report.md`

### Pantallas analizadas:
- Login
- Menú del cliente
- Creación de orden
- Panel del empleado
- Gestión de órdenes
- Checkout
- Confirmación de orden

## Requisitos

- Node.js 18+
- Python 3.9+
- Playwright (`npx playwright install`)
- OpenCode CLI (para análisis de diseño)
