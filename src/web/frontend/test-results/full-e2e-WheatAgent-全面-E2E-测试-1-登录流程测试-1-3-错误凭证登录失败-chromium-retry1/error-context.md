# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: full-e2e.spec.ts >> WheatAgent 全面 E2E 测试 >> 1. 登录流程测试 >> 1.3 错误凭证登录失败
- Location: e2e\full-e2e.spec.ts:116:5

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5173/login
Call log:
  - navigating to "http://localhost:5173/login", waiting until "load"

```

# Test source

```ts
  17  |  * 登录辅助函数
  18  |  * 使用更稳健的等待策略，增加超时时间和重试次数
  19  |  * @param page Playwright Page 实例
  20  |  */
  21  | async function loginAsAdmin(page: Page): Promise<void> {
  22  |   await page.goto('/login')
  23  |   await page.waitForLoadState('domcontentloaded')
  24  |   await page.waitForTimeout(1000)
  25  | 
  26  |   const usernameInput = page.locator('input[placeholder*="用户名"]').first()
  27  |   const passwordInput = page.locator('input[type="password"]').first()
  28  |   const submitBtn = page.locator('button:has-text("登录")').first()
  29  | 
  30  |   await usernameInput.waitFor({ state: 'visible', timeout: 10000 })
  31  |   await usernameInput.clear()
  32  |   await usernameInput.fill(ADMIN_USER.username)
  33  |   await passwordInput.clear()
  34  |   await passwordInput.fill(ADMIN_USER.password)
  35  |   await submitBtn.click()
  36  | 
  37  |   try {
  38  |     await page.waitForURL('**/dashboard**', { timeout: 30000 })
  39  |   } catch {
  40  |     await page.reload()
  41  |     await page.waitForLoadState('domcontentloaded')
  42  |     await page.waitForTimeout(1000)
  43  |     const u = page.locator('input[placeholder*="用户名"]').first()
  44  |     const p = page.locator('input[type="password"]').first()
  45  |     const b = page.locator('button:has-text("登录")').first()
  46  |     await u.waitFor({ state: 'visible', timeout: 10000 })
  47  |     await u.clear()
  48  |     await u.fill(ADMIN_USER.username)
  49  |     await p.clear()
  50  |     await p.fill(ADMIN_USER.password)
  51  |     await b.click()
  52  |     await page.waitForURL('**/dashboard**', { timeout: 30000 })
  53  |   }
  54  |   await page.waitForTimeout(1000)
  55  | }
  56  | 
  57  | /**
  58  |  * 收集控制台错误
  59  |  * @param page Playwright Page 实例
  60  |  */
  61  | function collectConsoleErrors(page: Page): void {
  62  |   page.on('console', (msg) => {
  63  |     if (msg.type() === 'error') {
  64  |       consoleErrors.push(msg)
  65  |     }
  66  |   })
  67  | }
  68  | 
  69  | /**
  70  |  * 截图辅助函数
  71  |  * @param page Playwright Page 实例
  72  |  * @param name 截图名称
  73  |  */
  74  | async function takeScreenshot(page: Page, name: string): Promise<string> {
  75  |   const path = `${SCREENSHOT_DIR}/${name}.png`
  76  |   await page.screenshot({ path, fullPage: true })
  77  |   return path
  78  | }
  79  | 
  80  | test.describe('WheatAgent 全面 E2E 测试', () => {
  81  | 
  82  |   test.beforeEach(({ page }) => {
  83  |     consoleErrors.length = 0
  84  |     collectConsoleErrors(page)
  85  |   })
  86  | 
  87  |   /* ==================== 1. 登录流程测试 ==================== */
  88  |   test.describe('1. 登录流程测试', () => {
  89  | 
  90  |     /**
  91  |      * 测试登录页面正确渲染
  92  |      */
  93  |     test('1.1 登录页面正确渲染', async ({ page }) => {
  94  |       await page.goto('/login')
  95  |       await page.waitForLoadState('domcontentloaded')
  96  |       await page.waitForTimeout(500)
  97  |       await expect(page.locator('input[placeholder*="用户名"]').first()).toBeVisible()
  98  |       await expect(page.locator('input[type="password"]').first()).toBeVisible()
  99  |       await expect(page.locator('button:has-text("登录")').first()).toBeVisible()
  100 |       await takeScreenshot(page, '01-login-page')
  101 |     })
  102 | 
  103 |     /**
  104 |      * 测试管理员登录成功并跳转到仪表盘
  105 |      */
  106 |     test('1.2 管理员登录成功跳转到 /dashboard', async ({ page }) => {
  107 |       await loginAsAdmin(page)
  108 |       const url = page.url()
  109 |       expect(url).toContain('/dashboard')
  110 |       await takeScreenshot(page, '01-login-success-dashboard')
  111 |     })
  112 | 
  113 |     /**
  114 |      * 测试错误凭证登录失败
  115 |      */
  116 |     test('1.3 错误凭证登录失败', async ({ page }) => {
> 117 |       await page.goto('/login')
      |                  ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5173/login
  118 |       await page.waitForLoadState('domcontentloaded')
  119 |       await page.waitForTimeout(500)
  120 |       await page.locator('input[placeholder*="用户名"]').first().fill('wrong_user')
  121 |       await page.locator('input[type="password"]').first().fill('wrong_pass')
  122 |       await page.locator('button:has-text("登录")').first().click()
  123 |       await page.waitForTimeout(3000)
  124 |       const stillOnLogin = page.url().includes('/login')
  125 |       const hasError = await page.locator('.el-message--error, .el-form-item__error, [class*="error"]').count() > 0
  126 |       expect(stillOnLogin || hasError).toBeTruthy()
  127 |       await takeScreenshot(page, '01-login-failed')
  128 |     })
  129 |   })
  130 | 
  131 |   /* ==================== 2. 仪表盘页面测试 ==================== */
  132 |   test.describe('2. 仪表盘页面测试', () => {
  133 | 
  134 |     /**
  135 |      * 测试仪表盘统计卡片显示
  136 |      */
  137 |     test('2.1 仪表盘统计卡片显示', async ({ page }) => {
  138 |       await loginAsAdmin(page)
  139 |       await page.goto('/dashboard')
  140 |       await page.waitForLoadState('domcontentloaded')
  141 |       await page.waitForTimeout(3000)
  142 | 
  143 |       const statCards = page.locator('.stat-card')
  144 |       await expect(statCards.first()).toBeVisible({ timeout: 15000 })
  145 | 
  146 |       const cardCount = await statCards.count()
  147 |       expect(cardCount).toBeGreaterThanOrEqual(4)
  148 | 
  149 |       await expect(page.locator('text=今日诊断次数')).toBeVisible()
  150 |       await expect(page.locator('text=总诊断次数')).toBeVisible()
  151 |       await expect(page.locator('text=平均准确率')).toBeVisible()
  152 |       await expect(page.locator('text=活跃用户数')).toBeVisible()
  153 | 
  154 |       await takeScreenshot(page, '02-dashboard-stats')
  155 |     })
  156 | 
  157 |     /**
  158 |      * 测试仪表盘图表渲染
  159 |      */
  160 |     test('2.2 仪表盘图表渲染', async ({ page }) => {
  161 |       await loginAsAdmin(page)
  162 |       await page.goto('/dashboard')
  163 |       await page.waitForLoadState('domcontentloaded')
  164 |       await page.waitForTimeout(3000)
  165 | 
  166 |       const hasChart = await page.locator('canvas, .echarts, [class*="chart"]').count()
  167 |       expect(hasChart).toBeGreaterThan(0)
  168 | 
  169 |       await takeScreenshot(page, '02-dashboard-charts')
  170 |     })
  171 |   })
  172 | 
  173 |   /* ==================== 3. 诊断页面测试 ==================== */
  174 |   test.describe('3. 诊断页面测试', () => {
  175 | 
  176 |     /**
  177 |      * 测试诊断页面上传区域显示
  178 |      */
  179 |     test('3.1 诊断页面上传区域显示', async ({ page }) => {
  180 |       await loginAsAdmin(page)
  181 |       await page.goto('/diagnosis')
  182 |       await page.waitForLoadState('domcontentloaded')
  183 |       await page.waitForTimeout(2000)
  184 | 
  185 |       await expect(page.locator('text=多模态融合诊断')).toBeVisible()
  186 | 
  187 |       const hasUploadArea = await page.locator('.upload-area, [class*="upload"], input[type="file"]').count()
  188 |       expect(hasUploadArea).toBeGreaterThan(0)
  189 | 
  190 |       await takeScreenshot(page, '03-diagnosis-upload')
  191 |     })
  192 | 
  193 |     /**
  194 |      * 测试诊断页面无严重控制台错误
  195 |      */
  196 |     test('3.2 诊断页面无严重控制台错误', async ({ page }) => {
  197 |       const pageErrors: string[] = []
  198 |       page.on('console', (msg) => {
  199 |         if (msg.type() === 'error') {
  200 |           pageErrors.push(msg.text())
  201 |         }
  202 |       })
  203 | 
  204 |       await loginAsAdmin(page)
  205 |       await page.goto('/diagnosis')
  206 |       await page.waitForLoadState('domcontentloaded')
  207 |       await page.waitForTimeout(3000)
  208 | 
  209 |       const criticalErrors = pageErrors.filter(e =>
  210 |         !e.includes('favicon') &&
  211 |         !e.includes('manifest') &&
  212 |         !e.includes('net::ERR') &&
  213 |         !e.includes('404') &&
  214 |         !e.includes('ResizeObserver') &&
  215 |         !e.includes('Non-Error promise rejection')
  216 |       )
  217 |       expect(criticalErrors.length).toBeLessThanOrEqual(5)
```