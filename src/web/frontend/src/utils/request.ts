/**
 * Axios 配置和拦截器
 * 负责配置 HTTP 请求和响应拦截器，自动携带 JWT Token
 */
import axios from 'axios'
import type { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError, InternalAxiosRequestConfig } from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import router from '@/router'

// 创建 axios 实例
const service: AxiosInstance = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000, // 30 秒超时（考虑 AI 推理时间）
  headers: {
    'Content-Type': 'application/json'
  }
})

// 是否正在刷新令牌
let isRefreshing = false
// 等待令牌刷新的请求队列
let refreshSubscribers: ((token: string) => void)[] = []

/**
 * 订阅令牌刷新
 * @param callback 刷新成功后的回调函数
 */
function subscribeTokenRefresh(callback: (token: string) => void): void {
  refreshSubscribers.push(callback)
}

/**
 * 通知所有订阅者令牌已刷新
 * @param token 新的访问令牌
 */
function onTokenRefreshed(token: string): void {
  refreshSubscribers.forEach((callback) => callback(token))
  refreshSubscribers = []
}

/**
 * 刷新访问令牌
 * @returns 新的访问令牌
 */
async function refreshAccessToken(): Promise<string | null> {
  const refreshToken = localStorage.getItem('refresh_token')
  if (!refreshToken) {
    return null
  }

  try {
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL || '/api/v1'}/users/token/refresh`,
      { refresh_token: refreshToken }
    )
    const { access_token, refresh_token: newRefreshToken } = response.data
    
    localStorage.setItem('token', access_token)
    if (newRefreshToken) {
      localStorage.setItem('refresh_token', newRefreshToken)
    }
    
    return access_token
  } catch (error) {
    console.error('刷新令牌失败:', error)
    return null
  }
}

/**
 * 跳转到登录页
 */
function redirectToLogin(): void {
  localStorage.removeItem('token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('userInfo')
  router.push('/login')
}

/**
 * 请求拦截器
 * 在发送请求前自动添加 JWT Token
 * 支持 httpOnly Cookie 和 Authorization Header 双模式认证
 */
service.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    config.withCredentials = true
    
    return config
  },
  (error: AxiosError) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

/**
 * 响应拦截器
 * 处理响应数据和错误
 */
service.interceptors.response.use(
  (response: AxiosResponse) => {
    const res = response.data
    
    // 如果响应包含 code 字段，检查是否成功
    if (res.code !== undefined && res.code !== 200) {
      // 401: 未授权，需要重新登录
      if (res.code === 401) {
        ElMessageBox.confirm('登录状态已过期，请重新登录', '提示', {
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning'
        }).then(() => {
          redirectToLogin()
        })
        return Promise.reject(new Error(res.message || 'Error'))
      }
      
      ElMessage.error(res.message || '请求失败')
      return Promise.reject(new Error(res.message || 'Error'))
    }
    
    // 直接返回响应数据
    return res
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean }
    
    // 处理 401 错误，尝试刷新令牌
    if (error.response?.status === 401 && originalRequest && !originalRequest._retry) {
      originalRequest._retry = true
      
      // 如果有 refresh_token，尝试刷新
      if (localStorage.getItem('refresh_token')) {
        // 如果正在刷新，将请求加入队列等待
        if (isRefreshing) {
          return new Promise((resolve) => {
            subscribeTokenRefresh((token: string) => {
              originalRequest.headers.Authorization = `Bearer ${token}`
              resolve(service(originalRequest))
            })
          })
        }
        
        isRefreshing = true
        
        try {
          const newToken = await refreshAccessToken()
          
          if (newToken) {
            // 通知所有等待的请求
            onTokenRefreshed(newToken)
            // 重新发送原请求
            originalRequest.headers.Authorization = `Bearer ${newToken}`
            return service(originalRequest)
          } else {
            // 刷新失败，跳转登录页
            ElMessage.error('令牌刷新失败，请重新登录')
            redirectToLogin()
            return Promise.reject(error)
          }
        } catch (refreshError) {
          // 刷新失败，跳转登录页
          ElMessage.error('令牌刷新失败，请重新登录')
          redirectToLogin()
          return Promise.reject(refreshError)
        } finally {
          isRefreshing = false
        }
      } else {
        // 没有 refresh_token，直接跳转登录页
        ElMessage.error('未授权，请重新登录')
        redirectToLogin()
        return Promise.reject(error)
      }
    }
    
    console.error('响应错误:', error)
    
    // 处理不同的 HTTP 状态码
    if (error.response) {
      switch (error.response.status) {
        case 400:
          ElMessage.error('请求参数错误')
          break
        case 403:
          ElMessage.error('拒绝访问')
          break
        case 404:
          ElMessage.error('请求资源不存在')
          break
        case 500:
          ElMessage.error('服务器内部错误')
          break
        case 502:
          ElMessage.error('网关错误')
          break
        case 503:
          ElMessage.error('服务不可用')
          break
        case 504:
          ElMessage.error('网关超时')
          break
        default:
          ElMessage.error(`请求失败：${error.response.status}`)
      }
    } else if (error.request) {
      ElMessage.error('网络错误，请检查网络连接')
    } else {
      ElMessage.error(error.message || '请求失败')
    }
    
    return Promise.reject(error)
  }
)

/**
 * 封装请求方法
 */
export const http = {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  },

  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  },

  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config)
  },

  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, config)
  },

  upload<T = any>(url: string, data: FormData, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, {
      ...config,
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    })
  }
}

export default service
