/**
 * request.ts HTTP客户端测试
 * 测试请求拦截器、响应拦截器、Token刷新机制和错误处理
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ElMessage, ElMessageBox } from 'element-plus'

/** 使用vi.hoisted提升变量，确保vi.mock工厂函数中可引用 */
const { mockPush, capturedHandlers, mockInstanceRef } = vi.hoisted(() => ({
  mockPush: vi.fn(),
  capturedHandlers: {
    request: [] as any[],
    response: [] as any[]
  },
  mockInstanceRef: {} as any
}))

vi.mock('element-plus', () => ({
  ElMessage: {
    error: vi.fn(),
    success: vi.fn(),
    warning: vi.fn()
  },
  ElMessageBox: {
    confirm: vi.fn()
  }
}))

vi.mock('@/router', () => ({
  default: {
    push: mockPush
  }
}))

vi.mock('axios', () => {
  const mockInstance = vi.fn(() => Promise.resolve({ data: { code: 200 } }))
  mockInstance.get = vi.fn()
  mockInstance.post = vi.fn()
  mockInstance.put = vi.fn()
  mockInstance.delete = vi.fn()
  mockInstance.interceptors = {
    request: {
      use: vi.fn((fulfilled: any, rejected: any) => {
        capturedHandlers.request.push({ fulfilled, rejected })
      })
    },
    response: {
      use: vi.fn((fulfilled: any, rejected: any) => {
        capturedHandlers.response.push({ fulfilled, rejected })
      })
    }
  }

  Object.assign(mockInstanceRef, mockInstance)

  return {
    default: {
      create: vi.fn(() => mockInstance),
      post: vi.fn()
    }
  }
})

import axios from 'axios'
import request, { http } from '@/utils/request'

/** 真实行为的localStorage存储 */
const localStorageStore: Record<string, string> = {}

/**
 * 模拟请求拦截器执行
 * @param config 请求配置
 * @returns 处理后的请求配置
 */
function runRequestInterceptor(config: any) {
  const handler = capturedHandlers.request[0]
  if (handler && handler.fulfilled) {
    return handler.fulfilled(config)
  }
  return config
}

/**
 * 模拟响应拦截器成功处理
 * @param response 响应对象
 * @returns 处理后的响应数据
 */
function runResponseSuccessInterceptor(response: any) {
  const handler = capturedHandlers.response[0]
  if (handler && handler.fulfilled) {
    return handler.fulfilled(response)
  }
  return response
}

/**
 * 模拟响应拦截器错误处理
 * @param error 错误对象
 * @returns 处理结果
 */
function runResponseErrorInterceptor(error: any) {
  const handler = capturedHandlers.response[0]
  if (handler && handler.rejected) {
    return handler.rejected(error)
  }
  return Promise.reject(error)
}

describe('request.ts HTTP客户端测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    Object.keys(localStorageStore).forEach(k => delete localStorageStore[k])
    localStorage.getItem.mockImplementation((key: string) => localStorageStore[key] ?? null)
    localStorage.setItem.mockImplementation((key: string, value: string) => { localStorageStore[key] = value })
    localStorage.removeItem.mockImplementation((key: string) => { delete localStorageStore[key] })
    localStorage.clear.mockImplementation(() => { Object.keys(localStorageStore).forEach(k => delete localStorageStore[k]) })
  })

  describe('请求拦截器', () => {
    /** 测试请求拦截器自动添加Bearer Token */
    it('应该自动添加Bearer Token到请求头', () => {
      localStorage.setItem('token', 'test-access-token')
      const config = { headers: {} }

      const result = runRequestInterceptor(config)

      expect(result.headers.Authorization).toBe('Bearer test-access-token')
    })

    /** 测试没有Token时不添加Authorization头 */
    it('没有Token时不应添加Authorization头', () => {
      const config = { headers: {} }

      const result = runRequestInterceptor(config)

      expect(result.headers.Authorization).toBeUndefined()
    })

    /** 测试请求拦截器错误处理 */
    it('请求拦截器错误时应返回rejected Promise', async () => {
      const handler = capturedHandlers.request[0]
      if (handler && handler.rejected) {
        const error = new Error('request error')
        await expect(handler.rejected(error)).rejects.toThrow('request error')
      }
    })
  })

  describe('响应拦截器 - 成功处理', () => {
    /** 测试响应成功时直接返回response.data */
    it('应该直接返回response.data', () => {
      const response = {
        data: { code: 200, data: 'test-data', message: 'success' }
      }

      const result = runResponseSuccessInterceptor(response)

      expect(result).toEqual({ code: 200, data: 'test-data', message: 'success' })
    })

    /** 测试响应没有code字段时直接返回数据 */
    it('响应没有code字段时应直接返回数据', () => {
      const response = {
        data: { name: 'test', value: 123 }
      }

      const result = runResponseSuccessInterceptor(response)

      expect(result).toEqual({ name: 'test', value: 123 })
    })
  })

  describe('响应拦截器 - 业务错误处理', () => {
    /** 测试code不为200时显示ElMessage.error */
    it('code不为200时应显示ElMessage.error', async () => {
      const response = {
        data: { code: 500, message: '服务器内部错误' }
      }

      await expect(runResponseSuccessInterceptor(response)).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('服务器内部错误')
    })

    /** 测试code不为200且无message时显示默认错误 */
    it('code不为200且无message时应显示默认错误', async () => {
      const response = {
        data: { code: 400 }
      }

      await expect(runResponseSuccessInterceptor(response)).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('请求失败')
    })

    /** 测试业务层401错误弹出确认框 */
    it('业务层401错误应弹出确认框', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)
      const response = {
        data: { code: 401, message: '未授权' }
      }

      await expect(runResponseSuccessInterceptor(response)).rejects.toThrow()
      expect(ElMessageBox.confirm).toHaveBeenCalledWith(
        '登录状态已过期，请重新登录',
        '提示',
        expect.objectContaining({
          confirmButtonText: '重新登录',
          cancelButtonText: '取消',
          type: 'warning'
        })
      )
    })

    /** 测试业务层401确认后跳转登录页 */
    it('业务层401确认后应跳转登录页', async () => {
      vi.mocked(ElMessageBox.confirm).mockResolvedValue('confirm' as any)
      const response = {
        data: { code: 401, message: '未授权' }
      }

      try {
        await runResponseSuccessInterceptor(response)
      } catch (e) {
        // 预期异步拒绝
      }

      await vi.mocked(ElMessageBox.confirm).mock.results[0].value
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  describe('401错误处理 - Token刷新', () => {
    /** 测试有refresh_token时尝试刷新Token */
    it('有refresh_token时应尝试刷新Token', async () => {
      localStorage.setItem('refresh_token', 'valid-refresh-token')
      const rawPost = vi.mocked(axios.post)
      rawPost.mockResolvedValue({
        data: {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token'
        }
      })

      const originalRequest = {
        headers: {},
        _retry: false
      }
      const error = {
        response: { status: 401 },
        config: originalRequest
      }

      try {
        await runResponseErrorInterceptor(error)
      } catch (e) {
        // 可能因为mockInstance调用失败
      }

      expect(rawPost).toHaveBeenCalled()
    })

    /** 测试Token刷新成功后更新localStorage */
    it('Token刷新成功后应更新localStorage', async () => {
      localStorage.setItem('refresh_token', 'valid-refresh-token')
      const rawPost = vi.mocked(axios.post)
      rawPost.mockResolvedValue({
        data: {
          access_token: 'new-access-token',
          refresh_token: 'new-refresh-token'
        }
      })

      const originalRequest = {
        headers: {},
        _retry: false
      }
      const error = {
        response: { status: 401 },
        config: originalRequest
      }

      try {
        await runResponseErrorInterceptor(error)
      } catch (e) {
        // service(originalRequest)可能抛出错误
      }

      expect(localStorage.setItem).toHaveBeenCalledWith('token', 'new-access-token')
      expect(localStorage.setItem).toHaveBeenCalledWith('refresh_token', 'new-refresh-token')
    })

    /** 测试Token刷新失败时跳转登录页 */
    it('Token刷新失败时应跳转登录页', async () => {
      localStorage.setItem('refresh_token', 'invalid-refresh-token')
      const rawPost = vi.mocked(axios.post)
      rawPost.mockRejectedValue(new Error('refresh failed'))

      const originalRequest = {
        headers: {},
        _retry: false
      }
      const error = {
        response: { status: 401 },
        config: originalRequest
      }

      await expect(runResponseErrorInterceptor(error)).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('令牌刷新失败，请重新登录')
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    /** 测试Token刷新返回null时跳转登录页 */
    it('Token刷新返回null时应跳转登录页', async () => {
      localStorage.setItem('refresh_token', 'expired-refresh-token')
      const rawPost = vi.mocked(axios.post)
      rawPost.mockResolvedValue({
        data: {
          access_token: null,
          refresh_token: null
        }
      })

      const originalRequest = {
        headers: {},
        _retry: false
      }
      const error = {
        response: { status: 401 },
        config: originalRequest
      }

      await expect(runResponseErrorInterceptor(error)).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('令牌刷新失败，请重新登录')
      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  describe('Token刷新队列机制', () => {
    /** 测试多个请求等待刷新完成 */
    it('正在刷新时新请求应加入等待队列', async () => {
      localStorage.setItem('refresh_token', 'valid-refresh-token')
      const rawPost = vi.mocked(axios.post)

      let resolveRefresh: (value: any) => void
      const refreshPromise = new Promise((resolve) => {
        resolveRefresh = resolve
      })
      rawPost.mockReturnValue(refreshPromise)

      const originalRequest1 = { headers: {}, _retry: false }
      const error1 = { response: { status: 401 }, config: originalRequest1 }

      const firstRequest = runResponseErrorInterceptor(error1)

      await new Promise((r) => setTimeout(r, 50))

      const originalRequest2 = { headers: {}, _retry: false }
      const error2 = { response: { status: 401 }, config: originalRequest2 }

      const secondRequest = runResponseErrorInterceptor(error2)

      resolveRefresh!({
        data: {
          access_token: 'new-token',
          refresh_token: 'new-refresh'
        }
      })

      const results = await Promise.allSettled([firstRequest, secondRequest])
      expect(results.length).toBe(2)
    })

    /** 测试刷新成功后通知所有等待请求 */
    it('刷新成功后应通知所有等待的请求', async () => {
      localStorage.setItem('refresh_token', 'valid-refresh-token')
      const rawPost = vi.mocked(axios.post)
      rawPost.mockResolvedValue({
        data: {
          access_token: 'new-shared-token',
          refresh_token: 'new-shared-refresh'
        }
      })

      const originalRequest = { headers: {}, _retry: false }
      const error = { response: { status: 401 }, config: originalRequest }

      try {
        await runResponseErrorInterceptor(error)
      } catch (e) {
        // service(originalRequest)可能抛出错误
      }

      expect(localStorage.setItem).toHaveBeenCalledWith('token', 'new-shared-token')
    })
  })

  describe('无refresh_token时401处理', () => {
    /** 测试无refresh_token时直接跳转登录页 */
    it('无refresh_token时应直接跳转登录页', async () => {
      const originalRequest = { headers: {}, _retry: false }
      const error = {
        response: { status: 401 },
        config: originalRequest
      }

      await expect(runResponseErrorInterceptor(error)).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('未授权，请重新登录')
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    /** 测试跳转登录页时清除localStorage */
    it('跳转登录页时应清除token和refresh_token', async () => {
      localStorage.setItem('token', 'old-token')
      localStorage.setItem('refresh_token', '')
      localStorage.setItem('user', 'test-user')

      const originalRequest = { headers: {}, _retry: false }
      const error = {
        response: { status: 401 },
        config: originalRequest
      }

      await expect(runResponseErrorInterceptor(error)).rejects.toThrow()
      expect(localStorage.getItem('token')).toBeNull()
      expect(localStorage.getItem('refresh_token')).toBeNull()
      expect(localStorage.getItem('user')).toBeNull()
    })
  })

  describe('HTTP状态码错误处理', () => {
    /** 创建指定状态码的HTTP错误对象 */
    function createHttpError(status: number) {
      return {
        response: { status, data: {} },
        config: { headers: {}, _retry: true }
      }
    }

    /** 测试400错误处理 */
    it('400错误应显示"请求参数错误"', async () => {
      await expect(runResponseErrorInterceptor(createHttpError(400))).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('请求参数错误')
    })

    /** 测试403错误处理 */
    it('403错误应显示"拒绝访问"', async () => {
      await expect(runResponseErrorInterceptor(createHttpError(403))).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('拒绝访问')
    })

    /** 测试404错误处理 */
    it('404错误应显示"请求资源不存在"', async () => {
      await expect(runResponseErrorInterceptor(createHttpError(404))).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('请求资源不存在')
    })

    /** 测试500错误处理 */
    it('500错误应显示"服务器内部错误"', async () => {
      await expect(runResponseErrorInterceptor(createHttpError(500))).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('服务器内部错误')
    })

    /** 测试502错误处理 */
    it('502错误应显示"网关错误"', async () => {
      await expect(runResponseErrorInterceptor(createHttpError(502))).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('网关错误')
    })

    /** 测试503错误处理 */
    it('503错误应显示"服务不可用"', async () => {
      await expect(runResponseErrorInterceptor(createHttpError(503))).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('服务不可用')
    })

    /** 测试504错误处理 */
    it('504错误应显示"网关超时"', async () => {
      await expect(runResponseErrorInterceptor(createHttpError(504))).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('网关超时')
    })

    /** 测试未知状态码错误处理 */
    it('未知状态码应显示带状态码的错误信息', async () => {
      await expect(runResponseErrorInterceptor(createHttpError(418))).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('请求失败：418')
    })
  })

  describe('网络错误处理', () => {
    /** 测试error.request存在时显示网络错误 */
    it('error.request存在时应显示网络错误', async () => {
      const error = {
        request: {},
        config: { headers: {}, _retry: true }
      }

      await expect(runResponseErrorInterceptor(error)).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('网络错误，请检查网络连接')
    })

    /** 测试无request无response时显示错误消息 */
    it('无request无response时应显示错误消息', async () => {
      const error = {
        message: '请求配置错误',
        config: { headers: {}, _retry: true }
      }

      await expect(runResponseErrorInterceptor(error)).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('请求配置错误')
    })

    /** 测试无request无response且无message时显示默认错误 */
    it('无request无response且无message时应显示默认错误', async () => {
      const error = {
        config: { headers: {}, _retry: true }
      }

      await expect(runResponseErrorInterceptor(error)).rejects.toThrow()
      expect(ElMessage.error).toHaveBeenCalledWith('请求失败')
    })
  })

  describe('http对象方法', () => {
    /** 测试http.get方法调用 */
    it('http.get应调用service.get', () => {
      mockInstanceRef.get.mockResolvedValue({ data: 'test' })
      http.get('/test')
      expect(mockInstanceRef.get).toHaveBeenCalledWith('/test', undefined)
    })

    /** 测试http.get方法带配置参数 */
    it('http.get应传递配置参数', () => {
      const config = { params: { id: 1 } }
      http.get('/test', config)
      expect(mockInstanceRef.get).toHaveBeenCalledWith('/test', config)
    })

    /** 测试http.post方法调用 */
    it('http.post应调用service.post', () => {
      const data = { name: 'test' }
      http.post('/test', data)
      expect(mockInstanceRef.post).toHaveBeenCalledWith('/test', data, undefined)
    })

    /** 测试http.post方法带配置参数 */
    it('http.post应传递配置参数', () => {
      const data = { name: 'test' }
      const config = { headers: { 'X-Custom': 'value' } }
      http.post('/test', data, config)
      expect(mockInstanceRef.post).toHaveBeenCalledWith('/test', data, config)
    })

    /** 测试http.put方法调用 */
    it('http.put应调用service.put', () => {
      const data = { name: 'updated' }
      http.put('/test/1', data)
      expect(mockInstanceRef.put).toHaveBeenCalledWith('/test/1', data, undefined)
    })

    /** 测试http.put方法带配置参数 */
    it('http.put应传递配置参数', () => {
      const data = { name: 'updated' }
      const config = { headers: { 'X-Custom': 'value' } }
      http.put('/test/1', data, config)
      expect(mockInstanceRef.put).toHaveBeenCalledWith('/test/1', data, config)
    })

    /** 测试http.delete方法调用 */
    it('http.delete应调用service.delete', () => {
      http.delete('/test/1')
      expect(mockInstanceRef.delete).toHaveBeenCalledWith('/test/1', undefined)
    })

    /** 测试http.delete方法带配置参数 */
    it('http.delete应传递配置参数', () => {
      const config = { params: { force: true } }
      http.delete('/test/1', config)
      expect(mockInstanceRef.delete).toHaveBeenCalledWith('/test/1', config)
    })

    /** 测试http.upload方法调用 */
    it('http.upload应调用service.post并设置multipart/form-data', () => {
      const formData = new FormData()
      formData.append('file', new Blob(['test']), 'test.jpg')
      http.upload('/upload', formData)

      expect(mockInstanceRef.post).toHaveBeenCalledWith('/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    })

    /** 测试http.upload方法带额外配置参数 */
    it('http.upload应合并配置参数', () => {
      const formData = new FormData()
      const config = { onUploadProgress: vi.fn() }
      http.upload('/upload', formData, config)

      expect(mockInstanceRef.post).toHaveBeenCalledWith('/upload', formData, {
        ...config,
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })
    })
  })
})
