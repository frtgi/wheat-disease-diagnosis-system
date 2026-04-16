/**
 * 布局组件测试
 * 测试导航菜单、登录状态显示、用户下拉菜单、退出登录和活跃菜单高亮
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Layout from '@/components/Layout.vue'

/** 模拟 vue-router */
const mockPush = vi.fn()
const mockRoute = { path: '/' }
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  }),
  useRoute: () => mockRoute,
  RouterView: {
    name: 'RouterView',
    template: '<div class="router-view-stub"><slot /></div>'
  }
}))

/** 模拟用户 Store */
const mockSetUserInfo = vi.fn()
const mockLogout = vi.fn()
vi.mock('@/stores', () => ({
  useUserStore: vi.fn()
}))

/** 模拟 Element Plus */
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn()
    }
  }
})

import { useUserStore } from '@/stores'

/** 创建已登录状态的 Store mock */
function createLoggedInStore() {
  return {
    isLoggedIn: true,
    userInfo: { id: 1, username: '测试用户', email: 'test@example.com', avatar: '' },
    setUserInfo: mockSetUserInfo,
    logout: mockLogout,
    token: 'mock-token'
  } as any
}

/** 创建未登录状态的 Store mock */
function createLoggedOutStore() {
  return {
    isLoggedIn: false,
    userInfo: { id: 0, username: '', email: '', avatar: '' },
    setUserInfo: mockSetUserInfo,
    logout: mockLogout,
    token: ''
  } as any
}

describe('Layout.vue 布局组件测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
    mockRoute.path = '/'
  })

  /**
   * 组件渲染测试
   */
  describe('组件渲染测试', () => {
    /** 测试渲染导航菜单 */
    it('应该渲染导航菜单', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.find('.layout-container').exists()).toBe(true)
      expect(wrapper.find('.header-menu').exists()).toBe(true)
    })

    /** 测试渲染Logo标题 */
    it('应该渲染Logo标题', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.find('.logo').text()).toBe('小麦病害诊断系统')
    })

    /** 测试导航菜单包含首页 */
    it('导航菜单应包含首页', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.text()).toContain('首页')
    })

    /** 测试导航菜单包含诊断 */
    it('导航菜单应包含诊断', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.text()).toContain('诊断')
    })

    /** 测试导航菜单包含记录 */
    it('导航菜单应包含记录', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.text()).toContain('记录')
    })

    /** 测试导航菜单包含知识库 */
    it('导航菜单应包含知识库', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.text()).toContain('知识库')
    })

    /** 测试导航菜单包含用户中心 */
    it('导航菜单应包含用户中心', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.text()).toContain('用户中心')
    })

    /** 测试渲染页脚 */
    it('应该渲染页脚', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.find('.layout-footer').exists()).toBe(true)
      expect(wrapper.find('.layout-footer').text()).toContain('小麦病害诊断系统')
    })
  })

  /**
   * 已登录状态显示测试
   */
  describe('已登录状态显示测试', () => {
    /** 测试已登录显示用户头像 */
    it('已登录应显示用户头像', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.find('.el-avatar').exists()).toBe(true)
    })

    /** 测试已登录显示用户名 */
    it('已登录应显示用户名', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.find('.username').text()).toBe('测试用户')
    })

    /** 测试已登录显示下拉菜单 */
    it('已登录应显示下拉菜单', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.find('.el-dropdown').exists()).toBe(true)
    })
  })

  /**
   * 未登录状态显示测试
   */
  describe('未登录状态显示测试', () => {
    /** 测试未登录显示登录按钮 */
    it('未登录应显示登录按钮', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedOutStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      const loginBtn = wrapper.find('.header-actions').find('button')
      expect(loginBtn.exists()).toBe(true)
      expect(loginBtn.text()).toContain('登录')
    })

    /** 测试未登录不显示用户头像 */
    it('未登录不应显示用户头像', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedOutStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.find('.user-info').exists()).toBe(false)
    })
  })

  /**
   * 退出登录功能测试
   */
  describe('退出登录功能测试', () => {
    /** 测试退出登录命令调用store的logout方法 */
    it('退出登录命令应调用store的logout方法', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      const vm = wrapper.vm as any
      vm.handleCommand('logout')

      expect(mockLogout).toHaveBeenCalled()
    })

    /** 测试退出登录后跳转到登录页 */
    it('退出登录后应跳转到登录页', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      const vm = wrapper.vm as any
      vm.handleCommand('logout')

      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    /** 测试个人中心命令跳转到用户中心 */
    it('个人中心命令应跳转到用户中心', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      const vm = wrapper.vm as any
      vm.handleCommand('profile')

      expect(mockPush).toHaveBeenCalledWith('/user')
    })
  })

  /**
   * 活跃菜单高亮测试
   */
  describe('活跃菜单高亮测试', () => {
    /** 测试活跃菜单根据路由路径计算 */
    it('activeMenu应根据当前路由路径计算', () => {
      mockRoute.path = '/records'
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      const vm = wrapper.vm as any
      expect(vm.activeMenu).toBe('/records')
    })

    /** 测试首页路由活跃菜单 */
    it('首页路由时activeMenu应为/', () => {
      mockRoute.path = '/'
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      const vm = wrapper.vm as any
      expect(vm.activeMenu).toBe('/')
    })

    /** 测试知识库路由活跃菜单 */
    it('知识库路由时activeMenu应为/knowledge', () => {
      mockRoute.path = '/knowledge'
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      const vm = wrapper.vm as any
      expect(vm.activeMenu).toBe('/knowledge')
    })
  })

  /**
   * 布局结构测试
   */
  describe('布局结构测试', () => {
    /** 测试渲染头部区域 */
    it('应该渲染头部区域', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.find('.layout-header').exists()).toBe(true)
    })

    /** 测试渲染主内容区域 */
    it('应该渲染主内容区域', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.find('.layout-main').exists()).toBe(true)
    })

    /** 测试渲染路由视图 */
    it('应该渲染路由视图', () => {
      vi.mocked(useUserStore).mockReturnValue(createLoggedInStore())

      const wrapper = mount(Layout, {
        global: { stubs: { 'router-view': true } }
      })

      expect(wrapper.findComponent({ name: 'RouterView' }).exists()).toBe(true)
    })
  })
})
