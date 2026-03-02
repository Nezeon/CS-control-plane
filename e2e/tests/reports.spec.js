import { test, expect } from '../fixtures/auth.js'

test.describe('Analytics Lab', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-reports').click()
    await expect(page.getByTestId('reports-page')).toBeVisible()
  })

  test('page loads with heading', async ({ authenticatedPage: page }) => {
    await expect(page.getByRole('heading', { name: /Analytics Lab/i })).toBeVisible()
  })

  test('KPI metric orbs display', async ({ authenticatedPage: page }) => {
    const orbs = page.locator('[data-testid^="metric-orb-"]')
    await expect(orbs.first()).toBeVisible({ timeout: 15000 })
    const count = await orbs.count()
    expect(count).toBeGreaterThanOrEqual(4)
  })

  test('health heatmap chart renders', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('health-heatmap')).toBeVisible({ timeout: 15000 })
  })

  test('ticket velocity chart renders', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('ticket-velocity')).toBeVisible({ timeout: 15000 })
  })

  test('sentiment river chart renders', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('sentiment-river')).toBeVisible({ timeout: 15000 })
  })

  test('agent throughput chart renders', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('agent-throughput')).toBeVisible({ timeout: 15000 })
  })

  test('report list section renders', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('report-list')).toBeVisible({ timeout: 15000 })
  })
})
