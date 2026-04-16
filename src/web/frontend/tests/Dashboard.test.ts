/**
 * 首页仪表盘组件测试
 * 测试欢迎卡片、统计卡片、图表区域渲染，统计数据加载和计算逻辑
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Dashboard from '@/views/Dashboard.vue'

/** 模拟诊断记录API */
const mockGetDiagnosisRecords = vi.fn()
vi.mock('@/api/diagnosis', () => ({
  getDiagnosisRecords: (...args: any[]) => mockGetDiagnosisRecords(...args)
}))

/** 模拟知识库统计API */
const mockGetDiseaseStats = vi.fn()
vi.mock('@/api/knowledge', () => ({
  getDiseaseStats: (...args: any[]) => mockGetDiseaseStats(...args)
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

/** 模拟 DiseaseChart 子组件 */
vi.mock('@/components/dashboard/DiseaseChart.vue', () => ({
  default: {
    name: 'DiseaseChart',
    template: '<div class="disease-chart-stub"><slot /></div>',
    props: ['distributionData', 'statsData', 'trendData']
  }
}))

/** 构造模拟诊断记录数据 */
function createMockRecords() {
  const today = new Date().toISOString()
  const yesterday = new Date(Date.now() - 86400000).toISOString()
  return [
    { id: 1, diagnosis_result: '小麦锈病', confidence: 0.95, created_at: today, symptoms: '叶片出现锈斑' },
    { id: 2, diagnosis_result: '小麦白粉病', confidence: 0.88, created_at: today, symptoms: '叶片白粉覆盖' },
    { id: 3, diagnosis_result: '小麦锈病', confidence: 0.92, created_at: yesterday, symptoms: '茎秆锈斑' },
    { id: 4, diagnosis_result: '小麦赤霉病', confidence: 0.78, created_at: yesterday, symptoms: '穗部粉红色霉层' },
    { id: 5, diagnosis_result: '小麦白粉病', confidence: 0.85, created_at: yesterday, symptoms: '叶鞘白粉' }
  ]
}

describe('Dashboard.vue 首页仪表盘测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  /**
   * 组件渲染测试
   */
  describe('组件渲染测试', () => {
    /** 测试渲染欢迎卡片 */
    it('应该渲染欢迎卡片', async () => {
      mockGetDiagnosisRecords.mockResolvedValue({
        records: [],
        total: 0
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      expect(wrapper.find('.welcome-card').exists()).toBe(true)
      expect(wrapper.find('.welcome-card h1').text()).toContain('欢迎使用基于多模态融合的小麦病害诊断系统')
    })

    /** 测试渲染欢迎卡片副标题 */
    it('应该渲染欢迎卡片副标题', async () => {
      mockGetDiagnosisRecords.mockResolvedValue({
        records: [],
        total: 0
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      expect(wrapper.find('.welcome-card p').text()).toContain('融合视觉感知、语义理解和知识推理的智能农业诊断平台')
    })

    /** 测试渲染4个统计卡片 */
    it('应该渲染4个统计卡片', async () => {
      mockGetDiagnosisRecords.mockResolvedValue({
        records: [],
        total: 0
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const statCards = wrapper.findAll('.stat-card')
      expect(statCards.length).toBe(4)
    })

    /** 测试统计卡片标题正确 */
    it('统计卡片应包含正确的标题', async () => {
      mockGetDiagnosisRecords.mockResolvedValue({
        records: [],
        total: 0
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const text = wrapper.text()
      expect(text).toContain('今日诊断次数')
      expect(text).toContain('总诊断次数')
      expect(text).toContain('平均准确率')
      expect(text).toContain('活跃用户数')
    })

    /** 测试渲染图表区域 */
    it('应该渲染图表区域组件', async () => {
      mockGetDiagnosisRecords.mockResolvedValue({
        records: [],
        total: 0
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      expect(wrapper.findComponent({ name: 'DiseaseChart' }).exists()).toBe(true)
    })
  })

  /**
   * 统计数据加载测试
   */
  describe('统计数据加载测试', () => {
    /** 测试统计数据从API加载 */
    it('组件挂载时应调用API加载数据', async () => {
      mockGetDiagnosisRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      expect(mockGetDiagnosisRecords).toHaveBeenCalledWith(0, 100)
    })

    /** 测试加载状态显示 */
    it('加载数据时isLoading应为true', async () => {
      let resolveApi: any
      mockGetDiagnosisRecords.mockImplementation(() => new Promise((resolve) => {
        resolveApi = resolve
      }))

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })

      const vm = wrapper.vm as any
      expect(vm.isLoading).toBe(true)

      resolveApi({ records: [], total: 0 })
      await flushPromises()

      expect(vm.isLoading).toBe(false)
    })

    /** 测试加载完成后isLoading为false */
    it('数据加载完成后isLoading应为false', async () => {
      mockGetDiagnosisRecords.mockResolvedValue({
        records: createMockRecords(),
        total: 5
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.isLoading).toBe(false)
    })

    /** 测试API加载失败显示错误消息 */
    it('API加载失败应显示错误消息', async () => {
      mockGetDiagnosisRecords.mockRejectedValue(new Error('网络错误'))

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const { ElMessage } = await import('element-plus')
      expect(ElMessage.error).toHaveBeenCalled()
    })
  })

  /**
   * 统计计算逻辑测试
   */
  describe('统计计算逻辑测试', () => {
    /** 测试今日诊断次数计算 */
    it('应正确计算今日诊断次数', async () => {
      const records = createMockRecords()
      mockGetDiagnosisRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const vm = wrapper.vm as any
      const todayRecords = records.filter(r => {
        const today = new Date().toDateString()
        return new Date(r.created_at).toDateString() === today
      })
      expect(vm.stats.todayDiagnoses).toBe(todayRecords.length)
    })

    /** 测试总诊断次数计算 */
    it('应正确计算总诊断次数', async () => {
      const records = createMockRecords()
      mockGetDiagnosisRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.stats.totalDiagnoses).toBe(records.length)
    })

    /** 测试平均准确率计算 */
    it('应正确计算平均准确率', async () => {
      const records = createMockRecords()
      mockGetDiagnosisRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const vm = wrapper.vm as any
      const avgConfidence = records.reduce((sum, r) => sum + r.confidence, 0) / records.length
      const expectedAccuracy = parseFloat((avgConfidence * 100).toFixed(1))
      expect(vm.stats.accuracy).toBe(expectedAccuracy)
    })

    /** 测试无记录时准确率为0 */
    it('无记录时准确率应为0', async () => {
      mockGetDiagnosisRecords.mockResolvedValue({
        records: [],
        total: 0
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.stats.accuracy).toBe(0)
    })

    /** 测试用户数计算 */
    it('应正确计算活跃用户数', async () => {
      const records = createMockRecords()
      mockGetDiagnosisRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.stats.userCount).toBe(Math.floor(records.length / 3))
    })

    /** 测试病害分布数据生成 */
    it('应正确生成病害分布数据', async () => {
      const records = createMockRecords()
      mockGetDiagnosisRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.distributionData.length).toBeGreaterThan(0)
      const rustEntry = vm.distributionData.find((d: any) => d.name === '小麦锈病')
      expect(rustEntry).toBeDefined()
    })

    /** 测试趋势数据生成 */
    it('应正确生成趋势数据', async () => {
      const records = createMockRecords()
      mockGetDiagnosisRecords.mockResolvedValue({
        records,
        total: records.length
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.trendData.length).toBeGreaterThan(0)
    })
  })

  /**
   * 时间范围变化测试
   */
  describe('时间范围变化测试', () => {
    /** 测试时间范围变化触发数据重新加载 */
    it('时间范围变化应重新加载数据', async () => {
      mockGetDiagnosisRecords.mockResolvedValue({
        records: [],
        total: 0
      })

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })
      await flushPromises()

      const vm = wrapper.vm as any
      const initialCallCount = mockGetDiagnosisRecords.mock.calls.length

      await vm.handleTimeRangeChange('month')
      await flushPromises()

      expect(mockGetDiagnosisRecords.mock.calls.length).toBe(initialCallCount + 1)
    })
  })

  /**
   * 初始状态测试
   */
  describe('初始状态测试', () => {
    /** 测试统计数据初始值 */
    it('统计数据初始值应为0', () => {
      mockGetDiagnosisRecords.mockImplementation(() => new Promise(() => {}))

      const wrapper = mount(Dashboard, {
        global: {
          stubs: {
            DiseaseChart: true
          }
        }
      })

      const vm = wrapper.vm as any
      expect(vm.stats.todayDiagnoses).toBe(0)
      expect(vm.stats.totalDiagnoses).toBe(0)
      expect(vm.stats.accuracy).toBe(0)
      expect(vm.stats.userCount).toBe(0)
    })
  })
})
