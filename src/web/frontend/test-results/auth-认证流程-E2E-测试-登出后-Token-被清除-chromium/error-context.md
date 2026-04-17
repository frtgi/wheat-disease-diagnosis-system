# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: auth.spec.ts >> 认证流程 E2E 测试 >> 登出后 Token 被清除
- Location: e2e\auth.spec.ts:42:3

# Error details

```
TimeoutError: page.waitForFunction: Timeout 15000ms exceeded.
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
        - text: v21test_admin
    - generic [ref=e15]:
      - generic [ref=e16]: "* 密码"
      - generic [ref=e19]:
        - textbox "* 密码" [ref=e20]:
          - /placeholder: 请输入密码
          - text: Test1234!
        - img [ref=e23] [cursor=pointer]
    - generic [ref=e28] [cursor=pointer]:
      - generic [ref=e29]:
        - checkbox "记住我"
      - generic [ref=e31]: 记住我
    - button "登录" [ref=e34] [cursor=pointer]:
      - generic [ref=e35]: 登录
    - generic [ref=e36]:
      - link "忘记密码？" [ref=e37] [cursor=pointer]:
        - /url: /forgot-password
      - text: "|"
      - link "还没有账号？立即注册" [ref=e38] [cursor=pointer]:
        - /url: /register
```

# Test source

```ts
  1  | import { test as base, expect } from '@playwright/test'
  2  | 
  3  | type TestFixtures = {
  4  |   loggedInPage: typeof base
  5  | }
  6  | 
  7  | async function login(page: import('@playwright/test').Page) {
  8  |   await page.goto('/login')
  9  |   await page.waitForLoadState('networkidle')
  10 |   const usernameInput = page.locator('input[placeholder*="用户名"]').first()
  11 |   const passwordInput = page.locator('input[type="password"]').first()
  12 |   const submitBtn = page.locator('button:has-text("登录")').first()
  13 |   await usernameInput.clear()
  14 |   await usernameInput.fill('v21test_admin')
  15 |   await passwordInput.clear()
  16 |   await passwordInput.fill('Test1234!')
  17 |   await submitBtn.click()
  18 |   await page.waitForFunction(() => {
  19 |     return !window.location.href.includes('/login')
  20 |   }, { timeout: 20000 }).catch(async () => {
  21 |     await page.reload()
  22 |     await page.waitForLoadState('networkidle')
  23 |     const u = page.locator('input[placeholder*="用户名"]').first()
  24 |     const p = page.locator('input[type="password"]').first()
  25 |     const b = page.locator('button:has-text("登录")').first()
  26 |     await u.clear()
  27 |     await u.fill('v21test_admin')
  28 |     await p.clear()
  29 |     await p.fill('Test1234!')
  30 |     await b.click()
> 31 |     await page.waitForFunction(() => !window.location.href.includes('/login'), { timeout: 20000 })
     |                ^ TimeoutError: page.waitForFunction: Timeout 15000ms exceeded.
  32 |   })
  33 |   await page.waitForTimeout(1500)
  34 | }
  35 | 
  36 | export const test = base.extend<TestFixtures>({
  37 |   loggedInPage: async ({ page }, use) => {
  38 |     await login(page)
  39 |     await use(page)
  40 |   },
  41 | })
  42 | 
  43 | export { expect, login }
  44 | 
  45 | export const ADMIN_USER = {
  46 |   username: 'v21test_admin',
  47 |   password: 'Test1234!',
  48 | }
  49 | 
  50 | export const WRONG_USER = {
  51 |   username: 'wrong_user',
  52 |   password: 'wrong_pass',
  53 | }
  54 | 
```