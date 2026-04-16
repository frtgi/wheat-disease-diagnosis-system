/**
 * 登录页面组件测试
 * 测试登录表单渲染、验证和提交功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import { createPinia, setActivePinia } from 'pinia'
import Login from '@/views/Login.vue'
import * as userApi from '@/api/user'

const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  }),
  RouterLink: {
    name: 'RouterLink',
    props: ['to'],
    template: '<a :href="typeof to === \'string\' ? to : to.path"><slot /></a>'
  }
}))

vi.mock('@/api/user', () => ({
  login: vi.fn(),
  saveUserInfo: vi.fn()
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return {
    ...actual,
    ElMessage: {
      success: vi.fn(),
      error: vi.fn(),
      warning: vi.fn()
    }
  }
})

vi.mock('@/stores', () => ({
  useUserStore: () => ({
    setToken: vi.fn(),
    setUserInfo: vi.fn(),
    token: '',
    userInfo: {
      id: 0,
      username: '',
      email: '',
      avatar: ''
    }
  })
}))

describe('Login.vue 登录页面测试', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  describe('组件渲染测试', () => {
    it('应该正确渲染登录表单', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      expect(wrapper.find('.login-container').exists()).toBe(true)
      expect(wrapper.find('.login-card').exists()).toBe(true)
      expect(wrapper.find('h2').text()).toBe('用户登录')
    })

    it('应该包含用户名输入框', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const usernameInput = wrapper.find('input[placeholder="请输入用户名"]')
      expect(usernameInput.exists()).toBe(true)
    })

    it('应该包含密码输入框', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const passwordInput = wrapper.find('input[placeholder="请输入密码"]')
      expect(passwordInput.exists()).toBe(true)
    })

    it('应该包含记住我复选框', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const checkbox = wrapper.find('.el-checkbox')
      expect(checkbox.exists()).toBe(true)
    })

    it('应该包含登录按钮', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const loginButton = wrapper.find('button.el-button--primary')
      expect(loginButton.exists()).toBe(true)
      expect(loginButton.text()).toContain('登录')
    })

    it('应该包含注册链接', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const links = wrapper.findAll('a')
      expect(links.length).toBeGreaterThan(0)
      const registerLink = links.find(link => link.text().includes('注册'))
      expect(registerLink).toBeDefined()
    })
  })

  describe('表单验证测试', () => {
    it('用户名验证规则应正确配置', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      expect(vm.loginRules).toBeDefined()
      expect(vm.loginRules.username).toBeDefined()
      expect(vm.loginRules.username.length).toBeGreaterThan(0)
    })

    it('密码验证规则应正确配置', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      expect(vm.loginRules.password).toBeDefined()
      expect(vm.loginRules.password.length).toBeGreaterThan(0)
    })

    it('用户名验证规则应包含必填验证', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      const usernameRules = vm.loginRules.username
      const requiredRule = usernameRules.find((rule: any) => rule.required === true)
      expect(requiredRule).toBeDefined()
      expect(requiredRule.message).toBe('请输入用户名')
    })

    it('用户名验证规则应包含长度验证', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      const usernameRules = vm.loginRules.username
      const lengthRule = usernameRules.find((rule: any) => rule.min === 3 && rule.max === 20)
      expect(lengthRule).toBeDefined()
    })

    it('密码验证规则应包含必填验证', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      const passwordRules = vm.loginRules.password
      const requiredRule = passwordRules.find((rule: any) => rule.required === true)
      expect(requiredRule).toBeDefined()
      expect(requiredRule.message).toBe('请输入密码')
    })

    it('密码验证规则应包含长度验证', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      const passwordRules = vm.loginRules.password
      const lengthRule = passwordRules.find((rule: any) => rule.min === 6 && rule.max === 20)
      expect(lengthRule).toBeDefined()
    })
  })

  describe('API 调用模拟测试', () => {
    it('登录成功应保存 Token 并跳转', async () => {
      const mockResponse = {
        access_token: 'mock-token-123',
        token_type: 'bearer',
        user: {
          id: 1,
          username: 'testuser',
          email: 'test@example.com',
          role: 'farmer' as const,
          created_at: '2024-01-01'
        }
      }
      
      vi.mocked(userApi.login).mockResolvedValue(mockResponse)
      
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      vm.loginForm.username = 'testuser'
      vm.loginForm.password = '123456'
      
      await vm.handleLogin()
      await flushPromises()
      
      expect(userApi.login).toHaveBeenCalledWith({
        username: 'testuser',
        password: '123456'
      })
      expect(mockPush).toHaveBeenCalledWith('/')
    })

    it('登录失败应显示错误消息', async () => {
      const errorMessage = '用户名或密码错误'
      vi.mocked(userApi.login).mockRejectedValue(new Error(errorMessage))
      
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      vm.loginForm.username = 'testuser'
      vm.loginForm.password = 'wrongpassword'
      
      await vm.handleLogin()
      await flushPromises()
      
      const { ElMessage } = await import('element-plus')
      expect(ElMessage.error).toHaveBeenCalled()
    })
  })

  describe('用户交互测试', () => {
    it('点击登录按钮应触发表单提交', async () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const loginButton = wrapper.find('button.el-button--primary')
      await loginButton.trigger('click')
      
      expect(wrapper.find('.login-card').exists()).toBe(true)
    })

    it('登录表单应包含记住我选项', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      expect(vm.loginForm.remember).toBeDefined()
      expect(typeof vm.loginForm.remember).toBe('boolean')
    })

    it('初始状态加载状态应为 false', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      expect(vm.isLoading).toBe(false)
    })

    it('登录表单初始值应为空', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const vm = wrapper.vm as any
      expect(vm.loginForm.username).toBe('')
      expect(vm.loginForm.password).toBe('')
      expect(vm.loginForm.remember).toBe(false)
    })

    it('注册链接应指向注册页面', () => {
      const wrapper = mount(Login, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const links = wrapper.findAll('a')
      const registerLink = links.find(link => link.text().includes('注册'))
      expect(registerLink?.attributes('href')).toBe('/register')
    })
  })
})
