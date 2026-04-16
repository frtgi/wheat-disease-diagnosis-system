/**
 * Pinia Store 测试
 * 测试用户状态管理和应用配置状态管理
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useUserStore, useAppStore } from '@/stores'

/** 真实行为的localStorage存储 */
const localStorageStore: Record<string, string> = {}

describe('Pinia Store 测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    Object.keys(localStorageStore).forEach(k => delete localStorageStore[k])
    localStorage.getItem.mockImplementation((key: string) => localStorageStore[key] ?? null)
    localStorage.setItem.mockImplementation((key: string, value: string) => { localStorageStore[key] = value })
    localStorage.removeItem.mockImplementation((key: string) => { delete localStorageStore[key] })
    localStorage.clear.mockImplementation(() => { Object.keys(localStorageStore).forEach(k => delete localStorageStore[k]) })
  })

  describe('useUserStore', () => {
    /** 测试初始状态token应为空字符串 */
    it('初始状态token应为空字符串', () => {
      const store = useUserStore()
      expect(store.token).toBe('')
    })

    /** 测试初始userInfo应为默认值 */
    it('初始userInfo应为默认空值', () => {
      const store = useUserStore()
      expect(store.userInfo).toEqual({
        id: 0,
        username: '',
        email: '',
        avatar: ''
      })
    })

    describe('setToken', () => {
      /** 测试setToken更新token值 */
      it('应该更新token值', () => {
        const store = useUserStore()
        store.setToken('new-access-token')
        expect(store.token).toBe('new-access-token')
      })

      /** 测试setToken同步更新localStorage */
      it('应该同步更新localStorage中的token', () => {
        const store = useUserStore()
        store.setToken('new-access-token')
        expect(localStorage.setItem).toHaveBeenCalledWith('token', 'new-access-token')
      })

      /** 测试多次调用setToken覆盖旧值 */
      it('多次调用应覆盖旧token值', () => {
        const store = useUserStore()
        store.setToken('first-token')
        store.setToken('second-token')
        expect(store.token).toBe('second-token')
        expect(localStorage.setItem).toHaveBeenCalledWith('token', 'second-token')
      })
    })

    describe('setUserInfo', () => {
      /** 测试setUserInfo更新userInfo值 */
      it('应该更新userInfo值', () => {
        const store = useUserStore()
        const info = {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          avatar: 'avatar.png'
        }
        store.setUserInfo(info)
        expect(store.userInfo).toEqual(info)
      })

      /** 测试setUserInfo同步更新localStorage */
      it('应该同步更新localStorage中的userInfo', () => {
        const store = useUserStore()
        const info = {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          avatar: 'avatar.png'
        }
        store.setUserInfo(info)
        expect(localStorage.setItem).toHaveBeenCalledWith('userInfo', JSON.stringify(info))
      })

      /** 测试setUserInfo部分更新 */
      it('应该支持部分更新userInfo', () => {
        const store = useUserStore()
        const partialInfo = {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          avatar: ''
        }
        store.setUserInfo(partialInfo)
        expect(store.userInfo.username).toBe('testuser')
        expect(store.userInfo.email).toBe('test@example.com')
      })
    })

    describe('logout', () => {
      /** 测试logout清除token */
      it('应该清除token', () => {
        const store = useUserStore()
        store.setToken('some-token')
        store.logout()
        expect(store.token).toBe('')
      })

      /** 测试logout重置userInfo为默认值 */
      it('应该重置userInfo为默认值', () => {
        const store = useUserStore()
        store.setUserInfo({
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          avatar: 'avatar.png'
        })
        store.logout()
        expect(store.userInfo).toEqual({
          id: 0,
          username: '',
          email: '',
          avatar: ''
        })
      })

      /** 测试logout清除localStorage中的token */
      it('应该清除localStorage中的token', () => {
        const store = useUserStore()
        store.setToken('some-token')
        store.logout()
        expect(localStorage.removeItem).toHaveBeenCalledWith('token')
      })

      /** 测试logout清除localStorage中的userInfo */
      it('应该清除localStorage中的userInfo', () => {
        const store = useUserStore()
        store.setUserInfo({
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          avatar: 'avatar.png'
        })
        store.logout()
        expect(localStorage.removeItem).toHaveBeenCalledWith('userInfo')
      })

      /** 测试logout清除localStorage中的refresh_token */
      it('应该清除localStorage中的refresh_token', () => {
        const store = useUserStore()
        localStorage.setItem('refresh_token', 'some-refresh-token')
        store.logout()
        expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
      })
    })

    describe('isLoggedIn', () => {
      /** 测试无token时isLoggedIn为false */
      it('无token时isLoggedIn应为false', () => {
        const store = useUserStore()
        expect(store.isLoggedIn).toBe(false)
      })

      /** 测试有token时isLoggedIn为true */
      it('有token时isLoggedIn应为true', () => {
        const store = useUserStore()
        store.setToken('valid-token')
        expect(store.isLoggedIn).toBe(true)
      })

      /** 测试logout后isLoggedIn变为false */
      it('logout后isLoggedIn应变为false', () => {
        const store = useUserStore()
        store.setToken('valid-token')
        expect(store.isLoggedIn).toBe(true)
        store.logout()
        expect(store.isLoggedIn).toBe(false)
      })

      /** 测试token为空字符串时isLoggedIn为false */
      it('token为空字符串时isLoggedIn应为false', () => {
        const store = useUserStore()
        store.setToken('')
        expect(store.isLoggedIn).toBe(false)
      })
    })

    describe('从localStorage恢复状态', () => {
      /** 测试从localStorage恢复token */
      it('应从localStorage恢复token', () => {
        localStorageStore['token'] = 'restored-token'
        const newPinia = createPinia()
        setActivePinia(newPinia)
        const store = useUserStore()
        expect(store.token).toBe('restored-token')
      })

      /** 测试从localStorage恢复userInfo */
      it('应从localStorage恢复userInfo', () => {
        const userInfo = {
          id: 2,
          username: 'restored-user',
          email: 'restored@example.com',
          avatar: 'restored-avatar.png'
        }
        localStorageStore['userInfo'] = JSON.stringify(userInfo)
        localStorageStore['token'] = 'restored-token'
        const newPinia = createPinia()
        setActivePinia(newPinia)
        const store = useUserStore()
        expect(store.userInfo).toEqual(userInfo)
      })

      /** 测试localStorage中无数据时使用默认值 */
      it('localStorage中无数据时应使用默认值', () => {
        const newPinia = createPinia()
        setActivePinia(newPinia)
        const store = useUserStore()
        expect(store.token).toBe('')
        expect(store.userInfo).toEqual({
          id: 0,
          username: '',
          email: '',
          avatar: ''
        })
      })

      /** 测试localStorage中userInfo格式错误时使用默认值 */
      it('localStorage中userInfo格式错误时应使用默认值', () => {
        localStorageStore['userInfo'] = 'invalid-json'
        localStorageStore['token'] = 'some-token'
        const newPinia = createPinia()
        setActivePinia(newPinia)
        const store = useUserStore()
        expect(store.userInfo).toEqual({
          id: 0,
          username: '',
          email: '',
          avatar: ''
        })
      })
    })
  })

  describe('useAppStore', () => {
    /** 测试初始侧边栏状态为未折叠 */
    it('初始sidebarCollapsed应为false', () => {
      const store = useAppStore()
      expect(store.sidebarCollapsed).toBe(false)
    })

    /** 测试初始主题色 */
    it('初始themeColor应为#409eff', () => {
      const store = useAppStore()
      expect(store.themeColor).toBe('#409eff')
    })

    describe('toggleSidebar', () => {
      /** 测试切换侧边栏折叠状态 */
      it('应该切换侧边栏折叠状态', () => {
        const store = useAppStore()
        expect(store.sidebarCollapsed).toBe(false)
        store.toggleSidebar()
        expect(store.sidebarCollapsed).toBe(true)
      })

      /** 测试多次切换侧边栏状态 */
      it('多次切换应正确反映状态', () => {
        const store = useAppStore()
        store.toggleSidebar()
        expect(store.sidebarCollapsed).toBe(true)
        store.toggleSidebar()
        expect(store.sidebarCollapsed).toBe(false)
        store.toggleSidebar()
        expect(store.sidebarCollapsed).toBe(true)
      })
    })

    describe('setThemeColor', () => {
      /** 测试设置主题色 */
      it('应该设置主题色', () => {
        const store = useAppStore()
        store.setThemeColor('#ff0000')
        expect(store.themeColor).toBe('#ff0000')
      })

      /** 测试多次设置主题色覆盖旧值 */
      it('多次设置应覆盖旧主题色', () => {
        const store = useAppStore()
        store.setThemeColor('#ff0000')
        store.setThemeColor('#00ff00')
        expect(store.themeColor).toBe('#00ff00')
      })

      /** 测试设置不同格式的主题色 */
      it('应支持不同格式的主题色', () => {
        const store = useAppStore()
        store.setThemeColor('rgb(255, 0, 0)')
        expect(store.themeColor).toBe('rgb(255, 0, 0)')
      })
    })
  })
})
