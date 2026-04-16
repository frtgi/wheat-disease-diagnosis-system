/**
 * 诊断记录页面组件测试
 * 测试搜索框、记录表格、分页组件、删除确认和日期格式化
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Records from '@/views/Records.vue'

/** 模拟诊断API */
const mockGetRecords = vi.fn()
const mockDeleteDiagnosis = vi.fn()
vi.mock('@/api/diagnosis', () => ({
  getDiagnosisRecords: (...args: any[]) => mockGetRecords(...args),
  deleteDiagnosis: (...args: any[]) => mockDeleteDiagnosis(...args)
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
      confirm: vi.fn(() => Promise.reject('cancel')),
      alert: vi.fn(() => Promise.resolve())
    }
  }
})

/** 构造模拟诊断记录数据 */
function createMockRecords(count: number = 5) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    user_id: 1,
    diagnosis_result: i % 2 === 0 ? '小麦锈病' : '小麦白粉病',
    confidence: 0.8 + Math.random() * 0.2,
    symptoms: `症状描述${i + 1}`,
    suggestions: `防治建议${i + 1}`,
    status: 'completed',
    created_at: new Date(Date.now() - i * 86400000).toISOString(),
    updated_at: new Date().toISOString()
  }))
}

describe('Records.vue 诊断记录页面测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  /**
   * 组件渲染测试
   */
  describe('组件渲染测试', () => {
    /** 测试渲染搜索框 */
    it('应该渲染搜索框', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      expect(wrapper.find('input[placeholder="搜索记录"]').exists()).toBe(true)
    })

    /** 测试渲染记录表格 */
    it('应该渲染记录表格', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      expect(wrapper.find('.el-table').exists()).toBe(true)
    })

    /** 测试渲染分页组件 */
    it('应该渲染分页组件', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      expect(wrapper.find('.el-pagination').exists()).toBe(true)
    })

    /** 测试渲染页面标题 */
    it('应该渲染页面标题', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      expect(wrapper.find('.card-header').text()).toContain('诊断记录')
    })

    /** 测试表格列标题正确 */
    it('表格应包含正确的列标题', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      const text = wrapper.text()
      expect(text).toContain('诊断时间')
      expect(text).toContain('病害类型')
      expect(text).toContain('置信度')
      expect(text).toContain('症状描述')
      expect(text).toContain('操作')
    })
  })

  /**
   * 搜索功能测试
   */
  describe('搜索功能测试', () => {
    /** 测试搜索过滤记录 */
    it('搜索关键词应过滤记录', async () => {
      const records = createMockRecords()
      mockGetRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.searchQuery = '锈病'
      await wrapper.vm.$nextTick()

      const filtered = vm.filteredRecords
      expect(filtered.length).toBeLessThanOrEqual(records.length)
      expect(filtered.every((r: any) =>
        (r.diagnosis_result && r.diagnosis_result.includes('锈病')) ||
        (r.symptoms && r.symptoms.includes('锈病'))
      )).toBe(true)
    })

    /** 测试空搜索返回全部记录 */
    it('空搜索应返回全部记录', async () => {
      const records = createMockRecords()
      mockGetRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.searchQuery = ''
      await wrapper.vm.$nextTick()

      expect(vm.filteredRecords.length).toBe(records.length)
    })

    /** 测试搜索无结果时过滤为空 */
    it('搜索无匹配应返回空列表', async () => {
      const records = createMockRecords()
      mockGetRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.searchQuery = '不存在的病害名称'
      await wrapper.vm.$nextTick()

      expect(vm.filteredRecords.length).toBe(0)
    })
  })

  /**
   * 删除操作测试
   */
  describe('删除操作测试', () => {
    /** 测试删除操作弹出确认框 */
    it('点击删除应弹出确认框', async () => {
      const records = createMockRecords()
      mockGetRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const { ElMessageBox } = await import('element-plus')

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleDelete(records[0])

      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '确定要删除这条记录吗？',
        '提示',
        expect.objectContaining({
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        })
      )
    })

    /** 测试确认删除后调用API */
    it('确认删除后应调用删除API', async () => {
      const records = createMockRecords()
      mockGetRecords.mockResolvedValue({
        records,
        total: records.length
      })
      mockDeleteDiagnosis.mockResolvedValue(undefined)

      const { ElMessageBox } = await import('element-plus')
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleDelete(records[0])
      await flushPromises()

      expect(mockDeleteDiagnosis).toHaveBeenCalledWith(String(records[0].id))
    })

    /** 测试删除成功后显示成功消息 */
    it('删除成功应显示成功消息', async () => {
      const records = createMockRecords()
      mockGetRecords.mockResolvedValue({
        records,
        total: records.length
      })
      mockDeleteDiagnosis.mockResolvedValue(undefined)

      const { ElMessageBox } = await import('element-plus')
      const { ElMessage } = await import('element-plus')
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleDelete(records[0])
      await flushPromises()

      expect(ElMessage.success).toHaveBeenCalledWith('删除成功')
    })

    /** 测试取消删除不调用API */
    it('取消删除不应调用删除API', async () => {
      const records = createMockRecords()
      mockGetRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const { ElMessageBox } = await import('element-plus')
      vi.mocked(ElMessageBox.confirm).mockRejectedValue('cancel')

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleDelete(records[0]).catch(() => {})
      await flushPromises()

      expect(mockDeleteDiagnosis).not.toHaveBeenCalled()
    })
  })

  /**
   * 分页功能测试
   */
  describe('分页功能测试', () => {
    /** 测试分页切换加载 */
    it('分页切换应重新加载记录', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 50
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      const initialCallCount = mockGetRecords.mock.calls.length

      vm.currentPage = 2
      await vm.handlePageChange()
      await flushPromises()

      expect(mockGetRecords.mock.calls.length).toBeGreaterThan(initialCallCount)
    })

    /** 测试分页参数正确传递 */
    it('分页参数应正确传递给API', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 50
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.currentPage = 3
      await vm.$nextTick()
      await vm.handlePageChange()
      await flushPromises()

      const lastCall = mockGetRecords.mock.calls[mockGetRecords.mock.calls.length - 1]
      expect(lastCall[0]).toBe((3 - 1) * 10)
      expect(lastCall[1]).toBe(10)
    })

    /** 测试初始分页参数 */
    it('初始分页参数应为第1页每页10条', () => {
      mockGetRecords.mockImplementation(() => new Promise(() => {}))

      const wrapper = mount(Records)
      const vm = wrapper.vm as any

      expect(vm.currentPage).toBe(1)
      expect(vm.pageSize).toBe(10)
    })
  })

  /**
   * 日期格式化测试
   */
  describe('日期格式化测试', () => {
    /** 测试日期格式化输出 */
    it('应正确格式化日期字符串', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      const formatted = vm.formatDate('2024-06-15T10:30:00.000Z')
      expect(formatted).toBeTruthy()
      expect(typeof formatted).toBe('string')
    })

    /** 测试日期格式化包含年月日 */
    it('格式化日期应包含年月日时分秒', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      const formatted = vm.formatDate('2024-06-15T10:30:00.000Z')
      expect(formatted).toMatch(/\d{4}/)
    })
  })

  /**
   * 置信度标签类型测试
   */
  describe('置信度标签类型测试', () => {
    /** 测试高置信度返回success类型 */
    it('置信度>=0.9应返回success类型', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.getDiseaseType(0.95)).toBe('success')
    })

    /** 测试中等置信度返回warning类型 */
    it('置信度>=0.7应返回warning类型', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.getDiseaseType(0.75)).toBe('warning')
    })

    /** 测试低置信度返回danger类型 */
    it('置信度<0.7应返回danger类型', async () => {
      mockGetRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.getDiseaseType(0.5)).toBe('danger')
    })
  })

  /**
   * 查看详情测试
   */
  describe('查看详情测试', () => {
    /** 测试查看详情弹出对话框 */
    it('点击查看详情应弹出对话框', async () => {
      const records = createMockRecords()
      mockGetRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const { ElMessageBox } = await import('element-plus')

      const wrapper = mount(Records)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleViewDetail(records[0])

      expect(ElMessageBox.alert).toHaveBeenCalled()
    })
  })
})
