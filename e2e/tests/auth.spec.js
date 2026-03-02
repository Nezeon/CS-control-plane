import { test as base, expect } from '@playwright/test'

base.describe('Authentication', () => {
  base.test('login page renders with form elements', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('login-page')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('login-email')).toBeVisible()
    await expect(page.getByTestId('login-password')).toBeVisible()
    await expect(page.getByTestId('login-submit')).toBeVisible()
  })

  base.test('login page has correct branding', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('login-page')).toBeVisible({ timeout: 15000 })
    await expect(page.getByText('Mission Control')).toBeVisible()
    await expect(page.getByText('CS Control Plane')).toBeVisible()
  })

  base.test('void background renders', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('login-page')).toBeVisible({ timeout: 15000 })
    const bgColor = await page.evaluate(() => getComputedStyle(document.body).backgroundColor)
    // #020408 = rgb(2, 4, 8)
    expect(bgColor).toBe('rgb(2, 4, 8)')
  })

  base.test('submit button disabled when form is empty', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('login-submit')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('login-submit')).toBeDisabled()
  })

  base.test('submit button disabled with only email', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('login-submit')).toBeVisible({ timeout: 15000 })
    await page.getByTestId('login-email').fill('demo@hivepro.com')
    await expect(page.getByTestId('login-submit')).toBeDisabled()
  })

  base.test('successful login redirects to dashboard', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('login-page')).toBeVisible({ timeout: 15000 })
    await page.getByTestId('login-email').fill('demo@hivepro.com')
    await page.getByTestId('login-password').fill('demo123')
    await page.getByTestId('login-submit').click()

    await expect(page.getByTestId('dashboard-page')).toBeVisible({ timeout: 15000 })
    await expect(page.getByTestId('orbital-nav')).toBeVisible()
    await expect(page.getByTestId('top-bar')).toBeVisible()
  })

  base.test('protected routes redirect to login when unauthenticated', async ({ page }) => {
    // Clear any stored tokens
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await page.evaluate(() => localStorage.clear())

    // Try to access protected routes
    for (const path of ['/customers', '/agents', '/insights', '/tickets', '/reports']) {
      await page.goto(path, { waitUntil: 'domcontentloaded' })
      await expect(page.getByTestId('login-page')).toBeVisible({ timeout: 15000 })
    }
  })

  base.test('page refresh preserves demo auth session', async ({ page }) => {
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await page.getByTestId('login-email').fill('demo@hivepro.com')
    await page.getByTestId('login-password').fill('demo123')
    await page.getByTestId('login-submit').click()
    await expect(page.getByTestId('dashboard-page')).toBeVisible({ timeout: 15000 })

    // Refresh
    await page.reload({ waitUntil: 'domcontentloaded' })
    await expect(page.getByTestId('dashboard-page')).toBeVisible({ timeout: 15000 })
  })

  base.test('logout clears session and redirects to login', async ({ page }) => {
    // Login first
    await page.goto('/login', { waitUntil: 'domcontentloaded' })
    await page.getByTestId('login-email').fill('demo@hivepro.com')
    await page.getByTestId('login-password').fill('demo123')
    await page.getByTestId('login-submit').click()
    await expect(page.getByTestId('dashboard-page')).toBeVisible({ timeout: 15000 })

    // Open user menu and logout
    // The user avatar is a button in TopBar - click it to open menu
    const avatarButton = page.locator('.fixed.top-0 button').last()
    await avatarButton.click()
    await page.getByTestId('logout-button').click()

    await expect(page.getByTestId('login-page')).toBeVisible({ timeout: 15000 })
  })
})
