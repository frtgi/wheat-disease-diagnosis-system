<template>
  <div class="disease-chart-container">
    <el-row :gutter="20">
      <!-- 饼图：病害类型分布 -->
      <el-col :xs="24" :sm="12" :md="12" :lg="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="title">
                <el-icon><pie-chart /></el-icon>
                病害类型分布
              </span>
            </div>
          </template>
          <div
            ref="pieChartRef"
            class="chart-wrapper"
          />
        </el-card>
      </el-col>

      <!-- 柱状图：诊断次数统计 -->
      <el-col :xs="24" :sm="12" :md="12" :lg="12">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="title">
                <el-icon><trend-charts /></el-icon>
                诊断次数统计
              </span>
            </div>
          </template>
          <div
            ref="barChartRef"
            class="chart-wrapper"
          />
        </el-card>
      </el-col>
    </el-row>

    <!-- 趋势图（可选） -->
    <el-row :gutter="20" style="margin-top: 20px;">
      <el-col :span="24">
        <el-card class="chart-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span class="title">
                <el-icon><data-line /></el-icon>
                诊断趋势分析
              </span>
              <el-radio-group v-model="timeRange" size="small" @change="handleTimeRangeChange">
                <el-radio-button value="week">近 7 天</el-radio-button>
                <el-radio-button value="month">近 30 天</el-radio-button>
                <el-radio-button value="year">近 1 年</el-radio-button>
              </el-radio-group>
            </div>
          </template>
          <div
            ref="lineChartRef"
            class="chart-wrapper line-chart"
          />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { PieChart, TrendCharts, DataLine } from '@element-plus/icons-vue'
import { echarts } from '@/utils/echarts'
import type { EChartsOption } from 'echarts'

/**
 * 病害分布数据类型
 */
interface DiseaseDistribution {
  name: string
  value: number
}

/**
 * 诊断统计数据类型
 */
interface DiagnosisStats {
  disease_name: string
  count: number
}

/**
 * 趋势数据类型
 */
interface TrendData {
  date: string
  count: number
}

/**
 * 图表组件 Props
 * @property {DiseaseDistribution[]} distributionData - 病害分布数据
 * @property {DiagnosisStats[]} statsData - 统计数据
 * @property {TrendData[]} trendData - 趋势数据
 * @property {boolean} autoResize - 是否自动调整大小
 */
interface Props {
  distributionData?: DiseaseDistribution[]
  statsData?: DiagnosisStats[]
  trendData?: TrendData[]
  autoResize?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  distributionData: () => [],
  statsData: () => [],
  trendData: () => [],
  autoResize: true
})

/**
 * 组件暴露的事件
 * @event timeRangeChange - 时间范围变化时触发
 */
const emit = defineEmits<{
  'timeRangeChange': [range: string]
}>()

// 图表引用
const pieChartRef = ref<HTMLElement | null>(null)
const barChartRef = ref<HTMLElement | null>(null)
const lineChartRef = ref<HTMLElement | null>(null)

// 图表实例
let pieChartInstance: echarts.ECharts | null = null
let barChartInstance: echarts.ECharts | null = null
let lineChartInstance: echarts.ECharts | null = null

// 时间范围
const timeRange = ref<string>('week')

// 响应式调整监听器
const resizeObserver = ref<ResizeObserver | null>(null)

/**
 * 初始化饼图
 */
const initPieChart = () => {
  if (!pieChartRef.value) return

  pieChartInstance = echarts.init(pieChartRef.value)

  const option: EChartsOption = {
    tooltip: {
      trigger: 'item',
      formatter: '{b}: {c} ({d}%)'
    },
    legend: {
      orient: 'vertical',
      left: 'left',
      top: 'middle'
    },
    series: [
      {
        name: '病害类型',
        type: 'pie',
        radius: '60%',
        data: props.distributionData,
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        },
        label: {
          formatter: '{b}: {d}%'
        }
      }
    ],
    color: ['#5470c6', '#91cc75', '#fac858', '#ee6666', '#73c0de']
  }

  pieChartInstance.setOption(option)
}

/**
 * 初始化柱状图
 */
const initBarChart = () => {
  if (!barChartRef.value) return

  barChartInstance = echarts.init(barChartRef.value)

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '15%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      data: props.statsData.map(item => item.disease_name),
      axisLabel: {
        interval: 0,
        rotate: 30
      }
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '诊断次数',
        type: 'bar',
        data: props.statsData.map(item => item.count),
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#83bff6' },
            { offset: 0.5, color: '#188df0' },
            { offset: 1, color: '#188df0' }
          ])
        },
        label: {
          show: true,
          position: 'top'
        }
      }
    ]
  }

  barChartInstance.setOption(option)
}

/**
 * 初始化折线图
 */
const initLineChart = () => {
  if (!lineChartRef.value) return

  lineChartInstance = echarts.init(lineChartRef.value)

  const option: EChartsOption = {
    tooltip: {
      trigger: 'axis'
    },
    grid: {
      left: '5%',
      right: '5%',
      bottom: '10%',
      top: '10%'
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: props.trendData.map(item => item.date)
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        name: '诊断次数',
        type: 'line',
        data: props.trendData.map(item => item.count),
        smooth: true,
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(64, 158, 255, 0.5)' },
            { offset: 1, color: 'rgba(64, 158, 255, 0.01)' }
          ])
        },
        itemStyle: {
          color: '#409eff'
        }
      }
    ]
  }

  lineChartInstance.setOption(option)
}

/**
 * 更新图表数据
 */
const updateCharts = () => {
  nextTick(() => {
    if (pieChartInstance) {
      pieChartInstance.setOption({
        series: [{ data: props.distributionData }]
      })
    }
    if (barChartInstance) {
      barChartInstance.setOption({
        xAxis: { data: props.statsData.map(item => item.disease_name) },
        series: [{ data: props.statsData.map(item => item.count) }]
      })
    }
    if (lineChartInstance) {
      lineChartInstance.setOption({
        xAxis: { data: props.trendData.map(item => item.date) },
        series: [{ data: props.trendData.map(item => item.count) }]
      })
    }
  })
}

/**
 * 处理时间范围变化
 */
const handleTimeRangeChange = () => {
  emit('timeRangeChange', timeRange.value)
}

/**
 * 调整图表大小
 */
const resizeCharts = () => {
  pieChartInstance?.resize()
  barChartInstance?.resize()
  lineChartInstance?.resize()
}

/**
 * 销毁图表实例
 */
const disposeCharts = () => {
  if (pieChartInstance) {
    pieChartInstance.dispose()
    pieChartInstance = null
  }
  if (barChartInstance) {
    barChartInstance.dispose()
    barChartInstance = null
  }
  if (lineChartInstance) {
    lineChartInstance.dispose()
    lineChartInstance = null
  }
}

// 监听数据变化
watch(
  () => [props.distributionData, props.statsData, props.trendData],
  () => {
    updateCharts()
  },
  { deep: true }
)

// 组件挂载时初始化
onMounted(() => {
  nextTick(() => {
    initPieChart()
    initBarChart()
    initLineChart()

    // 监听窗口大小变化
    if (props.autoResize) {
      window.addEventListener('resize', resizeCharts)
    }
  })
})

// 组件卸载时清理
onBeforeUnmount(() => {
  if (props.autoResize) {
    window.removeEventListener('resize', resizeCharts)
  }
  if (resizeObserver.value) {
    resizeObserver.value.disconnect()
    resizeObserver.value = null
  }
  disposeCharts()
})

// 暴露方法供父组件调用
defineExpose({
  resize: resizeCharts,
  refresh: updateCharts
})
</script>

<style scoped>
.disease-chart-container {
  width: 100%;
  padding: 20px;
}

.chart-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.title .el-icon {
  margin-right: 8px;
  font-size: 18px;
  color: #409eff;
}

.chart-wrapper {
  width: 100%;
  height: 300px;
}

.line-chart {
  height: 350px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .chart-wrapper {
    height: 250px;
  }
  
  .line-chart {
    height: 280px;
  }
}
</style>
