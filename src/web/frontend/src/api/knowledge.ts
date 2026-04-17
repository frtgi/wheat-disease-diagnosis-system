/**
 * 知识库 API 调用函数
 * 负责调用后端知识库相关接口
 */
import { http } from '@/utils/request'

// API 基础路径
const API_BASE = '/knowledge'

/**
 * 病害知识类型
 */
export interface DiseaseKnowledge {
  id: number
  name: string
  code?: string
  category?: string
  symptoms?: string
  causes?: string
  treatments?: string
  prevention?: string
  severity?: number
  created_at: string
  updated_at: string
}

/**
 * 知识图谱节点类型
 */
export interface KnowledgeNode {
  id: string
  name: string
  type: string
  properties: Record<string, any>
}

/**
 * 知识图谱关系类型
 */
export interface KnowledgeRelation {
  from: string
  to: string
  type: string
  properties?: Record<string, any>
}

/**
 * 获取病害知识列表
 * @param category 病害类别（可选）
 * @param skip 跳过记录数
 * @param limit 返回记录数
 * @returns 病害知识列表
 */
export async function getDiseaseKnowledge(
  category?: string,
  skip: number = 0,
  limit: number = 20
): Promise<DiseaseKnowledge[]> {
  const page = Math.floor(skip / limit) + 1
  return http.get<DiseaseKnowledge[]>(`${API_BASE}/search`, {
    params: { category, page, page_size: limit }
  })
}

/**
 * 获取病害知识详情
 * @param id 病害 ID
 * @returns 病害知识详情
 */
export async function getDiseaseDetail(id: number): Promise<DiseaseKnowledge> {
  return http.get<DiseaseKnowledge>(`${API_BASE}/${id}`)
}

/**
 * 搜索病害知识
 * @param keyword 搜索关键词
 * @param skip 跳过记录数
 * @param limit 返回记录数
 * @returns 搜索结果
 */
export async function searchDiseaseKnowledge(
  keyword: string,
  skip: number = 0,
  limit: number = 20
): Promise<DiseaseKnowledge[]> {
  return http.get<DiseaseKnowledge[]>(`${API_BASE}/search`, {
    params: { keyword, skip, limit }
  })
}

// TODO: 后端尚未实现知识图谱和统计端点

/**
 * 获取知识图谱
 * 后端 /knowledge/graph 端点未实现，返回空数据
 * @param _diseaseId 病害 ID（可选，暂未使用）
 * @returns 空的知识图谱数据
 */
export async function getKnowledgeGraph(_diseaseId?: number): Promise<{
  nodes: KnowledgeNode[]
  relations: KnowledgeRelation[]
}> {
  return { nodes: [], relations: [] }
}

/**
 * 获取病害统计信息
 * 后端 /knowledge/stats 端点未实现，返回空数据
 * @returns 空的统计数据
 */
export async function getDiseaseStats(): Promise<{
  total: number
  by_category: Record<string, number>
}> {
  return { total: 0, by_category: {} }
}
