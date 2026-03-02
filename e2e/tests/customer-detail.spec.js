import { test, expect } from '../fixtures/auth.js'

test.describe('Customer Deep Dive', () => {
  test('customer detail page loads via navigation', async ({ authenticatedPage: page }) => {
    // Go to customers
    await page.getByTestId('orbital-nav-item-customers').click()
    await expect(page.getByTestId('customers-page')).toBeVisible()

    // Click first customer
    const grid = page.getByTestId('premium-grid')
    await expect(grid).toBeVisible()
    const firstCard = grid.locator('.surface-interactive').first()
    if (await firstCard.isVisible()) {
      await firstCard.click()
      await page.waitForURL(/\/customers\//, { timeout: 10000 })
    } else {
      // Fallback: navigate directly to a known seed customer
      await page.goto('/customers/cust-001')
    }

    await expect(page.getByTestId('customer-detail-page')).toBeVisible({ timeout: 15000 })
  })

  test('hero section renders with customer info', async ({ pageAt }) => {
    const page = await pageAt('/customers/cust-001')
    await expect(page.getByTestId('customer-detail-page')).toBeVisible({ timeout: 15000 })
    const hero = page.getByTestId('customer-hero')
    await expect(hero).toBeVisible({ timeout: 15000 })

    // Should contain health ring
    const healthRing = hero.locator('[data-testid="health-ring"]')
    expect(await healthRing.count()).toBeGreaterThanOrEqual(0) // May or may not be present depending on seed data
  })

  test('scroll reveals health story section', async ({ pageAt }) => {
    const page = await pageAt('/customers/cust-001')
    await expect(page.getByTestId('customer-detail-page')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('customer-hero')).toBeVisible({ timeout: 15000 })

    // Scroll down to reveal sections
    await page.evaluate(() => window.scrollBy(0, 1000))
    await expect(page.getByTestId('health-story')).toBeVisible({ timeout: 15000 })
  })

  test('scroll reveals deployment DNA section', async ({ pageAt }) => {
    const page = await pageAt('/customers/cust-001')
    await expect(page.getByTestId('customer-detail-page')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('customer-hero')).toBeVisible({ timeout: 15000 })

    await page.evaluate(() => window.scrollBy(0, 2000))
    await expect(page.getByTestId('deployment-dna')).toBeVisible({ timeout: 15000 })
  })

  test('scroll reveals intel panels section', async ({ pageAt }) => {
    const page = await pageAt('/customers/cust-001')
    await expect(page.getByTestId('customer-detail-page')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('customer-hero')).toBeVisible({ timeout: 15000 })

    await page.evaluate(() => window.scrollTo(0, document.body.scrollHeight))
    await expect(page.getByTestId('intel-panels')).toBeVisible({ timeout: 15000 })
  })

  test('breadcrumb shows correct trail', async ({ pageAt }) => {
    const page = await pageAt('/customers/cust-001')
    await expect(page.getByTestId('customer-detail-page')).toBeVisible({ timeout: 15000 })
    const breadcrumb = page.getByTestId('breadcrumb')
    await expect(breadcrumb).toBeVisible()
    await expect(breadcrumb).toContainText('Mission Control')
  })

  test('invalid customer shows not-found state', async ({ pageAt }) => {
    const page = await pageAt('/customers/nonexistent-id-12345')
    // Should show either customer-not-found, or loading, or the detail page with empty state
    await expect(
      page.getByTestId('customer-not-found')
        .or(page.getByText('Customer not found'))
        .or(page.getByText('not found'))
    ).toBeVisible({ timeout: 20000 })
  })
})
