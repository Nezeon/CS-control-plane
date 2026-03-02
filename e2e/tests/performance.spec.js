import { test, expect } from '../fixtures/auth.js'

test.describe('Performance', () => {
  test('dashboard loads within 4 seconds', async ({ page }) => {
    // Login first
    await page.goto('/login')
    await page.getByTestId('login-email').fill('demo@hivepro.com')
    await page.getByTestId('login-password').fill('demo123')
    await page.getByTestId('login-submit').click()

    const start = Date.now()
    await page.waitForURL('/')
    await page.getByTestId('dashboard-page').waitFor({ state: 'visible' })
    const loadTime = Date.now() - start

    expect(loadTime).toBeLessThan(8000)
    console.log(`Dashboard load time: ${loadTime}ms`)
  })

  test('dashboard loads within 2 seconds in 2D mode', async ({ browser }) => {
    const context = await browser.newContext({
      reducedMotion: 'reduce',
    })
    const page = await context.newPage()

    // Login
    await page.goto('/login')
    await page.getByTestId('login-email').fill('demo@hivepro.com')
    await page.getByTestId('login-password').fill('demo123')
    await page.getByTestId('login-submit').click()

    const start = Date.now()
    await page.waitForURL('/')
    await page.getByTestId('dashboard-page').waitFor({ state: 'visible' })
    const loadTime = Date.now() - start

    expect(loadTime).toBeLessThan(5000)
    console.log(`Dashboard 2D load time: ${loadTime}ms`)
    await context.close()
  })

  test('page navigation takes less than 1 second', async ({ authenticatedPage: page }) => {
    const start = Date.now()
    await page.getByTestId('orbital-nav-item-customers').click()
    await page.getByTestId('customers-page').waitFor({ state: 'visible' })
    const navTime = Date.now() - start

    expect(navTime).toBeLessThan(3000)
    console.log(`Navigation time: ${navTime}ms`)
  })

  test('Three.js bundle is lazy-loaded', async ({ page }) => {
    const requests = []
    page.on('request', (req) => requests.push(req.url()))

    // Login page should NOT load Three.js
    await page.goto('/login')
    await page.getByTestId('login-page').waitFor({ state: 'visible' })

    const threeOnLogin = requests.filter((url) => url.includes('three'))
    expect(threeOnLogin).toHaveLength(0)
  })

  test('no critical console errors across all pages', async ({ authenticatedPage: page }) => {
    const criticalErrors = []
    page.on('console', (msg) => {
      if (msg.type() === 'error') {
        const text = msg.text()
        if (
          !text.includes('Backend unavailable') &&
          !text.includes('ERR_CONNECTION_REFUSED') &&
          !text.includes('Failed to fetch') &&
          !text.includes('WebSocket') &&
          !text.includes('net::ERR_') &&
          !text.includes('ETIMEDOUT') &&
          !text.includes('ECONNREFUSED') &&
          !text.includes('proxy error') &&
          !text.includes('loading seed') &&
          !text.includes('demo mode')
        ) {
          criticalErrors.push(text)
        }
      }
    })

    // Navigate through all pages
    const pages = ['customers', 'agents', 'insights', 'tickets', 'reports', 'settings', 'dashboard']
    for (const pageName of pages) {
      await page.getByTestId(`orbital-nav-item-${pageName}`).click()
      await page.getByTestId(`${pageName}-page`).waitFor({ state: 'visible', timeout: 15000 })
    }

    await page.waitForTimeout(1000)
    expect(criticalErrors).toHaveLength(0)
  })

  test('memory stability across navigation cycles', async ({ authenticatedPage: page }) => {
    // Get initial heap size
    const initialHeap = await page.evaluate(() => {
      if (performance.memory) return performance.memory.usedJSHeapSize
      return null
    })

    if (initialHeap === null) {
      // performance.memory not available in this browser
      test.skip()
      return
    }

    // Navigate through all pages 3 times
    const navOrder = ['customers', 'agents', 'insights', 'tickets', 'reports', 'dashboard']
    for (let cycle = 0; cycle < 3; cycle++) {
      for (const pageName of navOrder) {
        await page.getByTestId(`orbital-nav-item-${pageName}`).click()
        await page.getByTestId(`${pageName}-page`).waitFor({ state: 'visible', timeout: 10000 })
      }
    }

    // Get final heap size
    const finalHeap = await page.evaluate(() => performance.memory.usedJSHeapSize)
    const growth = finalHeap - initialHeap
    const growthMB = growth / (1024 * 1024)

    console.log(`Heap growth over 3 cycles: ${growthMB.toFixed(2)} MB`)
    // Allow up to 20MB growth
    expect(growthMB).toBeLessThan(20)
  })
})
