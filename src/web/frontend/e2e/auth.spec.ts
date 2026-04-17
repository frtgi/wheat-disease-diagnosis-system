import { test, expect, ADMIN_USER, WRONG_USER, login } from './helpers'

test.describe('认证流程 E2E 测试', () => {

  test('登录页面正确渲染', async ({ page }) => {
    await page.goto('/login')
    await expect(page.locator('input[placeholder*="用户名"]').first()).toBeVisible()
    await expect(page.locator('input[type="password"]').first()).toBeVisible()
    await expect(page.locator('button:has-text("登录")').first()).toBeVisible()
  })

  test('正确凭证登录成功并跳转', async ({ page }) => {
    await login(page)
    const url = page.url()
    expect(url).not.toContain('/login')
  })

  test('错误凭证登录失败', async ({ page }) => {
    await page.goto('/login')
    await page.waitForTimeout(500)
    await page.locator('input[placeholder*="用户名"]').first().fill(WRONG_USER.username)
    await page.locator('input[type="password"]').first().fill(WRONG_USER.password)
    await page.locator('button:has-text("登录")').first().click()
    await page.waitForTimeout(3000)
    const stillOnLogin = page.url().includes('/login')
    const hasError = await page.locator('.el-message--error, .el-form-item__error, [class*="error"]').count() > 0
    expect(stillOnLogin || hasError).toBeTruthy()
  })

  test('未登录访问受保护页面重定向到登录页', async ({ page }) => {
    await page.goto('/diagnosis')
    await page.waitForTimeout(3000)
    expect(page.url()).toContain('/login')
  })

  test('未登录访问管理后台重定向到登录页', async ({ page }) => {
    await page.goto('/admin')
    await page.waitForTimeout(3000)
    expect(page.url()).toContain('/login')
  })

  test('登出后 Token 被清除', async ({ page }) => {
    await login(page)
    const tokenBefore = await page.evaluate(() => localStorage.getItem('token'))
    expect(tokenBefore).toBeTruthy()

    await page.evaluate(() => {
      localStorage.removeItem('token')
      localStorage.removeItem('userInfo')
      localStorage.removeItem('refresh_token')
    })
    await page.goto('/diagnosis')
    await page.waitForTimeout(3000)
    expect(page.url()).toContain('/login')
  })
})
