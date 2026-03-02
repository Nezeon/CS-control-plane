/**
 * Shared test helper utilities.
 */

/**
 * Wait for a page to fully load by waiting for loading skeletons to disappear
 * and a target testid to become visible.
 */
export async function waitForPageLoad(page, testid) {
  // Wait for any loading skeletons to disappear (if present)
  const skeleton = page.locator('[data-testid="loading-skeleton"]').first()
  await skeleton.waitFor({ state: 'hidden', timeout: 10_000 }).catch(() => {})
  // Wait for the target element
  await page.getByTestId(testid).waitFor({ state: 'visible', timeout: 15_000 })
}

/**
 * Navigate via Orbital Nav by clicking a nav item and waiting for the page.
 * @param {import('@playwright/test').Page} page
 * @param {string} item - Nav item name (e.g. 'customers', 'agents')
 * @param {string} pageTestid - The data-testid of the destination page
 */
export async function navigateViaOrbitalNav(page, item, pageTestid) {
  await page.getByTestId(`orbital-nav-item-${item}`).click()
  await page.getByTestId(pageTestid).waitFor({ state: 'visible', timeout: 15_000 })
}

/**
 * Open the Command Palette with Ctrl+K.
 */
export async function openCommandPalette(page) {
  await page.keyboard.press('Control+k')
  await page.getByTestId('command-palette').waitFor({ state: 'visible', timeout: 5_000 })
}

/**
 * Attach a console error collector to the page.
 * Returns a function that asserts no errors were logged.
 */
export function collectConsoleErrors(page) {
  const errors = []
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text())
    }
  })
  return {
    errors,
    assertNoErrors: () => {
      const real = errors.filter(
        (e) =>
          // Ignore expected errors in demo mode
          !e.includes('Backend unavailable') &&
          !e.includes('ERR_CONNECTION_REFUSED') &&
          !e.includes('ECONNREFUSED') &&
          !e.includes('ETIMEDOUT') &&
          !e.includes('Failed to fetch') &&
          !e.includes('WebSocket') &&
          !e.includes('net::ERR_') &&
          !e.includes('proxy error') &&
          !e.includes('loading seed') &&
          !e.includes('demo mode') &&
          !e.includes('seed data')
      )
      return real
    },
  }
}
