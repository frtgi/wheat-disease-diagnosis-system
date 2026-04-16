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
  // TODO: 安全改进 - 将 Token 存储从 localStorage 迁移至 httpOnly cookie
  // 当前风险: localStorage 中的 Token 可被 XSS 攻击窃取
  // 迁移方案: 后端设置 httpOnly cookie, 前端无需手动管理 Token
  const token = ref<string>(localStorage.getItem('token') || '')
  const userInfo = ref(getStoredUserInfo())

  // 计算属性：是否已登录
  const isLoggedIn = computed(() => !!token.value)

  // 方法：设置 token
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
