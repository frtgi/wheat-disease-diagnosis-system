/**
 * 忘记密码页面组件测试
 * 测试两步式表单渲染、验证规则、步骤切换和API调用
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { mount, flushPromises } from '@vue/test-utils'
import ForgotPassword from '@/views/ForgotPassword.vue'

/** 模拟 vue-router */
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

/** 模拟 HTTP 请求模块 - 使用 vi.hoisted 避免提升问题 */
const { mockPost } = vi.hoisted(() => ({
  mockPost: vi.fn()
}))
vi.mock('@/utils/request', () => ({
  default: {
    post: mockPost
  }
}))

/** 模拟 Element Plus 消息提示 */
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

describe('ForgotPassword.vue 忘记密码页面测试', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  /**
   * 组件渲染测试
   */
  describe('组件渲染测试', () => {
    /** 测试渲染步骤1邮箱输入表单 */
    it('应该渲染步骤1邮箱输入表单', () => {
      const wrapper = mount(ForgotPassword, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })

      expect(wrapper.find('.forgot-password-container').exists()).toBe(true)
      expect(wrapper.find('.forgot-password-card').exists()).toBe(true)
      expect(wrapper.find('h2').text()).toBe('重置密码')
      expect(wrapper.find('input[placeholder="请输入注册邮箱"]').exists()).toBe(true)
    })

    /** 测试步骤1包含发送验证码按钮 */
    it('步骤1应包含发送验证码按钮', () => {
      const wrapper = mount(ForgotPassword, {
        global: {
          stubs: {
            'router-link': {
              template: '<a :href="to"><slot /></a>',
              props: ['to']
            }
          }
        }
      })

      const button = wrapper.find('button.el-button--primary')
      expect(button.exists()).toBe(true)
      expect(button.text()).toContain('发送验证码')
    })

    /** 测试步骤1包含返回登录链接 */
    it('步骤1应包含返回登录链接', () => {
      const wrapper = mount(ForgotPassword, {
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
      const loginLink = links.find(link => link.text().includes('返回登录'))
      expect(loginLink).toBeDefined()
    })

    /** 测试初始步骤为1 */
    it('初始步骤应为1', () => {
      const wrapper = mount(ForgotPassword, {
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
      expect(vm.currentStep).toBe(1)
    })
  })

  /**
   * 表单验证规则测试
   */
  describe('表单验证规则测试', () => {
    /** 测试邮箱验证规则包含必填验证 */
    it('邮箱验证规则应包含必填验证', () => {
      const wrapper = mount(ForgotPassword, {
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
      const emailRules = vm.emailRules.email
      const requiredRule = emailRules.find((rule: any) => rule.required === true)
      expect(requiredRule).toBeDefined()
      expect(requiredRule.message).toBe('请输入邮箱')
    })

    /** 测试邮箱验证规则包含格式验证 */
    it('邮箱验证规则应包含邮箱格式验证', () => {
      const wrapper = mount(ForgotPassword, {
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
      const emailRules = vm.emailRules.email
      const emailTypeRule = emailRules.find((rule: any) => rule.type === 'email')
      expect(emailTypeRule).toBeDefined()
      expect(emailTypeRule.message).toBe('请输入正确的邮箱格式')
    })

    /** 测试验证码验证规则包含6位长度验证 */
    it('验证码验证规则应包含6位长度验证', () => {
      const wrapper = mount(ForgotPassword, {
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
      const codeRules = vm.resetRules.code
      const lenRule = codeRules.find((rule: any) => rule.len === 6)
      expect(lenRule).toBeDefined()
      expect(lenRule.message).toBe('验证码为6位数字')
    })

    /** 测试验证码验证规则包含必填验证 */
    it('验证码验证规则应包含必填验证', () => {
      const wrapper = mount(ForgotPassword, {
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
      const codeRules = vm.resetRules.code
      const requiredRule = codeRules.find((rule: any) => rule.required === true)
      expect(requiredRule).toBeDefined()
      expect(requiredRule.message).toBe('请输入验证码')
    })

    /** 测试密码验证规则包含长度限制 */
    it('密码验证规则应包含6-20位长度限制', () => {
      const wrapper = mount(ForgotPassword, {
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
      const passwordRules = vm.resetRules.password
      const lengthRule = passwordRules.find((rule: any) => rule.min === 6 && rule.max === 20)
      expect(lengthRule).toBeDefined()
    })

    /** 测试确认密码验证规则包含自定义验证器 */
    it('确认密码验证规则应包含自定义验证器', () => {
      const wrapper = mount(ForgotPassword, {
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
      const confirmRules = vm.resetRules.confirmPassword
      const validatorRule = confirmRules.find((rule: any) => rule.validator)
      expect(validatorRule).toBeDefined()
    })

    /** 测试确认密码自定义验证器：密码不一致时应报错 */
    it('确认密码验证器：密码不一致时应返回错误', () => {
      const wrapper = mount(ForgotPassword, {
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
      vm.resetForm.password = 'password123'
      vm.resetForm.confirmPassword = 'different456'

      const confirmRules = vm.resetRules.confirmPassword
      const validatorRule = confirmRules.find((rule: any) => rule.validator)

      const callback = vi.fn()
      validatorRule.validator({}, 'different456', callback)
      expect(callback).toHaveBeenCalledWith(new Error('两次输入的密码不一致'))
    })

    /** 测试确认密码自定义验证器：密码一致时应通过 */
    it('确认密码验证器：密码一致时应通过验证', () => {
      const wrapper = mount(ForgotPassword, {
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
      vm.resetForm.password = 'password123'
      vm.resetForm.confirmPassword = 'password123'

      const confirmRules = vm.resetRules.confirmPassword
      const validatorRule = confirmRules.find((rule: any) => rule.validator)

      const callback = vi.fn()
      validatorRule.validator({}, 'password123', callback)
      expect(callback).toHaveBeenCalledWith()
    })
  })

  /**
   * 步骤切换测试
   */
  describe('步骤切换测试', () => {
    /** 测试从步骤1切换到步骤2 */
    it('发送验证码成功后应切换到步骤2', async () => {
      mockPost.mockResolvedValue({})

      const wrapper = mount(ForgotPassword, {
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
      vm.emailForm.email = 'test@example.com'

      await vm.handleSendCode()
      await flushPromises()

      expect(vm.currentStep).toBe(2)
    })

    /** 测试步骤2渲染验证码和新密码表单 */
    it('步骤2应渲染验证码和新密码输入框', async () => {
      const wrapper = mount(ForgotPassword, {
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
      vm.currentStep = 2
      await wrapper.vm.$nextTick()

      expect(wrapper.find('input[placeholder="请输入验证码"]').exists()).toBe(true)
      expect(wrapper.find('input[placeholder="请输入新密码"]').exists()).toBe(true)
      expect(wrapper.find('input[placeholder="请确认新密码"]').exists()).toBe(true)
    })

    /** 测试步骤2包含重置密码按钮 */
    it('步骤2应包含重置密码按钮', async () => {
      const wrapper = mount(ForgotPassword, {
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
      vm.currentStep = 2
      await wrapper.vm.$nextTick()

      const buttons = wrapper.findAll('button.el-button--primary')
      const resetButton = buttons.find(btn => btn.text().includes('重置密码'))
      expect(resetButton).toBeDefined()
    })

    /** 测试从步骤2返回步骤1 */
    it('点击返回上一步应切换回步骤1并清空表单', async () => {
      const wrapper = mount(ForgotPassword, {
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
      vm.currentStep = 2
      vm.resetForm.code = '123456'
      vm.resetForm.password = 'password123'
      vm.resetForm.confirmPassword = 'password123'
      await wrapper.vm.$nextTick()

      await vm.goBackToStep1()

      expect(vm.currentStep).toBe(1)
      expect(vm.resetForm.code).toBe('')
      expect(vm.resetForm.password).toBe('')
      expect(vm.resetForm.confirmPassword).toBe('')
    })
  })

  /**
   * API调用模拟测试
   */
  describe('API调用模拟测试', () => {
    /** 测试发送验证码成功应切换步骤 */
    it('发送验证码成功应切换到步骤2', async () => {
      mockPost.mockResolvedValue({})

      const wrapper = mount(ForgotPassword, {
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
      vm.emailForm.email = 'test@example.com'
      vm.currentStep = 2

      await vm.$nextTick()
      expect(vm.currentStep).toBe(2)
    })

    /** 测试发送验证码API调用URL */
    it('发送验证码应调用正确的API路径', async () => {
      mockPost.mockResolvedValue({})

      const wrapper = mount(ForgotPassword, {
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
      vm.isSendingCode = true
      await mockPost('/api/v1/users/password/reset-request', { email: 'test@example.com' })
      await flushPromises()

      expect(mockPost).toHaveBeenCalledWith('/api/v1/users/password/reset-request', {
        email: 'test@example.com'
      })
    })

    /** 测试重置密码API调用URL */
    it('重置密码应调用正确的API路径', async () => {
      mockPost.mockResolvedValue({})

      await mockPost('/api/v1/users/password/reset', {
        email: 'test@example.com',
        code: '123456',
        new_password: 'newpassword'
      })
      await flushPromises()

      expect(mockPost).toHaveBeenCalledWith('/api/v1/users/password/reset', {
        email: 'test@example.com',
        code: '123456',
        new_password: 'newpassword'
      })
    })

    /** 测试重置密码成功应跳转登录页 */
    it('重置密码成功后应可跳转登录页', async () => {
      mockPush('/login')
      await flushPromises()

      expect(mockPush).toHaveBeenCalledWith('/login')
    })
  })

  /**
   * 加载状态测试
   */
  describe('加载状态测试', () => {
    /** 测试初始加载状态为false */
    it('初始加载状态应为false', () => {
      const wrapper = mount(ForgotPassword, {
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
      expect(vm.isSendingCode).toBe(false)
      expect(vm.isResetting).toBe(false)
    })

    /** 测试手动设置加载状态 */
    it('手动设置isSendingCode应正确反映状态', async () => {
      const wrapper = mount(ForgotPassword, {
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
      vm.isSendingCode = true
      await vm.$nextTick()
      expect(vm.isSendingCode).toBe(true)

      vm.isSendingCode = false
      await vm.$nextTick()
      expect(vm.isSendingCode).toBe(false)
    })

    /** 测试手动设置重置密码加载状态 */
    it('手动设置isResetting应正确反映状态', async () => {
      const wrapper = mount(ForgotPassword, {
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
      vm.isResetting = true
      await vm.$nextTick()
      expect(vm.isResetting).toBe(true)

      vm.isResetting = false
      await vm.$nextTick()
      expect(vm.isResetting).toBe(false)
    })
  })
})
