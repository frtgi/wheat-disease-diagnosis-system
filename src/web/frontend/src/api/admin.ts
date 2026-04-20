/**
 * 管理员 API 调用函数
 * 封装管理员后台相关的接口调用
 */
import { http } from '@/utils/request'

export { getOverviewStats, getUserStats, getDiagnosisStats } from './stats'

const STATS_BASE = '/stats'
const LOGS_BASE = '/logs'

/**
 * 获取缓存统计
 * @returns 缓存统计数据
 */
export async function getCacheStats() {
  return http.get(`${STATS_BASE}/cache`)
}

/**
 * 清空推理缓存（需管理员权限）
 * @returns 清理结果
 */
export async function clearCache() {
  return http.delete(`${STATS_BASE}/cache`)
}

/**
 * 获取 GPU 显存状态（需管理员权限）
 * @returns 显存使用信息
 */
export async function getVramStatus() {
  return http.get(`${STATS_BASE}/vram`)
}

/**
 * 手动清理 GPU 显存（需管理员权限）
 * @returns 清理结果
 */
export async function cleanupVram() {
  return http.post(`${STATS_BASE}/vram/cleanup`)
}

/**
 * 获取诊断日志统计（需管理员权限）
 * @param durationHours 统计时长（小时）
 * @returns 统计数据
 */
export async function getLogStatistics(durationHours: number = 24) {
  return http.get(`${LOGS_BASE}/statistics`, { params: { duration_hours: durationHours } })
}

/**
 * 获取病害分布统计（需管理员权限）
 * @param durationHours 统计时长（小时）
 * @returns 病害分布数据
 */
export async function getDiseaseDistribution(durationHours: number = 24) {
  return http.get(`${LOGS_BASE}/disease-distribution`, { params: { duration_hours: durationHours } })
}

/**
 * 获取成功率趋势（需管理员权限）
 * @param durationHours 统计时长（小时）
 * @returns 趋势数据
 */
export async function getSuccessRateTrend(durationHours: number = 24) {
  return http.get(`${LOGS_BASE}/success-rate-trend`, { params: { duration_hours: durationHours } })
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
}) {
  return http.get(`${LOGS_BASE}/recent`, { params })
}

/**
 * 获取错误分析（需管理员权限）
 * @param durationHours 统计时长（小时）
 * @returns 错误分析数据
 */
export async function getErrorAnalysis(durationHours: number = 24) {
  return http.get(`${LOGS_BASE}/error-analysis`, { params: { duration_hours: durationHours } })
}

/**
 * 预加载 AI 模型（需管理员权限）
 * @returns 预加载结果
 */
export async function preloadAIModels() {
  return http.post('/diagnosis/admin/ai/preload')
}
