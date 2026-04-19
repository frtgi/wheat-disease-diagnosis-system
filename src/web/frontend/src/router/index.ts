/**
 * 路由配置文件
 * 负责配置应用的所有路由和导航守卫
 */
import { createRouter, createWebHistory } from 'vue-router'
import type { RouteRecordRaw } from 'vue-router'

declare module 'vue-router' {
  interface RouteMeta {
    title?: string
    requiresAuth?: boolean
    requiresAdmin?: boolean
  }
}

// 定义路由配置
const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', requiresAuth: false }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { title: '注册', requiresAuth: false }
  },
  {
    path: '/forgot-password',
    name: 'ForgotPassword',
    component: () => import('@/views/ForgotPassword.vue'),
    meta: { title: '忘记密码', requiresAuth: false }
  },
  {
    path: '/',
    component: () => import('@/components/Layout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '首页', requiresAuth: true }
      },
      {
        path: 'diagnosis',
        name: 'Diagnosis',
        component: () => import('@/views/Diagnosis.vue'),
        meta: { title: '诊断', requiresAuth: true }
      },
      {
        path: 'records',
        name: 'Records',
        component: () => import('@/views/Records.vue'),
        meta: { title: '记录', requiresAuth: true }
      },
      {
        path: 'knowledge',
        name: 'Knowledge',
        component: () => import('@/views/Knowledge.vue'),
        meta: { title: '知识库', requiresAuth: true }
      },
      {
        path: 'user',
        name: 'User',
        component: () => import('@/views/User.vue'),
        meta: { title: '用户中心', requiresAuth: true }
      },
      {
        path: 'sessions',
        name: 'Sessions',
        component: () => import('@/views/Sessions.vue'),
        meta: { title: '会话管理', requiresAuth: true }
      },
      {
        path: 'admin',
        name: 'Admin',
        component: () => import('@/views/Admin.vue'),
        meta: { title: '管理后台', requiresAuth: true, requiresAdmin: true }
      }
    ]
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由导航守卫
router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  const hasUserInfo = (() => {
    try {
      const info = JSON.parse(localStorage.getItem('userInfo') || '{}')
      return !!info.id
    } catch {
      return false
    }
  })()
  const isAuthenticated = !!token && hasUserInfo
  const hasSession = hasUserInfo
  
  document.title = to.meta.title ? `${to.meta.title} - 小麦病害诊断系统` : '小麦病害诊断系统'
  
  const requiresAuth = to.meta.requiresAuth

  if (requiresAuth && !isAuthenticated && !hasSession) {
    return { name: 'Login', query: { redirect: to.fullPath } }
  } else if (requiresAuth && !isAuthenticated && hasSession) {
    // token 过期但有 userInfo，允许访问页面，拦截器会自动刷新 token
  } else if ((to.name === 'Login' || to.name === 'Register') && isAuthenticated) {
    return { path: '/dashboard' }
  }
  
  // 检查管理员权限
  if (to.meta.requiresAdmin) {
    try {
      const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
      if (userInfo.role !== 'admin') {
        return { path: '/dashboard' }
      }
    } catch {
      return { path: '/dashboard' }
    }
  }
  
  // 允许导航
  return true
})

export default router
