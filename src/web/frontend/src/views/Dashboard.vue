<template>
  <div class="dashboard-container">
    <!-- 欢迎卡片 -->
    <el-card class="welcome-card">
      <h1>欢迎使用基于多模态融合的小麦病害诊断系统</h1>
      <p>融合视觉感知、语义理解和知识推理的智能农业诊断平台</p>
    </el-card>

    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row" v-loading="isLoading">
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-statistic title="今日诊断次数" :value="stats.todayDiagnoses">
            <template #prefix>
              <el-icon><circle-check /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-statistic title="总诊断次数" :value="stats.totalDiagnoses">
            <template #prefix>
              <el-icon><data-line /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-statistic title="平均准确率" :value="stats.accuracy" suffix="%">
            <template #prefix>
              <el-icon><trend-charts /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
      <el-col :xs="24" :sm="12" :md="6">
        <el-card class="stat-card">
          <el-statistic title="活跃用户数" :value="stats.userCount">
            <template #prefix>
              <el-icon><user /></el-icon>
            </template>
          </el-statistic>
        </el-card>
      </el-col>
    </el-row>

    <!-- 图表区域 -->
    <DiseaseChart
      :distribution-data="distributionData"
      :stats-data="statsData"
      :trend-data="trendData"
      @timeRangeChange="handleTimeRangeChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { CircleCheck, DataLine, TrendCharts, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import DiseaseChart from '@/components/dashboard/DiseaseChart.vue'
import { getStatsOverview, getDiagnosisStats } from '@/api/stats'
import type { DiseaseDistribution, DiagnosisStats, TrendData } from '@/types'

// 统计数据
const stats = ref({
  todayDiagnoses: 0,
  totalDiagnoses: 0,
  accuracy: 0,
  userCount: 0
})

// 病害分布数据（饼图）
const distributionData = ref<DiseaseDistribution[]>([])

// 诊断统计数据（柱状图）
const statsData = ref<DiagnosisStats[]>([])

// 诊断趋势数据（折线图）
const trendData = ref<TrendData[]>([])

// 加载状态
const isLoading = ref(false)

/**
 * 加载统计数据
 * 通过 stats API 获取概览统计和诊断统计，替代从诊断记录中计算的方式
 */
const loadStats = async () => {
  isLoading.value = true
  try {
    const [overview, diagnosisStatsData] = await Promise.all([
      getStatsOverview(),
      getDiagnosisStats()
    ])

    stats.value.totalDiagnoses = overview.total_diagnoses
    stats.value.userCount = overview.total_users

    stats.value.todayDiagnoses = (overview as any).today_diagnoses ?? 0
    stats.value.accuracy = (overview as any).avg_accuracy ?? 0

    const topDiseases = diagnosisStatsData.top_diseases || []
    const totalTopCount = topDiseases.reduce((sum, d) => sum + d.count, 0)

    // 将热门疾病数据转换为饼图格式
    distributionData.value = topDiseases.map(d => ({
      name: d.disease_name || `病害 #${d.disease_id}`,
      value: totalTopCount > 0 ? parseFloat(((d.count / totalTopCount) * 100).toFixed(1)) : 0
    }))

    statsData.value = topDiseases
      .map(d => ({ disease_name: d.disease_name || `病害 #${d.disease_id}`, count: d.count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)

    trendData.value = (overview as any).diagnosis_trend ?? []

  } catch (error: unknown) {
    console.error('加载统计数据失败:', error)
    const msg = error instanceof Error ? error.message : '加载统计数据失败'
    ElMessage.error(msg)
  } finally {
    isLoading.value = false
  }
}

// 生命周期钩子：组件挂载时加载数据
onMounted(() => {
  loadStats()
})

/**
 * 处理时间范围变化
 */
const handleTimeRangeChange = (range: string) => {
  loadStats()
}
</script>

<style scoped>
.dashboard-container {
  padding: 20px;
}

.welcome-card {
  margin-bottom: 20px;
  text-align: center;
}

.welcome-card h1 {
  color: #409eff;
  margin-bottom: 10px;
}

.welcome-card p {
  color: #606266;
  font-size: 16px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  transition: transform 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
}
</style>
