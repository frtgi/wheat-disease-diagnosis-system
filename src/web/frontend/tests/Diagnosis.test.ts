/**
 * 诊断页面组件测试
 * 测试诊断页面渲染、多模态输入和融合诊断功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createRouter, createWebHistory } from 'vue-router'
import Diagnosis from '@/views/Diagnosis.vue'

const mockPush = vi.fn()
const mockRouter = {
  push: mockPush,
  replace: vi.fn(),
  go: vi.fn(),
  back: vi.fn(),
  forward: vi.fn()
}

vi.mock('vue-router', async () => {
  const actual = await vi.importActual('vue-router')
  return {
    ...actual,
    useRouter: () => mockRouter
  }
})

vi.mock('@/utils/request', () => ({
  default: {
    post: vi.fn()
  }
}))

vi.mock('@/components/diagnosis/MultiModalInput.vue', () => ({
  default: {
    name: 'MultiModalInput',
    template: `
      <div class="multimodal-input">
        <slot></slot>
        <button class="diagnose-btn" @click="handleDiagnose">开始诊断</button>
      </div>
    `,
    emits: ['diagnose'],
    setup(props: any, { emit }: any) {
      const handleDiagnose = () => {
        emit('diagnose', {
          image: new File([''], 'test.jpg', { type: 'image/jpeg' }),
          symptoms: '测试症状描述',
          weather: 'sunny',
          growthStage: 'seedling',
          affectedPart: 'leaf',
          enableThinking: true,
          useGraphRag: true
        })
      }
      const setDiagnosing = () => {}
      return { handleDiagnose, setDiagnosing }
    }
  }
}))

vi.mock('@/components/diagnosis/FusionResult.vue', () => ({
  default: {
    name: 'FusionResult',
    template: `
      <div class="fusion-result">
        <div v-if="result" class="result-content">
          <div class="disease-name">{{ result.disease_name }}</div>
          <div class="confidence">{{ result.confidence }}</div>
        </div>
        <div v-else class="no-result">暂无诊断结果</div>
      </div>
    `,
    props: ['result', 'reasoningChain', 'imageSrc']
  }
}))

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

describe('Diagnosis.vue 诊断页面测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('组件渲染测试', () => {
    it('应该正确渲染诊断页面容器', () => {
      const wrapper = mount(Diagnosis)
      expect(wrapper.find('.diagnosis-container').exists()).toBe(true)
    })

    it('应该包含多模态输入组件', () => {
      const wrapper = mount(Diagnosis)
      expect(wrapper.find('.multimodal-input').exists()).toBe(true)
    })

    it('应该包含融合结果组件', () => {
      const wrapper = mount(Diagnosis)
      expect(wrapper.find('.fusion-result').exists()).toBe(true)
    })

    it('应该显示页面标题', () => {
      const wrapper = mount(Diagnosis)
      expect(wrapper.find('.page-title').exists()).toBe(true)
      expect(wrapper.text()).toContain('多模态融合诊断')
    })

    it('应该显示技术标签', () => {
      const wrapper = mount(Diagnosis)
      expect(wrapper.text()).toContain('KAD-Former + GraphRAG')
    })
  })

  describe('诊断功能测试', () => {
    it('初始状态诊断结果应为空', () => {
      const wrapper = mount(Diagnosis)
      const vm = wrapper.vm as any
      
      expect(vm.diagnosisResult).toBeNull()
      expect(vm.reasoningChain).toEqual([])
      expect(vm.isDiagnosing).toBe(false)
    })

    it('点击诊断按钮应触发诊断流程', async () => {
      const mockResponse = {
        success: true,
        diagnosis: {
          disease_name: '小麦锈病',
          confidence: 0.95,
          description: '小麦锈病是一种常见的真菌性病害',
          recommendations: ['及时喷洒杀菌剂', '加强田间管理'],
          knowledge_references: []
        },
        reasoning_chain: ['步骤1: 分析图像', '步骤2: 匹配症状']
      }
      
      const http = await import('@/utils/request')
      vi.mocked(http.default.post).mockResolvedValue(mockResponse)
      
      const wrapper = mount(Diagnosis)
      const diagnoseBtn = wrapper.find('.diagnose-btn')
      
      await diagnoseBtn.trigger('click')
      await flushPromises()
      
      expect(http.default.post).toHaveBeenCalled()
    })

    it('诊断成功应更新诊断结果', async () => {
      const mockResponse = {
        success: true,
        diagnosis: {
          disease_name: '小麦白粉病',
          confidence: 0.88,
          description: '测试描述',
          recommendations: ['建议1', '建议2']
        },
        reasoning_chain: ['推理步骤1', '推理步骤2']
      }
      
      const http = await import('@/utils/request')
      vi.mocked(http.default.post).mockResolvedValue(mockResponse)
      
      const wrapper = mount(Diagnosis)
      const diagnoseBtn = wrapper.find('.diagnose-btn')
      
      await diagnoseBtn.trigger('click')
      await flushPromises()
      
      const vm = wrapper.vm as any
      expect(vm.diagnosisResult).not.toBeNull()
      expect(vm.diagnosisResult.disease_name).toBe('小麦白粉病')
      expect(vm.reasoningChain).toHaveLength(2)
    })

    it('诊断失败应显示错误消息', async () => {
      const http = await import('@/utils/request')
      vi.mocked(http.default.post).mockRejectedValue(new Error('诊断服务暂时不可用'))
      
      const wrapper = mount(Diagnosis)
      const diagnoseBtn = wrapper.find('.diagnose-btn')
      
      await diagnoseBtn.trigger('click')
      await flushPromises()
      
      const { ElMessage } = await import('element-plus')
      expect(ElMessage.error).toHaveBeenCalled()
    })

    it('诊断返回失败状态应显示错误', async () => {
      const mockResponse = {
        success: false,
        error: '图像识别失败'
      }
      
      const http = await import('@/utils/request')
      vi.mocked(http.default.post).mockResolvedValue(mockResponse)
      
      const wrapper = mount(Diagnosis)
      const diagnoseBtn = wrapper.find('.diagnose-btn')
      
      await diagnoseBtn.trigger('click')
      await flushPromises()
      
      const { ElMessage } = await import('element-plus')
      expect(ElMessage.error).toHaveBeenCalledWith('图像识别失败')
    })
  })

  describe('路由导航测试', () => {
    it('点击返回应导航到首页', async () => {
      const wrapper = mount(Diagnosis)
      const vm = wrapper.vm as any
      vm.goBack()
      
      expect(mockPush).toHaveBeenCalledWith('/')
    })
  })

  describe('状态管理测试', () => {
    it('诊断过程中 isDiagnosing 应为 true', async () => {
      let resolvePost: any
      const http = await import('@/utils/request')
      vi.mocked(http.default.post).mockImplementation(() => {
        return new Promise((resolve) => {
          resolvePost = resolve
        })
      })
      
      const wrapper = mount(Diagnosis)
      const diagnoseBtn = wrapper.find('.diagnose-btn')
      
      await diagnoseBtn.trigger('click')
      
      const vm = wrapper.vm as any
      expect(vm.isDiagnosing).toBe(true)
      
      resolvePost({ success: true, diagnosis: {}, reasoning_chain: [] })
      await flushPromises()
      
      expect(vm.isDiagnosing).toBe(false)
    })

    it('上传图片后应生成预览URL', async () => {
      const mockResponse = {
        success: true,
        diagnosis: { disease_name: '测试病害' },
        reasoning_chain: []
      }
      
      const http = await import('@/utils/request')
      vi.mocked(http.default.post).mockResolvedValue(mockResponse)
      
      const wrapper = mount(Diagnosis)
      const diagnoseBtn = wrapper.find('.diagnose-btn')
      
      await diagnoseBtn.trigger('click')
      await flushPromises()
      
      const vm = wrapper.vm as any
      expect(vm.uploadedImageUrl).not.toBe('')
    })
  })

  describe('表单数据构建测试', () => {
    it('诊断请求应包含正确的表单数据', async () => {
      const mockResponse = { success: true, diagnosis: {}, reasoning_chain: [] }
      
      const http = await import('@/utils/request')
      vi.mocked(http.default.post).mockResolvedValue(mockResponse)
      
      const wrapper = mount(Diagnosis)
      const diagnoseBtn = wrapper.find('.diagnose-btn')
      
      await diagnoseBtn.trigger('click')
      await flushPromises()
      
      const callArgs = vi.mocked(http.default.post).mock.calls[0]
      expect(callArgs[0]).toBe('/diagnosis/fusion')
      expect(callArgs[1]).toBeInstanceOf(FormData)
    })
  })
})
