<template>
  <div class="inference-progress">
    <!-- 步骤指示器 -->
    <div class="steps-indicator" v-if="steps.length > 0">
      <div
        v-for="(step, index) in steps"
        :key="step.id"
        class="step-item"
        :class="{
          'active': currentStepId === step.id,
          'completed': isStepCompleted(step.id),
          'pending': !isStepCompleted(step.id) && currentStepId !== step.id
        }"
      >
        <div class="step-icon">
          <el-icon v-if="currentStepId === step.id && !isComplete" class="rotating">
            <Loading />
          </el-icon>
          <el-icon v-else-if="isStepCompleted(step.id)">
            <CircleCheckFilled />
          </el-icon>
          <el-icon v-else>
            <component :is="getStepIcon(step.icon)" />
          </el-icon>
        </div>
        <span class="step-name">{{ step.name }}</span>
        <div v-if="index < steps.length - 1" class="step-connector"></div>
      </div>
    </div>
    
    <!-- 进度条 -->
    <div class="progress-section">
      <div class="progress-header">
        <el-icon class="progress-icon" :class="{ 'rotating': !isComplete }">
          <Loading v-if="!isComplete" />
          <CircleCheckFilled v-else />
        </el-icon>
        <span class="stage-text">{{ stageText }}</span>
        <span v-if="estimatedTimeRemaining && !isComplete" class="eta-text">
          预计剩余 {{ estimatedTimeRemaining }}
        </span>
      </div>
      <el-progress
        :percentage="progress"
        :status="progressStatus"
        :stroke-width="12"
        striped
        striped-flow
      />
      <p class="progress-message">{{ message }}</p>
    </div>
    
    <!-- 日志流 -->
    <div class="log-stream" v-if="logs.length > 0">
      <div class="log-header">
        <el-icon><Document /></el-icon>
        <span>推理日志</span>
        <el-button type="primary" link size="small" @click="clearLogs">
          清空
        </el-button>
      </div>
      <div class="log-container" ref="logContainerRef">
        <div
          v-for="(log, index) in logs"
          :key="index"
          class="log-item"
          :class="`log-${log.level}`"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <el-tag :type="getLogTagType(log.level)" size="small" class="log-level">
            {{ log.level.toUpperCase() }}
          </el-tag>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick, onMounted, onUnmounted } from 'vue'
import { 
  Loading, 
  CircleCheckFilled, 
  Document,
  View,
  Search,
  Connection
} from '@element-plus/icons-vue'

/**
 * 步骤定义接口
 */
interface Step {
  id: string
  name: string
  icon: string
}

/**
 * 日志条目接口
 */
interface LogEntry {
  level: 'info' | 'warning' | 'error' | 'debug'
  message: string
  timestamp: number
  stage?: string
}

/**
 * 推理进度组件 Props
 */
interface Props {
  progress: number
  stage: string
  message: string
  isComplete: boolean
  steps?: Step[]
  logs?: LogEntry[]
  startTime?: number
}

const props = withDefaults(defineProps<Props>(), {
  progress: 0,
  stage: '',
  message: '',
  isComplete: false,
  steps: () => [],
  logs: () => [],
  startTime: 0
})

const emit = defineEmits<{
  (e: 'clear-logs'): void
}>()

const logContainerRef = ref<HTMLElement | null>(null)

/**
 * 当前步骤 ID
 */
const currentStepId = computed(() => props.stage)

/**
 * 计算阶段显示文本
 */
const stageText = computed((): string => {
  if (props.isComplete) {
    return '推理完成'
  }
  const currentStep = props.steps.find(s => s.id === props.stage)
  return currentStep?.name || props.stage || '准备中...'
})

/**
 * 计算进度条状态
 */
const progressStatus = computed((): 'success' | undefined => {
  return props.isComplete ? 'success' : undefined
})

/**
 * 当前时间戳（每秒更新，用于 ETA 计算）
 */
const now = ref(Date.now())
let etaTimer: ReturnType<typeof setInterval> | null = null

onMounted(() => {
  etaTimer = setInterval(() => {
    now.value = Date.now()
  }, 1000)
})

onUnmounted(() => {
  if (etaTimer) {
    clearInterval(etaTimer)
    etaTimer = null
  }
})

/**
 * 计算预估剩余时间
 * 基于已用时间和当前进度百分比推算剩余时间
 */
const estimatedTimeRemaining = computed((): string => {
  if (props.isComplete || props.progress <= 0 || !props.startTime) {
    return ''
  }

  const elapsed = now.value - props.startTime
  if (elapsed < 3000) return ''

  const progressRatio = Math.max(props.progress / 100, 0.01)
  const estimatedTotal = elapsed / progressRatio
  const remaining = estimatedTotal - elapsed

  if (remaining < 1000) return '不到 1 秒'

  const seconds = Math.floor(remaining / 1000)
  if (seconds < 60) return `${seconds} 秒`

  const minutes = Math.floor(seconds / 60)
  const remainSeconds = seconds % 60
  if (minutes < 60) return `${minutes} 分 ${remainSeconds} 秒`

  const hours = Math.floor(minutes / 60)
  const remainMinutes = minutes % 60
  return `${hours} 小时 ${remainMinutes} 分`
})

/**
 * 判断步骤是否已完成
 */
const isStepCompleted = (stepId: string): boolean => {
  const stepOrder = ['init', 'visual', 'knowledge', 'textual', 'fusion', 'complete']
  const currentIndex = stepOrder.indexOf(props.stage)
  const stepIndex = stepOrder.indexOf(stepId)
  
  if (props.isComplete) return true
  return stepIndex < currentIndex
}

/**
 * 获取步骤图标组件
 */
const getStepIcon = (iconName: string) => {
  const iconMap: Record<string, any> = {
    'Loading': Loading,
    'View': View,
    'Search': Search,
    'Document': Document,
    'Connection': Connection,
    'CircleCheck': CircleCheckFilled
  }
  return iconMap[iconName] || Document
}

/**
 * 格式化时间戳
 */
const formatTime = (timestamp: number): string => {
  const date = new Date(timestamp * 1000)
  return date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit', 
    second: '2-digit' 
  })
}

/**
 * 获取日志标签类型
 */
const getLogTagType = (level: string): 'success' | 'warning' | 'danger' | 'info' => {
  const typeMap: Record<string, 'success' | 'warning' | 'danger' | 'info'> = {
    'info': 'info',
    'warning': 'warning',
    'error': 'danger',
    'debug': 'info'
  }
  return typeMap[level] || 'info'
}

/**
 * 清空日志
 */
const clearLogs = () => {
  emit('clear-logs')
}

/**
 * 自动滚动到底部
 */
watch(() => props.logs, () => {
  nextTick(() => {
    if (logContainerRef.value) {
      logContainerRef.value.scrollTop = logContainerRef.value.scrollHeight
    }
  })
}, { deep: true })
</script>

<style scoped>
.inference-progress {
  padding: 24px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.08);
}

/* 步骤指示器样式 */
.steps-indicator {
  display: flex;
  justify-content: space-between;
  margin-bottom: 24px;
  padding: 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  position: relative;
  flex: 1;
}

.step-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.step-item.pending .step-icon {
  background-color: #e4e7ed;
  color: #909399;
}

.step-item.active .step-icon {
  background-color: #409eff;
  color: #fff;
}

.step-item.completed .step-icon {
  background-color: #67c23a;
  color: #fff;
}

.step-name {
  font-size: 12px;
  color: #606266;
  text-align: center;
}

.step-item.active .step-name {
  color: #409eff;
  font-weight: 600;
}

.step-item.completed .step-name {
  color: #67c23a;
}

.step-connector {
  position: absolute;
  top: 20px;
  left: calc(50% + 24px);
  width: calc(100% - 48px);
  height: 2px;
  background-color: #e4e7ed;
}

.step-item.completed .step-connector {
  background-color: #67c23a;
}

/* 进度条样式 */
.progress-section {
  margin-bottom: 20px;
}

.progress-header {
  display: flex;
  align-items: center;
  margin-bottom: 16px;
}

.progress-icon {
  font-size: 28px;
  margin-right: 12px;
  color: #409eff;
  transition: color 0.3s ease;
}

.progress-icon.rotating {
  animation: rotate 1.5s linear infinite;
}

.progress-icon:not(.rotating) {
  color: #67c23a;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.stage-text {
  font-size: 18px;
  font-weight: 600;
  color: #303133;
}

.eta-text {
  margin-left: auto;
  font-size: 14px;
  font-weight: 500;
  color: #e6a23c;
  background: #fdf6ec;
  padding: 4px 12px;
  border-radius: 4px;
}

.inference-progress :deep(.el-progress) {
  margin-bottom: 16px;
}

.inference-progress :deep(.el-progress-bar__outer) {
  background-color: #f0f2f5;
  border-radius: 8px;
}

.inference-progress :deep(.el-progress-bar__inner) {
  border-radius: 8px;
  transition: width 0.5s ease-in-out;
}

.inference-progress :deep(.el-progress__text) {
  font-weight: 600;
}

.progress-message {
  margin: 0;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-radius: 8px;
  color: #606266;
  font-size: 14px;
  line-height: 1.6;
  text-align: center;
}

/* 日志流样式 */
.log-stream {
  margin-top: 20px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  overflow: hidden;
}

.log-header {
  display: flex;
  align-items: center;
  padding: 12px 16px;
  background-color: #f5f7fa;
  border-bottom: 1px solid #e4e7ed;
}

.log-header .el-icon {
  margin-right: 8px;
  color: #409eff;
}

.log-header span {
  flex: 1;
  font-weight: 600;
  color: #303133;
}

.log-container {
  max-height: 200px;
  overflow-y: auto;
  padding: 8px;
  background-color: #fafafa;
}

.log-item {
  display: flex;
  align-items: flex-start;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 4px;
  font-size: 12px;
  font-family: 'Consolas', 'Monaco', monospace;
}

.log-item.log-info {
  background-color: #f0f9ff;
}

.log-item.log-warning {
  background-color: #fdf6ec;
}

.log-item.log-error {
  background-color: #fef0f0;
}

.log-item.log-debug {
  background-color: #f5f7fa;
}

.log-time {
  color: #909399;
  margin-right: 8px;
  white-space: nowrap;
}

.log-level {
  margin-right: 8px;
  font-size: 10px;
}

.log-message {
  flex: 1;
  color: #303133;
  word-break: break-all;
}
</style>
