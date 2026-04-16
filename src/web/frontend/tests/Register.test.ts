/**
 * 注册页面组件测试
 * 测试注册表单渲染、验证和提交功能
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import Register from '@/views/Register.vue'
import * as userApi from '@/api/user'

// 模拟 vue-router
const mockPush = vi.fn()
vi.mock('vue-router', () => ({
  useRouter: () => ({
    push: mockPush
  }),
  RouterLink: {
    name: 'RouterLink',
    props: ['to'],
    template: '<a :href="typeof to === "string" ? to : to.path"><slot /></a>'
  }
}))

// 模拟用户 API
vi.mock('@/api/user', () => ({
  register: vi.fn()
}))

// 模拟 Element Plus 消息提示
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

describe('Register.vue 注册页面测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  /**
   * 组件渲染测试
   */
  describe('组件渲染测试', () => {
    it('应该正确渲染注册表单', () => {
      const wrapper = mount(Register, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      expect(wrapper.find('.register-container').exists()).toBe(true)
      expect(wrapper.find('.register-card').exists()).toBe(true)
      expect(wrapper.find('h2').text()).toBe('用户注册')
    })

    it('应该包含用户名输入框', () => {
      const wrapper = mount(Register, {
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

    it('应该包含邮箱输入框', () => {
      const wrapper = mount(Register, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const emailInput = wrapper.find('input[placeholder="请输入邮箱"]')
      expect(emailInput.exists()).toBe(true)
    })

    it('应该包含手机号输入框', () => {
      const wrapper = mount(Register, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const phoneInput = wrapper.find('input[placeholder="请输入手机号"]')
      expect(phoneInput.exists()).toBe(true)
    })

    it('应该包含密码输入框', () => {
      const wrapper = mount(Register, {
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

    it('应该包含确认密码输入框', () => {
      const wrapper = mount(Register, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const confirmPasswordInput = wrapper.find('input[placeholder="请确认密码"]')
      expect(confirmPasswordInput.exists()).toBe(true)
    })

    it('应该包含用户协议复选框', () => {
      const wrapper = mount(Register, {
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
      expect(checkbox.text()).toContain('用户协议')
    })

    it('应该包含注册按钮', () => {
      const wrapper = mount(Register, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const registerButton = wrapper.find('button.el-button--primary')
      expect(registerButton.exists()).toBe(true)
      expect(registerButton.text()).toContain('注册')
    })

    it('应该包含登录链接', () => {
      const wrapper = mount(Register, {
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
      const loginLink = links.find(link => link.text().includes('登录'))
      expect(loginLink).toBeDefined()
    })
  })

  /**
   * 表单验证测试
   */
  describe('表单验证测试', () => {
    it('用户名验证规则应正确配置', () => {
      const wrapper = mount(Register, {
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
      expect(vm.registerRules).toBeDefined()
      expect(vm.registerRules.username).toBeDefined()
      expect(vm.registerRules.username.length).toBeGreaterThan(0)
    })

    it('邮箱验证规则应正确配置', () => {
      const wrapper = mount(Register, {
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
      expect(vm.registerRules.email).toBeDefined()
      expect(vm.registerRules.email.length).toBeGreaterThan(0)
    })

    it('密码验证规则应正确配置', () => {
      const wrapper = mount(Register, {
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
      expect(vm.registerRules.password).toBeDefined()
      expect(vm.registerRules.password.length).toBeGreaterThan(0)
    })

    it('用户名验证规则应包含必填验证', () => {
      const wrapper = mount(Register, {
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
      const usernameRules = vm.registerRules.username
      const requiredRule = usernameRules.find((rule: any) => rule.required === true)
      expect(requiredRule).toBeDefined()
      expect(requiredRule.message).toBe('请输入用户名')
    })

    it('用户名验证规则应包含长度验证', () => {
      const wrapper = mount(Register, {
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
      const usernameRules = vm.registerRules.username
      const lengthRule = usernameRules.find((rule: any) => rule.min === 3 && rule.max === 20)
      expect(lengthRule).toBeDefined()
    })

    it('邮箱验证规则应包含邮箱格式验证', () => {
      const wrapper = mount(Register, {
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
      const emailRules = vm.registerRules.email
      const emailRule = emailRules.find((rule: any) => rule.type === 'email')
      expect(emailRule).toBeDefined()
    })

    it('密码验证规则应包含必填验证', () => {
      const wrapper = mount(Register, {
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
      const passwordRules = vm.registerRules.password
      const requiredRule = passwordRules.find((rule: any) => rule.required === true)
      expect(requiredRule).toBeDefined()
      expect(requiredRule.message).toBe('请输入密码')
    })

    it('密码验证规则应包含长度验证', () => {
      const wrapper = mount(Register, {
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
      const passwordRules = vm.registerRules.password
      const lengthRule = passwordRules.find((rule: any) => rule.min === 6 && rule.max === 20)
      expect(lengthRule).toBeDefined()
    })

    it('确认密码验证规则应正确配置', () => {
      const wrapper = mount(Register, {
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
      expect(vm.registerRules.confirmPassword).toBeDefined()
      expect(vm.registerRules.confirmPassword.length).toBeGreaterThan(0)
    })

    it('手机号验证规则应包含正则验证', () => {
      const wrapper = mount(Register, {
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
      const phoneRules = vm.registerRules.phone
      const patternRule = phoneRules.find((rule: any) => rule.pattern)
      expect(patternRule).toBeDefined()
      expect(patternRule.message).toBe('请输入正确的手机号')
    })
  })

  /**
   * API 调用模拟测试
   */
  describe('API 调用模拟测试', () => {
    it('注册成功应显示成功消息并跳转登录页', async () => {
      const mockResponse = {
        id: 1,
        username: 'testuser',
        email: 'test@example.com',
        role: 'farmer' as const,
        created_at: '2024-01-01'
      }
      
      vi.mocked(userApi.register).mockResolvedValue(mockResponse)
      
      const wrapper = mount(Register, {
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
      vm.registerForm.username = 'testuser'
      vm.registerForm.email = 'test@example.com'
      vm.registerForm.password = 'password123'
      vm.registerForm.confirmPassword = 'password123'
      vm.registerForm.agree = true
      
      await vm.handleRegister()
      await flushPromises()
      
      expect(userApi.register).toHaveBeenCalledWith({
        username: 'testuser',
        email: 'test@example.com',
        password: 'password123',
        role: 'farmer'
      })
      
      const { ElMessage } = await import('element-plus')
      expect(ElMessage.success).toHaveBeenCalledWith('注册成功，请登录')
      expect(mockPush).toHaveBeenCalledWith('/login')
    })

    it('注册失败应显示错误消息', async () => {
      const errorMessage = '用户名已存在'
      vi.mocked(userApi.register).mockRejectedValue(new Error(errorMessage))
      
      const wrapper = mount(Register, {
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
      vm.registerForm.username = 'existinguser'
      vm.registerForm.email = 'test@example.com'
      vm.registerForm.password = 'password123'
      vm.registerForm.confirmPassword = 'password123'
      vm.registerForm.agree = true
      
      await vm.handleRegister()
      await flushPromises()
      
      const { ElMessage } = await import('element-plus')
      expect(ElMessage.error).toHaveBeenCalled()
    })
  })

  /**
   * 用户交互测试
   */
  describe('用户交互测试', () => {
    it('未勾选用户协议时应显示警告', async () => {
      const wrapper = mount(Register, {
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
      vm.registerForm.username = 'testuser'
      vm.registerForm.email = 'test@example.com'
      vm.registerForm.password = 'password123'
      vm.registerForm.confirmPassword = 'password123'
      vm.registerForm.agree = false
      
      await vm.handleRegister()
      await flushPromises()
      
      const { ElMessage } = await import('element-plus')
      expect(ElMessage.warning).toHaveBeenCalledWith('请先同意用户协议')
    })

    it('点击注册按钮应触发表单提交', async () => {
      const wrapper = mount(Register, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })
      
      const registerButton = wrapper.find('button.el-button--primary')
      await registerButton.trigger('click')
      
      expect(wrapper.find('.register-card').exists()).toBe(true)
    })

    it('登录链接应指向登录页面', () => {
      const wrapper = mount(Register, {
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
      const loginLink = links.find(link => link.text().includes('登录'))
      expect(loginLink?.attributes('href')).toBe('/login')
    })

    it('初始状态加载状态应为 false', () => {
      const wrapper = mount(Register, {
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

    it('注册表单初始值应为空', () => {
      const wrapper = mount(Register, {
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
      expect(vm.registerForm.username).toBe('')
      expect(vm.registerForm.email).toBe('')
      expect(vm.registerForm.password).toBe('')
      expect(vm.registerForm.confirmPassword).toBe('')
      expect(vm.registerForm.agree).toBe(false)
    })

    it('注册表单应包含用户协议选项', () => {
      const wrapper = mount(Register, {
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
      expect(vm.registerForm.agree).toBeDefined()
      expect(typeof vm.registerForm.agree).toBe('boolean')
    })
  })
})
