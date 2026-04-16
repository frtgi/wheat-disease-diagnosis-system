/**
 * 知识库 API 模块测试
 * 测试 knowledge.ts 中所有 API 调用函数的请求参数、URL、方法和响应解析
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  getDiseaseKnowledge,
  getDiseaseDetail,
  searchDiseaseKnowledge,
  getKnowledgeGraph,
  getDiseaseStats
} from '@/api/knowledge'
import type { DiseaseKnowledge, KnowledgeNode, KnowledgeRelation } from '@/api/knowledge'

/** Mock http 模块，拦截所有网络请求 */
vi.mock('@/utils/request', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

import { http } from '@/utils/request'

const mockHttp = vi.mocked(http)

describe('knowledge API 模块测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getDiseaseKnowledge - 获取病害知识列表', () => {
    /** 测试默认参数 skip=0, limit=20 且不传 category */
    it('应使用默认参数发送 GET 请求到 /knowledge/search', async () => {
      const mockData: DiseaseKnowledge[] = [
        {
          id: 1,
          name: '小麦锈病',
          category: 'fungal',
          severity: 3,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        }
      ]
      mockHttp.get.mockResolvedValue(mockData)

      const result = await getDiseaseKnowledge()

      expect(mockHttp.get).toHaveBeenCalledTimes(1)
      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/search', {
        params: { category: undefined, skip: 0, limit: 20 }
      })
      expect(result).toEqual(mockData)
    })

    /** 测试传入 category 参数时的请求参数 */
    it('应正确传递 category 参数', async () => {
      mockHttp.get.mockResolvedValue([])

      await getDiseaseKnowledge('fungal')

      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/search', {
        params: { category: 'fungal', skip: 0, limit: 20 }
      })
    })

    /** 测试自定义 skip 和 limit 参数 */
    it('应正确传递自定义 skip 和 limit 参数', async () => {
      mockHttp.get.mockResolvedValue([])

      await getDiseaseKnowledge('viral', 5, 10)

      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/search', {
        params: { category: 'viral', skip: 5, limit: 10 }
      })
    })

    /** 测试响应数据正确解析 */
    it('应正确解析病害知识列表响应', async () => {
      const mockData: DiseaseKnowledge[] = [
        {
          id: 1,
          name: '小麦锈病',
          code: 'WRS-001',
          category: 'fungal',
          symptoms: '叶片出现铁锈色斑点',
          severity: 3,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        },
        {
          id: 2,
          name: '小麦白粉病',
          code: 'WPM-001',
          category: 'fungal',
          symptoms: '叶片出现白色粉状物',
          severity: 2,
          created_at: '2024-01-02T00:00:00Z',
          updated_at: '2024-01-02T00:00:00Z'
        }
      ]
      mockHttp.get.mockResolvedValue(mockData)

      const result = await getDiseaseKnowledge('fungal', 0, 20)

      expect(result).toHaveLength(2)
      expect(result[0].name).toBe('小麦锈病')
      expect(result[1].category).toBe('fungal')
    })
  })

  describe('getDiseaseDetail - 获取病害知识详情', () => {
    /** 测试 URL 路径参数正确拼接 */
    it('应将病害 ID 拼接到 URL 路径中发送 GET 请求', async () => {
      const mockDetail: DiseaseKnowledge = {
        id: 42,
        name: '小麦赤霉病',
        code: 'WFHB-001',
        category: 'fungal',
        symptoms: '穗部出现粉红色霉层',
        causes: '禾谷镰刀菌感染',
        treatments: '喷洒多菌灵',
        prevention: '选用抗病品种',
        severity: 4,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
      mockHttp.get.mockResolvedValue(mockDetail)

      const result = await getDiseaseDetail(42)

      expect(mockHttp.get).toHaveBeenCalledTimes(1)
      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/diseases/42')
      expect(result).toEqual(mockDetail)
      expect(result.name).toBe('小麦赤霉病')
    })

    /** 测试不同 ID 值的路径拼接 */
    it('应正确处理不同 ID 值的路径拼接', async () => {
      mockHttp.get.mockResolvedValue({} as DiseaseKnowledge)

      await getDiseaseDetail(7)

      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/diseases/7')
    })
  })

  describe('searchDiseaseKnowledge - 搜索病害知识', () => {
    /** 测试搜索应传递 keyword 参数 */
    it('应发送 GET 请求并传递 keyword 参数', async () => {
      const mockResults: DiseaseKnowledge[] = [
        {
          id: 1,
          name: '小麦锈病',
          category: 'fungal',
          severity: 3,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        }
      ]
      mockHttp.get.mockResolvedValue(mockResults)

      const result = await searchDiseaseKnowledge('锈病')

      expect(mockHttp.get).toHaveBeenCalledTimes(1)
      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/search', {
        params: { keyword: '锈病', skip: 0, limit: 20 }
      })
      expect(result).toEqual(mockResults)
    })

    /** 测试自定义 skip 和 limit 参数 */
    it('应支持自定义 skip 和 limit 参数', async () => {
      mockHttp.get.mockResolvedValue([])

      await searchDiseaseKnowledge('白粉', 10, 5)

      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/search', {
        params: { keyword: '白粉', skip: 10, limit: 5 }
      })
    })

    /** 测试搜索结果为空时的响应 */
    it('应正确处理空搜索结果', async () => {
      mockHttp.get.mockResolvedValue([])

      const result = await searchDiseaseKnowledge('不存在的病害')

      expect(result).toEqual([])
      expect(result).toHaveLength(0)
    })
  })

  describe('getKnowledgeGraph - 获取知识图谱', () => {
    /** 测试不传 diseaseId 时的请求参数 */
    it('不传 diseaseId 时应发送 GET 请求到 /knowledge/graph', async () => {
      const mockNodes: KnowledgeNode[] = [
        { id: 'n1', name: '小麦锈病', type: 'disease', properties: {} },
        { id: 'n2', name: '禾柄锈菌', type: 'pathogen', properties: {} }
      ]
      const mockRelations: KnowledgeRelation[] = [
        { from: 'n2', to: 'n1', type: 'causes' }
      ]
      mockHttp.get.mockResolvedValue({ nodes: mockNodes, relations: mockRelations })

      const result = await getKnowledgeGraph()

      expect(mockHttp.get).toHaveBeenCalledTimes(1)
      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/graph', {
        params: { disease_id: undefined }
      })
      expect(result.nodes).toHaveLength(2)
      expect(result.relations).toHaveLength(1)
    })

    /** 测试传入 diseaseId 时的请求参数 */
    it('传入 diseaseId 时应正确传递参数', async () => {
      const mockNodes: KnowledgeNode[] = [
        { id: 'n1', name: '小麦锈病', type: 'disease', properties: { severity: 3 } }
      ]
      const mockRelations: KnowledgeRelation[] = []
      mockHttp.get.mockResolvedValue({ nodes: mockNodes, relations: mockRelations })

      const result = await getKnowledgeGraph(5)

      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/graph', {
        params: { disease_id: 5 }
      })
      expect(result.nodes[0].name).toBe('小麦锈病')
    })

    /** 测试知识图谱响应数据完整解析 */
    it('应正确解析包含节点和关系的知识图谱响应', async () => {
      const mockNodes: KnowledgeNode[] = [
        { id: 'd1', name: '小麦锈病', type: 'disease', properties: { severity: 3 } },
        { id: 'p1', name: '禾柄锈菌', type: 'pathogen', properties: { latin: 'Puccinia graminis' } },
        { id: 's1', name: '叶片锈斑', type: 'symptom', properties: {} }
      ]
      const mockRelations: KnowledgeRelation[] = [
        { from: 'p1', to: 'd1', type: 'causes', properties: { confidence: 0.95 } },
        { from: 'd1', to: 's1', type: 'has_symptom' }
      ]
      mockHttp.get.mockResolvedValue({ nodes: mockNodes, relations: mockRelations })

      const result = await getKnowledgeGraph(1)

      expect(result.nodes).toHaveLength(3)
      expect(result.relations).toHaveLength(2)
      expect(result.relations[0].type).toBe('causes')
      expect(result.relations[1].from).toBe('d1')
    })
  })

  describe('getDiseaseStats - 获取病害统计信息', () => {
    /** 测试获取统计信息应发送 GET 请求 */
    it('应发送 GET 请求到 /knowledge/stats', async () => {
      const mockStats = {
        total: 50,
        by_category: {
          fungal: 25,
          viral: 10,
          bacterial: 8,
          other: 7
        }
      }
      mockHttp.get.mockResolvedValue(mockStats)

      const result = await getDiseaseStats()

      expect(mockHttp.get).toHaveBeenCalledTimes(1)
      expect(mockHttp.get).toHaveBeenCalledWith('/knowledge/stats')
      expect(result.total).toBe(50)
      expect(result.by_category.fungal).toBe(25)
    })

    /** 测试统计信息响应数据完整解析 */
    it('应正确解析包含 total 和 by_category 的统计响应', async () => {
      const mockStats = {
        total: 100,
        by_category: {
          fungal: 60,
          viral: 20,
          bacterial: 15,
          other: 5
        }
      }
      mockHttp.get.mockResolvedValue(mockStats)

      const result = await getDiseaseStats()

      expect(result.total).toBe(100)
      expect(Object.keys(result.by_category)).toHaveLength(4)
    })
  })
})
