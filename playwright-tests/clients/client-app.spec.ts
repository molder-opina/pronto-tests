import { test, expect } from '@playwright/test';

test.describe('Client Application', () => {
  test('should display welcome page', async ({ page }) => {
    await page.goto('/');

    await expect(page.locator('#menu-search')).toBeVisible();
    await expect(page.locator('.category-tabs')).toBeVisible();
  });

  test('should display menu items', async ({ page }) => {
    await page.goto('/menu');

    await expect(page.locator('#menu-search')).toBeVisible();
    await expect(page.locator('.category-tabs')).toBeVisible();
  });

  test('should search for menu items', async ({ page }) => {
    await page.goto('/menu');

    await page.fill('input[data-testid="search-input"]', 'Pizza');

    const items = await page.locator('[data-testid="menu-item-card"]').count();
    for (let i = 0; i < items; i++) {
      const item = page.locator('[data-testid="menu-item-card"]').nth(i);
      await expect(item.locator('h3')).toContainText('Pizza', { ignoreCase: true });
    }
  });

  test('should filter by category', async ({ page }) => {
    await page.goto('/menu');

    await page.locator('button:has-text("Pizza")').click();

    const items = await page.locator('[data-testid="menu-item-card"]').count();
    for (let i = 0; i < items; i++) {
      const item = page.locator('[data-testid="menu-item-card"]').nth(i);
      await expect(item.locator('[data-testid="item-category"]')).toContainText('Pizza');
    }
  });

  test('should add item to cart', async ({ page }) => {
    await page.goto('/menu');

    const firstItem = page.locator('[data-testid="menu-item-card"]').first();
    await firstItem.locator('button:has-text("Add to Cart")').click();

    await expect(page.locator('[data-testid="cart-badge"]')).toContainText('1');
  });

  test('should view cart', async ({ page }) => {
    await page.goto('/menu');
    await page
      .locator('[data-testid="menu-item-card"]')
      .first()
      .locator('button:has-text("Add to Cart")')
      .click();
    await page.locator('[data-testid="cart-button"]').click();

    await expect(page).toHaveURL('/cart');
    await expect(page.locator('h1')).toContainText('Tu Carrito');
  });

  test('should update cart item quantity', async ({ page }) => {
    await page.goto('/menu');
    await page
      .locator('[data-testid="menu-item-card"]')
      .first()
      .locator('button:has-text("Add to Cart")')
      .click();
    await page.locator('[data-testid="cart-button"]').click();

    const firstItem = page.locator('[data-testid="cart-item"]').first();
    await firstItem.locator('button[aria-label="Increase quantity"]').click();

    await expect(firstItem.locator('[data-testid="item-quantity"]')).toContainText('2');
  });

  test('should remove item from cart', async ({ page }) => {
    await page.goto('/menu');
    await page
      .locator('[data-testid="menu-item-card"]')
      .first()
      .locator('button:has-text("Add to Cart")')
      .click();
    await page.locator('[data-testid="cart-button"]').click();

    const firstItem = page.locator('[data-testid="cart-item"]').first();
    await firstItem.locator('button:has-text("Remove")').click();

    await expect(page.locator('[data-testid="cart-empty-message"]')).toBeVisible();
  });

  test('should checkout with cart items', async ({ page }) => {
    await page.goto('/menu');
    await page
      .locator('[data-testid="menu-item-card"]')
      .first()
      .locator('button:has-text("Add to Cart")')
      .click();
    await page.locator('[data-testid="cart-button"]').click();

    await page.locator('button:has-text("Checkout")').click();

    await expect(page).toHaveURL('/checkout');
    await expect(page.locator('h1')).toContainText('Finalizar pedido');
  });

  test('should complete checkout process', async ({ page }) => {
    await page.goto('/menu');
    await page
      .locator('[data-testid="menu-item-card"]')
      .first()
      .locator('button:has-text("Add to Cart")')
      .click();
    await page.locator('[data-testid="cart-button"]').click();
    await page.locator('button:has-text("Checkout")').click();

    await page.locator('input[data-testid="name"]').fill('John Doe');
    await page.locator('input[data-testid="phone"]').fill('+1234567890');
    await page.locator('input[data-testid="address"]').fill('123 Test Street');

    await page.locator('button:has-text("Place Order")').click();

    await expect(page.locator('text=Pedido realizado exitosamente')).toBeVisible();
    await expect(page).toHaveURL(/\/orders\/\d+/);
  });
});
