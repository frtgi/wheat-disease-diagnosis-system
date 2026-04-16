<template>
  <div class="forgot-password-container">
    <el-card class="forgot-password-card">
      <template #header>
        <h2>重置密码</h2>
      </template>

      <!-- 步骤1：输入邮箱 -->
      <div v-if="currentStep === 1">
        <el-form
          ref="emailFormRef"
          :model="emailForm"
          :rules="emailRules"
          label-width="80px"
        >
          <el-form-item label="邮箱" prop="email">
            <el-input
              v-model="emailForm.email"
              placeholder="请输入注册邮箱"
              clearable
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              :loading="isSendingCode"
              style="width: 100%"
              @click="handleSendCode"
            >
              发送重置令牌
            </el-button>
          </el-form-item>
        </el-form>
      </div>

      <!-- 步骤2：输入重置令牌和新密码 -->
      <div v-else>
        <el-form
          ref="resetFormRef"
          :model="resetForm"
          :rules="resetRules"
          label-width="80px"
        >
          <el-form-item label="邮箱">
            <el-input :value="emailForm.email" disabled />
          </el-form-item>

          <el-form-item label="重置令牌" prop="token">
            <el-input
              v-model="resetForm.token"
              placeholder="请输入邮箱收到的重置令牌"
              clearable
            />
          </el-form-item>

          <el-form-item label="新密码" prop="password">
            <el-input
              v-model="resetForm.password"
              type="password"
              placeholder="请输入新密码"
              show-password
            />
          </el-form-item>

          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="resetForm.confirmPassword"
              type="password"
              placeholder="请确认新密码"
              show-password
              @keyup.enter="handleResetPassword"
            />
          </el-form-item>

          <el-form-item>
            <el-button
              type="primary"
              :loading="isResetting"
              style="width: 100%"
              @click="handleResetPassword"
            >
              重置密码
            </el-button>
          </el-form-item>
        </el-form>

        <div class="back-link">
          <el-button type="text" @click="goBackToStep1">
            返回上一步
          </el-button>
        </div>
      </div>

      <div class="links">
        <router-link to="/login">返回登录</router-link>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { requestPasswordReset, resetPassword } from '@/api/user'

const router = useRouter()

// 当前步骤
const currentStep = ref(1)

// 邮箱表单引用
const emailFormRef = ref<FormInstance>()

// 重置表单引用
const resetFormRef = ref<FormInstance>()

// 发送重置请求加载状态
const isSendingCode = ref(false)

// 重置密码加载状态
const isResetting = ref(false)

// 邮箱表单
const emailForm = reactive({
  email: ''
})

// 重置表单
const resetForm = reactive({
  token: '',
  password: '',
  confirmPassword: ''
})

// 邮箱验证规则
const emailRules: FormRules = {
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ]
}

/**
 * 自定义验证器：确认密码
 */
const validateConfirmPassword = (rule: any, value: string, callback: any) => {
  if (value !== resetForm.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

// 重置表单验证规则
const resetRules: FormRules = {
  token: [
    { required: true, message: '请输入重置令牌', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请确认新密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' }
  ]
}

/**
 * 发送密码重置请求
 */
const handleSendCode = async () => {
  if (!emailFormRef.value) return

  await emailFormRef.value.validate(async (valid) => {
    if (valid) {
      isSendingCode.value = true
      try {
        await requestPasswordReset(emailForm.email)
        
        ElMessage.success('重置令牌已发送到您的邮箱')
        currentStep.value = 2
      } catch (error: unknown) {
        console.error('发送重置请求失败:', error)
        const msg = error instanceof Error ? error.message : '发送重置请求失败，请稍后重试'
        ElMessage.error(msg)
      } finally {
        isSendingCode.value = false
      }
    }
  })
}

/**
 * 执行密码重置
 */
const handleResetPassword = async () => {
  if (!resetFormRef.value) return

  await resetFormRef.value.validate(async (valid) => {
    if (valid) {
      isResetting.value = true
      try {
        await resetPassword({
          token: resetForm.token,
          new_password: resetForm.password
        })
        
        ElMessage.success('密码重置成功，请登录')
        router.push('/login')
      } catch (error: unknown) {
        console.error('重置密码失败:', error)
        const msg = error instanceof Error ? error.message : '重置密码失败，请稍后重试'
        ElMessage.error(msg)
      } finally {
        isResetting.value = false
      }
    }
  })
}

/**
 * 返回步骤1
 */
const goBackToStep1 = () => {
  currentStep.value = 1
  resetForm.token = ''
  resetForm.password = ''
  resetForm.confirmPassword = ''
}
</script>

<style scoped>
.forgot-password-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.forgot-password-card {
  width: 450px;
}

.forgot-password-card h2 {
  text-align: center;
  margin: 0;
  color: #409eff;
}

.links {
  text-align: center;
  margin-top: 10px;
}

.links a {
  color: #409eff;
  text-decoration: none;
}

.links a:hover {
  text-decoration: underline;
}

.back-link {
  text-align: center;
  margin-top: 5px;
}
</style>
