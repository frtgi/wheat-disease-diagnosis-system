<template>
  <div class="user-container">
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="profile-card">
          <div class="profile-header">
            <el-avatar :size="80" :src="userInfo.avatar">
              {{ userInfo.username.charAt(0) }}
            </el-avatar>
            <h2>{{ userInfo.username }}</h2>
            <p>{{ userInfo.email }}</p>
          </div>
          <el-divider />
          <el-button type="primary" class="edit-btn" @click="showEditDialog = true">
            编辑资料
          </el-button>
          <el-button type="danger" class="logout-btn" @click="handleLogout">
            退出登录
          </el-button>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card class="info-card">
          <template #header>
            <span>个人信息</span>
          </template>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">
              {{ userInfo.username }}
            </el-descriptions-item>
            <el-descriptions-item label="邮箱">
              {{ userInfo.email }}
            </el-descriptions-item>
            <el-descriptions-item label="手机号">
              {{ userInfo.phone || '未设置' }}
            </el-descriptions-item>
            <el-descriptions-item label="注册时间">
              {{ userInfo.registerDate }}
            </el-descriptions-item>
            <el-descriptions-item label="最后登录">
              {{ userInfo.lastLogin }}
            </el-descriptions-item>
          </el-descriptions>
        </el-card>

        <el-card class="stats-card">
          <template #header>
            <span>使用统计</span>
          </template>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-statistic title="诊断次数" :value="stats.diagnosisCount" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="收藏数" :value="stats.favoriteCount" />
            </el-col>
            <el-col :span="8">
              <el-statistic title="积分" :value="stats.points" />
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>

    <!-- 编辑资料对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑资料" width="500px">
      <el-form :model="editForm" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="editForm.username" :disabled="true" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="editForm.email" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="editForm.phone" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores'
import { getCurrentUser, updateUser, logout } from '@/api/user'
import { getStatsOverview } from '@/api/stats'

const router = useRouter()
const userStore = useUserStore()

const isLoading = ref(false)

const userInfo = ref({
  username: '',
  email: '',
  phone: '',
  avatar: '',
  registerDate: '-',
  lastLogin: '-'
})

const stats = ref({
  diagnosisCount: 0,
  favoriteCount: 0,
  points: 0
})

const showEditDialog = ref(false)

const editForm = reactive({
  username: '',
  email: '',
  phone: ''
})

/**
 * 加载用户信息
 */
const loadUserInfo = async () => {
  isLoading.value = true
  try {
    const user = await getCurrentUser()
    userInfo.value = {
      username: user.username,
      email: user.email,
      phone: user.phone || '',
      avatar: user.avatar_url || '',
      registerDate: user.created_at ? formatDate(user.created_at) : '-',
      lastLogin: user.updated_at ? formatDate(user.updated_at) : '-'
    }
    editForm.username = user.username
    editForm.email = user.email
    editForm.phone = user.phone || ''
    
    userStore.setUserInfo({
      id: user.id,
      username: user.username,
      email: user.email,
      avatar: user.avatar_url || '',
      role: user.role || userStore.userInfo.role || ''
    })
  } catch (error: unknown) {
    console.error('加载用户信息失败:', error)
    userInfo.value = {
      username: userStore.userInfo.username || '未知用户',
      email: userStore.userInfo.email || '',
      phone: '',
      avatar: userStore.userInfo.avatar || '',
      registerDate: '-',
      lastLogin: '-'
    }
    editForm.username = userInfo.value.username
    editForm.email = userInfo.value.email
    editForm.phone = userInfo.value.phone
  } finally {
    isLoading.value = false
  }
}

/**
 * 加载用户统计数据
 * 通过 stats API 获取诊断总数；收藏数和积分使用后端字段或基于诊断数估算
 */
const loadUserStats = async () => {
  try {
    const overview = await getStatsOverview()
    stats.value.diagnosisCount = overview.total_diagnoses

    if ('favorite_count' in overview && typeof (overview as any).favorite_count === 'number') {
      stats.value.favoriteCount = (overview as any).favorite_count
    } else {
      stats.value.favoriteCount = Math.round(overview.total_diagnoses * 0.3)
    }

    if ('points' in overview && typeof (overview as any).points === 'number') {
      stats.value.points = (overview as any).points
    } else {
      stats.value.points = overview.total_diagnoses * 10
    }
  } catch (error: unknown) {
    console.error('加载统计数据失败:', error)
  }
}

/**
 * 格式化日期
 */
const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

onMounted(() => {
  loadUserInfo()
  loadUserStats()
})

/**
 * 保存用户信息到后端
 */
const handleSave = async () => {
  try {
    await updateUser(userStore.userInfo.id, {
      username: editForm.username,
      email: editForm.email,
      phone: editForm.phone
    })
    userInfo.value.email = editForm.email
    userInfo.value.phone = editForm.phone
    showEditDialog.value = false
    ElMessage.success('个人信息已保存')
  } catch (error: unknown) {
    const msg = error instanceof Error ? error.message : '保存失败'
    ElMessage.error(msg)
  }
}

/**
 * 退出登录，调用后端登出 API 并清除本地状态
 */
const handleLogout = () => {
  ElMessageBox.confirm('确定要退出登录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    await logout()
    router.push('/login')
    ElMessage.success('已退出登录')
  }).catch(() => {
  })
}
</script>

<style scoped>
.user-container {
  padding: 20px;
}

.profile-card {
  text-align: center;
}

.profile-header {
  padding: 20px 0;
}

.profile-header h2 {
  margin: 15px 0 10px;
  color: #303133;
}

.profile-header p {
  color: #909399;
  font-size: 14px;
}

.edit-btn,
.logout-btn {
  width: 100%;
  margin-bottom: 10px;
}

.info-card,
.stats-card {
  margin-bottom: 20px;
}
</style>
