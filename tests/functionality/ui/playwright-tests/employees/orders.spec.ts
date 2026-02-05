import { test, expect } from '@playwright/test'
import { installApi404405Guard } from '../helpers/api_guard'

test.describe('Order Management', () => {
  test.beforeEach(async ({ page }) => {
    const guard = installApi404405Guard(page)
    ;(page as any).__apiGuard = guard
  })

  test.afterEach(async ({ page }) => {
    const guard = (page as any).__apiGuard as
      | { assertNoFailures: () => void }
      | undefined
    guard?.assertNoFailures()
  })

  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.fill('input[type="email"]', 'admin@pronto.com')
    await page.fill('input[type="password"]', 'admin123')
    await page.click('button[type="submit"]')
    await page.waitForURL('/dashboard')
  })

  test('should display active orders table', async ({ page }) => {
    await page.goto('/orders')

    await expect(page.locator('h1')).toContainText('Active Orders')
    await expect(page.locator('table[data-testid="orders-table"]')).toBeVisible()
  })

  test('should create new order', async ({ page }) => {
    await page.goto('/orders/new')

    await page.fill('input[data-testid="customer-name"]', 'John Doe')
    await page.fill('input[data-testid="customer-phone"]', '+1234567890')

    await page.click('button:has-text("Add Item")')
    await page.fill('input[data-testid="item-search"]', 'Pizza')
    await page.click('text=Margherita Pizza')
    await page.fill('input[data-testid="item-quantity"]', '2')

    await page.click('button:has-text("Create Order")')

    await expect(page.locator('text=Order created successfully')).toBeVisible()
    await expect(page).toHaveURL(/\/orders\/\d+/)
  })

  test('should view order details', async ({ page }) => {
    await page.goto('/orders')
    await page.click('table[data-testid="orders-table"] tbody tr:first-child a:has-text("View")')

    await expect(page.locator('h1')).toContainText('Order Details')
    await expect(page.locator('[data-testid="order-id"]')).toBeVisible()
    await expect(page.locator('[data-testid="order-status"]')).toBeVisible()
  })

  test('should update order status', async ({ page }) => {
    await page.goto('/orders')
    await page.click('table[data-testid="orders-table"] tbody tr:first-child a:has-text("View")')

    await page.click('button:has-text("Mark as In Progress")')

    await expect(page.locator('[data-testid="order-status"]')).toContainText('In Progress')
  })

  test('should add payment to order', async ({ page }) => {
    await page.goto('/orders')
    await page.click('table[data-testid="orders-table"] tbody tr:first-child a:has-text("View")')

    await page.click('button:has-text("Add Payment")')
    await page.fill('input[data-testid="payment-amount"]', '50.00')
    await page.selectOption('select[data-testid="payment-method"]', 'cash')
    await page.click('button:has-text("Process Payment")')

    await expect(page.locator('text=Payment processed successfully')).toBeVisible()
  })

  test('should filter orders by status', async ({ page }) => {
    await page.goto('/orders')

    await page.selectOption('select[data-testid="status-filter"]', 'pending')

    const rows = await page.locator('table[data-testid="orders-table"] tbody tr').count()
    for (let i = 0; i < rows; i++) {
      const statusCell = page.locator('table[data-testid="orders-table"] tbody tr').nth(i).locator('td[data-status]')
      await expect(statusCell).toContainText('Pending')
    }
  })
})
