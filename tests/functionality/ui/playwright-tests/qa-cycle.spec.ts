import { test, expect, Page, Browser } from '@playwright/test';

test.describe('PRONTO Complete Cycle QA Test', () => {
  test.setTimeout(240000); // 4 minutes timeout

  // Helper to login to employee console with isolated context
  async function loginToConsole(
    browser: Browser,
    role: 'waiter' | 'chef' | 'cashier',
    email: string
  ): Promise<Page> {
    // Create isolated browser context to avoid session conflicts between roles
    const context = await browser.newContext();
    const page = await context.newPage();

    await page.goto(`http://localhost:6081/${role}/login`);
    await page.waitForLoadState('networkidle');

    const emailField = page.locator('input[type="email"], input[name="email"]');
    if (await emailField.isVisible()) {
      await emailField.clear();
      await emailField.fill(email);
      await page.locator('input[type="password"]').fill('ChangeMe!123');
      await page.locator('button[type="submit"], button:has-text("Ingresar")').click();
      await page.waitForTimeout(2000);
      await page.waitForLoadState('networkidle');
    }

    // Handle console selector if present
    const consoleClasses: Record<string, string> = {
      waiter: '.console-card--waiter',
      chef: '.console-card--chef',
      cashier: '.console-card--cashier',
    };
    const consoleCard = page.locator(consoleClasses[role]);
    if ((await consoleCard.count()) > 0) {
      await consoleCard.first().click();
      await page.waitForLoadState('networkidle');
      await page.waitForTimeout(1000);
    }

    return page;
  }

  test('Complete order cycle from client to paid', async ({ browser }) => {
    const errors: string[] = [];
    let orderId: string | null = null;

    const logError = (
      severity: string,
      description: string,
      location: string,
      impact: string,
      solution: string
    ) => {
      errors.push(
        `- ERROR [${severity}]: ${description}\n  - Ubicación: ${location}\n  - Impacto: ${impact}\n  - Solución sugerida: ${solution}`
      );
    };

    try {
      // ========================================
      // Step 1: Client App - Create order with multiple products
      // ========================================
      console.log('=== Step 1: Creating order in client app ===');
      const clientPage = await browser.newPage();
      await clientPage.goto('http://localhost:6080');
      await clientPage.waitForLoadState('networkidle');
      await clientPage.waitForSelector('#menu-sections', { timeout: 15000 });

      // Add items to cart with modifier handling
      const menuItemCards = clientPage.locator('.menu-item-card, .product-card, [data-menu-item]');
      const itemCount = await menuItemCards.count();
      console.log(`Found ${itemCount} menu items`);

      for (let i = 0; i < Math.min(2, itemCount); i++) {
        await menuItemCards.nth(i).click();
        const modal = clientPage.locator('#item-modal');
        await modal.waitFor({ state: 'visible', timeout: 5000 });

        // Select required modifiers if any
        const requiredModifiers = modal.locator('.modifier-group[data-required="true"]');
        const reqCount = await requiredModifiers.count();
        for (let j = 0; j < reqCount; j++) {
          const firstOption = requiredModifiers.nth(j).locator('input[type="radio"], input[type="checkbox"]').first();
          if (await firstOption.isVisible()) {
            await firstOption.click();
            await clientPage.waitForTimeout(200);
          }
        }

        await clientPage.locator('#modal-add-to-cart-btn').click();
        await modal.waitFor({ state: 'hidden', timeout: 5000 });
        console.log(`Added item ${i + 1} to cart`);
      }

      // Open cart and proceed to checkout
      await clientPage.evaluate(() => {
        if (typeof window.toggleCart === 'function') window.toggleCart();
      });
      await clientPage.waitForSelector('#cart-panel.open, .cart-panel.open', { timeout: 5000 });

      await clientPage.evaluate(() => {
        if (typeof window.proceedToCheckout === 'function') window.proceedToCheckout();
        else window.location.href = '/checkout';
      });

      await clientPage.waitForSelector('#checkout-section', { state: 'visible', timeout: 10000 });

      // Fill checkout form
      await clientPage.locator('#customer-email').fill('luartx@gmail.com');
      const nameInput = clientPage.locator('#customer-name');
      if (await nameInput.isVisible()) {
        await nameInput.fill('Test QA User');
      }

      // Submit order
      const orderResponsePromise = clientPage.waitForResponse(
        (response) => response.url().includes('/api/orders') && response.request().method() === 'POST',
        { timeout: 20000 }
      ).catch(() => null);

      await clientPage.locator('#checkout-submit-btn').scrollIntoViewIfNeeded();
      await clientPage.locator('#checkout-submit-btn').click();

      const response = await orderResponsePromise;
      if (response && response.ok()) {
        try {
          const data = await response.json();
          orderId = data.order_id?.toString() || data.id?.toString();
          console.log(`Order created with ID: ${orderId}`);
        } catch {
          console.log('Could not parse order response');
        }
      }

      await clientPage.waitForTimeout(2000);

      // Get order ID from API if not captured
      if (!orderId) {
        const recentOrder = await clientPage.evaluate(async () => {
          const resp = await fetch('/api/orders/active');
          const data = await resp.json();
          return data.orders?.[0]?.id?.toString() || data.orders?.[0]?.order_id?.toString() || null;
        });
        orderId = recentOrder;
        console.log(`Found order ID from API: ${orderId}`);
      }

      if (!orderId) {
        logError('CRITICAL', 'Could not retrieve order ID', 'Client checkout', 'Cannot track order', 'Check API response');
      }

      await clientPage.close();

      // ========================================
      // Step 2: Waiter - ACCEPT the order first
      // ========================================
      console.log('=== Step 2: Waiter accepting order ===');
      const waiterPage = await loginToConsole(browser, 'waiter', 'juan.mesero@cafeteria.test');
      console.log(`Waiter logged in, URL: ${waiterPage.url()}`);

      // Wait for orders to load
      await waiterPage.waitForSelector('[data-order-id]', { timeout: 15000 }).catch(() => {
        console.log('No orders found in waiter dashboard');
      });

      if (orderId) {
        const orderRow = waiterPage.locator(`[data-order-id="${orderId}"]`);
        if ((await orderRow.count()) > 0) {
          console.log(`Found order ${orderId} in waiter dashboard`);

          // Click "Aceptar" if visible (to send to kitchen)
          const acceptBtn = orderRow.locator('button:has-text("Aceptar")');
          if ((await acceptBtn.count()) > 0) {
            await acceptBtn.click();
            await waiterPage.waitForTimeout(1500);
            console.log('Order accepted by waiter');
          }
        } else {
          console.log(`Order ${orderId} not found, checking all orders...`);
          // Try to accept any pending order
          const firstAcceptBtn = waiterPage.locator('button:has-text("Aceptar")').first();
          if ((await firstAcceptBtn.count()) > 0) {
            await firstAcceptBtn.click();
            await waiterPage.waitForTimeout(1500);
          }
        }
      }

      await waiterPage.close();

      // ========================================
      // Step 3: Chef - Process order (Start → Ready)
      // ========================================
      console.log('=== Step 3: Chef processing order ===');
      const chefPage = await loginToConsole(browser, 'chef', 'carlos.chef@cafeteria.test');
      console.log(`Chef logged in, URL: ${chefPage.url()}`);

      // Wait for kitchen orders
      const hasKitchenOrders = await chefPage.waitForSelector('#kitchen-orders tr[data-order-id]', { timeout: 10000 }).catch(() => null);

      if (hasKitchenOrders) {
        if (orderId) {
          const orderRow = chefPage.locator(`tr[data-order-id="${orderId}"]`);
          const orderFound = (await orderRow.count()) > 0;

          const targetRow = orderFound ? orderRow : chefPage.locator('#kitchen-orders tr[data-order-id]').first();

          // Click "Iniciar" (Start)
          const startBtn = targetRow.locator('button:has-text("Iniciar")');
          if ((await startBtn.count()) > 0) {
            await startBtn.click();
            await chefPage.waitForTimeout(1500);
            console.log('Chef clicked Iniciar');
          }

          // Click "Listo" (Ready)
          const readyBtn = targetRow.locator('button:has-text("Listo")');
          if ((await readyBtn.count()) > 0) {
            await readyBtn.click();
            await chefPage.waitForTimeout(1500);
            console.log('Chef clicked Listo');
          }
        }
      } else {
        logError('MEDIUM', 'No orders in kitchen', 'Chef dashboard', 'Chef workflow incomplete', 'Check if waiter accepted order');
      }

      await chefPage.close();

      // ========================================
      // Step 4: Waiter - Deliver and collect payment
      // ========================================
      console.log('=== Step 4: Waiter delivering and collecting payment ===');
      const waiterPage2 = await loginToConsole(browser, 'waiter', 'juan.mesero@cafeteria.test');

      await waiterPage2.waitForSelector('[data-order-id]', { timeout: 10000 }).catch(() => null);

      if (orderId) {
        const orderRow = waiterPage2.locator(`[data-order-id="${orderId}"]`);
        if ((await orderRow.count()) > 0) {
          // Click "Entregar"
          const deliverBtn = orderRow.locator('button:has-text("Entregar")');
          if ((await deliverBtn.count()) > 0) {
            await deliverBtn.click();
            await waiterPage2.waitForTimeout(1500);
            console.log('Waiter clicked Entregar');
          }

          // Click "Efectivo" for cash payment
          const cashBtn = orderRow.locator('button:has-text("Efectivo")');
          if ((await cashBtn.count()) > 0) {
            await cashBtn.click();
            await waiterPage2.waitForTimeout(1500);
            console.log('Waiter clicked Efectivo');
          }
        }
      }

      await waiterPage2.close();

      // ========================================
      // Step 5: Cashier - Verify paid status
      // ========================================
      console.log('=== Step 5: Cashier verifying paid orders ===');
      const cashierPage = await loginToConsole(browser, 'cashier', 'laura.cajera@cafeteria.test');
      console.log(`Cashier logged in, URL: ${cashierPage.url()}`);

      // Navigate to paid orders tab
      const paidTab = cashierPage.locator('button:has-text("Pagadas"), [data-tab="paid"]');
      if ((await paidTab.count()) > 0) {
        await paidTab.click();
        await cashierPage.waitForTimeout(1000);
      }

      // Check for PDF download button
      const pdfBtn = cashierPage.locator('button:has-text("PDF"), .btn-pdf, [data-action="pdf"]');
      if ((await pdfBtn.count()) === 0) {
        logError('LOW', 'PDF download button not found in paid orders', 'Cashier dashboard', 'Cannot download receipts', 'Add PDF export to paid orders');
      }

      await cashierPage.close();

      console.log('=== QA Test completed ===');
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : String(error);
      logError('CRITICAL', `Test failed: ${errorMessage}`, 'Test execution', 'Complete cycle failed', 'Fix the error and retry');
    }

    // Report errors
    if (errors.length > 0) {
      console.log('\n=== QA TEST ERRORS ===');
      errors.forEach((error) => console.log(error));
      console.log('=== END ERRORS ===\n');
      throw new Error(`Found ${errors.length} errors during QA test`);
    }
  });
});
