import { test, expect } from '../fixtures/auth.js'

test.describe('Agent Nexus', () => {
  test.beforeEach(async ({ authenticatedPage: page }) => {
    await page.getByTestId('orbital-nav-item-agents').click()
    await expect(page.getByTestId('agents-page')).toBeVisible()
  })

  test('page loads with heading', async ({ authenticatedPage: page }) => {
    await expect(page.getByRole('heading', { name: /Agent Nexus/i })).toBeVisible()
  })

  test('neural network visualization renders', async ({ authenticatedPage: page }) => {
    const network = page.getByTestId('neural-network')
    await expect(network).toBeVisible({ timeout: 10000 })
    // Should contain SVG nodes
    const svgElements = network.locator('svg, circle, rect')
    const count = await svgElements.count()
    expect(count).toBeGreaterThan(0)
  })

  test('agent stats summary displays', async ({ authenticatedPage: page }) => {
    // Stats: active, idle, tasks today
    await expect(page.locator('text=/\\d+ active/i')).toBeVisible()
    await expect(page.locator('text=/\\d+ idle/i')).toBeVisible()
    await expect(page.locator('text=/\\d+ tasks today/i')).toBeVisible()
  })

  test('clicking agent node opens brain panel', async ({ authenticatedPage: page }) => {
    const network = page.getByTestId('neural-network')
    await expect(network).toBeVisible({ timeout: 10000 })

    // Click a node (circle/rect in the SVG)
    const node = network.locator('circle, [data-agent]').first()
    if (await node.isVisible()) {
      await node.click()
      await expect(page.getByTestId('agent-brain-panel')).toBeVisible({ timeout: 5000 })
    }
  })

  test('brain panel is dismissible', async ({ authenticatedPage: page }) => {
    const network = page.getByTestId('neural-network')
    await expect(network).toBeVisible({ timeout: 10000 })

    const node = network.locator('circle, [data-agent]').first()
    if (await node.isVisible()) {
      await node.click()
      await expect(page.getByTestId('agent-brain-panel')).toBeVisible({ timeout: 5000 })

      // Dismiss with Escape
      await page.keyboard.press('Escape')
      await expect(page.getByTestId('agent-brain-panel')).not.toBeVisible({ timeout: 5000 })
    }
  })
})
