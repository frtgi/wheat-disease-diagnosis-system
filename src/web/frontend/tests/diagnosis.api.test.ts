/**
 * 诊断 API 模块测试
 * 测试 diagnosis.ts 中所有 API 调用函数的请求参数、URL、方法和响应解析
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  diagnoseImage,
  diagnoseText,
  getDiagnosisRecords,
  getDiagnosisDetail,
  updateDiagnosis,
  deleteDiagnosis
} from '@/api/diagnosis'
import type { DiagnosisResult, DiagnosisListResponse } from '@/api/diagnosis'

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

describe('diagnosis API 模块测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('diagnoseImage - 图像诊断', () => {
    /** 测试仅传入图像文件时，FormData 应包含 image 字段 */
    it('应构造包含 image 的 FormData 并发送 POST 请求', async () => {
      const mockResult: DiagnosisResult = {
        diagnosis_id: 'diag-001',
        disease_name: '小麦锈病',
        confidence: 0.92,
        created_at: '2024-01-01T00:00:00Z'
      }
      mockHttp.post.mockResolvedValue(mockResult)

      const fakeFile = new File(['image-data'], 'wheat.jpg', { type: 'image/jpeg' })
      const result = await diagnoseImage({ image: fakeFile })

      expect(mockHttp.post).toHaveBeenCalledTimes(1)
      expect(mockHttp.post).toHaveBeenCalledWith('/diagnosis/image', expect.any(FormData))

      const calledArgs = mockHttp.post.mock.calls[0]
      const formData = calledArgs[1] as FormData
      expect(formData.get('image')).toBe(fakeFile)
      expect(formData.get('symptoms')).toBeNull()

      expect(result).toEqual(mockResult)
    })

    /** 测试传入图像和症状描述时，FormData 应同时包含 image 和 symptoms 字段 */
    it('应在提供 symptoms 时将其追加到 FormData', async () => {
      const mockResult: DiagnosisResult = {
        diagnosis_id: 'diag-002',
        disease_name: '小麦白粉病',
        confidence: 0.85,
        created_at: '2024-01-02T00:00:00Z'
      }
      mockHttp.post.mockResolvedValue(mockResult)

      const fakeFile = new File(['image-data'], 'leaf.jpg', { type: 'image/jpeg' })
      const result = await diagnoseImage({ image: fakeFile, symptoms: '叶片出现白色粉状物' })

      expect(mockHttp.post).toHaveBeenCalledWith('/diagnosis/image', expect.any(FormData))

      const calledArgs = mockHttp.post.mock.calls[0]
      const formData = calledArgs[1] as FormData
      expect(formData.get('image')).toBe(fakeFile)
      expect(formData.get('symptoms')).toBe('叶片出现白色粉状物')

      expect(result).toEqual(mockResult)
    })

    /** 测试请求 URL 正确 */
    it('应请求正确的 URL 路径 /diagnosis/image', async () => {
      mockHttp.post.mockResolvedValue({} as DiagnosisResult)
      const fakeFile = new File([''], 'test.png', { type: 'image/png' })
      await diagnoseImage({ image: fakeFile })

      expect(mockHttp.post).toHaveBeenCalledWith(
        '/diagnosis/image',
        expect.any(FormData)
      )
    })
  })

  describe('diagnoseText - 文本诊断', () => {
    /** 测试文本诊断应发送 JSON 请求体 */
    it('应发送 POST 请求并传递 JSON 请求体', async () => {
      const mockResult: DiagnosisResult = {
        diagnosis_id: 'diag-003',
        disease_name: '小麦赤霉病',
        confidence: 0.78,
        severity: 'moderate',
        created_at: '2024-01-03T00:00:00Z'
      }
      mockHttp.post.mockResolvedValue(mockResult)

      const result = await diagnoseText({ text: '穗部出现粉红色霉层' })

      expect(mockHttp.post).toHaveBeenCalledTimes(1)
      expect(mockHttp.post).toHaveBeenCalledWith('/diagnosis/text', { text: '穗部出现粉红色霉层' })
      expect(result).toEqual(mockResult)
    })

    /** 测试请求 URL 正确 */
    it('应请求正确的 URL 路径 /diagnosis/text', async () => {
      mockHttp.post.mockResolvedValue({} as DiagnosisResult)
      await diagnoseText({ text: 'test' })

      const calledUrl = mockHttp.post.mock.calls[0][0]
      expect(calledUrl).toBe('/diagnosis/text')
    })
  })

  describe('getDiagnosisRecords - 获取诊断记录列表', () => {
    /** 测试默认参数 skip=0, limit=20 的传递 */
    it('应使用默认参数 skip=0, limit=20 发送 GET 请求', async () => {
      const mockResponse: DiagnosisListResponse = {
        records: [],
        total: 0,
        skip: 0,
        limit: 20
      }
      mockHttp.get.mockResolvedValue(mockResponse)

      const result = await getDiagnosisRecords()

      expect(mockHttp.get).toHaveBeenCalledTimes(1)
      expect(mockHttp.get).toHaveBeenCalledWith('/diagnosis/records', {
        params: { skip: 0, limit: 20 }
      })
      expect(result).toEqual({ records: [], total: 0 })
    })

    /** 测试自定义 skip 和 limit 参数的传递 */
    it('应正确传递自定义 skip 和 limit 参数', async () => {
      const mockRecords = [
        { id: 1, user_id: 1, symptoms: 'test', status: 'completed', created_at: '', updated_at: '' }
      ]
      const mockResponse: DiagnosisListResponse = {
        records: mockRecords,
        total: 100,
        skip: 10,
        limit: 5
      }
      mockHttp.get.mockResolvedValue(mockResponse)

      const result = await getDiagnosisRecords(10, 5)

      expect(mockHttp.get).toHaveBeenCalledWith('/diagnosis/records', {
        params: { skip: 10, limit: 5 }
      })
      expect(result.records).toEqual(mockRecords)
      expect(result.total).toBe(100)
    })

    /** 测试响应数据正确解析为 records 和 total */
    it('应从响应中正确提取 records 和 total 字段', async () => {
      const mockResponse: DiagnosisListResponse = {
        records: [
          { id: 1, user_id: 1, symptoms: '锈病症状', status: 'completed', created_at: '2024-01-01', updated_at: '2024-01-01' },
          { id: 2, user_id: 2, symptoms: '白粉病症状', status: 'pending', created_at: '2024-01-02', updated_at: '2024-01-02' }
        ],
        total: 2,
        skip: 0,
        limit: 20
      }
      mockHttp.get.mockResolvedValue(mockResponse)

      const result = await getDiagnosisRecords()

      expect(result.records).toHaveLength(2)
      expect(result.total).toBe(2)
    })
  })

  describe('getDiagnosisDetail - 获取诊断详情', () => {
    /** 测试 URL 路径参数正确拼接 */
    it('应将 ID 拼接到 URL 路径中发送 GET 请求', async () => {
      const mockResult: DiagnosisResult = {
        diagnosis_id: '42',
        disease_name: '小麦锈病',
        confidence: 0.95,
        description: '严重锈病感染',
        created_at: '2024-01-01T00:00:00Z'
      }
      mockHttp.get.mockResolvedValue(mockResult)

      const result = await getDiagnosisDetail('42')

      expect(mockHttp.get).toHaveBeenCalledTimes(1)
      expect(mockHttp.get).toHaveBeenCalledWith('/diagnosis/42')
      expect(result).toEqual(mockResult)
    })

    /** 测试不同 ID 值的路径拼接 */
    it('应正确处理不同 ID 值的路径拼接', async () => {
      mockHttp.get.mockResolvedValue({} as DiagnosisResult)
      await getDiagnosisDetail('abc-123')

      expect(mockHttp.get).toHaveBeenCalledWith('/diagnosis/abc-123')
    })
  })

  describe('updateDiagnosis - 更新诊断记录', () => {
    /** 测试 PUT 请求和 Partial 数据的传递 */
    it('应发送 PUT 请求并传递部分更新数据', async () => {
      const mockResult: DiagnosisResult = {
        diagnosis_id: '10',
        disease_name: '小麦锈病',
        confidence: 0.88,
        severity: 'severe',
        created_at: '2024-01-01T00:00:00Z'
      }
      mockHttp.put.mockResolvedValue(mockResult)

      const partialData: Partial<DiagnosisResult> = {
        severity: 'severe',
        recommendations: '立即喷洒杀菌剂'
      }
      const result = await updateDiagnosis('10', partialData)

      expect(mockHttp.put).toHaveBeenCalledTimes(1)
      expect(mockHttp.put).toHaveBeenCalledWith('/diagnosis/10', partialData)
      expect(result).toEqual(mockResult)
    })

    /** 测试仅更新单个字段 */
    it('应支持仅更新单个字段', async () => {
      mockHttp.put.mockResolvedValue({} as DiagnosisResult)

      await updateDiagnosis('5', { confidence: 0.99 })

      expect(mockHttp.put).toHaveBeenCalledWith('/diagnosis/5', { confidence: 0.99 })
    })
  })

  describe('deleteDiagnosis - 删除诊断记录', () => {
    /** 测试 DELETE 请求和正确的 URL 路径 */
    it('应发送 DELETE 请求到正确的 URL', async () => {
      mockHttp.delete.mockResolvedValue(undefined)

      await deleteDiagnosis('99')

      expect(mockHttp.delete).toHaveBeenCalledTimes(1)
      expect(mockHttp.delete).toHaveBeenCalledWith('/diagnosis/99')
    })

    /** 测试返回值为 void */
    it('应返回 void 类型', async () => {
      mockHttp.delete.mockResolvedValue(undefined)

      const result = await deleteDiagnosis('1')

      expect(result).toBeUndefined()
    })
  })
})
