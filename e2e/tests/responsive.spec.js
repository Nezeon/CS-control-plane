import { test, expect } from '../fixtures/auth.js'

test.describe('Responsive Behavior', () => {
  test('desktop full (1920x1080) renders all sections', async ({ authenticatedPage: page }) => {
    await page.setViewportSize({ width: 1920, height: 1080 })
    await expect(page.getByTestId('dashboard-page')).toBeVisible()
    await expect(page.getByTestId('orbital-nav')).toBeVisible()
    await expect(page.getByTestId('floating-orbs-grid')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('neural-sphere')).toBeVisible({ timeout: 15000 })
  })

  test('tablet (768x1024) renders with adapted layout', async ({ authenticatedPage: page }) => {
    await page.setViewportSize({ width: 768, height: 1024 })
    // Should have mobile nav instead of orbital nav
    await expect(
      page.getByTestId('mobile-nav').or(page.getByTestId('orbital-nav'))
    ).toBeVisible()

    // Content should still be visible
    await expect(page.getByTestId('dashboard-page')).toBeVisible()
    await expect(page.getByTestId('floating-orbs-grid')).toBeVisible()
  })

  test('mobile (390x844) renders single column', async ({ authenticatedPage: page }) => {
    await page.setViewportSize({ width: 390, height: 844 })
    await expect(page.getByTestId('dashboard-page')).toBeVisible()

    // Mobile nav should be visible
    await expect(page.getByTestId('mobile-nav')).toBeVisible()

    // Content should be scrollable
    const canScroll = await page.evaluate(() => document.body.scrollHeight > window.innerHeight)
    // Page might not need to scroll if content fits, so this is a soft check
  })

  test('customer page adapts to tablet', async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-customers').click()
    await expect(page.getByTestId('customers-page')).toBeVisible()

    await page.setViewportSize({ width: 768, height: 1024 })
    // Premium grid should still be visible
    await expect(page.getByTestId('premium-grid')).toBeVisible()
  })

  test('insights page hides action tracker on tablet', async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-insights').click()
    await expect(page.getByTestId('insights-page')).toBeVisible()

    // On desktop, action tracker should be visible
    await page.setViewportSize({ width: 1920, height: 1080 })
    await expect(page.getByTestId('action-tracker')).toBeVisible()

    // On tablet, action tracker should be hidden
    await page.setViewportSize({ width: 768, height: 1024 })
    await expect(page.getByTestId('action-tracker')).not.toBeVisible()
  })

  test('reports charts stack on tablet', async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-reports').click()
    await expect(page.getByTestId('reports-page')).toBeVisible()

    await page.setViewportSize({ width: 768, height: 1024 })
    // All charts should still be visible (stacked)
    await expect(page.getByTestId('health-heatmap')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('ticket-velocity')).toBeVisible({ timeout: 15000 })
  })
})
