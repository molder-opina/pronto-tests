import { test, expect, type Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const SCREENSHOTS_DIR = 'tests/design/screenshots';
const REPORT_FILE = 'tests/design/reports/design-report.md';

interface ScreenInfo {
  name: string;
  path: string;
  description: string;
}

const PAGES_TO_TEST: ScreenInfo[] = [
  { name: 'login', path: '/login', description: 'Pantalla de inicio de sesión' },
  { name: 'client-menu', path: '/menu', description: 'Menú del cliente' },
  { name: 'client-order', path: '/order', description: 'Creación de orden' },
  { name: 'employee-dashboard', path: '/employee/dashboard', description: 'Panel del empleado' },
  { name: 'employee-orders', path: '/employee/orders', description: 'Gestión de órdenes' },
  { name: 'checkout', path: '/checkout', description: 'Página de pago' },
  { name: 'order-confirmation', path: '/confirmation', description: 'Confirmación de orden' },
];

interface Recommendation {
  page: string;
  screenshot: string;
  analysis: string;
  status?: string;
}

test.describe('Pruebas de Diseño Visual', () => {
  test.beforeAll(() => {
    if (!fs.existsSync(SCREENSHOTS_DIR)) {
      fs.mkdirSync(SCREENSHOTS_DIR, { recursive: true });
    }
    if (!fs.existsSync('tests/design/reports')) {
      fs.mkdirSync('tests/design/reports', { recursive: true });
    }
  });

  for (const { name, path: pagePath, description } of PAGES_TO_TEST) {
    test(`Screenshot de ${description}`, async ({ page }: { page: Page }) => {
      const url = `${process.env.BASE_URL || 'http://localhost:5173'}${pagePath}`;
      
      await page.goto(url, { waitUntil: 'networkidle' });
      await page.waitForTimeout(2000);

      const screenshotPath = path.join(SCREENSHOTS_DIR, `${name}.png`);
      await page.screenshot({ 
        path: screenshotPath, 
        fullPage: true,
        animations: 'disabled'
      });

      console.log(`Screenshot guardado: ${screenshotPath}`);
    });
  }

  test('Analizar screenshots con OpenCode AI', async () => {
    const recommendations: Recommendation[] = [];
    
    for (const { name, description } of PAGES_TO_TEST) {
      const screenshotPath = path.join(SCREENSHOTS_DIR, `${name}.png`);
      
      if (fs.existsSync(screenshotPath)) {
        try {
          const result = await analyzeWithOpenCode(screenshotPath, description);
          
          recommendations.push({
            page: description,
            screenshot: `${name}.png`,
            analysis: result
          });
        } catch (error: unknown) {
          const errorMessage = error instanceof Error ? error.message : String(error);
          recommendations.push({
            page: description,
            screenshot: `${name}.png`,
            analysis: `Error al analizar: ${errorMessage}`,
            status: 'failed'
          });
        }
      }
    }

    const reportContent = generateReport(recommendations);
    fs.writeFileSync(REPORT_FILE, reportContent);
    console.log(`Reporte generado: ${REPORT_FILE}`);
  });
});

async function analyzeWithOpenCode(screenshotPath: string, description: string): Promise<string> {
  const { execSync } = await import('child_process');
  
  try {
    const result = execSync(
      `opencode run --analyze-design --image "${screenshotPath}" --description "${description}"`,
      { encoding: 'utf8', timeout: 30000 }
    );
    return result;
  } catch {
    return `Análisis no disponible - revisar screenshot manualmente: ${screenshotPath}`;
  }
}

function generateReport(recommendations: Recommendation[]): string {
  const timestamp = new Date().toISOString();
  
  let report = `# Reporte de Análisis de Diseño\n`;
  report += `Fecha: ${timestamp}\n\n`;
  report += `## Resumen Ejecutivo\n\n`;
  report += `Este reporte contiene el análisis de diseño de ${recommendations.length} pantallas de la aplicación.\n\n`;
  report += `## Análisis por Pantalla\n\n`;
  
  recommendations.forEach((rec, index) => {
    report += `### ${index + 1}. ${rec.page}\n\n`;
    report += `- **Screenshot**: ${rec.screenshot}\n`;
    report += `- **Estado**: ${rec.status === 'failed' ? '❌ Error' : '✅ Analizado'}\n\n`;
    
    if (rec.analysis) {
      report += `**Recomendaciones:**\n${rec.analysis}\n\n`;
    }
    
    report += `---\n\n`;
  });
  
  report += `## Recomendaciones Generales de Diseño Gráfico\n\n`;
  report += extractGeneralRecommendations();
  
  report += `\n## Screenshots\n\n`;
  recommendations.forEach(rec => {
    if (rec.status !== 'failed') {
      report += `![${rec.page}](./screenshots/${rec.screenshot})\n\n`;
    }
  });
  
  return report;
}

function extractGeneralRecommendations(): string {
  return `### Mejores Prácticas de Diseño\n\n` +
         `1. **Consistencia visual**: Usar paleta de colores uniforme y tipografía consistente.\n` +
         `2. **Espaciado**: Mantener márgenes y paddings coherentes (sistema de grid).\n` +
         `3. **Accesibilidad**: Verificar contraste WCAG AA y tamaños mínimos de elementos interactivos.\n` +
         `4. **Responsive**: Asegurar adaptación correcta a diferentes tamaños de pantalla.\n` +
         `5. **Feedback visual**: Proporcionar estados de hover, focus y active claros.\n\n` +
         `### Prioridades de Mejora\n\n` +
         `- Revisar jerarquía visual en páginas de alto tráfico.\n` +
         `- Optimizar tiempos de carga de assets visuales.\n` +
         `- Estandarizar componentes reutilizables.\n`;
}
