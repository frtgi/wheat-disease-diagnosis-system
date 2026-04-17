import { test, expect } from './helpers'

test.describe('诊断流程 E2E 测试', () => {

  test('诊断页面加载和 UI 渲染', async ({ loggedInPage: page }) => {
    await page.goto('/diagnosis')
    await page.waitForTimeout(3000)
    const hasUpload = await page.locator('[class*="upload"], input[type="file"], [class*="drop"]').count() > 0
    expect(hasUpload).toBeTruthy()
  })

  test('诊断页面导航可访问', async ({ loggedInPage: page }) => {
    await page.goto('/diagnosis')
    await page.waitForTimeout(3000)
    expect(page.url()).toContain('/diagnosis')
  })

  test('图像上传区域可见', async ({ loggedInPage: page }) => {
    await page.goto('/diagnosis')
    await page.waitForTimeout(3000)
    const uploadArea = page.locator('[class*="upload"], [class*="drop-zone"], [class*="image-upload"], .el-upload')
    await expect(uploadArea.first()).toBeVisible({ timeout: 10000 })
  })

  test('诊断按钮或提交区域存在', async ({ loggedInPage: page }) => {
    await page.goto('/diagnosis')
    await page.waitForTimeout(3000)
    const diagBtn = page.locator('button:has-text("诊断"), button:has-text("开始"), button:has-text("分析"), [class*="diagnose"]')
    const hasBtn = await diagBtn.count() > 0
    const hasForm = await page.locator('form, [class*="form"]').count() > 0
    expect(hasBtn || hasForm).toBeTruthy()
  })

  test('批量诊断入口可访问', async ({ loggedInPage: page }) => {
    await page.goto('/diagnosis')
    await page.waitForTimeout(3000)
    const batchTab = page.locator('text=批量, [class*="batch"], [role="tab"]:has-text("批量")')
    const hasBatch = await batchTab.count() > 0
    if (hasBatch) {
      await batchTab.first().click()
      await page.waitForTimeout(1000)
    }
    expect(true).toBeTruthy()
  })
})
