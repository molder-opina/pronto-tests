import { test, expect } from '@playwright/test';

test('complete order cycle - client side', async ({ page }) => {
  await page.goto('http://localhost:6080');

  // Step 1: Add item with mandatory options and verify validation
  await page.click('text=Combo Familiar');
  // Attempt to add without options - button should be disabled
  const addToCartButton = page.locator('text=Agregar al carrito');
  await expect(addToCartButton).toBeDisabled();
  // Check if validation message is shown
  const validationMessage = await page.locator('[title*="Selecciona:"]').first();
  await expect(validationMessage).toBeVisible();

  // Select mandatory options
  await page.click('text=Coca-Cola');
  await page.click('text=Papas Fritas Clásicas');
  await page.click('text=Salsa BBQ');
  await page.click('text=Agregar al carrito');

  // Step 2: Add more distinct products
  // Product 2: Drink
  await page.click('text=Bebidas');
  await page.locator('article:has-text("Coca-Cola") .menu-item-card__quick-add').click();
  await page.click('text=Mediana (500ml)');
  await page.click('text=Agregar al carrito');

  // Product 3: Dessert
  await page.click('text=Postres');
  await page
    .locator('article:has-text("Cheesecake Frutos Rojos") .menu-item-card__quick-add')
    .click();
  await page.click('text=Salsa de Chocolate');
  await page.click('text=Agregar al carrito');

  // Step 3: Checkout
  await page.click('button[aria-label="Ver carrito"]');
  await page.click('text=Ir a pagar');

  // Step 4: Fill customer details
  await page.fill('#customer-name', 'Juan Perez');
  await page.fill('#customer-email', 'luartx@gmail.com');

  // Step 5: Submit order
  await page.click('text=Confirmar Pedido');

  // Step 6: Verify confirmation
  await expect(page.locator('text=En progreso')).toBeVisible();
});
