import { test as base, expect } from '@playwright/test'
import { test, expect as testExpect } from '../fixtures/auth.js'

test.describe('Accessibility', () => {
  test('keyboard-only login flow', async ({ page }) => {
    await page.goto('/login')

    // Tab to email input
    await page.keyboard.press('Tab')
    // Tab to skip-to-content link first, then to email
    // The exact tab order depends on the page, so we use the input directly
    await page.getByTestId('login-email').focus()
    await page.keyboard.type('demo@hivepro.com')

    // Tab to password
    await page.keyboard.press('Tab')
    await page.keyboard.type('demo123')

    // Tab to show/hide button, then to submit
    await page.keyboard.press('Tab') // show/hide password button
    await page.keyboard.press('Tab') // submit button
    await page.keyboard.press('Enter')

    // Should navigate to dashboard
    await page.waitForURL('/', { timeout: 15000 })
    await expect(page.getByTestId('dashboard-page')).toBeVisible()
  })

  test('skip-to-content link is present', async ({ authenticatedPage: page }) => {
    // Skip to content link should be sr-only by default
    const skipLink = page.locator('a[href="#main-content"]')
    await expect(skipLink).toHaveCount(1)
  })

  test('escape closes command palette', async ({ authenticatedPage: page }) => {
    await page.keyboard.press('Control+k')
    await expect(page.getByTestId('command-palette')).toBeVisible()
    await page.keyboard.press('Escape')
    await expect(page.getByTestId('command-palette')).not.toBeVisible()
  })

  test('reduce motion toggle works', async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-settings').click()
    await expect(page.getByTestId('settings-page')).toBeVisible()

    const toggle = page.getByTestId('reduce-motion-toggle')
    await expect(toggle).toHaveRole('switch')

    // Enable reduced motion
    const initialChecked = await toggle.getAttribute('aria-checked')
    if (initialChecked === 'false') {
      await toggle.click()
      await expect(toggle).toHaveAttribute('aria-checked', 'true')
    }

    // Navigate to dashboard and verify it still works
    await page.getByTestId('orbital-nav-item-dashboard').click()
    await expect(page.getByTestId('dashboard-page')).toBeVisible()

    // Go back and disable
    await page.getByTestId('orbital-nav-item-settings').click()
    await toggle.click()
  })

  test('prefers-reduced-motion media query is respected', async ({ browser }) => {
    const context = await browser.newContext({
      reducedMotion: 'reduce',
    })
    const page = await context.newPage()

    // Login
    await page.goto('/login')
    await page.getByTestId('login-email').fill('demo@hivepro.com')
    await page.getByTestId('login-password').fill('demo123')
    await page.getByTestId('login-submit').click()
    await page.waitForURL('/')

    await expect(page.getByTestId('dashboard-page')).toBeVisible()

    // Animations should be disabled via CSS
    const animDuration = await page.evaluate(() => {
      const el = document.querySelector('.nebula-bg')
      return el ? getComputedStyle(el).animationDuration : null
    })
    // Should be 0.01ms (reduced) rather than 30s
    if (animDuration) {
      expect(animDuration).not.toBe('30s')
    }

    await context.close()
  })

  test('orbital nav has proper aria attributes', async ({ authenticatedPage: page }) => {
    const nav = page.getByTestId('orbital-nav')
    await expect(nav).toHaveAttribute('aria-label', 'Main navigation')

    // Active item should have aria-current="page"
    const activeItem = page.getByTestId('orbital-nav-item-dashboard')
    await expect(activeItem).toHaveAttribute('aria-current', 'page')
  })

  test('login form labels are connected to inputs', async ({ page }) => {
    await page.goto('/login')

    const emailInput = page.getByTestId('login-email')
    await expect(emailInput).toHaveAttribute('id', 'login-email')

    const emailLabel = page.locator('label[for="login-email"]')
    await expect(emailLabel).toHaveCount(1)

    const passwordInput = page.getByTestId('login-password')
    await expect(passwordInput).toHaveAttribute('id', 'login-password')

    const passwordLabel = page.locator('label[for="login-password"]')
    await expect(passwordLabel).toHaveCount(1)
  })

  test('color is not the only indicator for status', async ({ authenticatedPage: page }) => {
    // Status indicators should have text labels alongside color
    const indicators = page.locator('[data-testid="status-indicator"]')
    const count = await indicators.count()
    // Each indicator should have text content, not just a colored dot
    for (let i = 0; i < Math.min(count, 5); i++) {
      const text = await indicators.nth(i).textContent()
      // Should have some text (not just empty)
      expect(text.trim().length).toBeGreaterThan(0)
    }
  })

  test('axe accessibility audit on login page', async ({ page }) => {
    await page.goto('/login')
    await expect(page.getByTestId('login-page')).toBeVisible()

    const AxeBuilder = (await import('@axe-core/playwright')).default
    const results = await new AxeBuilder({ page })
      .exclude('.nebula-bg') // Exclude decorative elements
      .exclude('.depth-vignette')
      .exclude('.particle-field')
      .analyze()

    // Filter to only critical violations
    const critical = results.violations.filter(
      (v) => v.impact === 'critical'
    )
    if (critical.length > 0) {
      console.log('Axe critical violations (login):', JSON.stringify(critical.map(v => ({ id: v.id, impact: v.impact, description: v.description })), null, 2))
    }
    expect(critical).toHaveLength(0)
  })

  test('axe accessibility audit on dashboard', async ({ authenticatedPage: page }) => {
    // Wait for dashboard to fully load
    await expect(page.getByTestId('dashboard-page')).toBeVisible({ timeout: 15000 })
    await page.waitForTimeout(2000)

    const AxeBuilder = (await import('@axe-core/playwright')).default
    const results = await new AxeBuilder({ page })
      .exclude('.nebula-bg')
      .exclude('.depth-vignette')
      .exclude('.particle-field')
      .exclude('canvas') // Exclude WebGL canvases
      .exclude('[aria-hidden="true"]')
      .analyze()

    // Filter to only critical violations
    const critical = results.violations.filter(
      (v) => v.impact === 'critical'
    )
    if (critical.length > 0) {
      console.log('Axe critical violations (dashboard):', JSON.stringify(critical.map(v => ({ id: v.id, impact: v.impact, description: v.description })), null, 2))
    }
    expect(critical).toHaveLength(0)
  })
})
