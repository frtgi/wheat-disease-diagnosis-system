/**
 * 管理员 API 调用函数
 * 封装管理员后台相关的接口调用
 */
import { http } from '@/utils/request'

export { getStatsOverview as getOverviewStats, getUserStats, getDiagnosisStats } from './stats'

const STATS_BASE = '/stats'
const LOGS_BASE = '/logs'

/**
 * 缓存统计数据类型
 */
export interface CacheStatsData {
  uptime_seconds?: number
  total_requests?: number
  cache_hits?: number
  overall_hit_rate?: number
  image_cache?: {
    size?: number
    max_size?: number
    hit_rate?: number
  }
  semantic_cache?: {
    size?: number
    capacity?: number
  }
  enabled?: {
    image_cache: boolean
    semantic_cache: boolean
  }
}

/**
 * 缓存统计响应类型
 */
export interface CacheStatsResponse {
  success: boolean
  data: CacheStatsData
}

/**
 * 清空缓存响应类型
 */
export interface ClearCacheResponse {
  success: boolean
  message: string
  deleted_count?: number
}

/**
 * GPU 显存状态类型
 */
export interface VramStatusData {
  used_mb: number
  free_mb: number
  total_mb: number
  reserved_mb: number
  usage_ratio: number
  warning_threshold: number
  critical_threshold: number
  is_critical: boolean
  is_warning: boolean
}

/**
 * GPU 显存状态响应类型
 */
export interface VramStatusResponse {
  success: boolean
  data: VramStatusData
}

/**
 * GPU 显存清理响应类型
 */
export interface VramCleanupResponse {
  success: boolean
  message: string
  freed_memory_mb?: number
}

/**
 * 日志统计项类型
 */
export interface LogStatisticsData {
  total_logs?: number
  success_count?: number
  failed_count?: number
  avg_response_time_ms?: number
  by_status?: Record<string, number>
  by_disease?: Record<string, number>
}

/**
 * 病害分布项类型
 */
export interface DiseaseDistributionItem {
  disease_name: string
  count: number
  percentage?: number
}

/**
 * 病害分布响应类型
 */
export interface DiseaseDistributionResponse {
  distribution: DiseaseDistributionItem[]
  total?: number
}

/**
 * 成功率趋势数据点类型
 */
export interface SuccessRateTrendPoint {
  time: string
  success_rate: number
  total_count?: number
}

/**
 * 日志项类型
 */
export interface LogItem {
  id?: number
  timestamp?: string
  disease_name?: string
  symptoms?: string
  confidence?: number
  success?: boolean
  response_time_ms?: number
  error_message?: string
}

/**
 * 最近日志响应类型
 */
export interface RecentLogsResponse {
  logs: LogItem[]
  total?: number
  page?: number
  page_size?: number
}

/**
 * 错误分析项类型
 */
export interface ErrorAnalysisItem {
  error_type: string
  count: number
  percentage?: number
  recent_occurrences?: string[]
}

/**
 * 错误分析响应类型
 */
export interface ErrorAnalysisResponse {
  total_errors?: number
  errors?: ErrorAnalysisItem[]
  trend?: SuccessRateTrendPoint[]
}

/**
 * 模型预加载响应类型
 */
export interface PreloadModelsResponse {
  success: boolean
  message: string
  models_loaded?: string[]
}

/**
 * 获取缓存统计
 * @returns 缓存统计数据
 */
export async function getCacheStats(): Promise<CacheStatsResponse> {
  return http.get<CacheStatsResponse>(`${STATS_BASE}/cache`)
}

/**
 * 清空推理缓存（需管理员权限）
 * @returns 清理结果
 */
export async function clearCache(): Promise<ClearCacheResponse> {
  return http.delete<ClearCacheResponse>(`${STATS_BASE}/cache`)
}

/**
 * 获取 GPU 显存状态（需管理员权限）
 * @returns 显存使用信息
 */
export async function getVramStatus(): Promise<VramStatusResponse> {
  return http.get<VramStatusResponse>(`${STATS_BASE}/vram`)
}

/**
 * 手动清理 GPU 显存（需管理员权限）
 * @returns 清理结果
 */
export async function cleanupVram(): Promise<VramCleanupResponse> {
  return http.post<VramCleanupResponse>(`${STATS_BASE}/vram/cleanup`)
}

/**
 * 获取诊断日志统计（需管理员权限）
 * @param durationHours 统计时长（小时）
 * @returns 统计数据
 */
export async function getLogStatistics(durationHours: number = 24): Promise<LogStatisticsData> {
  return http.get<LogStatisticsData>(`${LOGS_BASE}/statistics`, { params: { duration_hours: durationHours } })
}

/**
 * 获取病害分布统计（需管理员权限）
 * @param durationHours 统计时长（小时）
 * @returns 病害分布数据
 */
export async function getDiseaseDistribution(durationHours: number = 24): Promise<DiseaseDistributionResponse> {
  return http.get<DiseaseDistributionResponse>(`${LOGS_BASE}/disease-distribution`, { params: { duration_hours: durationHours } })
}

/**
 * 获取成功率趋势（需管理员权限）
 * @param durationHours 统计时长（小时）
 * @returns 趋势数据
 */
export async function getSuccessRateTrend(durationHours: number = 24): Promise<SuccessRateTrendPoint[]> {
  return http.get<SuccessRateTrendPoint[]>(`${LOGS_BASE}/success-rate-trend`, { params: { duration_hours: durationHours } })
}

/**
 * 获取最近诊断日志（需管理员权限）
 * @param params 查询参数
 * @returns 日志列表
 */
export async function getRecentLogs(params?: {
  page?: number
  page_size?: number
  success_only?: boolean
  disease_filter?: string
}): Promise<RecentLogsResponse> {
  return http.get<RecentLogsResponse>(`${LOGS_BASE}/recent`, { params })
}

/**
 * 获取错误分析（需管理员权限）
 * @param durationHours 统计时长（小时）
 * @returns 错误分析数据
 */
export async function getErrorAnalysis(durationHours: number = 24): Promise<ErrorAnalysisResponse> {
  return http.get<ErrorAnalysisResponse>(`${LOGS_BASE}/error-analysis`, { params: { duration_hours: durationHours } })
}

/**
 * 预加载 AI 模型（需管理员权限）
 * @returns 预加载结果
 */
export async function preloadAIModels(): Promise<PreloadModelsResponse> {
  return http.post<PreloadModelsResponse>('/diagnosis/admin/ai/preload')
}
