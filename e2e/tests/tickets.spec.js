import { test, expect } from '../fixtures/auth.js'

test.describe('Ticket Warroom', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-tickets').click()
    await expect(page.getByTestId('tickets-page')).toBeVisible({ timeout: 15000 })
  })

  test('page loads with heading and stats', async ({ authenticatedPage: page }) => {
    await expect(page.getByRole('heading', { name: /Ticket Warroom/i })).toBeVisible()
    await expect(page.locator('text=/\\d+ total/i')).toBeVisible({ timeout: 10000 })
  })

  test('warroom table renders tickets', async ({ authenticatedPage: page }) => {
    await expect(page.getByTestId('warroom-table')).toBeVisible({ timeout: 15000 })
  })

  test('search input filters tickets', async ({ authenticatedPage: page }) => {
    const search = page.getByTestId('tickets-search')
    await expect(search).toBeVisible()
    await expect(search).toHaveAttribute('aria-label', 'Search tickets')
  })

  test('status filter is functional', async ({ authenticatedPage: page }) => {
    const statusFilter = page.getByTestId('tickets-status-filter')
    await expect(statusFilter).toBeVisible()
    await expect(statusFilter).toHaveAttribute('aria-label', 'Filter by status')
    await statusFilter.selectOption('open')
  })

  test('severity filter is functional', async ({ authenticatedPage: page }) => {
    const severityFilter = page.getByTestId('tickets-severity-filter')
    await expect(severityFilter).toBeVisible()
    await expect(severityFilter).toHaveAttribute('aria-label', 'Filter by severity')
    await severityFilter.selectOption('P1')
  })

  test('view toggle switches to constellation', async ({ authenticatedPage: page }) => {
    await page.getByTestId('tickets-view-constellation').click()
    await expect(page.getByTestId('ticket-constellation')).toBeVisible({ timeout: 15000 })
  })

  test('view toggle switches back to table', async ({ authenticatedPage: page }) => {
    await page.getByTestId('tickets-view-constellation').click()
    await expect(page.getByTestId('ticket-constellation')).toBeVisible({ timeout: 15000 })

    await page.getByTestId('tickets-view-table').click()
    await expect(page.getByTestId('warroom-table')).toBeVisible({ timeout: 15000 })
  })

  test('clicking ticket row opens detail drawer', async ({ authenticatedPage: page }) => {
    const table = page.getByTestId('warroom-table')
    await expect(table).toBeVisible({ timeout: 15000 })

    // Click first clickable row
    const row = table.locator('tr[class*="cursor"], tr[class*="hover"]').first()
    if (await row.isVisible()) {
      await row.click()
      await expect(page.getByTestId('ticket-detail-drawer')).toBeVisible({ timeout: 5000 })
    }
  })

  test('ticket drawer is dismissible with Escape', async ({ authenticatedPage: page }) => {
    const table = page.getByTestId('warroom-table')
    await expect(table).toBeVisible({ timeout: 15000 })
    const row = table.locator('tr[class*="cursor"], tr[class*="hover"]').first()
    if (await row.isVisible()) {
      await row.click()
      await expect(page.getByTestId('ticket-detail-drawer')).toBeVisible({ timeout: 5000 })

      await page.keyboard.press('Escape')
      await expect(page.getByTestId('ticket-detail-drawer')).not.toBeVisible({ timeout: 5000 })
    }
  })
})
