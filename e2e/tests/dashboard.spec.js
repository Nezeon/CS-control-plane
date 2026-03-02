import { test, expect } from '../fixtures/auth.js'
import { collectConsoleErrors } from '../fixtures/helpers.js'

test.describe('Command Center (Dashboard)', () => {
  test('dashboard loads with all sections', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('dashboard-page')).toBeVisible()
    await expect(page.getByRole('heading', { name: /Command Center/i })).toBeVisible()

    // Check all main sections exist (allow time for async seed data)
    await expect(page.getByTestId('floating-orbs-grid')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('neural-sphere')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('data-flow-rivers')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('live-pulse')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('quick-actions')).toBeVisible({ timeout: 15000 })
  })

  test('metric orbs display data from seed', async ({ authenticatedPage: page }) => {
    const orbsGrid = page.getByTestId('floating-orbs-grid')
    await expect(orbsGrid).toBeVisible()

    // Should have metric orb containers with values
    const orbs = page.locator('[data-testid^="metric-orb-"]')
    const count = await orbs.count()
    expect(count).toBeGreaterThanOrEqual(4)
  })

  test('neural sphere section renders content', async ({ authenticatedPage: page }) => {
    const sphere = page.getByTestId('neural-sphere')
    await expect(sphere).toBeVisible()
    // Should have either a Canvas (3D) or SVG content (2D fallback)
    const hasCanvas = await sphere.locator('canvas').count() > 0
    const hasSvg = await sphere.locator('svg').count() > 0
    expect(hasCanvas || hasSvg).toBe(true)
  })

  test('data flow rivers section renders', async ({ authenticatedPage: page }) => {
    const rivers = page.getByTestId('data-flow-rivers')
    await expect(rivers).toBeVisible({ timeout: 15000 })
  })

  test('live pulse section renders', async ({ authenticatedPage: page }) => {
    const pulse = page.getByTestId('live-pulse')
    await expect(pulse).toBeVisible({ timeout: 15000 })
  })

  test('quick actions section is accessible', async ({ authenticatedPage: page }) => {
    const actions = page.getByTestId('quick-actions')
    await expect(actions).toBeVisible()
  })

  test('orbital nav shows dashboard as active', async ({ authenticatedPage: page }) => {
    const dashNav = page.getByTestId('orbital-nav-item-dashboard')
    await expect(dashNav).toHaveAttribute('aria-current', 'page')
  })

  test('no critical console errors on dashboard', async ({ authenticatedPage: page }) => {
    const { assertNoErrors } = collectConsoleErrors(page)
    // Navigate away and back to trigger any lazy-load errors
    await page.getByTestId('orbital-nav-item-customers').click()
    await expect(page.getByTestId('customers-page')).toBeVisible({ timeout: 15000 })
    await page.getByTestId('orbital-nav-item-dashboard').click()
    await expect(page.getByTestId('dashboard-page')).toBeVisible({ timeout: 15000 })

    await page.waitForTimeout(1000)
    const errors = assertNoErrors()
    expect(errors).toHaveLength(0)
  })
})
