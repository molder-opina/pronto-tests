import { test, expect } from '@playwright/test'

test.describe('Menu Management', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="email"]', 'admin@pronto.com')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('/dashboard')
  })

  test('should display menu items', async ({ page }) => {
    await page.goto('/menu')

    await expect(page.locator('h1')).toContainText('Menu Items')
    await expect(page.locator('[data-testid="menu-items-grid"]')).toBeVisible()
  })

  test('should create new menu item', async ({ page }) => {
    await page.goto('/menu/new')

    await page.fill('input[data-testid="item-name"]', 'Test Item')
    await page.fill('textarea[data-testid="item-description"]', 'Test description')
    await page.fill('input[data-testid="item-price"]', '15.00')
    await page.fill('input[data-testid="item-prep-time"]', '20')

    await page.click('button:has-text("Save Item")')

    await expect(page.locator('text=Item created successfully')).toBeVisible()
    await expect(page).toHaveURL('/menu')
  })

  test('should edit menu item', async ({ page }) => {
    await page.goto('/menu')
    await page.click('[data-testid="menu-items-grid"] article:first-child button:has-text("Edit")')

    await page.fill('input[data-testid="item-name"]', 'Updated Item Name')
    await page.click('button:has-text("Save Item")')

    await expect(page.locator('text=Item updated successfully')).toBeVisible()
    await expect(page.locator('text=Updated Item Name')).toBeVisible()
  })

  test('should toggle item availability', async ({ page }) => {
    await page.goto('/menu')
    const firstItem = page.locator('[data-testid="menu-items-grid"] article:first-child')

    const toggleButton = firstItem.locator('button:has-text("Toggle Availability")')
    await toggleButton.click()

    await expect(page.locator('text=Item availability updated')).toBeVisible()
  })

  test('should delete menu item', async ({ page }) => {
    await page.goto('/menu')
    const firstItem = page.locator('[data-testid="menu-items-grid"] article:first-child')

    await firstItem.click('button:has-text("Delete")')
    await page.click('button:has-text("Confirm")')

    await expect(page.locator('text=Item deleted successfully')).toBeVisible()
  })

  test('should filter menu items by category', async ({ page }) => {
    await page.goto('/menu')

    await page.selectOption('select[data-testid="category-filter"]', 'pizza')

    const items = await page.locator('[data-testid="menu-items-grid"] article').count()
    for (let i = 0; i < items; i++) {
      const item = page.locator('[data-testid="menu-items-grid"] article').nth(i)
      await expect(item.locator('[data-testid="item-category"]')).toContainText('Pizza')
    }
  })
})
