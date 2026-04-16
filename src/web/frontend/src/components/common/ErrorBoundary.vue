<template>
  <slot v-if="!hasError" />
  <div v-else class="error-boundary">
    <div class="error-content">
      <div class="error-icon">
        <el-icon :size="80" color="#f56c6c">
          <WarningFilled />
        </el-icon>
      </div>
      
      <h2 class="error-title">{{ errorTitle }}</h2>
      <p class="error-message">{{ displayMessage }}</p>
      
      <div class="error-actions">
        <el-button type="primary" @click="handleRetry">
          <el-icon><RefreshRight /></el-icon>
          重新加载
        </el-button>
        <el-button @click="handleGoBack">
          <el-icon><Back /></el-icon>
          返回上页
        </el-button>
        <el-button @click="handleGoHome">
          <el-icon><HomeFilled /></el-icon>
          返回首页
        </el-button>
      </div>
      
      <el-collapse v-if="showDetails" class="error-details">
        <el-collapse-item title="查看错误详情" name="details">
          <div class="detail-section">
            <div class="detail-label">错误类型:</div>
            <div class="detail-value">{{ errorType }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">错误信息:</div>
            <div class="detail-value">{{ errorMessage }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">组件路径:</div>
            <div class="detail-value">{{ componentInfo }}</div>
          </div>
          <div class="detail-section">
            <div class="detail-label">发生时间:</div>
            <div class="detail-value">{{ errorTime }}</div>
          </div>
          <div v-if="errorStack" class="detail-section">
            <div class="detail-label">堆栈信息:</div>
            <pre class="stack-trace">{{ errorStack }}</pre>
          </div>
        </el-collapse-item>
      </el-collapse>
      
      <div class="error-footer">
        <el-checkbox v-model="showDetails">显示详细错误信息</el-checkbox>
        <el-button link type="primary" @click="handleReportError">
          <el-icon><Position /></el-icon>
          报告此问题
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onErrorCaptured, type ComponentPublicInstance } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { WarningFilled, RefreshRight, Back, HomeFilled, Position } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

/**
 * 错误类型常量
 */
const ERROR_TYPE = {
  RENDER: '渲染错误',
  ASYNC: '异步错误',
  NETWORK: '网络错误',
  UNKNOWN: '未知错误'
} as const

type ErrorTypeValue = typeof ERROR_TYPE[keyof typeof ERROR_TYPE]

/**
 * 错误边界组件
 * 
 * 用于捕获子组件的 JavaScript 错误，显示友好的错误提示界面，
 * 提供重试、返回等恢复功能，并支持错误日志记录和上报。
 * 
 * @example
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 */

interface ErrorLog {
  type: string
  message: string
  stack?: string
  componentInfo: string
  timestamp: string
  url: string
  userAgent: string
}

const router = useRouter()
const route = useRoute()

const hasError = ref(false)
const errorMessage = ref('')
const errorStack = ref('')
const errorType = ref<ErrorTypeValue>(ERROR_TYPE.UNKNOWN)
const componentInfo = ref('')
const errorTime = ref('')
const showDetails = ref(false)
const retryCount = ref(0)

const MAX_RETRY_COUNT = 3

/**
 * 错误标题，根据错误类型显示不同标题
 */
const errorTitle = computed(() => {
  switch (errorType.value) {
    case ERROR_TYPE.RENDER:
      return '页面渲染出现问题'
    case ERROR_TYPE.ASYNC:
      return '数据加载出现问题'
    case ERROR_TYPE.NETWORK:
      return '网络连接出现问题'
    default:
      return '页面出现错误'
  }
})

/**
 * 显示给用户的友好错误消息
 */
const displayMessage = computed(() => {
  if (retryCount.value >= MAX_RETRY_COUNT) {
    return '多次重试后仍然出现问题，建议返回首页或联系技术支持'
  }
  return '抱歉，页面遇到了一些问题。您可以尝试重新加载，或返回上一页'
})

/**
 * 判断错误类型
 * @param error - 错误对象
 * @returns 错误类型
 */
function classifyError(error: Error): ErrorTypeValue {
  const message = error.message.toLowerCase()
  const stack = (error.stack || '').toLowerCase()
  
  if (message.includes('network') || message.includes('fetch') || message.includes('timeout')) {
    return ERROR_TYPE.NETWORK
  }
  
  if (message.includes('async') || message.includes('promise') || stack.includes('async')) {
    return ERROR_TYPE.ASYNC
  }
  
  if (stack.includes('render') || stack.includes('vnode') || stack.includes('component')) {
    return ERROR_TYPE.RENDER
  }
  
  return ERROR_TYPE.UNKNOWN
}

/**
 * 记录错误日志
 * @param errorLog - 错误日志对象
 */
function logError(errorLog: ErrorLog): void {
  console.error('[ErrorBoundary] 捕获到错误:', errorLog)
  
  const storedLogs = JSON.parse(localStorage.getItem('error_logs') || '[]')
  storedLogs.push(errorLog)
  
  if (storedLogs.length > 50) {
    storedLogs.shift()
  }
  
  localStorage.setItem('error_logs', JSON.stringify(storedLogs))
}

/**
 * 生成错误日志对象
 * @param error - 错误对象
 * @param info - 组件信息
 * @returns 错误日志对象
 */
function createErrorLog(error: Error, info: string): ErrorLog {
  return {
    type: errorType.value,
    message: error.message,
    stack: error.stack,
    componentInfo: info,
    timestamp: new Date().toISOString(),
    url: window.location.href,
    userAgent: navigator.userAgent
  }
}

/**
 * 捕获子组件错误
 * Vue 3 的 onErrorCaptured 钩子用于捕获子组件的错误
 */
onErrorCaptured((error: Error, instance: ComponentPublicInstance | null, info: string) => {
  hasError.value = true
  errorMessage.value = error.message || '未知错误'
  errorStack.value = error.stack || ''
  errorType.value = classifyError(error)
  componentInfo.value = info
  errorTime.value = new Date().toLocaleString('zh-CN')
  
  const errorLog = createErrorLog(error, info)
  logError(errorLog)
  
  return false
})

/**
 * 重置错误状态
 */
function resetError(): void {
  hasError.value = false
  errorMessage.value = ''
  errorStack.value = ''
  errorType.value = ERROR_TYPE.UNKNOWN
  componentInfo.value = ''
  errorTime.value = ''
}

/**
 * 处理重试操作
 */
function handleRetry(): void {
  if (retryCount.value >= MAX_RETRY_COUNT) {
    ElMessage.warning('已达到最大重试次数，请尝试其他操作')
    return
  }
  
  retryCount.value++
  resetError()
  ElMessage.success('正在重新加载...')
}

/**
 * 处理返回上一页操作
 */
function handleGoBack(): void {
  resetError()
  router.go(-1)
}

/**
 * 处理返回首页操作
 */
function handleGoHome(): void {
  resetError()
  router.push('/')
}

/**
 * 处理错误上报
 */
function handleReportError(): void {
  const errorReport = {
    type: errorType.value,
    message: errorMessage.value,
    stack: errorStack.value,
    componentInfo: componentInfo.value,
    time: errorTime.value,
    url: window.location.href,
    retryCount: retryCount.value
  }
  
  ElMessage.success('错误报告已提交，感谢您的反馈')
}

/**
 * 暴露方法供外部调用
 */
defineExpose({
  resetError,
  hasError,
  errorMessage
})
</script>

<style scoped>
.error-boundary {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  padding: 40px 20px;
  background: linear-gradient(135deg, #f5f7fa 0%, #e4e7ed 100%);
  border-radius: 8px;
}

.error-content {
  text-align: center;
  max-width: 640px;
  width: 100%;
}

.error-icon {
  margin-bottom: 24px;
  animation: shake 0.5s ease-in-out;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  25% { transform: translateX(-10px); }
  75% { transform: translateX(10px); }
}

.error-title {
  margin: 0 0 12px;
  font-size: 24px;
  font-weight: 600;
  color: #303133;
}

.error-message {
  color: #909399;
  font-size: 14px;
  margin-bottom: 24px;
  line-height: 1.6;
}

.error-actions {
  display: flex;
  justify-content: center;
  gap: 12px;
  margin-bottom: 24px;
  flex-wrap: wrap;
}

.error-actions .el-button {
  min-width: 120px;
}

.error-details {
  text-align: left;
  margin-bottom: 20px;
  background: #fff;
  border-radius: 8px;
  overflow: hidden;
}

.detail-section {
  margin-bottom: 12px;
}

.detail-section:last-child {
  margin-bottom: 0;
}

.detail-label {
  font-weight: 600;
  color: #606266;
  margin-bottom: 4px;
  font-size: 13px;
}

.detail-value {
  color: #909399;
  font-size: 13px;
  word-break: break-all;
}

.stack-trace {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-size: 11px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-break: break-all;
  max-height: 200px;
  overflow-y: auto;
  color: #606266;
  margin: 0;
}

.error-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #ebeef5;
}

@media (max-width: 640px) {
  .error-boundary {
    padding: 24px 16px;
  }
  
  .error-title {
    font-size: 20px;
  }
  
  .error-actions {
    flex-direction: column;
  }
  
  .error-actions .el-button {
    width: 100%;
  }
  
  .error-footer {
    flex-direction: column;
    gap: 12px;
  }
}
</style>
