/**
 * 路由导航守卫测试
 * 测试路由权限控制、页面标题更新和导航重定向逻辑
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createRouter, createMemoryHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

/** 定义与源文件相同的路由配置 */
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: { template: '<div>Login</div>' },
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: { template: '<div>Register</div>' },
    meta: { title: '注册', requiresAuth: false }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: { template: '<div>ForgotPassword</div>' },
    meta: { title: '忘记密码', requiresAuth: false }
  },
  {
    path: '/',
    component: { template: '<div><router-view /></div>' },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: { template: '<div>Dashboard</div>' },
        meta: { title: '首页', requiresAuth: true }
      },
      {
        path: 'diagnosis',
        name: 'Diagnosis',
        component: { template: '<div>Diagnosis</div>' },
        meta: { title: '诊断', requiresAuth: true }
      },
      {
        path: 'records',
        name: 'Records',
        component: { template: '<div>Records</div>' },
        meta: { title: '记录', requiresAuth: true }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: { template: '<div>Knowledge</div>' },
        meta: { title: '知识库', requiresAuth: true }
      },
      {
        path: 'user',
        name: 'User',
        component: { template: '<div>User</div>' },
        meta: { title: '用户中心', requiresAuth: true }
      },
      {
        path: 'sessions',
        name: 'Sessions',
        component: { template: '<div>Sessions</div>' },
        meta: { title: '会话管理', requiresAuth: true }
      }
    ]
  }
]

/** 真实行为的localStorage存储 */
const localStorageStore: Record<string, string> = {}

/**
 * 创建带导航守卫的测试路由实例
 * @returns 配置好的路由实例
 */
function createTestRouter() {
  const router = createRouter({
    history: createMemoryHistory(),
    routes
  })

  router.beforeEach((to) => {
    document.title = to.meta.title ? `${to.meta.title} - 小麦病害诊断系统` : '小麦病害诊断系统'

    const requiresAuth = to.meta.requiresAuth
    const token = localStorage.getItem('token')

    if (requiresAuth && !token) {
      return { name: 'Login' }
    } else if ((to.name === 'Login' || to.name === 'Register') && token) {
      return { path: '/' }
    }

    return true
  })

  return router
}

describe('路由导航守卫测试', () => {
  let router: ReturnType<typeof createTestRouter>

  beforeEach(() => {
    router = createTestRouter()
    vi.clearAllMocks()
    Object.keys(localStorageStore).forEach(k => delete localStorageStore[k])
    localStorage.getItem.mockImplementation((key: string) => localStorageStore[key] ?? null)
    localStorage.setItem.mockImplementation((key: string, value: string) => { localStorageStore[key] = value })
    localStorage.removeItem.mockImplementation((key: string) => { delete localStorageStore[key] })
    localStorage.clear.mockImplementation(() => { Object.keys(localStorageStore).forEach(k => delete localStorageStore[k]) })
    document.title = ''
  })

  describe('未登录访问受保护页面', () => {
    /** 测试未登录访问Dashboard重定向到登录页 */
    it('未登录访问Dashboard应重定向到/login', async () => {
      await router.push('/dashboard')
      expect(router.currentRoute.value.name).toBe('Login')
    })

    /** 测试未登录访问Diagnosis重定向到登录页 */
    it('未登录访问Diagnosis应重定向到/login', async () => {
      await router.push('/diagnosis')
      expect(router.currentRoute.value.name).toBe('Login')
    })

    /** 测试未登录访问Records重定向到登录页 */
    it('未登录访问Records应重定向到/login', async () => {
      await router.push('/records')
      expect(router.currentRoute.value.name).toBe('Login')
    })

    /** 测试未登录访问Knowledge重定向到登录页 */
    it('未登录访问Knowledge应重定向到/login', async () => {
      await router.push('/knowledge')
      expect(router.currentRoute.value.name).toBe('Login')
    })

    /** 测试未登录访问User重定向到登录页 */
    it('未登录访问User应重定向到/login', async () => {
      await router.push('/user')
      expect(router.currentRoute.value.name).toBe('Login')
    })

    /** 测试未登录访问Sessions重定向到登录页 */
    it('未登录访问Sessions应重定向到/login', async () => {
      await router.push('/sessions')
      expect(router.currentRoute.value.name).toBe('Login')
    })
  })

  describe('已登录访问登录/注册页面', () => {
    /** 测试已登录访问/login重定向到首页 */
    it('已登录访问/login应重定向到首页', async () => {
      localStorage.setItem('token', 'valid-token')
      await router.push('/login')
      expect(router.currentRoute.value.path).toBe('/dashboard')
    })

    /** 测试已登录访问/register重定向到首页 */
    it('已登录访问/register应重定向到首页', async () => {
      localStorage.setItem('token', 'valid-token')
      await router.push('/register')
      expect(router.currentRoute.value.path).toBe('/dashboard')
    })
  })

  describe('页面标题更新', () => {
    /** 测试访问带标题的页面时更新document.title */
    it('访问Dashboard时应设置标题为"首页 - 小麦病害诊断系统"', async () => {
      localStorage.setItem('token', 'valid-token')
      await router.push('/dashboard')
      expect(document.title).toBe('首页 - 小麦病害诊断系统')
    })

    /** 测试访问登录页时更新document.title */
    it('访问登录页时应设置标题为"登录 - 小麦病害诊断系统"', async () => {
      await router.push('/login')
      expect(document.title).toBe('登录 - 小麦病害诊断系统')
    })

    /** 测试访问注册页时更新document.title */
    it('访问注册页时应设置标题为"注册 - 小麦病害诊断系统"', async () => {
      await router.push('/register')
      expect(document.title).toBe('注册 - 小麦病害诊断系统')
    })

    /** 测试访问诊断页时更新document.title */
    it('访问诊断页时应设置标题为"诊断 - 小麦病害诊断系统"', async () => {
      localStorage.setItem('token', 'valid-token')
      await router.push('/diagnosis')
      expect(document.title).toBe('诊断 - 小麦病害诊断系统')
    })

    /** 测试访问知识库页时更新document.title */
    it('访问知识库页时应设置标题为"知识库 - 小麦病害诊断系统"', async () => {
      localStorage.setItem('token', 'valid-token')
      await router.push('/knowledge')
      expect(document.title).toBe('知识库 - 小麦病害诊断系统')
    })
  })

  describe('不需要认证的页面', () => {
    /** 测试未登录访问登录页允许通过 */
    it('未登录访问/login应允许访问', async () => {
      await router.push('/login')
      expect(router.currentRoute.value.name).toBe('Login')
    })

    /** 测试未登录访问注册页允许通过 */
    it('未登录访问/register应允许访问', async () => {
      await router.push('/register')
      expect(router.currentRoute.value.name).toBe('Register')
    })

    /** 测试未登录访问忘记密码页允许通过 */
    it('未登录访问/forgot-password应允许访问', async () => {
      await router.push('/forgot-password')
      expect(router.currentRoute.value.name).toBe('ForgotPassword')
    })

    /** 测试已登录访问受保护页面允许通过 */
    it('已登录访问Dashboard应允许访问', async () => {
      localStorage.setItem('token', 'valid-token')
      await router.push('/dashboard')
      expect(router.currentRoute.value.name).toBe('Dashboard')
    })

    /** 测试已登录访问诊断页允许通过 */
    it('已登录访问Diagnosis应允许访问', async () => {
      localStorage.setItem('token', 'valid-token')
      await router.push('/diagnosis')
      expect(router.currentRoute.value.name).toBe('Diagnosis')
    })
  })
})
