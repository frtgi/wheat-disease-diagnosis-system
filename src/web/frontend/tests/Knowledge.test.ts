/**
 * 知识库页面组件测试
 * 测试搜索栏、类别筛选、病害卡片列表、搜索防抖、空状态和卡片交互
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Knowledge from '@/views/Knowledge.vue'

/** 模拟知识库API */
const mockGetDiseaseKnowledge = vi.fn()
const mockSearchDiseaseKnowledge = vi.fn()
const mockGetDiseaseDetail = vi.fn()
vi.mock('@/api/knowledge', () => ({
  getDiseaseKnowledge: (...args: any[]) => mockGetDiseaseKnowledge(...args),
  searchDiseaseKnowledge: (...args: any[]) => mockSearchDiseaseKnowledge(...args),
  getDiseaseDetail: (...args: any[]) => mockGetDiseaseDetail(...args)
}))

/** 模拟 Element Plus 消息提示 */
vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn(),
      info: vi.fn()
    }
  }
})

/** 模拟 DiseaseCard 子组件 */
vi.mock('@/components/knowledge/DiseaseCard.vue', () => ({
  default: {
    name: 'DiseaseCard',
    template: `
      <div class="disease-card-stub" @click="$emit('click', id)" >
        <span class="disease-name">{{ diseaseName }}</span>
        <button class="view-detail-btn" @click.stop="$emit('viewDetail', id)">查看详情</button>
        <button class="prevention-btn" @click.stop="$emit('prevention', id)">防治方法</button>
      </div>
    `,
    props: ['id', 'diseaseName', 'symptomsBrief', 'symptoms', 'category', 'severity', 'highSeason', 'suitableTemp'],
    emits: ['click', 'viewDetail', 'prevention']
  }
}))

/** 构造模拟病害知识数据 */
function createMockDiseases(count: number = 6) {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    name: i % 3 === 0 ? '小麦锈病' : i % 3 === 1 ? '小麦白粉病' : '小麦赤霉病',
    category: i % 3 === 0 ? '真菌性病害' : i % 3 === 1 ? '细菌性病害' : '病毒性病害',
    symptoms: `症状描述${i + 1}。叶片出现异常。茎秆变色。`,
    causes: '高温高湿',
    treatments: '喷洒杀菌剂',
    prevention: '加强田间管理',
    severity: i % 3,
    created_at: '2024-01-01',
    updated_at: '2024-01-01'
  }))
}

describe('Knowledge.vue 知识库页面测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.useFakeTimers()
    localStorage.clear()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  /**
   * 组件渲染测试
   */
  describe('组件渲染测试', () => {
    /** 测试渲染搜索栏 */
    it('应该渲染搜索栏', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())

      const wrapper = mount(Knowledge)
      await flushPromises()

      expect(wrapper.find('.search-card').exists()).toBe(true)
      expect(wrapper.find('input[placeholder="搜索病害名称或症状"]').exists()).toBe(true)
    })

    /** 测试渲染页面标题 */
    it('应该渲染页面标题', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())

      const wrapper = mount(Knowledge)
      await flushPromises()

      expect(wrapper.find('.search-header h2').text()).toBe('病害知识库')
    })

    /** 测试渲染类别筛选下拉框 */
    it('应该渲染类别筛选下拉框', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())

      const wrapper = mount(Knowledge)
      await flushPromises()

      expect(wrapper.find('.category-select').exists()).toBe(true)
    })

    /** 测试渲染病害卡片列表 */
    it('应该渲染病害卡片列表', async () => {
      const diseases = createMockDiseases()
      mockGetDiseaseKnowledge.mockResolvedValue(diseases)

      const wrapper = mount(Knowledge)
      await flushPromises()

      const cards = wrapper.findAll('.disease-card-stub')
      expect(cards.length).toBe(diseases.length)
    })

    /** 测试类别选项正确 */
    it('类别选项应包含正确的类别', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.categoryOptions).toContain('真菌性病害')
      expect(vm.categoryOptions).toContain('细菌性病害')
      expect(vm.categoryOptions).toContain('病毒性病害')
      expect(vm.categoryOptions).toContain('虫害')
      expect(vm.categoryOptions).toContain('营养性病害')
    })
  })

  /**
   * 搜索防抖测试
   */
  describe('搜索防抖测试', () => {
    /** 测试搜索输入触发防抖 */
    it('搜索输入应触发防抖处理', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())
      mockSearchDiseaseKnowledge.mockResolvedValue(createMockDiseases(2))

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.searchKeyword = '锈病'
      vm.handleSearchChange()

      expect(mockSearchDiseaseKnowledge).not.toHaveBeenCalled()

      vi.advanceTimersByTime(500)
      await flushPromises()

      expect(mockSearchDiseaseKnowledge).toHaveBeenCalledWith('锈病')
    })

    /** 测试防抖时间内多次输入只触发一次搜索 */
    it('防抖时间内多次输入应只触发一次搜索', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())
      mockSearchDiseaseKnowledge.mockResolvedValue(createMockDiseases(2))

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.searchKeyword = '锈'
      vm.handleSearchChange()

      vi.advanceTimersByTime(200)

      vm.searchKeyword = '锈病'
      vm.handleSearchChange()

      vi.advanceTimersByTime(500)
      await flushPromises()

      expect(mockSearchDiseaseKnowledge).toHaveBeenCalledTimes(1)
      expect(mockSearchDiseaseKnowledge).toHaveBeenCalledWith('锈病')
    })

    /** 测试空关键词搜索应加载全部数据 */
    it('空关键词搜索应调用loadDiseases', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())

      const wrapper = mount(Knowledge)
      await flushPromises()

      const initialCallCount = mockGetDiseaseKnowledge.mock.calls.length

      const vm = wrapper.vm as any
      vm.searchKeyword = ''
      await vm.searchDiseases()
      await flushPromises()

      expect(mockGetDiseaseKnowledge.mock.calls.length).toBe(initialCallCount + 1)
    })
  })

  /**
   * 类别筛选测试
   */
  describe('类别筛选测试', () => {
    /** 测试类别筛选触发数据重载 */
    it('类别筛选变化应触发数据重载', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())

      const wrapper = mount(Knowledge)
      await flushPromises()

      const initialCallCount = mockGetDiseaseKnowledge.mock.calls.length

      const vm = wrapper.vm as any
      vm.selectedCategory = '真菌性病害'
      await vm.loadDiseases()
      await flushPromises()

      expect(mockGetDiseaseKnowledge.mock.calls.length).toBe(initialCallCount + 1)
      expect(mockGetDiseaseKnowledge).toHaveBeenCalledWith('真菌性病害', 0, 100)
    })

    /** 测试空类别筛选不传category参数 */
    it('空类别筛选应不传category参数', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.selectedCategory = ''
      await vm.loadDiseases()
      await flushPromises()

      expect(mockGetDiseaseKnowledge).toHaveBeenCalledWith(undefined, 0, 100)
    })
  })

  /**
   * 空状态显示测试
   */
  describe('空状态显示测试', () => {
    /** 测试无数据时显示空状态 */
    it('无数据时应显示空状态', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue([])

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.isLoading).toBe(false)
      expect(vm.filteredDiseases.length).toBe(0)
    })

    /** 测试搜索无结果时显示空状态 */
    it('搜索无结果时应显示空状态', async () => {
      mockSearchDiseaseKnowledge.mockResolvedValue([])

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      vm.searchKeyword = '不存在的病害'
      await vm.searchDiseases()
      await flushPromises()

      expect(vm.filteredDiseases.length).toBe(0)
    })
  })

  /**
   * 卡片交互测试
   */
  describe('卡片交互测试', () => {
    /** 测试查看详情交互 */
    it('点击查看详情应调用getDiseaseDetail', async () => {
      const diseases = createMockDiseases()
      mockGetDiseaseKnowledge.mockResolvedValue(diseases)
      mockGetDiseaseDetail.mockResolvedValue(diseases[0])

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleViewDetail(1)
      await flushPromises()

      expect(mockGetDiseaseDetail).toHaveBeenCalledWith(1)
    })

    /** 测试查看详情成功显示消息 */
    it('查看详情成功应显示成功消息', async () => {
      const diseases = createMockDiseases()
      mockGetDiseaseKnowledge.mockResolvedValue(diseases)
      mockGetDiseaseDetail.mockResolvedValue(diseases[0])

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleViewDetail(1)
      await flushPromises()

      const { ElMessage } = await import('element-plus')
      expect(ElMessage.success).toHaveBeenCalled()
    })

    /** 测试查看详情失败显示错误消息 */
    it('查看详情失败应显示错误消息', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue(createMockDiseases())
      mockGetDiseaseDetail.mockRejectedValue(new Error('加载失败'))

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handleViewDetail(1)
      await flushPromises()

      const { ElMessage } = await import('element-plus')
      expect(ElMessage.error).toHaveBeenCalledWith('加载详情失败')
    })

    /** 测试防治方法交互 */
    it('点击防治方法应显示病害防治信息', async () => {
      const diseases = createMockDiseases()
      mockGetDiseaseKnowledge.mockResolvedValue(diseases)

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      await vm.handlePrevention(1)
      await flushPromises()

      const { ElMessage } = await import('element-plus')
      expect(ElMessage.info).toHaveBeenCalled()
    })

    /** 测试卡片点击交互 */
    it('点击卡片应触发handleClick', async () => {
      const diseases = createMockDiseases()
      mockGetDiseaseKnowledge.mockResolvedValue(diseases)

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      const consoleSpy = vi.spyOn(console, 'log').mockImplementation(() => {})
      vm.handleClick(1)
      expect(consoleSpy).toHaveBeenCalledWith('点击病害卡片:', 1)
      consoleSpy.mockRestore()
    })
  })

  /**
   * 加载状态测试
   */
  describe('加载状态测试', () => {
    /** 测试组件挂载后触发加载 */
    it('组件挂载后应触发数据加载', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue([])

      mount(Knowledge)
      await flushPromises()

      expect(mockGetDiseaseKnowledge).toHaveBeenCalled()
    })

    /** 测试数据加载完成后isLoading为false */
    it('数据加载完成后isLoading应为false', async () => {
      mockGetDiseaseKnowledge.mockResolvedValue([
        { id: 1, name: '小麦锈病', symptoms: '测试' }
      ])

      const wrapper = mount(Knowledge)
      await flushPromises()

      const vm = wrapper.vm as any
      expect(vm.isLoading).toBe(false)
    })
  })
})
