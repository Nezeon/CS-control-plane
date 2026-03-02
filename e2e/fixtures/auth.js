import { test as base, expect } from '@playwright/test'

/**
 * Authentication fixture for E2E tests.
 *
 * The app has demo mode: when the backend is unavailable,
 * authStore.login() catches the API error and creates a mock
 * user with a 'demo-token' in localStorage. This means ANY
 * email/password combination works for testing.
 */
export const test = base.extend({
  /**
   * Pre-authenticated page — logs in before the test runs.
   */
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await page.getByTestId('login-email').fill('demo@hivepro.com')
    await page.getByTestId('login-password').fill('demo123')
    await page.getByTestId('login-submit').click()

    // Wait for dashboard to appear (don't rely on URL load event — proxy errors may stall it)
    await page.getByTestId('dashboard-page').waitFor({ state: 'visible', timeout: 30_000 })

    await use(page)
  },

  /**
   * Navigate to a specific route after authentication.
   * Usage: test('...', async ({ pageAt }) => { const page = await pageAt('/customers') })
   */
  pageAt: async ({ page }, use) => {
    const navigate = async (path) => {
      // Login if not already authenticated
      await page.goto('/login', { waitUntil: 'domcontentloaded' })
      await page.getByTestId('login-email').fill('demo@hivepro.com')
      await page.getByTestId('login-password').fill('demo123')
      await page.getByTestId('login-submit').click()
      await page.getByTestId('dashboard-page').waitFor({ state: 'visible', timeout: 30_000 })

      if (path !== '/') {
        await page.goto(path, { waitUntil: 'domcontentloaded' })
        // Wait for the page content, not networkidle (proxy errors prevent it)
        await page.waitForTimeout(2000)
      }
      return page
    }
    await use(navigate)
  },
})

export { expect }
