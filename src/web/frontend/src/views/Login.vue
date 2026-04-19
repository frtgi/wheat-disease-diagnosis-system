<template>
  <div class="login-container">
    <el-card class="login-card">
      <template #header>
        <h2>用户登录</h2>
      </template>

      <el-form
        ref="loginFormRef"
        :model="loginForm"
        :rules="loginRules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input
            v-model="loginForm.username"
            placeholder="请输入用户名"
            clearable
          />
        </el-form-item>

        <el-form-item label="密码" prop="password">
          <el-input
            v-model="loginForm.password"
            type="password"
            placeholder="请输入密码"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>

        <el-form-item>
          <el-checkbox v-model="loginForm.remember">记住我</el-checkbox>
        </el-form-item>

        <el-form-item>
          <el-button
            type="primary"
            :loading="isLoading"
            style="width: 100%"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>

        <div class="links">
          <router-link to="/forgot-password">忘记密码？</router-link>
          <span class="divider">|</span>
          <router-link to="/register">还没有账号？立即注册</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { login as apiLogin } from '@/api/user'
import { useUserStore } from '@/stores'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 表单引用
const loginFormRef = ref<FormInstance>()

// 加载状态
const isLoading = ref(false)

// 登录表单
const loginForm = reactive({
  username: '',
  password: '',
  remember: false
})

// 表单验证规则
const loginRules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度在 3 到 20 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, max: 20, message: '密码长度在 6 到 20 个字符', trigger: 'blur' }
  ]
}

// 处理登录
const handleLogin = async () => {
  if (!loginFormRef.value) return

  await loginFormRef.value.validate(async (valid) => {
    if (valid) {
      isLoading.value = true
      try {
        // 调用后端登录 API
        const response = await apiLogin({
          username: loginForm.username,
          password: loginForm.password
        })
        
        // 适配响应格式 { success, data: { access_token, refresh_token, user }, message }
        const data = (response as any).data || response
        
        if (!data.access_token) {
          throw new Error((response as any).error || '登录失败')
        }
        
        // Token 现在通过 httpOnly Cookie 传递，不再需要存储到 localStorage
        // 但保留 localStorage 存储以支持向后兼容（SSE 连接等场景）
        userStore.setToken(data.access_token)
        
        // 保存用户信息到 store（包含 role 字段用于权限判断）
        userStore.setUserInfo({
          id: data.user.id,
          username: data.user.username,
          email: data.user.email,
          avatar: data.user.avatar_url || '',
          role: data.user.role
        })
        
        // refresh_token 现在也通过 httpOnly Cookie 传递
        // 保留 localStorage 存储以支持 token 刷新流程
        if (data.refresh_token) {
          localStorage.setItem('refresh_token', data.refresh_token)
        }
        
        ElMessage.success('登录成功')
        
        const redirect = (route.query.redirect as string) || '/dashboard'
        if (redirect.startsWith('/') && !redirect.startsWith('//')) {
          router.push(redirect)
        } else {
          router.push('/dashboard')
        }
      } catch (error: unknown) {
        console.error('登录失败:', error)
        const msg = error instanceof Error ? error.message : '登录失败，请检查用户名和密码'
        ElMessage.error(msg)
      } finally {
        isLoading.value = false
      }
    }
  })
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.login-card {
  width: 450px;
}

.login-card h2 {
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

.links .divider {
  color: #ccc;
  margin: 0 10px;
}
</style>
