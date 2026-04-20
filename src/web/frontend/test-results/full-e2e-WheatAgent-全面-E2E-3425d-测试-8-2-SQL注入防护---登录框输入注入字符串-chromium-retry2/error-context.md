# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: full-e2e.spec.ts >> WheatAgent 全面 E2E 测试 >> 8. 安全性测试 >> 8.2 SQL注入防护 - 登录框输入注入字符串
- Location: e2e\full-e2e.spec.ts:421:5

# Error details

```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5173/login
Call log:
  - navigating to "http://localhost:5173/login", waiting until "load"

```

# Test source

```ts
  322 | 
  323 |       await takeScreenshot(page, '06-admin-logs')
  324 |     })
  325 | 
  326 |     /**
  327 |      * 测试病害分布标签页 - ECharts饼图
  328 |      */
  329 |     test('6.4 病害分布 - ECharts饼图', async ({ page }) => {
  330 |       await loginAsAdmin(page)
  331 |       await page.goto('/admin?tab=distribution')
  332 |       await page.waitForLoadState('domcontentloaded')
  333 |       await page.waitForTimeout(3000)
  334 | 
  335 |       await expect(page.locator('text=病害分布统计')).toBeVisible({ timeout: 10000 })
  336 | 
  337 |       const hasChart = await page.locator('canvas, .echarts, [class*="chart"]').count()
  338 |       expect(hasChart).toBeGreaterThan(0)
  339 | 
  340 |       await takeScreenshot(page, '06-admin-distribution')
  341 |     })
  342 | 
  343 |     /**
  344 |      * 测试AI模型管理标签页 - 模型管理信息
  345 |      */
  346 |     test('6.5 AI模型管理 - 模型管理信息', async ({ page }) => {
  347 |       await loginAsAdmin(page)
  348 |       await page.goto('/admin?tab=models')
  349 |       await page.waitForLoadState('domcontentloaded')
  350 |       await page.waitForTimeout(3000)
  351 | 
  352 |       await expect(page.locator('text=AI 模型管理')).toBeVisible({ timeout: 10000 })
  353 |       await expect(page.locator('text=Qwen3-VL-2B-Instruct')).toBeVisible()
  354 |       await expect(page.locator('text=预加载模型')).toBeVisible()
  355 | 
  356 |       await takeScreenshot(page, '06-admin-models')
  357 |     })
  358 |   })
  359 | 
  360 |   /* ==================== 7. 用户中心测试 ==================== */
  361 |   test.describe('7. 用户中心测试', () => {
  362 | 
  363 |     /**
  364 |      * 测试用户信息显示
  365 |      */
  366 |     test('7.1 用户信息显示', async ({ page }) => {
  367 |       await loginAsAdmin(page)
  368 |       await page.goto('/user')
  369 |       await page.waitForLoadState('domcontentloaded')
  370 |       await page.waitForTimeout(3000)
  371 | 
  372 |       await expect(page.locator('text=个人信息')).toBeVisible({ timeout: 10000 })
  373 | 
  374 |       const hasUsername = await page.locator('text=v21test_admin').count()
  375 |       expect(hasUsername).toBeGreaterThan(0)
  376 | 
  377 |       await expect(page.locator('text=使用统计')).toBeVisible()
  378 | 
  379 |       await takeScreenshot(page, '07-user-center')
  380 |     })
  381 |   })
  382 | 
  383 |   /* ==================== 8. 安全性测试 ==================== */
  384 |   test.describe('8. 安全性测试', () => {
  385 | 
  386 |     /**
  387 |      * 测试XSS防护：在搜索框输入脚本标签，验证不被执行
  388 |      */
  389 |     test('8.1 XSS防护 - 搜索框输入脚本标签', async ({ page }) => {
  390 |       let xssTriggered = false
  391 |       page.on('dialog', async () => {
  392 |         xssTriggered = true
  393 |         await page.dismissDialog()
  394 |       })
  395 | 
  396 |       await loginAsAdmin(page)
  397 |       await page.goto('/knowledge')
  398 |       await page.waitForLoadState('domcontentloaded')
  399 |       await page.waitForTimeout(2000)
  400 | 
  401 |       const searchInput = page.locator('input[placeholder*="搜索"]').first()
  402 |       if (await searchInput.count() > 0) {
  403 |         await searchInput.fill('<script>alert(1)</script>')
  404 |         await page.waitForTimeout(2000)
  405 | 
  406 |         expect(xssTriggered).toBeFalsy()
  407 | 
  408 |         const pageContent = await page.content()
  409 |         const hasRawScript = pageContent.includes('<script>alert(1)</script>') &&
  410 |           !pageContent.includes('&lt;script&gt;')
  411 |         expect(hasRawScript).toBeFalsy()
  412 |       }
  413 | 
  414 |       await takeScreenshot(page, '08-xss-test')
  415 |     })
  416 | 
  417 |     /**
  418 |      * 测试SQL注入防护：在登录框输入SQL注入字符串，验证登录失败
  419 |      * 使用绕过前端验证的方式直接提交
  420 |      */
  421 |     test('8.2 SQL注入防护 - 登录框输入注入字符串', async ({ page }) => {
> 422 |       await page.goto('/login')
      |                  ^ Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:5173/login
  423 |       await page.waitForLoadState('domcontentloaded')
  424 |       await page.waitForTimeout(500)
  425 | 
  426 |       const usernameInput = page.locator('input[placeholder*="用户名"]').first()
  427 |       const passwordInput = page.locator('input[type="password"]').first()
  428 | 
  429 |       await usernameInput.fill("admin' OR '1'='1")
  430 |       await passwordInput.fill("any' OR '1'='1")
  431 | 
  432 |       await page.locator('button:has-text("登录")').first().click()
  433 |       await page.waitForTimeout(3000)
  434 | 
  435 |       const stillOnLogin = page.url().includes('/login')
  436 |       const hasError = await page.locator('.el-message--error, .el-form-item__error, [class*="error"]').count() > 0
  437 |       expect(stillOnLogin || hasError).toBeTruthy()
  438 | 
  439 |       await takeScreenshot(page, '08-sql-injection-test')
  440 |     })
  441 | 
  442 |     /**
  443 |      * 测试权限越权：无Token访问管理接口，验证返回401/403
  444 |      * 使用 127.0.0.1 避免 IPv6 解析问题
  445 |      */
  446 |     test('8.3 权限越权 - 无Token访问管理接口返回401', async ({ page }) => {
  447 |       const apiContext = await page.context().request
  448 | 
  449 |       const endpoints = [
  450 |         `${BACKEND_URL}/stats/overview`,
  451 |         `${BACKEND_URL}/stats/users`,
  452 |         `${BACKEND_URL}/stats/vram`,
  453 |         `${BACKEND_URL}/logs/statistics`,
  454 |       ]
  455 | 
  456 |       for (const endpoint of endpoints) {
  457 |         const response = await apiContext.get(endpoint, {
  458 |           headers: {
  459 |             'Cookie': '',
  460 |           },
  461 |           failOnStatusCode: false,
  462 |         })
  463 |         const status = response.status()
  464 |         expect([401, 403, 422]).toContain(status)
  465 |       }
  466 |     })
  467 |   })
  468 | })
  469 | 
```