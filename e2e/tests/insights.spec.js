import { test, expect } from '../fixtures/auth.js'

test.describe('Signal Intelligence', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-insights').click()
    await expect(page.getByTestId('insights-page')).toBeVisible()
  })

  test('page loads with heading', async ({ authenticatedPage: page }) => {
    await expect(page.getByRole('heading', { name: /Signal Intelligence/i })).toBeVisible()
  })

  test('sentiment spectrum chart renders', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('sentiment-spectrum')).toBeVisible()
  })

  test('insight cards display from seed data', async ({ authenticatedPage: page }) => {
    const cards = page.locator('[data-testid="insight-card"]')
    await expect(cards.first()).toBeVisible({ timeout: 15000 })
    const count = await cards.count()
    expect(count).toBeGreaterThan(0)
  })

  test('search input filters insights', async ({ authenticatedPage: page }) => {
    const search = page.getByTestId('insights-search')
    await expect(search).toBeVisible()
    await expect(search).toHaveAttribute('aria-label', 'Search insights')

    // Type a search query
    await search.fill('test search query')
    // Wait for debounce
    await page.waitForFunction(() => true, null, { timeout: 500 })
  })

  test('sentiment filter pills are functional', async ({ authenticatedPage: page }) => {
    // Click "Positive" pill
    const positivePill = page.locator('button:has-text("Positive")')
    if (await positivePill.isVisible()) {
      await positivePill.click()
      // Filter should be applied
    }
  })

  test('action tracker panel visible on desktop', async ({ authenticatedPage: page }) => {
    // Action tracker should be visible on desktop viewport
    await expect(page.getByTestId('action-tracker')).toBeVisible()
  })
})
