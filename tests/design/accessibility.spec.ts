import { test, expect, type Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const SCREENSHOTS_DIR = 'tests/design/screenshots';
const REPORT_FILE = 'tests/design/reports/accessibility-report.md';

interface AccessibilityCheck {
  name: string;
  path: string;
  description: string;
}

const PAGES_TO_CHECK: AccessibilityCheck[] = [
  { name: 'login', path: '/login', description: 'Pantalla de inicio de sesión' },
  { name: 'client-menu', path: '/menu', description: 'Menú del cliente' },
  { name: 'client-order', path: '/order', description: 'Creación de orden' },
  { name: 'employee-dashboard', path: '/employee/dashboard', description: 'Panel del empleado' },
];

test.describe('Pruebas de Accesibilidad', () => {
  for (const { name, path: pagePath, description } of PAGES_TO_CHECK) {
    test(`Verificar accesibilidad de ${description}`, async ({ page }: { page: Page }) => {
      const url = `${process.env.BASE_URL || 'http://localhost:5173'}${pagePath}`;
      
      await page.goto(url, { waitUntil: 'networkidle' });

      const accessibilityViolations: string[] = [];

      const imagesWithoutAlt = await page.locator('img:not([alt])').all();
      if (imagesWithoutAlt.length > 0) {
        accessibilityViolations.push(`Imágenes sin alt: ${imagesWithoutAlt.length}`);
      }

      const inputsWithoutLabel = await page.locator('input:not([aria-label]):not([id])').all();
      if (inputsWithoutLabel.length > 0) {
        accessibilityViolations.push(`Inputs sin label/aria-label: ${inputsWithoutLabel.length}`);
      }

      const buttonsEmpty = await page.locator('button:empty').all();
      if (buttonsEmpty.length > 0) {
        accessibilityViolations.push(`Botones vacíos: ${buttonsEmpty.length}`);
      }

      const screenshotPath = path.join(SCREENSHOTS_DIR, `a11y-${name}.png`);
      await page.screenshot({ path: screenshotPath, fullPage: true });

      if (accessibilityViolations.length > 0) {
        console.log(`${description}: ${accessibilityViolations.join(', ')}`);
      }

      expect(accessibilityViolations.length).toBe(0);
    });
  }
});

function generateA11yReport(checks: { page: string; violations: string[] }[]): string {
  const timestamp = new Date().toISOString();
  
  let report = `# Reporte de Accesibilidad\n`;
  report += `Fecha: ${timestamp}\n\n`;
  report += `## Resumen\n\n`;
  report += `Total de páginas verificadas: ${checks.length}\n`;
  report += `Páginas con problemas: ${checks.filter(c => c.violations.length > 0).length}\n\n`;
  
  return report;
}
