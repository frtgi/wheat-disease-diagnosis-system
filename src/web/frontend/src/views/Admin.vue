<template>
  <div class="admin-container">
    <el-page-header title="返回" @back="goBack">
      <template #content>
        <span class="page-title">管理后台</span>
      </template>
      <template #extra>
        <el-tag type="danger">管理员</el-tag>
      </template>
    </el-page-header>

    <el-divider />

    <el-tabs v-model="activeTab" class="admin-tabs">
      <el-tab-pane label="系统概览" name="overview">
        <el-row :gutter="16" class="stats-row">
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="用户总数" :value="overviewStats.total_users || 0">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="诊断总数" :value="overviewStats.total_diagnoses || 0">
                <template #prefix><el-icon><DataAnalysis /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card">
              <el-statistic title="疾病知识" :value="overviewStats.total_diseases || 0">
                <template #prefix><el-icon><Reading /></el-icon></template>
              </el-statistic>
            </el-card>
          </el-col>
          <el-col :span="6">
            <el-card shadow="hover" class="stat-card stat-card-vram">
              <el-statistic title="GPU 显存" :value="vramStatus.total_mb || 0" suffix="MB">
                <template #prefix><el-icon><Monitor /></el-icon></template>
              </el-statistic>
              <el-progress
                :percentage="Math.round((vramStatus.usage_ratio || 0) * 100)"
                :color="getVramColor(vramStatus.usage_ratio || 0)"
                :stroke-width="8"
                class="vram-progress"
              />
            </el-card>
          </el-col>
        </el-row>

        <el-row :gutter="16">
          <el-col :span="12">
            <el-card class="section-card">
              <template #header>
                <div class="section-header">
                  <span>用户统计</span>
                </div>
              </template>
              <el-descriptions :column="2" border v-if="userStats.total_users">
                <el-descriptions-item label="活跃用户">{{ userStats.active_users || 0 }}</el-descriptions-item>
                <el-descriptions-item label="非活跃用户">{{ userStats.inactive_users || 0 }}</el-descriptions-item>
                <el-descriptions-item label="角色分布" :span="2">
                  <el-tag v-for="(count, role) in (userStats.by_role || {})" :key="String(role)" size="small" style="margin-right: 8px">
                    {{ role }}: {{ count }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
              <el-empty v-else description="暂无用户数据" :image-size="60" />
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="section-card">
              <template #header>
                <div class="section-header">
                  <span>诊断统计</span>
                </div>
              </template>
              <el-descriptions :column="2" border v-if="diagnosisStats.by_status">
                <el-descriptions-item label="状态分布" :span="2">
                  <el-tag v-for="(count, status) in (diagnosisStats.by_status || {})" :key="String(status)" size="small" style="margin-right: 8px">
                    {{ status }}: {{ count }}
                  </el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="热门疾病" :span="2">
                  <span v-for="(item, idx) in (diagnosisStats.top_diseases || []).slice(0, 5)" :key="idx" style="margin-right: 12px">
                    <el-tag type="warning" size="small">{{ item.disease_name || `ID:${item.disease_id}` }}</el-tag> {{ item.count }}次
                  </span>
                </el-descriptions-item>
              </el-descriptions>
              <el-empty v-else description="暂无诊断数据" :image-size="60" />
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="系统监控" name="monitor">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-card class="section-card">
              <template #header>
                <div class="section-header">
                  <span>GPU 显存监控</span>
                  <div class="section-actions">
                    <el-button size="small" @click="refreshVramStatus" :loading="vramLoading">刷新</el-button>
                    <el-button size="small" type="danger" @click="handleCleanupVram" :loading="vramCleaning">清理显存</el-button>
                  </div>
                </div>
              </template>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="已用显存">
                  <span :style="{ color: getVramColor(vramStatus.usage_ratio || 0) }">
                    {{ vramStatus.used_mb || 0 }} MB
                  </span>
                </el-descriptions-item>
                <el-descriptions-item label="空闲显存">{{ vramStatus.free_mb || 0 }} MB</el-descriptions-item>
                <el-descriptions-item label="保留显存">{{ vramStatus.reserved_mb || 0 }} MB</el-descriptions-item>
                <el-descriptions-item label="使用率">
                  <el-progress
                    :percentage="Math.round((vramStatus.usage_ratio || 0) * 100)"
                    :color="getVramColor(vramStatus.usage_ratio || 0)"
                    :stroke-width="14"
                  />
                </el-descriptions-item>
                <el-descriptions-item label="警告阈值">{{ Math.round((vramStatus.warning_threshold || 0.85) * 100) }}%</el-descriptions-item>
                <el-descriptions-item label="临界阈值">{{ Math.round((vramStatus.critical_threshold || 0.95) * 100) }}%</el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
          <el-col :span="12">
            <el-card class="section-card">
              <template #header>
                <div class="section-header">
                  <span>缓存管理</span>
                  <div class="section-actions">
                    <el-button size="small" @click="refreshCacheStats" :loading="cacheLoading">刷新</el-button>
                    <el-popconfirm title="确定要清空所有推理缓存吗？" @confirm="handleClearCache">
                      <template #reference>
                        <el-button size="small" type="warning" :loading="cacheClearing">清空缓存</el-button>
                      </template>
                    </el-popconfirm>
                  </div>
                </div>
              </template>
              <el-descriptions :column="1" border>
                <el-descriptions-item label="缓存状态">
                  <el-tag :type="cacheStats.success ? 'success' : 'info'" size="small">
                    {{ cacheStats.success ? '正常' : '未启用' }}
                  </el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </el-card>
          </el-col>
        </el-row>
      </el-tab-pane>

      <el-tab-pane label="诊断日志" name="logs">
        <el-card class="section-card">
          <template #header>
            <div class="section-header">
              <span>最近诊断日志</span>
              <div class="section-actions">
                <el-select v-model="logDuration" size="small" style="width: 140px" @change="refreshLogStats">
                  <el-option label="最近 24 小时" :value="24" />
                  <el-option label="最近 7 天" :value="168" />
                  <el-option label="最近 30 天" :value="720" />
                </el-select>
                <el-button size="small" @click="refreshLogStats" :loading="logLoading">刷新</el-button>
              </div>
            </div>
          </template>

          <el-descriptions :column="3" border class="log-stats-desc" v-if="logStatistics.data">
            <el-descriptions-item label="总诊断数">{{ logStatistics.data.total_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="成功数">{{ logStatistics.data.success_count || 0 }}</el-descriptions-item>
            <el-descriptions-item label="失败数">{{ logStatistics.data.error_count || 0 }}</el-descriptions-item>
          </el-descriptions>

          <el-table :data="recentLogs" stripe border size="small" class="log-table" v-loading="logLoading">
            <el-table-column prop="timestamp" label="时间" width="170" />
            <el-table-column prop="disease_detected" label="病害" width="140" show-overflow-tooltip />
            <el-table-column prop="success" label="状态" width="80">
              <template #default="{ row }">
                <el-tag :type="row.success ? 'success' : 'danger'" size="small">
                  {{ row.success ? '成功' : '失败' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="confidence" label="置信度" width="100">
              <template #default="{ row }">
                {{ row.confidence ? `${Math.round(row.confidence * 100)}%` : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="processing_time_ms" label="耗时" width="100">
              <template #default="{ row }">
                {{ row.processing_time_ms ? `${row.processing_time_ms}ms` : '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="error" label="错误信息" show-overflow-tooltip>
              <template #default="{ row }">
                <el-text v-if="row.error" type="danger" size="small">{{ row.error }}</el-text>
                <span v-else>-</span>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="病害分布" name="distribution">
        <el-card class="section-card">
          <template #header>
            <div class="section-header">
              <span>病害分布统计</span>
            </div>
          </template>
          <div ref="diseaseChartRef" style="height: 400px; width: 100%;"></div>
        </el-card>
      </el-tab-pane>

      <el-tab-pane label="AI 模型管理" name="models">
        <el-card class="section-card">
          <template #header>
            <div class="section-header">
              <span>AI 模型管理</span>
              <div class="section-actions">
                <el-button type="primary" size="small" @click="handlePreloadModels" :loading="preloading">
                  预加载模型
                </el-button>
              </div>
            </div>
          </template>

          <el-alert
            title="模型预加载说明"
            type="info"
            :closable="false"
            show-icon
            class="model-alert"
          >
            <template #default>
              预加载会将 Qwen3-VL 模型加载到内存中，首次诊断时无需等待加载。
              在低内存环境下请谨慎操作，模型加载可能需要 1-2 分钟。
            </template>
          </el-alert>

          <el-descriptions :column="2" border>
            <el-descriptions-item label="模型名称">Qwen3-VL-2B-Instruct</el-descriptions-item>
            <el-descriptions-item label="量化方式">INT4 (NF4 + 双重量化)</el-descriptions-item>
            <el-descriptions-item label="KV Cache 量化">4-bit (quanto)</el-descriptions-item>
            <el-descriptions-item label="CPU Offload">已启用</el-descriptions-item>
            <el-descriptions-item label="Flash Attention">自动检测</el-descriptions-item>
            <el-descriptions-item label="torch.compile">已启用</el-descriptions-item>
          </el-descriptions>
        </el-card>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onActivated, onBeforeUnmount, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, DataAnalysis, Reading, Monitor } from '@element-plus/icons-vue'
import { echarts } from '@/utils/echarts'
import {
  getOverviewStats,
  getUserStats,
  getDiagnosisStats,
  getVramStatus,
  cleanupVram,
  getCacheStats,
  clearCache,
  getLogStatistics,
  getRecentLogs,
  preloadAIModels,
  getDiseaseDistribution
} from '@/api/admin'

/**
 * 管理员后台页面
 * 提供系统概览、监控、日志和模型管理功能
 */

const router = useRouter()
const route = useRoute()
const activeTab = ref((route.query.tab as string) || 'overview')

const overviewStats = ref<Record<string, number>>({})
const userStats = ref<Record<string, any>>({})
const diagnosisStats = ref<Record<string, any>>({})
const vramStatus = ref<Record<string, any>>({})
const cacheStats = ref<Record<string, any>>({})
const logStatistics = ref<Record<string, any>>({})
const recentLogs = ref<any[]>([])

const vramLoading = ref(false)
const vramCleaning = ref(false)
const cacheLoading = ref(false)
const cacheClearing = ref(false)
const logLoading = ref(false)
const logDuration = ref(24)
const preloading = ref(false)

const diseaseChartRef = ref<HTMLElement | null>(null)
let diseaseChartInstance: any = null

/**
 * 返回上一页
 * 使用浏览器历史记录返回
 */
const goBack = () => {
  router.back()
}

/**
 * 获取显存使用颜色
 */
const getVramColor = (ratio: number): string => {
  if (ratio >= 0.92) return '#f56c6c'
  if (ratio >= 0.80) return '#e6a23c'
  return '#67c23a'
}

/**
 * 加载概览统计
 */
const loadOverviewStats = async () => {
  try {
    const data = await getOverviewStats()
    overviewStats.value = data?.data || data || {}
  } catch (e) {
    ElMessage.error('加载概览统计失败')
  }
}

/**
 * 加载用户统计
 */
const loadUserStats = async () => {
  try {
    const data = await getUserStats()
    userStats.value = data?.data || data || {}
  } catch (e) {
    ElMessage.error('加载用户统计失败')
  }
}

/**
 * 加载诊断统计
 */
const loadDiagnosisStats = async () => {
  try {
    const data = await getDiagnosisStats()
    diagnosisStats.value = data?.data || data || {}
  } catch (e) {
    ElMessage.error('加载诊断统计失败')
  }
}

/**
 * 刷新显存状态
 */
const refreshVramStatus = async () => {
  vramLoading.value = true
  try {
    const res = await getVramStatus()
    vramStatus.value = res?.data || res || {}
  } catch (e) {
    ElMessage.error('获取显存状态失败')
  } finally {
    vramLoading.value = false
  }
}

/**
 * 清理显存
 */
const handleCleanupVram = async () => {
  vramCleaning.value = true
  try {
    const res = await cleanupVram()
    const freed = res?.data?.freed_mb || res?.freed_mb || 0
    ElMessage.success(`显存清理完成，释放 ${freed}MB`)
    await refreshVramStatus()
  } catch (e) {
    ElMessage.error('显存清理失败')
  } finally {
    vramCleaning.value = false
  }
}

/**
 * 刷新缓存统计
 */
const refreshCacheStats = async () => {
  cacheLoading.value = true
  try {
    const res = await getCacheStats()
    cacheStats.value = res?.data || res || {}
  } catch (e) {
    ElMessage.error('获取缓存统计失败')
  } finally {
    cacheLoading.value = false
  }
}

/**
 * 清空缓存
 */
const handleClearCache = async () => {
  cacheClearing.value = true
  try {
    await clearCache()
    ElMessage.success('缓存已清空')
    await refreshCacheStats()
  } catch (e) {
    ElMessage.error('清空缓存失败')
  } finally {
    cacheClearing.value = false
  }
}

/**
 * 刷新日志统计
 */
const refreshLogStats = async () => {
  logLoading.value = true
  try {
    const [statsRes, logsRes] = await Promise.all([
      getLogStatistics(logDuration.value),
      getRecentLogs({ page_size: 20 })
    ])
    logStatistics.value = statsRes?.data || statsRes || {}
    recentLogs.value = logsRes?.data?.logs || logsRes?.logs || []
  } catch (e) {
    ElMessage.error('加载日志统计失败')
  } finally {
    logLoading.value = false
  }
}

/**
 * 预加载模型
 */
const handlePreloadModels = async () => {
  preloading.value = true
  try {
    await preloadAIModels()
    ElMessage.success('模型预加载成功')
  } catch (e) {
    ElMessage.error('模型预加载失败')
  } finally {
    preloading.value = false
  }
}

/**
 * 加载病害分布统计并渲染饼图
 */
const loadDiseaseDistribution = async () => {
  try {
    if (!diseaseChartRef.value) return
    const data = await getDiseaseDistribution(logDuration.value)
    if (diseaseChartRef.value && data) {
      if (!diseaseChartInstance) {
        diseaseChartInstance = echarts.init(diseaseChartRef.value)
      }
      const resData = data?.data || data || {}
      const items = resData.distribution || (Array.isArray(resData) ? resData : [])
      const chartData = Array.isArray(items) ? items : []
      diseaseChartInstance.setOption({
        tooltip: { trigger: 'item', formatter: '{b}: {c} ({d}%)' },
        legend: { orient: 'vertical', left: 'left', top: 'middle' },
        series: [{
          name: '病害分布',
          type: 'pie',
          radius: ['40%', '70%'],
          data: chartData.map((item: any) => ({
            name: item.disease_name || item.name || `病害#${item.disease_id || 0}`,
            value: item.count || 0
          })),
          emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0,0,0,0.5)' } }
        }]
      })
    }
  } catch (e) {
    ElMessage.error('加载病害分布失败')
  }
}

watch(activeTab, (newTab) => {
  router.replace({ query: { ...route.query, tab: newTab } })
  if (newTab === 'distribution') {
    loadDiseaseDistribution()
  } else if (newTab === 'logs') {
    refreshLogStats()
  }
})

/**
 * keep-alive 激活时同步 activeTab 到 URL
 */
onActivated(() => {
  if (activeTab.value) {
    router.replace({ query: { ...route.query, tab: activeTab.value } })
  }
})

onMounted(async () => {
  await Promise.all([
    loadOverviewStats(),
    loadUserStats(),
    loadDiagnosisStats(),
    refreshVramStatus(),
    refreshCacheStats(),
    refreshLogStats(),
    loadDiseaseDistribution()
  ])
})

/** 组件卸载前销毁 ECharts 实例，防止内存泄漏 */
onBeforeUnmount(() => {
  if (diseaseChartInstance) {
    diseaseChartInstance.dispose()
    diseaseChartInstance = null
  }
})
</script>

<style scoped>
.admin-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
}

.admin-tabs {
  margin-top: 10px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
}

.stat-card-vram {
  position: relative;
}

.vram-progress {
  margin-top: 8px;
}

.section-card {
  margin-bottom: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
  color: #303133;
}

.section-actions {
  display: flex;
  gap: 8px;
}

.log-stats-desc {
  margin-bottom: 16px;
}

.log-table {
  margin-top: 16px;
}

.model-alert {
  margin-bottom: 16px;
}
</style>
