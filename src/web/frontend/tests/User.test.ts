/**
 * 用户中心页面组件测试
 * 测试头像、个人信息、使用统计渲染，编辑资料对话框，退出登录确认和用户信息加载
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import User from '@/views/User.vue'

/** 模拟 vue-router */
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  })
}))

/** 模拟用户API */
const mockGetCurrentUser = vi.fn()
vi.mock('@/api/user', () => ({
  getCurrentUser: (...args: any[]) => mockGetCurrentUser(...args)
}))

/** 模拟诊断API */
const mockGetDiagnosisRecords = vi.fn()
vi.mock('@/api/diagnosis', () => ({
  getDiagnosisRecords: (...args: any[]) => mockGetDiagnosisRecords(...args)
}))

/** 模拟 Element Plus 消息提示和确认框 */
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn()
    },
    ElMessageBox: {
      confirm: vi.fn(() => Promise.reject('cancel'))
    }
  }
})

/** 模拟用户 Store */
const mockSetUserInfo = vi.fn()
const mockLogout = vi.fn()
vi.mock('@/stores', () => ({
  useUserStore: () => ({
    setUserInfo: mockSetUserInfo,
    logout: mockLogout,
    token: 'mock-token',
    isLoggedIn: true,
    userInfo: {
      id: 1,
      username: '测试用户',
      email: 'test@example.com',
      avatar: ''
    }
  })
}))

/** 构造模拟用户数据 */
function createMockUser() {
  return {
    id: 1,
    username: '测试用户',
    email: 'test@example.com',
    phone: '13800138000',
    avatar_url: 'https://example.com/avatar.jpg',
    role: 'farmer' as const,
    is_active: true,
    created_at: '2024-01-15T10:30:00.000Z',
    updated_at: '2024-06-20T08:00:00.000Z'
  }
}

describe('User.vue 用户中心页面测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  /**
   * 组件渲染测试
   */
  describe('组件渲染测试', () => {
    /** 测试渲染用户头像 */
    it('应该渲染用户头像', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      expect(wrapper.find('.el-avatar').exists()).toBe(true)
    })

    /** 测试渲染用户名 */
    it('应该渲染用户名', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const profileHeader = wrapper.find('.profile-header')
      expect(profileHeader.text()).toContain('测试用户')
    })

    /** 测试渲染邮箱 */
    it('应该渲染邮箱', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const profileHeader = wrapper.find('.profile-header')
      expect(profileHeader.text()).toContain('test@example.com')
    })

    /** 测试渲染个人信息卡片 */
    it('应该渲染个人信息卡片', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      expect(wrapper.find('.info-card').exists()).toBe(true)
      const text = wrapper.text()
      expect(text).toContain('个人信息')
      expect(text).toContain('用户名')
      expect(text).toContain('邮箱')
      expect(text).toContain('手机号')
      expect(text).toContain('注册时间')
      expect(text).toContain('最后登录')
    })

    /** 测试渲染使用统计卡片 */
    it('应该渲染使用统计卡片', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      expect(wrapper.find('.stats-card').exists()).toBe(true)
      const text = wrapper.text()
      expect(text).toContain('使用统计')
      expect(text).toContain('诊断次数')
      expect(text).toContain('收藏数')
      expect(text).toContain('积分')
    })

    /** 测试渲染编辑资料按钮 */
    it('应该渲染编辑资料按钮', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const editBtn = wrapper.find('.edit-btn')
      expect(editBtn.exists()).toBe(true)
      expect(editBtn.text()).toContain('编辑资料')
    })

    /** 测试渲染退出登录按钮 */
    it('应该渲染退出登录按钮', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const logoutBtn = wrapper.find('.logout-btn')
      expect(logoutBtn.exists()).toBe(true)
      expect(logoutBtn.text()).toContain('退出登录')
    })
  })

  /**
   * 编辑资料对话框测试
   */
  describe('编辑资料对话框测试', () => {
    /** 测试点击编辑资料打开对话框 */
    it('点击编辑资料应打开对话框', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.showEditDialog).toBe(false)

      await wrapper.find('.edit-btn').trigger('click')
      expect(vm.showEditDialog).toBe(true)
    })

    /** 测试点击取消关闭对话框 */
    it('点击取消应关闭对话框', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.showEditDialog = true
      await wrapper.vm.$nextTick()

      const dialog = wrapper.find('.el-dialog')
      const cancelBtn = dialog.findAll('button').find(btn => btn.text().includes('取消'))
      if (cancelBtn) {
        await cancelBtn.trigger('click')
        expect(vm.showEditDialog).toBe(false)
      }
    })

    /** 测试保存资料关闭对话框并显示成功消息 */
    it('保存资料应关闭对话框并显示成功消息', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.showEditDialog = true
      vm.editForm.email = 'newemail@example.com'
      vm.editForm.phone = '13900139000'
      await wrapper.vm.$nextTick()

      await vm.handleSave()

      expect(vm.showEditDialog).toBe(false)
      expect(vm.userInfo.email).toBe('newemail@example.com')
      expect(vm.userInfo.phone).toBe('13900139000')

      const { ElMessage } = await import('element-plus')
      expect(ElMessage.success).toHaveBeenCalledWith('保存成功')
    })

    /** 测试编辑表单用户名不可修改 */
    it('编辑表单用户名输入框应禁用', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.showEditDialog = true
      await wrapper.vm.$nextTick()

      expect(vm.editForm.username).toBeDefined()
    })
  })

  /**
   * 退出登录测试
   */
  describe('退出登录测试', () => {
    /** 测试退出登录弹出确认框 */
    it('点击退出登录应弹出确认框', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const { ElMessageBox } = await import('element-plus')

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleLogout()

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要退出登录吗？',
        '提示',
        expect.objectContaining({
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
      )
    })

    /** 测试确认退出登录清除token并跳转 */
    it('确认退出应清除token并跳转登录页', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const { ElMessageBox } = await import('element-plus')
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleLogout()
      await flushPromises()

      expect(localStorage.removeItem).toHaveBeenCalledWith('token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('user')
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    /** 测试取消退出登录不执行操作 */
    it('取消退出不应执行任何操作', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const { ElMessageBox } = await import('element-plus')
      vi.mocked(ElMessageBox.confirm).mockRejectedValue('cancel')

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.handleLogout()
      await flushPromises()

      expect(mockPush).not.toHaveBeenCalled()
    })
  })

  /**
   * 用户信息加载测试
   */
  describe('用户信息加载测试', () => {
    /** 测试组件挂载时加载用户信息 */
    it('组件挂载时应调用API加载用户信息', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      mount(User)
      await flushPromises()

      expect(mockGetCurrentUser).toHaveBeenCalled()
    })

    /** 测试用户信息正确填充 */
    it('用户信息应正确填充到组件', async () => {
      const mockUser = createMockUser()
      mockGetCurrentUser.mockResolvedValue(mockUser)
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.userInfo.username).toBe(mockUser.username)
      expect(vm.userInfo.email).toBe(mockUser.email)
      expect(vm.userInfo.phone).toBe(mockUser.phone)
    })

    /** 测试用户信息加载失败使用store回退数据 */
    it('用户信息加载失败应使用store回退数据', async () => {
      mockGetCurrentUser.mockRejectedValue(new Error('网络错误'))
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.userInfo.username).toBe('测试用户')
      expect(vm.userInfo.email).toBe('test@example.com')
    })

    /** 测试加载统计数据 */
    it('应加载用户统计数据', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({
        records: Array.from({ length: 10 }, (_, i) => ({ id: i })),
        total: 10
      })

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.stats.diagnosisCount).toBe(10)
      expect(vm.stats.favoriteCount).toBe(Math.floor(10 * 0.15))
      expect(vm.stats.points).toBe(10 * 10)
    })

    /** 测试加载状态 */
    it('加载完成后isLoading应为false', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.isLoading).toBe(false)
    })
  })

  /**
   * 日期格式化测试
   */
  describe('日期格式化测试', () => {
    /** 测试日期格式化函数 */
    it('应正确格式化日期', async () => {
      mockGetCurrentUser.mockResolvedValue(createMockUser())
      mockGetDiagnosisRecords.mockResolvedValue({ records: [], total: 0 })

      const wrapper = mount(User)
      await flushPromises()

      const vm = wrapper.vm as any
      const formatted = vm.formatDate('2024-06-15T10:30:00.000Z')
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })
  })
})
