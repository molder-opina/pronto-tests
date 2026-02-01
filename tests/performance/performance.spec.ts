import { test, expect } from '@playwright/test';
import { chromium } from '@playwright/test';

test.describe('Performance Tests', () => {
  test('Measure page load time - Login', async ({ page }) => {
    const startTime = Date.now();
    await page.goto(`${process.env.BASE_URL || 'http://localhost:5173'}/login`);
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    console.log(`Login page load time: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(3000);
  });

  test('Measure page load time - Menu', async ({ page }) => {
    const startTime = Date.now();
    await page.goto(`${process.env.BASE_URL || 'http://localhost:5173'}/menu`);
    await page.waitForLoadState('networkidle');
    const loadTime = Date.now() - startTime;
    
    console.log(`Menu page load time: ${loadTime}ms`);
    expect(loadTime).toBeLessThan(3000);
  });

  test('Measure API response time', async ({ request }) => {
    const startTime = Date.now();
    const response = await request.get(`${process.env.API_URL || 'http://localhost:3000'}/api/health`);
    const responseTime = Date.now() - startTime;
    
    console.log(`API health check response time: ${responseTime}ms`);
    expect(response.ok()).toBeTruthy();
    expect(responseTime).toBeLessThan(1000);
  });

  test('Measure time to interactive', async ({ page }) => {
    await page.goto(`${process.env.BASE_URL || 'http://localhost:5173'}/menu`);
    
    const tti = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          for (const entry of list.getEntries()) {
            if (entry.entryType === 'measure' && entry.name === 'timeToInteractive') {
              resolve(entry.duration);
            }
          }
        }).observe({ type: 'measure', buffered: true });
        
        window.performance.mark('fullyLoaded');
      });
    });
    
    console.log(`Time to Interactive: ${tti}ms`);
    expect(tti).toBeLessThan(5000);
  });
});

export default { test };
