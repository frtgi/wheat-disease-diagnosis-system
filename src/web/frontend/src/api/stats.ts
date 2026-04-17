/**
 * 统计 API 调用函数
 * 负责调用后端统计相关接口
 */
import { http } from '@/utils/request'

const API_BASE = '/stats'

/**
 * 概览统计响应类型
 */
export interface StatsOverview {
  total_users: number
  total_diagnoses: number
  total_diseases: number
  today_diagnoses: number
  avg_accuracy: number
  diagnosis_trend: Array<{ date: string; count: number }>
}

/**
 * 热门疾病项类型
 */
export interface TopDiseaseItem {
  disease_id: number
  disease_name: string
  count: number
}

/**
 * 诊断统计响应类型
 */
export interface DiagnosisStatsResponse {
  by_status: Record<string, number>
  top_diseases: TopDiseaseItem[]
}

/**
 * 用户统计响应类型
 */
export interface UserStatsResponse {
  total_users: number
  active_users: number
  inactive_users: number
  by_role: Record<string, number>
}

/**
 * 获取系统概览统计数据
 * 返回用户总数、诊断记录总数、疾病知识总数等
 * @returns 概览统计数据
 */
export async function getStatsOverview(): Promise<StatsOverview> {
  return http.get<StatsOverview>(`${API_BASE}/overview`)
}

/**
 * 获取诊断相关统计数据
 * 返回诊断状态分布、热门疾病等
 * @returns 诊断统计数据
 */
export async function getDiagnosisStats(): Promise<DiagnosisStatsResponse> {
  return http.get<DiagnosisStatsResponse>(`${API_BASE}/diagnoses`)
}

/**
 * 获取用户相关统计数据
 * 需要管理员权限，返回活跃用户数、角色分布等
 * @returns 用户统计数据
 */
export async function getUserStats(): Promise<UserStatsResponse> {
  return http.get<UserStatsResponse>(`${API_BASE}/users`)
}
