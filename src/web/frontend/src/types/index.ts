/**
 * TypeScript 类型定义文件
 */

// API 响应数据结构
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
}

// 用户信息
export interface UserInfo {
  id: number
  username: string
  email: string
  phone?: string
  avatar?: string
  registerDate?: string
  lastLogin?: string
}

// 登录参数
export interface LoginParams {
  username: string
  password: string
  remember?: boolean
}

// 注册参数
export interface RegisterParams {
  username: string
  email: string
  phone?: string
  password: string
}

// 诊断结果
export interface DiagnosisResult {
  id: number
  disease: string
  confidence: number
  suggestion: string
  imageUrl: string
  createTime: string
}

// 诊断记录
export interface DiagnosisRecord {
  id: number
  date: string
  disease: string
  confidence: number
  suggestion: string
}

// 知识库条目
export interface KnowledgeItem {
  id: number
  disease: string
  title: string
  symptoms: string
  conditions: string
  prevention: string
}

// 分页参数
export interface PageParams {
  page: number
  pageSize: number
}

// 分页响应
export interface PageResult<T> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

// 病害信息
export interface Disease {
  id: number
  name: string
  image_url: string
  symptoms_brief: string
  symptoms: string[]
  category: string
  severity: number
  high_season: string
  suitable_temp: string
  description: string
  prevention: string[]
}

// 诊断统计
export interface DiagnosisStatistics {
  total: number
  today: number
  week: number
  month: number
}

// 病害分布数据
export interface DiseaseDistribution {
  name: string
  value: number
}

// 诊断统计数据
export interface DiagnosisStats {
  disease_name: string
  count: number
}

// 趋势数据
export interface TrendData {
  date: string
  count: number
}

// 知识链接
export interface KnowledgeLink {
  id: number
  title: string
  url: string
  type: string
}

// 检测结果
export interface Detection {
  class_name: string
  confidence: number
  box?: number[]
}

// 知识引用
export interface KnowledgeReference {
  entity_name: string
  relation: string
  tail: string
  source: string
  confidence: number
}

// 融合诊断结果
export interface FusionDiagnosisResult {
  disease_name: string  // 中文名称
  disease_name_en?: string  // 英文名称
  confidence: number
  visual_confidence?: number
  textual_confidence?: number
  knowledge_confidence?: number
  description?: string
  symptoms?: string[]  // 症状特征
  causes?: string[]  // 发病原因
  recommendations?: string[]  // 防治建议
  treatment?: string[]  // 治疗方法
  medicines?: Medicine[]  // 用药指导
  knowledge_references?: KnowledgeReference[]
  roi_boxes?: Detection[]
  annotated_image?: string
  inference_time_ms?: number
  severity?: string  // 严重程度
}

// 用药指导
export interface Medicine {
  name: string  // 药物名称
  name_en?: string  // 英文名称
  concentration?: string  // 浓度
  dosage?: string  // 用量
  method?: string  // 使用方法
  frequency?: string  // 使用频率
  safety_period?: string  // 安全间隔期
}

// 融合诊断响应
export interface FusionDiagnosisResponse {
  success: boolean
  diagnosis?: FusionDiagnosisResult
  reasoning_chain?: string[]
  error?: string
}
