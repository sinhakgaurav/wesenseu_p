import { test, expect } from '@playwright/test'

const EMAIL = process.env.PLAYWRIGHT_DEMO_EMAIL || 'admin@monitour.in'
const PASSWORD = process.env.PLAYWRIGHT_DEMO_PASSWORD || 'Admin@2026'

test.describe('Admin login', () => {
  test('super admin can log in and reach platform dashboard', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('you@example.com').fill(EMAIL)
    await page.getByPlaceholder('••••••••').fill(PASSWORD)
    await page.getByRole('button', { name: /sign in/i }).click()

    await expect(page).toHaveURL(/admin/, { timeout: 20000 })
    await expect(
      page.getByRole('heading', { name: /platform dashboard|dashboard/i }).first()
    ).toBeVisible({ timeout: 15000 })
  })

  test('invalid credentials show error', async ({ page }) => {
    await page.goto('/login')
    await page.getByPlaceholder('you@example.com').fill('bad@example.com')
    await page.getByPlaceholder('••••••••').fill('wrongpassword')
    await page.getByRole('button', { name: /sign in/i }).click()
    await expect(page.getByText(/incorrect|invalid|failed/i).first()).toBeVisible({
      timeout: 10000,
    })
  })
})
