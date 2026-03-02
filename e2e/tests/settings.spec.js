import { test, expect } from '../fixtures/auth.js'

test.describe('Settings', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-settings').click()
    await expect(page.getByTestId('settings-page')).toBeVisible()
  })

  test('page loads with heading', async ({ authenticatedPage: page }) => {
    await expect(page.getByRole('heading', { name: /Configuration/i })).toBeVisible()
  })

  test('reduce motion toggle is present', async ({ authenticatedPage: page }) => {
    const toggle = page.getByTestId('reduce-motion-toggle')
    await expect(toggle).toBeVisible()
    await expect(toggle).toHaveRole('switch')
  })

  test('reduce motion toggle toggles state', async ({ authenticatedPage: page }) => {
    const toggle = page.getByTestId('reduce-motion-toggle')

    // Get initial state
    const initialState = await toggle.getAttribute('aria-checked')

    // Click toggle
    await toggle.click()

    // State should have changed
    const newState = await toggle.getAttribute('aria-checked')
    expect(newState).not.toBe(initialState)

    // Click again to revert
    await toggle.click()
    const revertedState = await toggle.getAttribute('aria-checked')
    expect(revertedState).toBe(initialState)
  })

  test('system info section displays', async ({ authenticatedPage: page }) => {
    await expect(page.getByRole('heading', { name: /System Info/i })).toBeVisible()
    await expect(page.getByText('Deep Ocean Bioluminescence')).toBeVisible()
    await expect(page.getByText('Spatial Depth v1.0')).toBeVisible()
  })

  test('about section displays', async ({ authenticatedPage: page }) => {
    await expect(page.getByRole('heading', { name: /About/i })).toBeVisible()
    await expect(page.getByText('CS Control Plane')).toBeVisible()
    await expect(page.getByTestId('settings-page').getByText('Mission Control')).toBeVisible()
  })
})
