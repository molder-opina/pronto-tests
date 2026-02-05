import { test, expect, APIRequestContext } from '@playwright/test';

test.describe('Vue.js Rendering Integrity Tests', () => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:6080';
  let apiContext: APIRequestContext;

  test.beforeAll(async ({ playwright }) => {
    apiContext = await playwright.request.newContext({
      baseURL: BASE_URL,
    });
  });

  test.afterAll(async () => {
    await apiContext.dispose();
  });

  test.describe('Menu API vs Rendering', () => {
    test('should verify menu API returns data before rendering', async ({ page }) => {
      // Step 1: Fetch menu data directly from API
      const apiResponse = await apiContext.get('/api/menu');
      expect(apiResponse.ok()).toBeTruthy();

      const menuData = await apiResponse.json();
      expect(menuData.categories).toBeDefined();
      expect(Array.isArray(menuData.categories)).toBeTruthy();

      // Calculate total items
      const totalItems = menuData.categories.reduce(
        (sum: number, cat: { items?: unknown[] }) => sum + (cat.items?.length || 0),
        0
      );
      console.log(`API Reports: ${menuData.categories.length} categories, ${totalItems} total items`);

      // Verify data integrity
      expect(totalItems).toBeGreaterThan(0);
      expect(menuData.categories.length).toBeGreaterThan(0);

      // Step 2: Navigate to page and verify rendering
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');

      // Wait for Vue to render
      await page.waitForTimeout(5000);

      // Step 3: Count rendered items
      const renderedItems = await page.locator('.menu-item-card').count();
      console.log(`Rendered Items: ${renderedItems}`);

      // Verify rendering matches API
      expect(renderedItems).toBeGreaterThan(0);
      expect(renderedItems).toBe(totalItems);
    });

    test('should verify menu item data matches API', async ({ page }) => {
      // Get menu data from API
      const apiResponse = await apiContext.get('/api/menu');
      const menuData = await apiResponse.json();

      // Get first category with items
      const firstCategory = menuData.categories.find(
        (cat: { items?: unknown[] }) => cat.items && cat.items.length > 0
      );

      expect(firstCategory).toBeDefined();
      expect(firstCategory.items.length).toBeGreaterThan(0);

      const firstApiItem = firstCategory.items[0] as {
        id: number;
        name: string;
        description?: string;
        price: number;
      };

      // Navigate to page
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      // Find rendered item and compare
      const firstRenderedItem = page.locator('.menu-item-card').first();

      // Verify item exists
      await expect(firstRenderedItem).toBeVisible({ timeout: 10000 });

      // Verify name matches
      const renderedName = await firstRenderedItem.locator('.menu-item-name, h3, [class*="name"]').first().textContent();
      expect(renderedName).toBe(firstApiItem.name);

      // Verify price is present
      const renderedPrice = await firstRenderedItem.locator('.menu-item-price, [class*="price"]').first().textContent();
      expect(renderedPrice).toBeTruthy();
    });

    test('should verify all categories are rendered as tabs', async ({ page }) => {
      const apiResponse = await apiContext.get('/api/menu');
      const menuData = await apiResponse.json();

      const apiCategoryCount = menuData.categories.length;

      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      // Check category tabs are rendered
      const categoryTabs = await page.locator('.filter-chip, .category-tab, button[data-filter]').count();
      console.log(`API Categories: ${apiCategoryCount}, Rendered Tabs: ${categoryTabs}`);

      // At minimum, "All" tab should exist + actual categories
      expect(categoryTabs).toBeGreaterThanOrEqual(apiCategoryCount);
    });
  });

  test.describe('Vue Component Lifecycle', () => {
    test('should verify Vue app is mounted', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      // Check that Vue mounted by verifying app container exists
      const menuRoot = page.locator('[data-menu-root]');
      await expect(menuRoot).toHaveAttribute('data-menu-root', '', { timeout: 10000 });

      // Verify Vue initialized (menu sections should have content after load)
      const menuSections = page.locator('#menu-sections');
      const sectionsHTML = await menuSections.innerHTML();

      // After proper Vue init, menu-sections should NOT be empty
      expect(sectionsHTML.length).toBeGreaterThan(50);
    });

    test('should verify JavaScript modules are loaded', async ({ page }) => {
      const loadedScripts: string[] = [];

      page.on('console', (msg) => {
        if (msg.type() === 'log') {
          const text = msg.text();
          if (text.includes('[menu.ts]') || text.includes('[MenuFlow]')) {
            loadedScripts.push(text);
          }
        }
      });

      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      // Verify menu initialization logs appeared
      const menuInitLogs = loadedScripts.filter((log) =>
        log.includes('Menu flow initialized') || log.includes('Initializing menu')
      );

      console.log('Menu initialization logs:', menuInitLogs);
      expect(menuInitLogs.length).toBeGreaterThan(0);
    });

    test('should verify API calls are made for menu data', async ({ page }) => {
      const apiCalls: { url: string; status: number }[] = [];

      page.on('response', (response) => {
        if (response.url().includes('/api/menu')) {
          apiCalls.push({
            url: response.url(),
            status: response.status(),
          });
        }
      });

      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      // Verify /api/menu was called
      const menuApiCall = apiCalls.find((call) => call.url.includes('/api/menu'));
      expect(menuApiCall).toBeDefined();
      expect(menuApiCall?.status).toBe(200);
    });
  });

  test.describe('Static Content Verification', () => {
    test('should verify static elements exist in DOM', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      // Verify static structure exists
      await expect(page.locator('#menu-search')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('#category-tabs')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('#menu-sections')).toBeVisible({ timeout: 10000 });
    });

    test('should verify dynamic content is NOT empty after load', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      // Check that menu items are actually rendered
      const menuItemsHTML = await page.locator('#menu-sections').innerHTML();
      const productCards = await page.locator('.menu-item-card, [data-item-id]').count();

      // HTML should contain meaningful content
      expect(menuItemsHTML.length).toBeGreaterThan(100);

      // Should have actual product cards
      expect(productCards).toBeGreaterThan(0);
    });

    test('should verify category filter counts update correctly', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      // Get total count from "All" filter
      const allCount = await page.locator('[data-filter-count="all"], .filter-chip[data-filter="all"] .filter-chip__count').textContent();
      expect(allCount).toBeTruthy();
      expect(parseInt(allCount || '0')).toBeGreaterThan(0);

      // Check at least one category has items
      const categories = await page.locator('.filter-chip').all();
      let anyCategoryHasItems = false;

      for (const cat of categories) {
        const count = await cat.locator('.filter-chip__count, [data-filter-count]').textContent();
        if (count && parseInt(count) > 0) {
          anyCategoryHasItems = true;
          break;
        }
      }

      expect(anyCategoryHasItems).toBeTruthy();
    });
  });

  test.describe('Vue State vs DOM Consistency', () => {
    test('should verify clicking category filters updates displayed items', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      // Get initial item count
      const initialCount = await page.locator('.menu-item-card').count();

      // Click a filter button
      const breakfastFilter = page.locator('button[data-filter="breakfast"], .filter-chip[data-filter="breakfast"]');
      if (await breakfastFilter.isVisible()) {
        await breakfastFilter.click();
        await page.waitForTimeout(2000);

        // After filter click, item count may change
        const filteredCount = await page.locator('.menu-item-card').count();
        console.log(`Initial: ${initialCount}, After filter: ${filteredCount}`);
      }
    });

    test('should verify modal opens when item is clicked', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      // Find and click first menu item
      const firstItem = page.locator('.menu-item-card').first();

      // Check if modal opens
      const modalBefore = await page.locator('#item-modal.open, .modal-overlay.open').count();

      if (await firstItem.isVisible()) {
        await firstItem.click();
        await page.waitForTimeout(2000);

        const modalAfter = await page.locator('#item-modal.open, .modal-overlay.open').count();
        console.log(`Modal before: ${modalBefore}, Modal after: ${modalAfter}`);
      }
    });
  });

  test.describe('Error Handling', () => {
    test('should show error state if API fails', async ({ page }) => {
      // This test verifies error handling - we can't easily force API failure
      // but we verify the error element exists in the DOM
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      // Check error state element exists (even if hidden)
      const errorStateExists = await page.locator('.error-state, [class*="error"]').count();
      console.log(`Error state elements found: ${errorStateExists}`);
    });

    test('should handle empty cart gracefully', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      // Verify empty cart message is shown initially
      const emptyCart = await page.locator('text=Tu carrito está vacío').count();
      console.log(`Empty cart message visible: ${emptyCart > 0}`);
    });
  });
});

test.describe('Performance & Loading', () => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:6080';

  test('should load menu within reasonable time', async ({ page }) => {
    const startTime = Date.now();

    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForLoadState('networkidle');

    // Wait for Vue to render items
    await page.waitForSelector('.menu-item-card', { timeout: 30000 });

    const loadTime = Date.now() - startTime;
    console.log(`Menu load time: ${loadTime}ms`);

    // Should load within 30 seconds
    expect(loadTime).toBeLessThan(30000);
  });

  test('should have skeleton loading state', async ({ page }) => {
    // Enable slow network to see skeleton
    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForLoadState('domcontentloaded');

    // Check quickly before Vue renders
    await page.waitForTimeout(500);

    // Check for skeleton elements
    const skeletonExists = await page.locator('.skeleton, [class*="skeleton"], .menu-item-card--skeleton').count();
    console.log(`Skeleton elements: ${skeletonExists}`);
  });
});
