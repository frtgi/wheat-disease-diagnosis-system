/**
 * Pinia Store 配置文件
 * 负责管理应用的全局状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * 用户状态管理
 */
export const useUserStore = defineStore('user', () => {
  // 从 localStorage 恢复用户信息
  const getStoredUserInfo = () => {
    try {
      const stored = localStorage.getItem('userInfo')
      if (stored) {
        return JSON.parse(stored)
      }
    } catch (e) {
      console.error('Failed to parse userInfo from localStorage:', e)
    }
    return { id: 0, username: '', email: '', avatar: '', role: '' }
  }

  // 状态
  // Token 主要通过 httpOnly Cookie 传递，localStorage 作为 SSE 等场景的 fallback
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref(getStoredUserInfo())

  // 计算属性：是否已登录
  const isLoggedIn = computed(() => !!token.value)

  // 方法：设置 token
  // Token 主要通过 httpOnly Cookie 由后端设置，前端无需手动管理
  // 此方法保留 localStorage 写入，作为 SSE 等无法自动携带 Cookie 场景的 fallback
  const setToken = (newToken: string) => {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }

  // 方法：设置用户信息
  const setUserInfo = (info: typeof userInfo.value) => {
    userInfo.value = info
    localStorage.setItem('userInfo', JSON.stringify(info))
  }

  // 方法：登出
  const logout = () => {
    token.value = ''
    userInfo.value = { id: 0, username: '', email: '', avatar: '', role: '' }
    localStorage.removeItem('token')
    localStorage.removeItem('userInfo')
    localStorage.removeItem('refresh_token')
  }

  return {
    token,
    userInfo,
    isLoggedIn,
    setToken,
    setUserInfo,
    logout
  }
})

/**
 * 应用配置状态管理
 */
export const useAppStore = defineStore('app', () => {
  // 侧边栏是否折叠
  const sidebarCollapsed = ref(false)

  // 主题色
  const themeColor = ref('#409eff')

  // 方法：切换侧边栏
  const toggleSidebar = () => {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  // 方法：设置主题色
  const setThemeColor = (color: string) => {
    themeColor.value = color
  }

  return {
    sidebarCollapsed,
    themeColor,
    toggleSidebar,
    setThemeColor
  }
})
