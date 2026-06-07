import { test, expect } from '@playwright/test'

test.describe('Public marketing pages', () => {
  test('home loads', async ({ page }) => {
    await page.goto('/')
    await expect(page).toHaveTitle(/Monitour/i)
  })

  test('about page shows heading', async ({ page }) => {
    await page.goto('/about')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
  })

  test('contact page has form', async ({ page }) => {
    await page.goto('/contact')
    await expect(page.getByRole('button', { name: /send message/i })).toBeVisible()
  })

  test('pricing page loads plans or skeleton', async ({ page }) => {
    await page.goto('/pricing')
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible()
    await expect(
      page.getByText(/pricing|plan|trial/i).first()
    ).toBeVisible({ timeout: 15000 })
  })
})
