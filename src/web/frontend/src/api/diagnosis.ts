/**
 * 诊断 API 调用函数
 * 负责调用后端诊断相关接口
 */
import { http } from '@/utils/request'

// API 基础路径
const API_BASE = '/diagnosis'

/**
 * 诊断结果类型
 */
export interface DiagnosisResult {
  diagnosis_id: string
  disease_name: string
  confidence: number
  severity?: string
  description?: string
  recommendations?: string
  knowledge_links?: string[]
  created_at: string
}

/**
 * 诊断记录列表响应类型
 */
export interface DiagnosisListResponse {
  records: DiagnosisRecordItem[]
  total: number
  skip: number
  limit: number
}

/**
 * 诊断记录项类型（后端返回格式）
 */
export interface DiagnosisRecordItem {
  id: number
  user_id: number
  disease_id?: number
  symptoms: string
  diagnosis_result?: string
  confidence?: number
  suggestions?: string
  status: string
  created_at: string
  updated_at: string
  disease_name?: string
}

/**
 * 图像诊断请求参数
 */
export interface DiagnosisImageRequest {
  image: File
  symptoms?: string
}

/**
 * 文本诊断请求参数
 */
export interface DiagnosisTextRequest {
  text: string
}

/**
 * 图像诊断
 * @param data 诊断参数（包含图像文件和可选症状描述）
 * @returns 诊断结果
 */
export async function diagnoseImage(data: DiagnosisImageRequest): Promise<DiagnosisResult> {
  const formData = new FormData()
  formData.append('image', data.image)
  if (data.symptoms) {
    formData.append('symptoms', data.symptoms)
  }
  
  return http.post<DiagnosisResult>(`${API_BASE}/image`, formData)
}

/**
 * 文本诊断
 * @param data 文本诊断参数
 * @returns 诊断结果
 */
export async function diagnoseText(data: DiagnosisTextRequest): Promise<DiagnosisResult> {
  return http.post<DiagnosisResult>(`${API_BASE}/text`, data)
}

/**
 * 获取诊断记录列表
 * @param skip 跳过记录数
 * @param limit 返回记录数
 * @returns 诊断记录列表
 */
export async function getDiagnosisRecords(
  skip: number = 0,
  limit: number = 20
): Promise<{ records: DiagnosisRecordItem[]; total: number }> {
  const response = await http.get<DiagnosisListResponse>(`${API_BASE}/records`, {
    params: { skip, limit }
  })
  return {
    records: response.records,
    total: response.total
  }
}

/**
 * 获取诊断详情
 * @param id 诊断记录 ID
 * @returns 诊断详情
 */
export async function getDiagnosisDetail(id: string): Promise<DiagnosisResult> {
  return http.get<DiagnosisResult>(`${API_BASE}/${id}`)
}

/**
 * 更新诊断记录
 * @param id 诊断记录 ID
 * @param data 更新数据
 * @returns 更新后的诊断记录
 */
export async function updateDiagnosis(
  id: string,
  data: Partial<DiagnosisResult>
): Promise<DiagnosisResult> {
  return http.put<DiagnosisResult>(`${API_BASE}/${id}`, data)
}

/**
 * 删除诊断记录
 * @param id 诊断记录 ID
 */
export async function deleteDiagnosis(id: string): Promise<void> {
  return http.delete<void>(`${API_BASE}/${id}`)
}

/**
 * 批量诊断结果项类型
 */
export interface BatchDiagnosisItem {
  index: number
  filename: string
  success: boolean
  diagnosis?: any
  error?: string
  cache_hit?: boolean
}

/**
 * 批量诊断响应类型
 */
export interface BatchDiagnosisResponse {
  success: boolean
  summary: {
    total_images: number
    success_count: number
    failed_count: number
    cache_hits: number
    cache_hit_rate: number
    success_rate: number
  }
  results: BatchDiagnosisItem[]
  performance: {
    total_time_ms: number
    avg_time_per_image_ms: number
  }
  message: string
}

/**
 * 批量图像诊断
 * @param images 图像文件列表（最多10张）
 * @param symptoms 症状描述
 * @param thinkingMode 是否启用 Thinking 推理链
 * @param useGraphRag 是否使用 GraphRAG
 * @returns 批量诊断结果
 */
export async function diagnoseBatch(
  images: File[],
  symptoms: string = '',
  thinkingMode: boolean = false,
  useGraphRag: boolean = false
): Promise<BatchDiagnosisResponse> {
  const formData = new FormData()
  images.forEach((image) => {
    formData.append('images', image)
  })
  if (symptoms) {
    formData.append('symptoms', symptoms)
  }
  formData.append('thinking_mode', String(thinkingMode))
  formData.append('use_graph_rag', String(useGraphRag))
  formData.append('use_cache', 'true')

  return http.post<BatchDiagnosisResponse>(`${API_BASE}/batch`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 600000
  })
}
