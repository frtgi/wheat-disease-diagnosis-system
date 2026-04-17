# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: diagnosis.spec.ts >> 诊断流程 E2E 测试 >> 诊断页面导航可访问
- Location: e2e\diagnosis.spec.ts:12:3

# Error details

```
Error: expect(received).toContain(expected) // indexOf

Expected substring: "/diagnosis"
Received string:    "http://localhost:5173/login"
```

# Page snapshot

```yaml
- generic [ref=e4]:
  - heading "用户登录" [level=2] [ref=e6]
  - generic [ref=e8]:
    - generic [ref=e9]:
      - generic [ref=e10]: "* 用户名"
      - textbox "* 用户名" [ref=e14]:
        - /placeholder: 请输入用户名
    - generic [ref=e15]:
      - generic [ref=e16]: "* 密码"
      - textbox "* 密码" [ref=e20]:
        - /placeholder: 请输入密码
    - generic [ref=e23] [cursor=pointer]:
      - generic [ref=e24]:
        - checkbox "记住我"
      - generic [ref=e26]: 记住我
    - button "登录" [ref=e29] [cursor=pointer]:
      - generic [ref=e30]: 登录
    - generic [ref=e31]:
      - link "忘记密码？" [ref=e32] [cursor=pointer]:
        - /url: /forgot-password
      - text: "|"
      - link "还没有账号？立即注册" [ref=e33] [cursor=pointer]:
        - /url: /register
```

# Test source

```ts
  1  | import { test, expect } from './helpers'
  2  | 
  3  | test.describe('诊断流程 E2E 测试', () => {
  4  | 
  5  |   test('诊断页面加载和 UI 渲染', async ({ loggedInPage: page }) => {
  6  |     await page.goto('/diagnosis')
  7  |     await page.waitForTimeout(2000)
  8  |     const hasUpload = await page.locator('[class*="upload"], input[type="file"], [class*="drop"]').count() > 0
  9  |     expect(hasUpload).toBeTruthy()
  10 |   })
  11 | 
  12 |   test('诊断页面导航可访问', async ({ loggedInPage: page }) => {
  13 |     await page.goto('/diagnosis')
  14 |     await page.waitForTimeout(1000)
> 15 |     expect(page.url()).toContain('/diagnosis')
     |                        ^ Error: expect(received).toContain(expected) // indexOf
  16 |   })
  17 | 
  18 |   test('图像上传区域可见', async ({ loggedInPage: page }) => {
  19 |     await page.goto('/diagnosis')
  20 |     await page.waitForTimeout(2000)
  21 |     const uploadArea = page.locator('[class*="upload"], [class*="drop-zone"], [class*="image-upload"], .el-upload')
  22 |     await expect(uploadArea.first()).toBeVisible({ timeout: 10000 })
  23 |   })
  24 | 
  25 |   test('诊断按钮或提交区域存在', async ({ loggedInPage: page }) => {
  26 |     await page.goto('/diagnosis')
  27 |     await page.waitForTimeout(2000)
  28 |     const diagBtn = page.locator('button:has-text("诊断"), button:has-text("开始"), button:has-text("分析"), [class*="diagnose"]')
  29 |     const hasBtn = await diagBtn.count() > 0
  30 |     const hasForm = await page.locator('form, [class*="form"]').count() > 0
  31 |     expect(hasBtn || hasForm).toBeTruthy()
  32 |   })
  33 | 
  34 |   test('批量诊断入口可访问', async ({ loggedInPage: page }) => {
  35 |     await page.goto('/diagnosis')
  36 |     await page.waitForTimeout(2000)
  37 |     const batchTab = page.locator('text=批量, [class*="batch"], [role="tab"]:has-text("批量")')
  38 |     const hasBatch = await batchTab.count() > 0
  39 |     if (hasBatch) {
  40 |       await batchTab.first().click()
  41 |       await page.waitForTimeout(1000)
  42 |     }
  43 |     expect(true).toBeTruthy()
  44 |   })
  45 | })
  46 | 
```