import { test, expect } from '@playwright/test'

const EMAIL = process.env.PLAYWRIGHT_DEMO_EMAIL || 'admin@monitour.in'
const PASSWORD = process.env.PLAYWRIGHT_DEMO_PASSWORD || 'Admin@2026'

test.describe('Super admin diagnostics', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('you@example.com').fill(EMAIL)
    await page.getByPlaceholder('••••••••').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page).toHaveURL(/admin/, { timeout: 20000 })
  })

  test('run all endpoint probes from diagnostics tab', async ({ page }) => {
    await page.goto('/admin/super-admin')
    await page.getByRole('button', { name: /^diagnostics$/i }).click()
    await expect(page.getByRole('heading', { name: /system diagnostics/i })).toBeVisible()

    await page.getByRole('button', { name: /run all checks/i }).click()

    await expect(page.getByText(/^Total$/)).toBeVisible({ timeout: 120000 })
    const moduleSection = page.locator('section').filter({
      has: page.getByRole('heading', { name: /^module$/i }),
    })
    const moduleErrors = await moduleSection.locator('.border-red-100').count()
    expect(moduleErrors, 'all API module probes should pass').toBe(0)
  })
})
