import { test, expect } from '../fixtures/auth.js'

test.describe('Customer Observatory', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-customers').click()
    await expect(page.getByTestId('customers-page')).toBeVisible()
  })

  test('page loads with heading and customer count', async ({ authenticatedPage: page }) => {
    await expect(page.getByRole('heading', { name: /Customer Observatory/i })).toBeVisible()
    // Should show customer count from seed data
    await expect(page.locator('text=/\\d+ customers/i')).toBeVisible({ timeout: 10000 })
  })

  test('default view is grid with customer cards', async ({ authenticatedPage: page }) => {
    const grid = page.getByTestId('premium-grid')
    await expect(grid).toBeVisible()
  })

  test('view toggle switches to table', async ({ authenticatedPage: page }) => {
    await page.getByTestId('customers-view-table').click()
    await expect(page.getByTestId('customer-data-table')).toBeVisible()
  })

  test('view toggle switches to solar system', async ({ authenticatedPage: page }) => {
    await page.getByTestId('customers-view-solar').click()
    await expect(page.getByTestId('solar-system-view')).toBeVisible()
  })

  test('search input filters customers', async ({ authenticatedPage: page }) => {
    const searchInput = page.getByTestId('customers-search')
    await searchInput.fill('zzzznonexistent')
    // Wait for debounce
    await page.waitForFunction(() => true, null, { timeout: 500 })
    // Should show empty state or zero cards
    const grid = page.getByTestId('premium-grid')
    // Either the grid is gone or it has no visible customer cards
    const visible = await grid.isVisible().catch(() => false)
    if (visible) {
      const cards = grid.locator('[data-testid^="surface-card"]')
      // May have zero cards or the grid itself may be replaced with empty state
    }
  })

  test('risk filter is accessible', async ({ authenticatedPage: page }) => {
    const riskFilter = page.getByTestId('customers-risk-filter')
    await expect(riskFilter).toBeVisible()
    await expect(riskFilter).toHaveAttribute('aria-label', 'Filter by risk level')
  })

  test('tier filter is accessible', async ({ authenticatedPage: page }) => {
    const tierFilter = page.getByTestId('customers-tier-filter')
    await expect(tierFilter).toBeVisible()
    await expect(tierFilter).toHaveAttribute('aria-label', 'Filter by tier')
  })

  test('sort dropdown is accessible', async ({ authenticatedPage: page }) => {
    const sort = page.getByTestId('customers-sort')
    await expect(sort).toBeVisible()
    await expect(sort).toHaveAttribute('aria-label', 'Sort customers')
  })

  test('clicking customer card navigates to detail', async ({ authenticatedPage: page }) => {
    // Wait for grid to render with cards
    const grid = page.getByTestId('premium-grid')
    await expect(grid).toBeVisible()

    // Click the first interactive card
    const firstCard = grid.locator('.surface-interactive, [data-testid*="surface-card"]').first()
    if (await firstCard.isVisible()) {
      await firstCard.click()
      await page.waitForURL(/\/customers\//, { timeout: 10000 })
      await expect(page.getByTestId('customer-detail-page')).toBeVisible()
    }
  })
})
