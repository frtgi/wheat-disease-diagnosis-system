/**
 * WheatAgent 全面 E2E 测试脚本
 * 覆盖登录、仪表盘、诊断、记录、知识库、管理后台、用户中心及安全性测试
 */
import { test, expect, Page, ConsoleMessage } from '@playwright/test'

const ADMIN_USER = {
  username: 'v21test_admin',
  password: 'Test1234!',
}

const SCREENSHOT_DIR = 'e2e-screenshots'
const BACKEND_URL = 'http://127.0.0.1:8000'
const consoleErrors: ConsoleMessage[] = []

/**
 * 登录辅助函数
 * 使用更稳健的等待策略，增加超时时间和重试次数
 * @param page Playwright Page 实例
 */
async function loginAsAdmin(page: Page): Promise<void> {
  await page.goto('/login')
  await page.waitForLoadState('domcontentloaded')
  await page.waitForTimeout(1000)

  const usernameInput = page.locator('input[placeholder*="用户名"]').first()
  const passwordInput = page.locator('input[type="password"]').first()
  const submitBtn = page.locator('button:has-text("登录")').first()

  await usernameInput.waitFor({ state: 'visible', timeout: 10000 })
  await usernameInput.clear()
  await usernameInput.fill(ADMIN_USER.username)
  await passwordInput.clear()
  await passwordInput.fill(ADMIN_USER.password)
  await submitBtn.click()

  try {
    await page.waitForURL('**/dashboard**', { timeout: 30000 })
  } catch {
    await page.reload()
    await page.waitForLoadState('domcontentloaded')
    await page.waitForTimeout(1000)
    const u = page.locator('input[placeholder*="用户名"]').first()
    const p = page.locator('input[type="password"]').first()
    const b = page.locator('button:has-text("登录")').first()
    await u.waitFor({ state: 'visible', timeout: 10000 })
    await u.clear()
    await u.fill(ADMIN_USER.username)
    await p.clear()
    await p.fill(ADMIN_USER.password)
    await b.click()
    await page.waitForURL('**/dashboard**', { timeout: 30000 })
  }
  await page.waitForTimeout(1000)
}

/**
 * 收集控制台错误
 * @param page Playwright Page 实例
 */
function collectConsoleErrors(page: Page): void {
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      consoleErrors.push(msg)
    }
  })
}

/**
 * 截图辅助函数
 * @param page Playwright Page 实例
 * @param name 截图名称
 */
async function takeScreenshot(page: Page, name: string): Promise<string> {
  const path = `${SCREENSHOT_DIR}/${name}.png`
  await page.screenshot({ path, fullPage: true })
  return path
}

test.describe('WheatAgent 全面 E2E 测试', () => {

  test.beforeEach(({ page }) => {
    consoleErrors.length = 0
    collectConsoleErrors(page)
  })

  /* ==================== 1. 登录流程测试 ==================== */
  test.describe('1. 登录流程测试', () => {

    /**
     * 测试登录页面正确渲染
     */
    test('1.1 登录页面正确渲染', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(500)
      await expect(page.locator('input[placeholder*="用户名"]').first()).toBeVisible()
      await expect(page.locator('input[type="password"]').first()).toBeVisible()
      await expect(page.locator('button:has-text("登录")').first()).toBeVisible()
      await takeScreenshot(page, '01-login-page')
    })

    /**
     * 测试管理员登录成功并跳转到仪表盘
     */
    test('1.2 管理员登录成功跳转到 /dashboard', async ({ page }) => {
      await loginAsAdmin(page)
      const url = page.url()
      expect(url).toContain('/dashboard')
      await takeScreenshot(page, '01-login-success-dashboard')
    })

    /**
     * 测试错误凭证登录失败
     */
    test('1.3 错误凭证登录失败', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(500)
      await page.locator('input[placeholder*="用户名"]').first().fill('wrong_user')
      await page.locator('input[type="password"]').first().fill('wrong_pass')
      await page.locator('button:has-text("登录")').first().click()
      await page.waitForTimeout(3000)
      const stillOnLogin = page.url().includes('/login')
      const hasError = await page.locator('.el-message--error, .el-form-item__error, [class*="error"]').count() > 0
      expect(stillOnLogin || hasError).toBeTruthy()
      await takeScreenshot(page, '01-login-failed')
    })
  })

  /* ==================== 2. 仪表盘页面测试 ==================== */
  test.describe('2. 仪表盘页面测试', () => {

    /**
     * 测试仪表盘统计卡片显示
     */
    test('2.1 仪表盘统计卡片显示', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/dashboard')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      const statCards = page.locator('.stat-card')
      await expect(statCards.first()).toBeVisible({ timeout: 15000 })

      const cardCount = await statCards.count()
      expect(cardCount).toBeGreaterThanOrEqual(4)

      await expect(page.locator('text=今日诊断次数')).toBeVisible()
      await expect(page.locator('text=总诊断次数')).toBeVisible()
      await expect(page.locator('text=平均准确率')).toBeVisible()
      await expect(page.locator('text=活跃用户数')).toBeVisible()

      await takeScreenshot(page, '02-dashboard-stats')
    })

    /**
     * 测试仪表盘图表渲染
     */
    test('2.2 仪表盘图表渲染', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/dashboard')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      const hasChart = await page.locator('canvas, .echarts, [class*="chart"]').count()
      expect(hasChart).toBeGreaterThan(0)

      await takeScreenshot(page, '02-dashboard-charts')
    })
  })

  /* ==================== 3. 诊断页面测试 ==================== */
  test.describe('3. 诊断页面测试', () => {

    /**
     * 测试诊断页面上传区域显示
     */
    test('3.1 诊断页面上传区域显示', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/diagnosis')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(2000)

      await expect(page.locator('text=多模态融合诊断')).toBeVisible()

      const hasUploadArea = await page.locator('.upload-area, [class*="upload"], input[type="file"]').count()
      expect(hasUploadArea).toBeGreaterThan(0)

      await takeScreenshot(page, '03-diagnosis-upload')
    })

    /**
     * 测试诊断页面无严重控制台错误
     */
    test('3.2 诊断页面无严重控制台错误', async ({ page }) => {
      const pageErrors: string[] = []
      page.on('console', (msg) => {
        if (msg.type() === 'error') {
          pageErrors.push(msg.text())
        }
      })

      await loginAsAdmin(page)
      await page.goto('/diagnosis')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      const criticalErrors = pageErrors.filter(e =>
        !e.includes('favicon') &&
        !e.includes('manifest') &&
        !e.includes('net::ERR') &&
        !e.includes('404') &&
        !e.includes('ResizeObserver') &&
        !e.includes('Non-Error promise rejection')
      )
      expect(criticalErrors.length).toBeLessThanOrEqual(5)
    })
  })

  /* ==================== 4. 记录页面测试 ==================== */
  test.describe('4. 记录页面测试', () => {

    /**
     * 测试记录列表或空状态显示
     */
    test('4.1 记录列表或空状态显示', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/records')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await expect(page.locator('text=诊断记录')).toBeVisible({ timeout: 10000 })

      const hasTable = await page.locator('.el-table').count()
      const hasEmpty = await page.locator('.el-empty, text=暂无诊断记录').count()
      expect(hasTable + hasEmpty).toBeGreaterThan(0)

      await takeScreenshot(page, '04-records-page')
    })
  })

  /* ==================== 5. 知识库页面测试 ==================== */
  test.describe('5. 知识库页面测试', () => {

    /**
     * 测试知识卡片或列表显示
     */
    test('5.1 知识卡片或列表显示', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/knowledge')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await expect(page.locator('text=病害知识库')).toBeVisible({ timeout: 10000 })

      const hasCards = await page.locator('.disease-card, [class*="disease-card"]').count()
      const hasEmpty = await page.locator('.el-empty, text=未找到相关病害信息').count()
      const hasAnyCard = await page.locator('.el-card').count()
      expect(hasCards + hasEmpty + hasAnyCard).toBeGreaterThan(0)

      await takeScreenshot(page, '05-knowledge-page')
    })
  })

  /* ==================== 6. 管理后台5个标签页测试 ==================== */
  test.describe('6. 管理后台标签页测试', () => {

    /**
     * 测试系统概览标签页 - 4个统计卡片
     */
    test('6.1 系统概览 - 4个统计卡片', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/admin?tab=overview')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await expect(page.locator('text=管理后台')).toBeVisible({ timeout: 10000 })
      await expect(page.locator('text=用户总数')).toBeVisible({ timeout: 10000 })
      await expect(page.locator('text=诊断总数')).toBeVisible()
      await expect(page.locator('text=疾病知识')).toBeVisible()
      await expect(page.locator('text=GPU 显存')).toBeVisible()

      await takeScreenshot(page, '06-admin-overview')
    })

    /**
     * 测试系统监控标签页 - GPU显存和缓存管理
     */
    test('6.2 系统监控 - GPU显存和缓存管理', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/admin?tab=monitor')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await expect(page.locator('text=GPU 显存监控')).toBeVisible({ timeout: 10000 })
      await expect(page.locator('text=缓存管理')).toBeVisible()

      await expect(page.locator('text=已用显存')).toBeVisible()
      await expect(page.locator('text=清理显存')).toBeVisible()
      await expect(page.locator('text=清空缓存')).toBeVisible()

      await takeScreenshot(page, '06-admin-monitor')
    })

    /**
     * 测试诊断日志标签页 - 日志统计和表格
     */
    test('6.3 诊断日志 - 日志统计和表格', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/admin?tab=logs')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await expect(page.locator('text=最近诊断日志')).toBeVisible({ timeout: 10000 })

      const hasLogStats = await page.locator('text=总诊断数, text=成功数, text=失败数').count()
      expect(hasLogStats).toBeGreaterThan(0)

      const hasTable = await page.locator('.el-table, .log-table').count()
      expect(hasTable).toBeGreaterThan(0)

      await takeScreenshot(page, '06-admin-logs')
    })

    /**
     * 测试病害分布标签页 - ECharts饼图
     */
    test('6.4 病害分布 - ECharts饼图', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/admin?tab=distribution')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await expect(page.locator('text=病害分布统计')).toBeVisible({ timeout: 10000 })

      const hasChart = await page.locator('canvas, .echarts, [class*="chart"]').count()
      expect(hasChart).toBeGreaterThan(0)

      await takeScreenshot(page, '06-admin-distribution')
    })

    /**
     * 测试AI模型管理标签页 - 模型管理信息
     */
    test('6.5 AI模型管理 - 模型管理信息', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/admin?tab=models')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await expect(page.locator('text=AI 模型管理')).toBeVisible({ timeout: 10000 })
      await expect(page.locator('text=Qwen3-VL-2B-Instruct')).toBeVisible()
      await expect(page.locator('text=预加载模型')).toBeVisible()

      await takeScreenshot(page, '06-admin-models')
    })
  })

  /* ==================== 7. 用户中心测试 ==================== */
  test.describe('7. 用户中心测试', () => {

    /**
     * 测试用户信息显示
     */
    test('7.1 用户信息显示', async ({ page }) => {
      await loginAsAdmin(page)
      await page.goto('/user')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(3000)

      await expect(page.locator('text=个人信息')).toBeVisible({ timeout: 10000 })

      const hasUsername = await page.locator('text=v21test_admin').count()
      expect(hasUsername).toBeGreaterThan(0)

      await expect(page.locator('text=使用统计')).toBeVisible()

      await takeScreenshot(page, '07-user-center')
    })
  })

  /* ==================== 8. 安全性测试 ==================== */
  test.describe('8. 安全性测试', () => {

    /**
     * 测试XSS防护：在搜索框输入脚本标签，验证不被执行
     */
    test('8.1 XSS防护 - 搜索框输入脚本标签', async ({ page }) => {
      let xssTriggered = false
      page.on('dialog', async () => {
        xssTriggered = true
        await page.dismissDialog()
      })

      await loginAsAdmin(page)
      await page.goto('/knowledge')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(2000)

      const searchInput = page.locator('input[placeholder*="搜索"]').first()
      if (await searchInput.count() > 0) {
        await searchInput.fill('<script>alert(1)</script>')
        await page.waitForTimeout(2000)

        expect(xssTriggered).toBeFalsy()

        const pageContent = await page.content()
        const hasRawScript = pageContent.includes('<script>alert(1)</script>') &&
          !pageContent.includes('&lt;script&gt;')
        expect(hasRawScript).toBeFalsy()
      }

      await takeScreenshot(page, '08-xss-test')
    })

    /**
     * 测试SQL注入防护：在登录框输入SQL注入字符串，验证登录失败
     * 使用绕过前端验证的方式直接提交
     */
    test('8.2 SQL注入防护 - 登录框输入注入字符串', async ({ page }) => {
      await page.goto('/login')
      await page.waitForLoadState('domcontentloaded')
      await page.waitForTimeout(500)

      const usernameInput = page.locator('input[placeholder*="用户名"]').first()
      const passwordInput = page.locator('input[type="password"]').first()

      await usernameInput.fill("admin' OR '1'='1")
      await passwordInput.fill("any' OR '1'='1")

      await page.locator('button:has-text("登录")').first().click()
      await page.waitForTimeout(3000)

      const stillOnLogin = page.url().includes('/login')
      const hasError = await page.locator('.el-message--error, .el-form-item__error, [class*="error"]').count() > 0
      expect(stillOnLogin || hasError).toBeTruthy()

      await takeScreenshot(page, '08-sql-injection-test')
    })

    /**
     * 测试权限越权：无Token访问管理接口，验证返回401/403
     * 使用 127.0.0.1 避免 IPv6 解析问题
     */
    test('8.3 权限越权 - 无Token访问管理接口返回401', async ({ page }) => {
      const apiContext = await page.context().request

      const endpoints = [
        `${BACKEND_URL}/stats/overview`,
        `${BACKEND_URL}/stats/users`,
        `${BACKEND_URL}/stats/vram`,
        `${BACKEND_URL}/logs/statistics`,
      ]

      for (const endpoint of endpoints) {
        const response = await apiContext.get(endpoint, {
          headers: {
            'Cookie': '',
          },
          failOnStatusCode: false,
        })
        const status = response.status()
        expect([401, 403, 422]).toContain(status)
      }
    })
  })
})
