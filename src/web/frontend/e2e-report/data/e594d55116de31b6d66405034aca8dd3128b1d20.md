# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: full-e2e.spec.ts >> WheatAgent 全面 E2E 测试 >> 7. 用户中心测试 >> 7.1 用户信息显示
- Location: e2e\full-e2e.spec.ts:366:5

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5173/login
Call log:
  - navigating to "http://localhost:5173/login", waiting until "load"

```

# Test source

```ts
  1   | /**
  2   |  * WheatAgent 全面 E2E 测试脚本
  3   |  * 覆盖登录、仪表盘、诊断、记录、知识库、管理后台、用户中心及安全性测试
  4   |  */
  5   | import { test, expect, Page, ConsoleMessage } from '@playwright/test'
  6   | 
  7   | const ADMIN_USER = {
  8   |   username: 'v21test_admin',
  9   |   password: 'Test1234!',
  10  | }
  11  | 
  12  | const SCREENSHOT_DIR = 'e2e-screenshots'
  13  | const BACKEND_URL = 'http://127.0.0.1:8000'
  14  | const consoleErrors: ConsoleMessage[] = []
  15  | 
  16  | /**
  17  |  * 登录辅助函数
  18  |  * 使用更稳健的等待策略，增加超时时间和重试次数
  19  |  * @param page Playwright Page 实例
  20  |  */
  21  | async function loginAsAdmin(page: Page): Promise<void> {
> 22  |   await page.goto('/login')
      |              ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5173/login
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
  117 |       await page.goto('/login')
  118 |       await page.waitForLoadState('domcontentloaded')
  119 |       await page.waitForTimeout(500)
  120 |       await page.locator('input[placeholder*="用户名"]').first().fill('wrong_user')
  121 |       await page.locator('input[type="password"]').first().fill('wrong_pass')
  122 |       await page.locator('button:has-text("登录")').first().click()
```