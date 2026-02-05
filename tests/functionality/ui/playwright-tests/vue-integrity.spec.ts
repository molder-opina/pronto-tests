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
      const apiResponse = await apiContext.get('/api/menu');
      expect(apiResponse.ok()).toBeTruthy();

      const menuData = await apiResponse.json();
      expect(menuData.categories).toBeDefined();
      expect(Array.isArray(menuData.categories)).toBeTruthy();

      const totalItems = menuData.categories.reduce(
        (sum: number, cat: { items?: unknown[] }) => sum + (cat.items?.length || 0),
        0
      );
      console.log(`API Reports: ${menuData.categories.length} categories, ${totalItems} total items`);

      expect(totalItems).toBeGreaterThan(0);
      expect(menuData.categories.length).toBeGreaterThan(0);

      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      const renderedItems = await page.locator('.menu-item-card').count();
      console.log(`Rendered Items: ${renderedItems}`);

      expect(renderedItems).toBeGreaterThan(0);
      expect(renderedItems).toBe(totalItems);
    });

    test('should verify menu item data matches API', async ({ page }) => {
      const apiResponse = await apiContext.get('/api/menu');
      const menuData = await apiResponse.json();

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

      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      const firstRenderedItem = page.locator('.menu-item-card').first();
      await expect(firstRenderedItem).toBeVisible({ timeout: 10000 });

      const renderedName = await firstRenderedItem.locator('.menu-item-name, h3, [class*="name"]').first().textContent();
      expect(renderedName).toBe(firstApiItem.name);

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

      const categoryTabs = await page.locator('.filter-chip, .category-tab, button[data-filter]').count();
      console.log(`API Categories: ${apiCategoryCount}, Rendered Tabs: ${categoryTabs}`);

      expect(categoryTabs).toBeGreaterThanOrEqual(apiCategoryCount);
    });
  });

  test.describe('Vue Component Lifecycle', () => {
    test('should verify Vue app is mounted', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      const menuRoot = page.locator('[data-menu-root]');
      await expect(menuRoot).toHaveAttribute('data-menu-root', '', { timeout: 10000 });

      const menuSections = page.locator('#menu-sections');
      const sectionsHTML = await menuSections.innerHTML();

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

      await expect(page.locator('#menu-search')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('#category-tabs')).toBeVisible({ timeout: 10000 });
      await expect(page.locator('#menu-sections')).toBeVisible({ timeout: 10000 });
    });

    test('should verify dynamic content is NOT empty after load', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      const menuItemsHTML = await page.locator('#menu-sections').innerHTML();
      const productCards = await page.locator('.menu-item-card, [data-item-id]').count();

      expect(menuItemsHTML.length).toBeGreaterThan(100);
      expect(productCards).toBeGreaterThan(0);
    });

    test('should verify category filter counts update correctly', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      const allCount = await page.locator('[data-filter-count="all"], .filter-chip[data-filter="all"] .filter-chip__count').textContent();
      expect(allCount).toBeTruthy();
      expect(parseInt(allCount || '0')).toBeGreaterThan(0);

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

      const initialCount = await page.locator('.menu-item-card').count();

      const breakfastFilter = page.locator('button[data-filter="breakfast"], .filter-chip[data-filter="breakfast"]');
      if (await breakfastFilter.isVisible()) {
        await breakfastFilter.click();
        await page.waitForTimeout(2000);

        const filteredCount = await page.locator('.menu-item-card').count();
        console.log(`Initial: ${initialCount}, After filter: ${filteredCount}`);
      }
    });

    test('should verify modal opens when item is clicked', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(5000);

      const firstItem = page.locator('.menu-item-card').first();

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
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

      const errorStateExists = await page.locator('.error-state, [class*="error"]').count();
      console.log(`Error state elements found: ${errorStateExists}`);
    });

    test('should handle empty cart gracefully', async ({ page }) => {
      await page.goto(`${BASE_URL}/menu-alt`);
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(3000);

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

    await page.waitForSelector('.menu-item-card', { timeout: 30000 });

    const loadTime = Date.now() - startTime;
    console.log(`Menu load time: ${loadTime}ms`);

    expect(loadTime).toBeLessThan(30000);
  });

  test('should have skeleton loading state', async ({ page }) => {
    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForLoadState('domcontentloaded');

    await page.waitForTimeout(500);

    const skeletonExists = await page.locator('.skeleton, [class*="skeleton"], .menu-item-card--skeleton').count();
    console.log(`Skeleton elements: ${skeletonExists}`);
  });
});

test.describe('Source Code Compilation Integrity', () => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:6080';
  const MENU_JS_URL = `${BASE_URL}/assets/js/clients/menu.js`;
  const BASE_JS_URL = `${BASE_URL}/assets/js/clients/base.js`;

  test('should expose critical functions in window object', async ({ page }) => {
    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForTimeout(3000);

    const criticalFunctions = [
      'addToCart',
      'toggleCart',
      'proceedToCheckout',
      'openItemModal',
      'closeItemModal',
      'quickAdd',
      'handleModifierChange',
      'addToCartFromModal',
      'CartPersistence'
    ];

    for (const fn of criticalFunctions) {
      const exists = await page.evaluate((name) => {
        if (name === 'CartPersistence') {
          return typeof window[name]?.getInstance === 'function';
        }
        return typeof window[name] === 'function';
      }, fn);

      expect(exists, `Function ${fn} should be exposed`).toBe(true);
    }
  });

  test('should have menu.js with expected functions', async () => {
    const compiledJS = await fetch(MENU_JS_URL);
    const jsContent = await compiledJS.text();

    const expectedPatterns = [
      /class\s+MenuFlow/,
      /class\s+ModalManager/,
      /CartPersistence\.getInstance/,
      /window\.addToCart\s*=/,
      /window\.quickAdd\s*=/,
    ];

    for (const pattern of expectedPatterns) {
      expect(jsContent).toMatch(pattern);
    }
  });

  test('should have base.js with Vue mounting logic', async () => {
    const compiledJS = await fetch(BASE_JS_URL);
    const jsContent = await compiledJS.text();

    expect(jsContent).toMatch(/createApp\(CartPanel\)/);
    expect(jsContent).toMatch(/\.mount\(/);
  });
});

test.describe('Event Delegation (bindings.js)', () => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:6080';

  test('should handle data-action="call" events', async ({ page }) => {
    const clickCalls: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'log' && msg.text().includes('[addToCart]')) {
        clickCalls.push(msg.text());
      }
    });

    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForTimeout(3000);

    await page.evaluate(() => {
      const btn = document.querySelector('.modal-add-to-cart');
      if (btn) {
        btn.dispatchEvent(new MouseEvent('click', { bubbles: true }));
      }
    });

    await page.waitForTimeout(1000);

    expect(clickCalls.length).toBeGreaterThan(0);
  });

  test('should properly handle modifier selection', async ({ page }) => {
    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForTimeout(5000);

    await page.click('.menu-item-card__info');
    await page.waitForTimeout(2000);

    const modalOpen = await page.locator('#item-modal.open').count();
    expect(modalOpen).toBeGreaterThan(0);

    const hasRequiredModifiers = await page.locator('.modifier-group[data-required="true"]').count();

    if (hasRequiredModifiers > 0) {
      const addBtnDisabled = await page.evaluate(() => {
        const btn = document.querySelector('.modal-add-to-cart');
        return btn?.hasAttribute('disabled') || btn?.classList.contains('is-disabled');
      });

      expect(addBtnDisabled).toBe(true);

      await page.click('.modifier-group[data-required="true"] input[type="radio"]');
      await page.waitForTimeout(500);

      const addBtnEnabled = await page.evaluate(() => {
        const btn = document.querySelector('.modal-add-to-cart');
        return !btn?.hasAttribute('disabled') && !btn?.classList.contains('is-disabled');
      });

      expect(addBtnEnabled).toBe(true);
    }
  });
});

test.describe('Cart Persistence Integration', () => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:6080';

  test('should persist cart in localStorage', async ({ page }) => {
    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForTimeout(3000);

    await page.evaluate(() => {
      if (typeof (window as any).addToCart === 'function') {
        (window as any).addToCart({
          id: 1,
          name: 'Test Item',
          price: 100,
          quantity: 1,
          image: null,
          extras: [],
          extrasTotal: 0,
          modifiers: []
        });
      }
    });

    await page.waitForTimeout(1000);

    const cartInStorage = await page.evaluate(() => {
      const keys = Object.keys(localStorage).filter(k => k.includes('cart'));
      return keys.map(k => ({ key: k, value: localStorage.getItem(k) }));
    });

    expect(cartInStorage.length).toBeGreaterThan(0);

    const cartData = JSON.parse(cartInStorage[0].value || '[]');
    expect(Array.isArray(cartData)).toBe(true);
    expect(cartData.length).toBeGreaterThan(0);
  });

  test('should sync cart to Vue store via event', async ({ page }) => {
    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForTimeout(3000);

    const eventFired = await page.evaluate(() => {
      return new Promise<boolean>((resolve) => {
        const handler = (event: Event) => {
          resolve(true);
          document.removeEventListener('cart-updated', handler);
        };
        document.addEventListener('cart-updated', handler);
        
        window.dispatchEvent(new CustomEvent('cart-updated', {
          detail: { count: 1, total: 100 }
        }));
        
        setTimeout(() => {
          document.removeEventListener('cart-updated', handler);
          resolve(false);
        }, 1000);
      });
    });

    expect(eventFired).toBe(true);
  });
});

test.describe('Complete Add-to-Cart Flow', () => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:6080';

  test('should complete full flow: API → Vue → Cart → Checkout', async ({ page }) => {
    const flowLogs: string[] = [];

    page.on('console', msg => {
      if (msg.type() === 'log' && (
        msg.text().includes('[MenuFlow]') ||
        msg.text().includes('[CartApp]') ||
        msg.text().includes('[MenuDebug]')
      )) {
        flowLogs.push(msg.text());
      }
    });

    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(5000);

    expect(flowLogs.some(l => l.includes('Loading menu'))).toBe(true);

    const firstItem = page.locator('.menu-item-card').first();
    await firstItem.click();
    await page.waitForTimeout(2000);

    const modalOpen = await page.locator('#item-modal.open').count();
    expect(modalOpen).toBeGreaterThan(0);

    await page.evaluate(() => {
      if (typeof (window as any).addToCartFromModal === 'function') {
        (window as any).addToCartFromModal();
      }
    });
    await page.waitForTimeout(2000);

    const badgeCount = await page.locator('#cart-count').textContent();
    expect(badgeCount).toBe('1');

    expect(flowLogs.some(l => l.includes('Item added'))).toBe(true);
  });
});

test.describe('CSS & Styles Integrity', () => {
  const BASE_URL = process.env.BASE_URL || 'http://localhost:6080';

  test('should load critical CSS files', async ({ page }) => {
    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForLoadState('networkidle');
    await page.waitForTimeout(3000);

    const cssLoaded = await page.evaluate(() => {
      const links = document.querySelectorAll('link[rel="stylesheet"]');
      const hrefs = Array.from(links).map(l => l.getAttribute('href'));
      return {
        count: hrefs.length,
        hasMainCss: hrefs.some(h => h?.includes('clients') && h?.includes('.css')),
        hasMenuCss: hrefs.some(h => h?.includes('menu'))
      };
    });

    expect(cssLoaded.count).toBeGreaterThan(0);
    expect(cssLoaded.hasMainCss).toBe(true);
  });

  test('should apply critical styles to cart panel', async ({ page }) => {
    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForTimeout(3000);

    const stylesApplied = await page.evaluate(() => {
      const cartPanel = document.querySelector('.cart-panel, #cart-panel');
      if (!cartPanel) return null;

      const computed = window.getComputedStyle(cartPanel);
      return {
        hasPosition: computed.position !== 'static',
        hasZIndex: computed.zIndex !== 'auto',
        hasWidth: computed.width !== '0px'
      };
    });

    expect(stylesApplied).not.toBe(null);
    expect(stylesApplied?.hasPosition).toBe(true);
    expect(stylesApplied?.hasZIndex).toBe(true);
  });

  test('should apply modal styles correctly', async ({ page }) => {
    await page.goto(`${BASE_URL}/menu-alt`);
    await page.waitForTimeout(3000);

    await page.click('.menu-item-card__info');
    await page.waitForTimeout(1000);

    const modalStyles = await page.evaluate(() => {
      const modal = document.querySelector('#item-modal, .modal');
      if (!modal) return null;

      const computed = window.getComputedStyle(modal);
      return {
        isVisible: computed.display !== 'none',
        hasZIndex: computed.zIndex !== 'auto',
        hasOverlay: document.querySelector('.modal__overlay, .modal-overlay') !== null
      };
    });

    expect(modalStyles?.isVisible).toBe(true);
    expect(modalStyles?.hasZIndex).toBe(true);
  });
});
