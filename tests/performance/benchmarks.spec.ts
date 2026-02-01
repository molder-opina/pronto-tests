import { test, expect, type Page } from '@playwright/test';
import fs from 'fs';
import path from 'path';

const REPORT_FILE = 'tests/performance/performance-report.md';

interface PerformanceMetric {
  name: string;
  value: number;
  unit: string;
  threshold: number;
  passed: boolean;
}

test.describe('Performance Benchmarks', () => {
  test('Full performance audit', async ({ page }: { page: Page }) => {
    const metrics: PerformanceMetric[] = [];
    const baseUrl = process.env.BASE_URL || 'http://localhost:5173';
    
    const pages = [
      { name: 'Login Page', path: '/login' },
      { name: 'Menu Page', path: '/menu' },
      { name: 'Employee Dashboard', path: '/employee/dashboard' },
    ];

    for (const { name, path: pagePath } of pages) {
      await page.goto(`${baseUrl}${pagePath}`, { waitUntil: 'networkidle' });
      
      const perfMetrics = await page.evaluate(() => {
        const timing = performance.timing;
        return {
          loadTime: timing.loadEventEnd - timing.navigationStart,
          domContentLoaded: timing.domContentLoadedEventEnd - timing.navigationStart,
          firstPaint: performance.getEntriesByType('paint')
            .find((e: PerformanceEntry) => e.name === 'first-paint')?.duration || 0,
          firstContentfulPaint: performance.getEntriesByType('paint')
            .find((e: PerformanceEntry) => e.name === 'first-contentful-paint')?.duration || 0,
        };
      });

      metrics.push({
        name: `${name} - Load Time`,
        value: perfMetrics.loadTime,
        unit: 'ms',
        threshold: 3000,
        passed: perfMetrics.loadTime < 3000
      });

      metrics.push({
        name: `${name} - First Contentful Paint`,
        value: perfMetrics.firstContentfulPaint,
        unit: 'ms',
        threshold: 1500,
        passed: perfMetrics.firstContentfulPaint < 1500
      });
    }

    const report = generatePerformanceReport(metrics);
    fs.writeFileSync(REPORT_FILE, report);
    
    const allPassed = metrics.every(m => m.passed);
    expect(allPassed).toBeTruthy();
  });
});

function generatePerformanceReport(metrics: PerformanceMetric[]): string {
  const timestamp = new Date().toISOString();
  
  let report = `# Reporte de Performance\n`;
  report += `Fecha: ${timestamp}\n\n`;
  report += `## Métricas Recolectadas\n\n`;
  report += `| Métrica | Valor | Umbral | Estado |\n`;
  report += `|---------|-------|--------|--------|\n`;
  
  for (const metric of metrics) {
    const status = metric.passed ? '✅ Pasa' : '❌ Falla';
    report += `| ${metric.name} | ${metric.value}${metric.unit} | <${metric.threshold}${metric.unit} | ${status} |\n`;
  }
  
  const passedCount = metrics.filter(m => m.passed).length;
  report += `\n**Resumen**: ${passedCount}/${metrics.length} métricas pasaron los umbrales.\n`;
  
  report += `\n## Recomendaciones\n\n`;
  report += `1. Optimizar recursos estáticos (compresión, caching).\n`;
  report += `2. Implementar lazy loading para imágenes.\n`;
  report += `3. Minimizar JavaScript crítico (above-the-fold).\n`;
  report += `4. Usar CDN para assets estáticos.\n`;
  
  return report;
}

export default { test };
