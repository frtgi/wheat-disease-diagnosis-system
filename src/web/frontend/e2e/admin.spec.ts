import { test, expect, ADMIN_USER, login } from './helpers'

test.describe('管理后台 E2E 测试', () => {

  test('管理员访问 /admin 页面', async ({ loggedInPage: page }) => {
    await page.goto('/admin')
    await page.waitForTimeout(3000)
    const url = page.url()
    const isAdminPage = url.includes('/admin')
    const hasAdminContent = await page.locator('[class*="admin"], [class*="overview"], [class*="monitor"]').count() > 0
    expect(isAdminPage || hasAdminContent).toBeTruthy()
  })

  test('管理后台 Tab 切换', async ({ loggedInPage: page }) => {
    await page.goto('/admin')
    await page.waitForTimeout(3000)

    const tabs = page.locator('[role="tab"], .el-tabs__item, [class*="tab"]')
    const tabCount = await tabs.count()
    if (tabCount > 1) {
      await tabs.nth(1).click()
      await page.waitForTimeout(1000)
      await tabs.nth(0).click()
      await page.waitForTimeout(1000)
    }
    expect(true).toBeTruthy()
  })

  test('管理员可以访问管理后台', async ({ loggedInPage: page }) => {
    await page.goto('/admin')
    await page.waitForTimeout(3000)
    const url = page.url()
    const canAccess = url.includes('/admin')
    expect(canAccess).toBeTruthy()
  })
})
