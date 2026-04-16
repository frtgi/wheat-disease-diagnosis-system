/**
 * 用户 API 模块测试
 * 测试 user.ts 中所有 API 调用函数的请求参数、URL、方法和响应解析
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import {
  login,
  register,
  getCurrentUser,
  logout,
  saveUserInfo,
  getUserInfo,
  refreshToken,
  requestPasswordReset,
  resetPassword,
  getSessions,
  terminateSession
} from '@/api/user'
import type { LoginResponse, User, RefreshTokenResponse, Session } from '@/api/user'

/** Mock http 模块，拦截所有网络请求 */
vi.mock('@/utils/request', () => ({
  http: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn()
  }
}))

import { http } from '@/utils/request'

const mockHttp = vi.mocked(http)

describe('user API 模块测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('login - 用户登录', () => {
    /** 测试登录应发送 POST 请求并返回 Token 和用户信息 */
    it('应发送 POST 请求到 /users/login 并返回登录响应', async () => {
      const mockUser: User = {
        id: 1,
        username: 'farmer1',
        email: 'farmer@test.com',
        role: 'farmer',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
      const mockResponse: LoginResponse = {
        access_token: 'jwt-token-abc',
        refresh_token: 'refresh-token-xyz',
        token_type: 'bearer',
        user: mockUser
      }
      mockHttp.post.mockResolvedValue(mockResponse)

      const result = await login({ username: 'farmer1', password: '123456' })

      expect(mockHttp.post).toHaveBeenCalledTimes(1)
      expect(mockHttp.post).toHaveBeenCalledWith('/users/login', {
        username: 'farmer1',
        password: '123456'
      })
      expect(result.access_token).toBe('jwt-token-abc')
      expect(result.token_type).toBe('bearer')
      expect(result.user.username).toBe('farmer1')
    })

    /** 测试登录响应数据完整解析 */
    it('应正确解析包含 refresh_token 的登录响应', async () => {
      const mockResponse: LoginResponse = {
        access_token: 'access-123',
        refresh_token: 'refresh-456',
        token_type: 'bearer',
        user: {
          id: 2,
          username: 'admin',
          email: 'admin@test.com',
          role: 'admin',
          is_active: true,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z'
        }
      }
      mockHttp.post.mockResolvedValue(mockResponse)

      const result = await login({ username: 'admin', password: 'admin123' })

      expect(result.refresh_token).toBe('refresh-456')
      expect(result.user.role).toBe('admin')
    })
  })

  describe('register - 用户注册', () => {
    /** 测试注册应发送 POST 请求 */
    it('应发送 POST 请求到 /users/register', async () => {
      const mockUser: User = {
        id: 3,
        username: 'newuser',
        email: 'new@test.com',
        role: 'farmer',
        is_active: true,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z'
      }
      mockHttp.post.mockResolvedValue(mockUser)

      const result = await register({
        username: 'newuser',
        email: 'new@test.com',
        password: 'password123'
      })

      expect(mockHttp.post).toHaveBeenCalledWith('/users/register', {
        username: 'newuser',
        email: 'new@test.com',
        password: 'password123'
      })
      expect(result.username).toBe('newuser')
    })

    /** 测试注册时指定角色默认值 */
    it('应支持指定角色参数', async () => {
      const mockUser: User = {
        id: 4,
        username: 'tech1',
        email: 'tech@test.com',
        role: 'technician',
        is_active: true,
        created_at: '2024-01-03T00:00:00Z',
        updated_at: '2024-01-03T00:00:00Z'
      }
      mockHttp.post.mockResolvedValue(mockUser)

      const result = await register({
        username: 'tech1',
        email: 'tech@test.com',
        password: 'password123',
        role: 'technician'
      })

      expect(mockHttp.post).toHaveBeenCalledWith('/users/register', expect.objectContaining({
        role: 'technician'
      }))
      expect(result.role).toBe('technician')
    })

    /** 测试不指定角色时请求体不包含 role 字段 */
    it('不指定角色时请求体不应包含 role 字段', async () => {
      mockHttp.post.mockResolvedValue({} as User)

      await register({
        username: 'user1',
        email: 'user1@test.com',
        password: 'pass123'
      })

      const calledData = mockHttp.post.mock.calls[0][1]
      expect(calledData).not.toHaveProperty('role')
    })
  })

  describe('getCurrentUser - 获取当前用户信息', () => {
    /** 测试获取当前用户应发送 GET 请求 */
    it('应发送 GET 请求到 /users/me', async () => {
      const mockUser: User = {
        id: 1,
        username: 'farmer1',
        email: 'farmer@test.com',
        role: 'farmer',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
      mockHttp.get.mockResolvedValue(mockUser)

      const result = await getCurrentUser()

      expect(mockHttp.get).toHaveBeenCalledTimes(1)
      expect(mockHttp.get).toHaveBeenCalledWith('/users/me')
      expect(result).toEqual(mockUser)
    })
  })

  describe('logout - 用户登出', () => {
    /** 测试登出应调用 localStorage.removeItem 移除 token、refresh_token 和 user */
    it('应调用 localStorage.removeItem 移除 token、refresh_token 和 user', () => {
      logout()

      expect(localStorage.removeItem).toHaveBeenCalledWith('token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('refresh_token')
      expect(localStorage.removeItem).toHaveBeenCalledWith('user')
    })

    /** 测试登出不应发送任何 HTTP 请求 */
    it('不应发送任何 HTTP 请求', () => {
      logout()

      expect(mockHttp.post).not.toHaveBeenCalled()
      expect(mockHttp.get).not.toHaveBeenCalled()
    })
  })

  describe('saveUserInfo - 保存用户信息到本地', () => {
    /** 测试保存用户信息应调用 localStorage.setItem 并传入序列化后的 JSON */
    it('应将用户信息序列化为 JSON 并调用 localStorage.setItem', () => {
      const user: User = {
        id: 1,
        username: 'farmer1',
        email: 'farmer@test.com',
        role: 'farmer',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }

      saveUserInfo(user)

      expect(localStorage.setItem).toHaveBeenCalledWith('user', JSON.stringify(user))
    })
  })

  describe('getUserInfo - 从本地获取用户信息', () => {
    /** 测试 localStorage 中有数据时应调用 getItem 并正确解析返回 */
    it('应调用 localStorage.getItem 并正确解析用户信息', () => {
      const user: User = {
        id: 1,
        username: 'farmer1',
        email: 'farmer@test.com',
        role: 'farmer',
        is_active: true,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z'
      }
      vi.mocked(localStorage.getItem).mockReturnValue(JSON.stringify(user))

      const result = getUserInfo()

      expect(localStorage.getItem).toHaveBeenCalledWith('user')
      expect(result).toEqual(user)
    })

    /** 测试 localStorage 中无数据时应返回 null */
    it('localStorage 中无数据时应返回 null', () => {
      vi.mocked(localStorage.getItem).mockReturnValue(null)

      const result = getUserInfo()

      expect(result).toBeNull()
    })

    /** 测试 localStorage 中数据损坏时应返回 null */
    it('localStorage 中数据格式错误时应返回 null', () => {
      vi.mocked(localStorage.getItem).mockReturnValue('invalid-json{{{')

      const result = getUserInfo()

      expect(result).toBeNull()
    })
  })

  describe('refreshToken - 刷新访问令牌', () => {
    /** 测试刷新令牌应发送 POST 请求并传递 refresh_token */
    it('应发送 POST 请求到 /users/token/refresh', async () => {
      const mockResponse: RefreshTokenResponse = {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
        token_type: 'bearer'
      }
      mockHttp.post.mockResolvedValue(mockResponse)

      const result = await refreshToken('old-refresh-token')

      expect(mockHttp.post).toHaveBeenCalledTimes(1)
      expect(mockHttp.post).toHaveBeenCalledWith('/users/token/refresh', {
        refresh_token: 'old-refresh-token'
      })
      expect(result.access_token).toBe('new-access-token')
      expect(result.refresh_token).toBe('new-refresh-token')
    })
  })

  describe('requestPasswordReset - 请求密码重置', () => {
    /** 测试请求密码重置应发送 POST 请求并传递邮箱 */
    it('应发送 POST 请求到 /users/password/reset-request', async () => {
      const mockResponse = { message: '重置链接已发送' }
      mockHttp.post.mockResolvedValue(mockResponse)

      const result = await requestPasswordReset('user@test.com')

      expect(mockHttp.post).toHaveBeenCalledWith('/users/password/reset-request', {
        email: 'user@test.com'
      })
      expect(result.message).toBe('重置链接已发送')
    })
  })

  describe('resetPassword - 执行密码重置', () => {
    /** 测试执行密码重置应发送 POST 请求并传递 token 和新密码 */
    it('应发送 POST 请求到 /users/password/reset', async () => {
      const mockResponse = { message: '密码重置成功' }
      mockHttp.post.mockResolvedValue(mockResponse)

      const result = await resetPassword({
        token: 'reset-token-abc',
        new_password: 'newPass123'
      })

      expect(mockHttp.post).toHaveBeenCalledWith('/users/password/reset', {
        token: 'reset-token-abc',
        new_password: 'newPass123'
      })
      expect(result.message).toBe('密码重置成功')
    })
  })

  describe('getSessions - 获取用户会话列表', () => {
    /** 测试获取会话列表应发送 GET 请求 */
    it('应发送 GET 请求到 /users/sessions/list', async () => {
      const mockSessions: Session[] = [
        {
          id: 'sess-1',
          user_agent: 'Chrome/120',
          ip_address: '192.168.1.1',
          created_at: '2024-01-01T00:00:00Z',
          last_activity: '2024-01-02T00:00:00Z',
          is_current: true
        },
        {
          id: 'sess-2',
          user_agent: 'Firefox/121',
          ip_address: '10.0.0.1',
          created_at: '2024-01-01T00:00:00Z',
          last_activity: '2024-01-01T12:00:00Z',
          is_current: false
        }
      ]
      mockHttp.get.mockResolvedValue(mockSessions)

      const result = await getSessions()

      expect(mockHttp.get).toHaveBeenCalledTimes(1)
      expect(mockHttp.get).toHaveBeenCalledWith('/users/sessions/list')
      expect(result).toHaveLength(2)
      expect(result[0].is_current).toBe(true)
    })
  })

  describe('terminateSession - 终止指定会话', () => {
    /** 测试终止会话应发送 DELETE 请求并拼接会话 ID */
    it('应发送 DELETE 请求到 /users/sessions/:sessionId', async () => {
      const mockResponse = { message: '会话已终止' }
      mockHttp.delete.mockResolvedValue(mockResponse)

      const result = await terminateSession('sess-1')

      expect(mockHttp.delete).toHaveBeenCalledTimes(1)
      expect(mockHttp.delete).toHaveBeenCalledWith('/users/sessions/sess-1')
      expect(result.message).toBe('会话已终止')
    })

    /** 测试不同会话 ID 的路径拼接 */
    it('应正确拼接不同会话 ID 到 URL', async () => {
      mockHttp.delete.mockResolvedValue({ message: 'ok' })

      await terminateSession('abc-999')

      expect(mockHttp.delete).toHaveBeenCalledWith('/users/sessions/abc-999')
    })
  })
})
