/**
 * 诊断报告 API 调用函数
 * 封装报告生成、下载、列表查询接口
 */
import { http } from '@/utils/request'

const API_BASE = '/reports'

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
): Promise<any> {
  const formData = new FormData()
  formData.append('image', image)
  formData.append('symptoms', symptoms)
  formData.append('report_format', reportFormat)
  const response = await http.post(`${API_BASE}/generate`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000
  })
  return response.data?.data || response.data
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
): Promise<any> {
  const formData = new FormData()
  formData.append('report_format', reportFormat)
  const response = await http.post(`${API_BASE}/generate-from-record/${diagnosisId}`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000
  })
  return response.data?.data || response.data
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
 * 获取报告列表
 * @returns 报告文件列表
 */
export async function getReportList(): Promise<any> {
  const response = await http.get(`${API_BASE}/list`)
  return response.data?.data || response.data
}
