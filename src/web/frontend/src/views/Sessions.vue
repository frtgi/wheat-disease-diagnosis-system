<template>
  <div class="sessions-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>会话管理</span>
          <div class="header-actions">
            <el-button type="primary" @click="fetchSessions" :loading="loading">
              刷新列表
            </el-button>
            <el-popconfirm
              title="确定要终止所有其他会话吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleTerminateAllOther"
            >
              <template #reference>
                <el-button type="danger" :loading="terminatingAll">
                  终止所有其他会话
                </el-button>
              </template>
            </el-popconfirm>
          </div>
        </div>
      </template>

      <el-table :data="sessions" v-loading="loading" stripe>
        <el-table-column prop="device_info" label="设备信息" min-width="180">
          <template #default="{ row }">
            <div class="device-info">
              <div>
                <el-icon><Monitor /></el-icon>
                {{ row.browser || '未知浏览器' }}
              </div>
              <div class="os-info">
                <el-icon><Platform /></el-icon>
                {{ row.os || '未知操作系统' }}
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="ip_address" label="IP 地址" width="140">
          <template #default="{ row }">
            {{ row.ip_address || '未知' }}
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="登录时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </el-table-column>

        <el-table-column prop="expires_at" label="过期时间" width="180">
          <template #default="{ row }">
            {{ formatDateTime(row.expires_at) }}
          </template>
        </el-table-column>

        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <el-tag v-if="row.is_current" type="success">当前会话</el-tag>
            <el-tag v-else type="info">其他设备</el-tag>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" align="center">
          <template #default="{ row }">
            <el-popconfirm
              v-if="!row.is_current"
              title="确定要终止此会话吗？"
              confirm-button-text="确定"
              cancel-button-text="取消"
              @confirm="handleTerminateSession(row.session_id)"
            >
              <template #reference>
                <el-button type="danger" size="small" :loading="row.terminating">
                  终止
                </el-button>
              </template>
            </el-popconfirm>
            <span v-else class="current-session-hint">当前会话</span>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && sessions.length === 0" description="暂无活跃会话" />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Monitor, Platform } from '@element-plus/icons-vue'
import { http } from '@/utils/request'

/**
 * 会话信息接口
 */
interface Session {
  session_id: string
  device_info: string
  browser: string
  os: string
  ip_address: string
  created_at: string
  expires_at: string
  is_current: boolean
  terminating?: boolean
}

/**
 * 会话列表响应接口
 */
interface SessionListResponse {
  sessions: Session[]
}

const sessions = ref<Session[]>([])
const loading = ref(false)
const terminatingAll = ref(false)

/**
 * 获取会话列表
 */
const fetchSessions = async () => {
  loading.value = true
  try {
    const response = await http.get<SessionListResponse>('/users/sessions/list')
    sessions.value = response.sessions.map((session) => ({
      ...session,
      browser: parseBrowser(session.device_info),
      os: parseOS(session.device_info),
      terminating: false
    }))
  } catch (error) {
    console.error('获取会话列表失败:', error)
  } finally {
    loading.value = false
  }
}

/**
 * 解析浏览器信息
 * @param deviceInfo 设备信息字符串
 * @returns 浏览器名称
 */
const parseBrowser = (deviceInfo: string): string => {
  if (!deviceInfo) return '未知浏览器'
  const browserPatterns: { [key: string]: RegExp } = {
    Chrome: /Chrome\/[\d.]+/,
    Firefox: /Firefox\/[\d.]+/,
    Safari: /Safari\/[\d.]+/,
    Edge: /Edg\/[\d.]+/,
    Opera: /OPR\/[\d.]+/,
    IE: /MSIE\s[\d.]+|Trident\/[\d.]+/
  }
  for (const [browser, pattern] of Object.entries(browserPatterns)) {
    if (pattern.test(deviceInfo)) {
      return browser
    }
  }
  return '未知浏览器'
}

/**
 * 解析操作系统信息
 * @param deviceInfo 设备信息字符串
 * @returns 操作系统名称
 */
const parseOS = (deviceInfo: string): string => {
  if (!deviceInfo) return '未知操作系统'
  const osPatterns: { [key: string]: RegExp } = {
    Windows: /Windows NT\s[\d.]+/,
    macOS: /Mac OS X\s[\d._]+/,
    Linux: /Linux/,
    Android: /Android\s[\d.]+/,
    iOS: /iPhone OS\s[\d._]+/
  }
  for (const [os, pattern] of Object.entries(osPatterns)) {
    if (pattern.test(deviceInfo)) {
      return os
    }
  }
  return '未知操作系统'
}

/**
 * 格式化日期时间
 * @param dateTime 日期时间字符串
 * @returns 格式化后的日期时间
 */
const formatDateTime = (dateTime: string): string => {
  if (!dateTime) return '未知'
  try {
    const date = new Date(dateTime)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  } catch {
    return dateTime
  }
}

/**
 * 终止单个会话
 * @param sessionId 会话ID
 */
const handleTerminateSession = async (sessionId: string) => {
  const session = sessions.value.find((s) => s.session_id === sessionId)
  if (session) {
    session.terminating = true
  }
  try {
    await http.delete(`/users/sessions/${sessionId}`)
    ElMessage.success('会话已终止')
    await fetchSessions()
  } catch (error) {
    console.error('终止会话失败:', error)
    if (session) {
      session.terminating = false
    }
  }
}

/**
 * 终止所有其他会话
 */
const handleTerminateAllOther = async () => {
  terminatingAll.value = true
  try {
    const otherSessions = sessions.value.filter((s) => !s.is_current)
    await Promise.all(
      otherSessions.map((session) => http.delete(`/users/sessions/${session.session_id}`))
    )
    ElMessage.success('已终止所有其他会话')
    await fetchSessions()
  } catch (error) {
    console.error('终止会话失败:', error)
  } finally {
    terminatingAll.value = false
  }
}

onMounted(() => {
  fetchSessions()
})
</script>

<style scoped>
.sessions-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  gap: 10px;
}

.device-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.device-info > div {
  display: flex;
  align-items: center;
  gap: 6px;
}

.os-info {
  color: #909399;
  font-size: 12px;
}

.current-session-hint {
  color: #909399;
  font-size: 12px;
}
</style>
