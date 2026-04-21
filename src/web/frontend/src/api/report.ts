/**
 * 诊断报告 API 调用函数
 * 封装报告生成、下载、列表查询接口
 */
import { http } from '@/utils/request'

const API_BASE = '/reports'

/**
 * 报告文件路径信息
 */
export interface ReportFiles {
  pdf?: string
  html?: string
}

/**
 * 报告生成响应类型
 */
export interface ReportGenerateResponse {
  success: boolean
  diagnosis: {
    disease_name: string
    confidence: number
    severity?: string
    symptoms?: string
    prevention_methods?: string
    treatment_methods?: string
  }
  report_files: ReportFiles
  message: string
  has_image?: boolean
}

/**
 * 报告列表项类型
 */
export interface ReportListItem {
  filename: string
  size: number
  created_at: number
  format: 'pdf' | 'html'
}

/**
 * 报告列表响应类型
 */
export interface ReportListResponse {
  success: boolean
  reports: ReportListItem[]
  total: number
  message?: string
}

/**
 * 生成诊断报告
 * @param image 病害图像文件
 * @param symptoms 症状描述
 * @param reportFormat 报告格式: pdf / html / both
 * @returns 报告文件路径信息
 */
export async function generateReport(
  image: File,
  symptoms: string = '',
  reportFormat: string = 'both'
): Promise<ReportGenerateResponse> {
  const formData = new FormData()
  formData.append('image', image)
  formData.append('symptoms', symptoms)
  formData.append('report_format', reportFormat)
  const response = await http.post<ReportGenerateResponse>(`${API_BASE}/generate`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000
  })
  return response.data || response
}

/**
 * 从诊断记录生成报告
 * @param diagnosisId 诊断记录 ID
 * @param reportFormat 报告格式: pdf / html / both
 * @returns 报告文件路径信息
 */
export async function generateReportFromRecord(
  diagnosisId: number,
  reportFormat: string = 'both'
): Promise<ReportGenerateResponse> {
  const formData = new FormData()
  formData.append('report_format', reportFormat)
  const response = await http.post<ReportGenerateResponse>(`${API_BASE}/generate-from-record/${diagnosisId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
  return response.data || response
}

/**
 * 获取报告下载 URL
 * @param filename 报告文件名
 * @returns 下载 URL
 */
export function getReportDownloadUrl(filename: string): string {
  return `/api/v1${API_BASE}/download/${filename}`
}

/**
 * 下载报告文件（通过 axios 携带认证信息）
 * @param filename 报告文件名
 */
export async function downloadReport(filename: string): Promise<void> {
  const response = await http.get(`${API_BASE}/download/${filename}`, {
    responseType: 'blob',
    timeout: 60000
  })
  const blob = response instanceof Blob ? response : new Blob([response])
  const url = window.URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = filename
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  window.URL.revokeObjectURL(url)
}

/**
 * 获取报告列表
 * @returns 报告文件列表
 */
export async function getReportList(): Promise<ReportListResponse> {
  const response = await http.get<ReportListResponse>(`${API_BASE}/list`)
  return response.data || response
}
