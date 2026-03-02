import { test, expect } from '../fixtures/auth.js'
import { openCommandPalette } from '../fixtures/helpers.js'

test.describe('Navigation System', () => {
  test('orbital nav is visible on dashboard', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('orbital-nav')).toBeVisible()
  })

  test('orbital nav highlights active page', async ({ authenticatedPage: page }) => {
    // Dashboard should be active (has aria-current="page")
    const dashNav = page.getByTestId('orbital-nav-item-dashboard')
    await expect(dashNav).toHaveAttribute('aria-current', 'page')
  })

  test('orbital nav navigates to each page', async ({ authenticatedPage: page }) => {
    const routes = [
      { item: 'customers', testid: 'customers-page', url: '/customers' },
      { item: 'agents', testid: 'agents-page', url: '/agents' },
      { item: 'insights', testid: 'insights-page', url: '/insights' },
      { item: 'tickets', testid: 'tickets-page', url: '/tickets' },
      { item: 'reports', testid: 'reports-page', url: '/reports' },
      { item: 'dashboard', testid: 'dashboard-page', url: '/' },
    ]

    for (const route of routes) {
      await page.getByTestId(`orbital-nav-item-${route.item}`).click()
      await expect(page.getByTestId(route.testid)).toBeVisible({ timeout: 10000 })
    }
  })

  test('breadcrumbs update on navigation', async ({ authenticatedPage: page }) => {
    // Dashboard breadcrumb
    const breadcrumb = page.getByTestId('breadcrumb')
    await expect(breadcrumb).toBeVisible()
    await expect(breadcrumb).toContainText('Mission Control')

    // Navigate to customers
    await page.getByTestId('orbital-nav-item-customers').click()
    await expect(page.getByTestId('customers-page')).toBeVisible({ timeout: 15000 })
    await expect(breadcrumb).toContainText('Customer Observatory')
  })

  test('command palette opens with Ctrl+K', async ({ authenticatedPage: page }) => {
    await openCommandPalette(page)
    await expect(page.getByTestId('command-palette')).toBeVisible()
    await expect(page.getByTestId('command-palette-input')).toBeFocused()
  })

  test('command palette search filters results', async ({ authenticatedPage: page }) => {
    await openCommandPalette(page)
    await page.getByTestId('command-palette-input').fill('Dashboard')
    // Should show Dashboard in results
    const results = page.getByTestId('command-palette-results')
    await expect(results).toContainText('Dashboard')
  })

  test('command palette closes on Escape', async ({ authenticatedPage: page }) => {
    await openCommandPalette(page)
    await page.keyboard.press('Escape')
    await expect(page.getByTestId('command-palette')).not.toBeVisible()
  })

  test('command palette navigates on selection', async ({ authenticatedPage: page }) => {
    await openCommandPalette(page)
    await page.getByTestId('command-palette-input').fill('Customers')

    // Wait for results to filter, then click the first result
    const results = page.getByTestId('command-palette-results')
    await expect(results).toContainText('Customers')
    await page.keyboard.press('Enter')

    await expect(page.getByTestId('customers-page')).toBeVisible({ timeout: 10000 })
  })

  test('browser back/forward navigation works', async ({ authenticatedPage: page }) => {
    // Navigate: Dashboard -> Customers -> Agents
    await page.getByTestId('orbital-nav-item-customers').click()
    await expect(page.getByTestId('customers-page')).toBeVisible({ timeout: 15000 })

    await page.getByTestId('orbital-nav-item-agents').click()
    await expect(page.getByTestId('agents-page')).toBeVisible({ timeout: 15000 })

    // Back to customers
    await page.goBack()
    await expect(page.getByTestId('customers-page')).toBeVisible({ timeout: 15000 })

    // Back to dashboard
    await page.goBack()
    await expect(page.getByTestId('dashboard-page')).toBeVisible({ timeout: 15000 })

    // Forward to customers
    await page.goForward()
    await expect(page.getByTestId('customers-page')).toBeVisible({ timeout: 15000 })
  })

  test('direct URL navigation works', async ({ pageAt }) => {
    const page = await pageAt('/tickets')
    await expect(page.getByTestId('tickets-page')).toBeVisible({ timeout: 15000 })
  })
})
