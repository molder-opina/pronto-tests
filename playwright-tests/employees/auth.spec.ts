import { test, expect } from '@playwright/test';

test.describe('Employee Authentication', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('should display login form', async ({ page }) => {
    await expect(page.locator('h1')).toContainText('Administración');
    await expect(page.locator('input[type="email"]')).toBeVisible();
    await expect(page.locator('input[type="password"]')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
  });

  test('should login with valid credentials', async ({ page }) => {
    await page.fill('input[type="email"]', 'admin@cafeteria.test');
    await page.fill('input[type="password"]', 'ChangeMe!123');
    await page.click('button[type="submit"]');

    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('text=Órdenes en Curso')).toBeVisible();
  });

  test('should show error with invalid credentials', async ({ page }) => {
    await page.fill('input[type="email"]', 'wrong@email.com');
    await page.fill('input[type="password"]', 'wrongpassword');
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Credenciales inválidas')).toBeVisible();
  });

  test('should require email and password', async ({ page }) => {
    await page.click('button[type="submit"]');

    await expect(page.locator('text=Email es requerido')).toBeVisible();
    await expect(page.locator('text=Contraseña es requerida')).toBeVisible();
  });

  test('should logout successfully', async ({ page }) => {
    await page.fill('input[type="email"]', 'admin@cafeteria.test');
    await page.fill('input[type="password"]', 'ChangeMe!123');
    await page.click('button[type="submit"]');
    await page.waitForURL('/dashboard');

    await page.click('button:has-text("Cerrar Sesión")');

    await expect(page).toHaveURL('/login');
  });
});
