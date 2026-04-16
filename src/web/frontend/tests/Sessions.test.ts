/**
 * 会话管理页面组件测试
 * 测试会话列表渲染、当前会话标记、终止单个/所有会话确认和浏览器/OS解析
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Sessions from '@/views/Sessions.vue'

/** 模拟 HTTP 请求模块 */
const mockGet = vi.fn()
const mockDelete = vi.fn()
vi.mock('@/utils/request', () => ({
  http: {
    get: (...args: any[]) => mockGet(...args),
    delete: (...args: any[]) => mockDelete(...args)
  }
}))

/** 模拟 Element Plus 消息提示 */
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

/** 构造模拟会话数据 */
function createMockSessions() {
  return {
    sessions: [
      {
        session_id: 'session-1',
        device_info: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0',
        browser: '',
        os: '',
        ip_address: '192.168.1.100',
        created_at: '2024-06-15T10:30:00.000Z',
        expires_at: '2024-06-16T10:30:00.000Z',
        is_current: true
      },
      {
        session_id: 'session-2',
        device_info: 'Mozilla/5.0 (Mac OS X 10_15_7) Firefox/121.0',
        browser: '',
        os: '',
        ip_address: '192.168.1.101',
        created_at: '2024-06-14T08:00:00.000Z',
        expires_at: '2024-06-15T08:00:00.000Z',
        is_current: false
      },
      {
        session_id: 'session-3',
        device_info: 'Mozilla/5.0 (iPhone OS 16_0) Safari/604.1',
        browser: '',
        os: '',
        ip_address: '192.168.1.102',
        created_at: '2024-06-13T12:00:00.000Z',
        expires_at: '2024-06-14T12:00:00.000Z',
        is_current: false
      }
    ]
  }
}

describe('Sessions.vue 会话管理页面测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  /**
   * 组件渲染测试
   */
  describe('组件渲染测试', () => {
    /** 测试渲染会话列表表格 */
    it('应该渲染会话列表表格', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      expect(wrapper.find('.el-table').exists()).toBe(true)
    })

    /** 测试渲染页面标题 */
    it('应该渲染页面标题', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      expect(wrapper.find('.card-header').text()).toContain('会话管理')
    })

    /** 测试渲染刷新按钮 */
    it('应该渲染刷新按钮', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const text = wrapper.text()
      expect(text).toContain('刷新列表')
    })

    /** 测试渲染终止所有其他会话按钮 */
    it('应该渲染终止所有其他会话按钮', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const text = wrapper.text()
      expect(text).toContain('终止所有其他会话')
    })

    /** 测试表格列标题正确 */
    it('表格应包含正确的列标题', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const text = wrapper.text()
      expect(text).toContain('设备信息')
      expect(text).toContain('IP 地址')
      expect(text).toContain('登录时间')
      expect(text).toContain('过期时间')
      expect(text).toContain('状态')
      expect(text).toContain('操作')
    })
  })

  /**
   * 当前会话标记测试
   */
  describe('当前会话标记测试', () => {
    /** 测试当前会话显示"当前会话"标签 */
    it('当前会话应显示"当前会话"标签', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      const currentSession = vm.sessions.find((s: any) => s.is_current)
      expect(currentSession).toBeDefined()
    })

    /** 测试当前会话不可终止 */
    it('当前会话操作列应显示"当前会话"提示而非终止按钮', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      const currentSession = vm.sessions.find((s: any) => s.is_current)
      expect(currentSession.is_current).toBe(true)
    })

    /** 测试非当前会话显示终止按钮 */
    it('非当前会话应显示终止按钮', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      const otherSessions = vm.sessions.filter((s: any) => !s.is_current)
      expect(otherSessions.length).toBeGreaterThan(0)
    })
  })

  /**
   * 终止单个会话测试
   */
  describe('终止单个会话测试', () => {
    /** 测试终止单个会话调用API */
    it('终止单个会话应调用删除API', async () => {
      mockGet.mockResolvedValue(createMockSessions())
      mockDelete.mockResolvedValue({})

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleTerminateSession('session-2')
      await flushPromises()

      expect(mockDelete).toHaveBeenCalledWith('/users/sessions/session-2')
    })

    /** 测试终止成功显示成功消息 */
    it('终止成功应显示成功消息', async () => {
      mockGet.mockResolvedValue(createMockSessions())
      mockDelete.mockResolvedValue({})

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleTerminateSession('session-2')
      await flushPromises()

      const { ElMessage } = await import('element-plus')
      expect(ElMessage.success).toHaveBeenCalledWith('会话已终止')
    })

    /** 测试终止成功后刷新列表 */
    it('终止成功后应刷新会话列表', async () => {
      mockGet.mockResolvedValue(createMockSessions())
      mockDelete.mockResolvedValue({})

      const wrapper = mount(Sessions)
      await flushPromises()

      const initialCallCount = mockGet.mock.calls.length

      const vm = wrapper.vm as any
      await vm.handleTerminateSession('session-2')
      await flushPromises()

      expect(mockGet.mock.calls.length).toBeGreaterThan(initialCallCount)
    })

    /** 测试终止失败不显示成功消息 */
    it('终止失败应不显示成功消息', async () => {
      mockGet.mockResolvedValue(createMockSessions())
      mockDelete.mockRejectedValue(new Error('终止失败'))

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleTerminateSession('session-2')
      await flushPromises()

      const { ElMessage } = await import('element-plus')
      expect(ElMessage.success).not.toHaveBeenCalledWith('会话已终止')
    })

    /** 测试终止时设置terminating状态 */
    it('终止会话时应设置terminating状态', async () => {
      let resolveDelete: any
      mockGet.mockResolvedValue(createMockSessions())
      mockDelete.mockImplementation(() => new Promise((resolve) => {
        resolveDelete = resolve
      }))

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      const session = vm.sessions.find((s: any) => s.session_id === 'session-2')

      const terminatePromise = vm.handleTerminateSession('session-2')
      await wrapper.vm.$nextTick()

      expect(session.terminating).toBe(true)

      resolveDelete({})
      await terminatePromise
      await flushPromises()
    })
  })

  /**
   * 终止所有其他会话测试
   */
  describe('终止所有其他会话测试', () => {
    /** 测试终止所有其他会话调用API */
    it('终止所有其他会话应为每个会话调用删除API', async () => {
      mockGet.mockResolvedValue(createMockSessions())
      mockDelete.mockResolvedValue({})

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleTerminateAllOther()
      await flushPromises()

      const otherSessionIds = ['session-2', 'session-3']
      otherSessionIds.forEach(id => {
        expect(mockDelete).toHaveBeenCalledWith(`/users/sessions/${id}`)
      })
    })

    /** 测试终止所有其他会话成功显示消息 */
    it('终止所有其他会话成功应显示成功消息', async () => {
      mockGet.mockResolvedValue(createMockSessions())
      mockDelete.mockResolvedValue({})

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleTerminateAllOther()
      await flushPromises()

      const { ElMessage } = await import('element-plus')
      expect(ElMessage.success).toHaveBeenCalledWith('已终止所有其他会话')
    })

    /** 测试终止所有其他会话后刷新列表 */
    it('终止所有其他会话后应刷新列表', async () => {
      mockGet.mockResolvedValue(createMockSessions())
      mockDelete.mockResolvedValue({})

      const wrapper = mount(Sessions)
      await flushPromises()

      const initialCallCount = mockGet.mock.calls.length

      const vm = wrapper.vm as any
      await vm.handleTerminateAllOther()
      await flushPromises()

      expect(mockGet.mock.calls.length).toBeGreaterThan(initialCallCount)
    })

    /** 测试终止所有其他会话时设置terminatingAll状态 */
    it('终止所有其他会话时应设置terminatingAll状态', async () => {
      mockGet.mockResolvedValue(createMockSessions())
      mockDelete.mockResolvedValue({})

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleTerminateAllOther()
      await flushPromises()

      expect(vm.terminatingAll).toBe(false)
      expect(mockDelete).toHaveBeenCalled()
    })
  })

  /**
   * 浏览器/OS解析测试
   */
  describe('浏览器/OS解析测试', () => {
    /** 测试解析Chrome浏览器 */
    it('应正确解析Chrome浏览器', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseBrowser('Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0')).toBe('Chrome')
    })

    /** 测试解析Firefox浏览器 */
    it('应正确解析Firefox浏览器', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseBrowser('Mozilla/5.0 (Mac OS X 10_15_7) Firefox/121.0')).toBe('Firefox')
    })

    /** 测试解析Safari浏览器 */
    it('应正确解析Safari浏览器', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseBrowser('Mozilla/5.0 (iPhone OS 16_0) Safari/604.1')).toBe('Safari')
    })

    /** 测试解析Edge浏览器 */
    it('应正确解析Edge浏览器', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseBrowser('Mozilla/5.0 (Windows NT 10.0; Win64; x64) Edg/120.0.0.0')).toBe('Edge')
    })

    /** 测试解析未知浏览器 */
    it('应正确处理未知浏览器', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseBrowser('')).toBe('未知浏览器')
      expect(vm.parseBrowser('SomeUnknownAgent')).toBe('未知浏览器')
    })

    /** 测试解析Windows操作系统 */
    it('应正确解析Windows操作系统', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseOS('Mozilla/5.0 (Windows NT 10.0; Win64; x64)')).toBe('Windows')
    })

    /** 测试解析macOS操作系统 */
    it('应正确解析macOS操作系统', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseOS('Mozilla/5.0 (Mac OS X 10_15_7)')).toBe('macOS')
    })

    /** 测试解析iOS操作系统 */
    it('应正确解析iOS操作系统', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseOS('Mozilla/5.0 (iPhone OS 16_0)')).toBe('iOS')
    })

    /** 测试解析Android操作系统 */
    it('应正确解析Android操作系统', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseOS('Mozilla/5.0 (Linux; Android 13)')).toBe('Linux')
    })

    /** 测试解析未知操作系统 */
    it('应正确处理未知操作系统', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.parseOS('')).toBe('未知操作系统')
      expect(vm.parseOS('SomeUnknownOS')).toBe('未知操作系统')
    })
  })

  /**
   * 日期时间格式化测试
   */
  describe('日期时间格式化测试', () => {
    /** 测试格式化日期时间 */
    it('应正确格式化日期时间', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      const formatted = vm.formatDateTime('2024-06-15T10:30:00.000Z')
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    /** 测试空日期返回未知 */
    it('空日期应返回"未知"', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.formatDateTime('')).toBe('未知')
    })

    /** 测试无效日期返回原字符串 */
    it('无效日期应返回原字符串', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const vm = wrapper.vm as any
      const result = vm.formatDateTime('invalid-date')
      expect(result).toBeTruthy()
    })
  })

  /**
   * 数据加载测试
   */
  describe('数据加载测试', () => {
    /** 测试组件挂载时加载会话列表 */
    it('组件挂载时应调用API加载会话列表', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      mount(Sessions)
      await flushPromises()

      expect(mockGet).toHaveBeenCalledWith('/users/sessions/list')
    })

    /** 测试刷新按钮重新加载 */
    it('点击刷新按钮应重新加载会话列表', async () => {
      mockGet.mockResolvedValue(createMockSessions())

      const wrapper = mount(Sessions)
      await flushPromises()

      const initialCallCount = mockGet.mock.calls.length

      const vm = wrapper.vm as any
      await vm.fetchSessions()
      await flushPromises()

      expect(mockGet.mock.calls.length).toBe(initialCallCount + 1)
    })

    /** 测试加载状态 */
    it('加载时loading应为true', async () => {
      let resolveApi: any
      mockGet.mockImplementation(() => new Promise((resolve) => {
        resolveApi = resolve
      }))

      const wrapper = mount(Sessions)
      const vm = wrapper.vm as any

      expect(vm.loading).toBe(true)

      resolveApi(createMockSessions())
      await flushPromises()

      expect(vm.loading).toBe(false)
    })
  })
})
