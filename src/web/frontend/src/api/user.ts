/**
 * 用户 API 调用函数
 * 负责调用后端用户相关接口
 */
import { http } from '@/utils/request'

// API 基础路径
const API_BASE = '/users'

/**
 * 用户类型
 */
export interface User {
  id: number
  username: string
  email: string
  phone?: string
  avatar_url?: string
  role: 'farmer' | 'technician' | 'admin'
  is_active: boolean
  created_at: string
  updated_at: string
}

/**
 * 登录请求参数
 */
export interface LoginRequest {
  username: string
  password: string
}

/**
 * 登录响应
 */
export interface LoginResponse {
  success: boolean
  data?: {
    access_token: string
    refresh_token?: string
    token_type: string
    user: User
  }
  error?: string
  message?: string
}

/**
 * 注册请求参数
 */
export interface RegisterRequest {
  username: string
  email: string
  password: string
  role?: 'farmer' | 'technician' | 'admin'
}

/**
 * 刷新令牌响应
 */
export interface RefreshTokenResponse {
  access_token: string
  refresh_token?: string
  token_type: string
}

/**
 * 密码重置请求参数
 */
export interface PasswordResetRequest {
  email: string
}

/**
 * 密码重置确认参数
 */
export interface PasswordResetConfirm {
  token: string
  new_password: string
}

/**
 * 会话信息
 */
export interface Session {
  id: string
  user_agent: string
  ip_address: string
  created_at: string
  last_activity: string
  is_current: boolean
}

/**
 * 用户登录
 * @param data 登录参数
 * @returns 登录响应（包含 Token 和用户信息）
 */
export async function login(data: LoginRequest): Promise<LoginResponse> {
  return http.post<LoginResponse>(`${API_BASE}/login`, data)
}

/**
 * 用户注册
 * @param data 注册参数
 * @returns 注册响应
 */
export async function register(data: RegisterRequest): Promise<User> {
  return http.post<User>(`${API_BASE}/register`, data)
}

/**
 * 获取当前用户信息
 * @returns 当前用户信息
 */
export async function getCurrentUser(): Promise<User> {
  return http.get<User>(`${API_BASE}/me`)
}

/**
 * 更新用户信息
 * @param userId 用户 ID
 * @param data 更新数据
 * @returns 更新后的用户信息
 */
export async function updateUser(userId: number, data: Partial<Pick<User, 'username' | 'email' | 'phone' | 'avatar_url'>>): Promise<User> {
  return http.put<User>(`${API_BASE}/${userId}`, data)
}

/**
 * 用户登出
 * 先调用后端登出端点撤销令牌，再清除本地状态
 */
export const logout = async () => {
  try {
    await http.post('/users/logout')
  } catch (error) {
    // 即使后端登出失败，仍清除本地状态
  }
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('user')
}

/**
 * 保存用户信息到本地
 * @param user 用户信息
 */
export function saveUserInfo(user: User): void {
  localStorage.setItem('user', JSON.stringify(user))
}

/**
 * 从本地获取用户信息
 * @returns 用户信息
 */
export function getUserInfo(): User | null {
  const userStr = localStorage.getItem('user')
  if (userStr) {
    try {
      return JSON.parse(userStr)
    } catch (e) {
      return null
    }
  }
  return null
}

/**
 * 刷新访问令牌
 * @param refreshToken 刷新令牌
 * @returns 新的令牌信息
 */
export async function refreshToken(refreshToken: string): Promise<RefreshTokenResponse> {
  return http.post<RefreshTokenResponse>('/users/token/refresh', { refresh_token: refreshToken })
}

/**
 * 请求密码重置
 * @param email 用户邮箱
 * @returns 请求结果
 */
export async function requestPasswordReset(email: string): Promise<{ message: string }> {
  return http.post<{ message: string }>('/users/password/reset-request', { email })
}

/**
 * 执行密码重置
 * @param data 密码重置确认数据
 * @returns 重置结果
 */
export async function resetPassword(data: PasswordResetConfirm): Promise<{ message: string }> {
  return http.post<{ message: string }>('/users/password/reset', data)
}

/**
 * 获取用户会话列表
 * @returns 会话列表
 */
export async function getSessions(): Promise<Session[]> {
  return http.get<Session[]>('/users/sessions/list')
}

/**
 * 终止指定会话
 * @param sessionId 会话ID
 * @returns 终止结果
 */
export async function terminateSession(sessionId: string): Promise<{ message: string }> {
  return http.delete<{ message: string }>(`/users/sessions/${sessionId}`)
}
