import { test as base, expect } from '@playwright/test'

type TestFixtures = {
  loggedInPage: typeof base
}

async function login(page: import('@playwright/test').Page) {
  await page.goto('/login')
  await page.waitForLoadState('networkidle')
  const usernameInput = page.locator('input[placeholder*="用户名"]').first()
  const passwordInput = page.locator('input[type="password"]').first()
  const submitBtn = page.locator('button:has-text("登录")').first()
  await usernameInput.clear()
  await usernameInput.fill('v21test_admin')
  await passwordInput.clear()
  await passwordInput.fill('Test1234!')
  await submitBtn.click()
  await page.waitForFunction(() => {
    return !window.location.href.includes('/login')
  }, { timeout: 20000 }).catch(async () => {
    await page.reload()
    await page.waitForLoadState('networkidle')
    const u = page.locator('input[placeholder*="用户名"]').first()
    const p = page.locator('input[type="password"]').first()
    const b = page.locator('button:has-text("登录")').first()
    await u.clear()
    await u.fill('v21test_admin')
    await p.clear()
    await p.fill('Test1234!')
    await b.click()
    await page.waitForFunction(() => !window.location.href.includes('/login'), { timeout: 20000 })
  })
  await page.waitForTimeout(1500)
}

export const test = base.extend<TestFixtures>({
  loggedInPage: async ({ page }, use) => {
    await login(page)
    await use(page)
  },
})

export { expect, login }

export const ADMIN_USER = {
  username: 'v21test_admin',
  password: 'Test1234!',
}

export const WRONG_USER = {
  username: 'wrong_user',
  password: 'wrong_pass',
}
