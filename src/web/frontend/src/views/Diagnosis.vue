<template>
  <div class="diagnosis-container">
    <el-page-header @back="goBack" title="返回">
      <template #content>
        <span class="page-title">多模态融合诊断</span>
      </template>
      <template #extra>
        <el-tag type="info">KAD-Former + GraphRAG</el-tag>
      </template>
    </el-page-header>
    
    <el-divider />
    
    <el-tabs v-model="activeTab" class="diagnosis-tabs">
      <el-tab-pane label="单图诊断" name="single">
        <MultiModalInput
          ref="multiModalInputRef"
          @diagnose="handleDiagnose"
        />
      </el-tab-pane>
      <el-tab-pane label="批量诊断" name="batch">
        <BatchDiagnosis />
      </el-tab-pane>
    </el-tabs>
    
    <InferenceProgress
      v-if="isDiagnosing && !isInferenceComplete"
      :progress="inferenceProgress"
      :stage="inferenceStage"
      :message="inferenceMessage"
      :is-complete="isInferenceComplete"
      :steps="inferenceSteps"
      :logs="inferenceLogs"
      :start-time="inferenceStartTime"
      @clear-logs="clearLogs"
    />
    
    <div v-if="diagnosisResult" class="result-section">
      <FusionResult
        :result="diagnosisResult"
        :reasoning-chain="reasoningChain"
        :image-src="uploadedImageUrl"
      />
      
      <div class="export-actions">
        <el-dropdown @command="handleExportReport" :loading="isExporting">
          <el-button type="success" :loading="isExporting">
            <el-icon><Download /></el-icon>
            导出诊断报告
            <el-icon class="el-icon--right"><ArrowDown /></el-icon>
          </el-button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="pdf">导出 PDF 报告</el-dropdown-item>
              <el-dropdown-item command="html">导出 HTML 报告</el-dropdown-item>
              <el-dropdown-item command="both" divided>同时导出 PDF 和 HTML</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download, ArrowDown } from '@element-plus/icons-vue'
import MultiModalInput from '@/components/diagnosis/MultiModalInput.vue'
import FusionResult from '@/components/diagnosis/FusionResult.vue'
import InferenceProgress from '@/components/diagnosis/InferenceProgress.vue'
import BatchDiagnosis from '@/components/diagnosis/BatchDiagnosis.vue'
import http from '@/utils/request'
import { generateReport, getReportDownloadUrl } from '@/api/report'
import type { FusionDiagnosisResult, FusionDiagnosisResponse } from '@/types'
import { useUserStore } from '@/stores'

const router = useRouter()

const multiModalInputRef = ref()

/**
 * 诊断参数接口
 * 定义多模态诊断所需的输入参数
 */
interface DiagnoseParams {
  image: File | null
  symptoms: string
  weather: string
  growthStage: string
  affectedPart: string
  enableThinking: boolean
  useGraphRag: boolean
}

/**
 * SSE 连接状态类型
 * 定义 SSE 连接的生命周期状态
 */
type SSEConnectionStateType = 'disconnected' | 'connecting' | 'connected' | 'error'

const SSE_CONNECTION_STATE = {
  DISCONNECTED: 'disconnected',
  CONNECTING: 'connecting',
  CONNECTED: 'connected',
  ERROR: 'error'
} as const

/**
 * SSE 配置常量
 * 注意：AI 推理可能需要很长时间（Qwen Thinking 模式可能需要 5-10 分钟）
 * 心跳超时应该设置得足够长，避免在推理过程中误判超时
 */
const SSE_CONFIG = {
  HEARTBEAT_TIMEOUT: 600000,  // 心跳超时时间（毫秒）= 10分钟，足够长以支持长时间推理
  MAX_RECONNECT_ATTEMPTS: 3,  // 最大重连次数
  RECONNECT_DELAY: 2000,      // 重连延迟（毫秒）
  CONNECTION_TIMEOUT: 30000,  // 连接超时时间（毫秒）
  PROGRESS_TIMEOUT: 360000    // 进度更新超时（毫秒）= 6分钟，如果没有任何进度更新则触发重连
}

const diagnosisResult = ref<FusionDiagnosisResult | null>(null)
const reasoningChain = ref<string[]>([])
const isDiagnosing = ref(false)
const uploadedImageUrl = ref<string>('')
const inferenceProgress = ref<number>(0)
const inferenceStage = ref<string>('')
const inferenceMessage = ref<string>('')
const isInferenceComplete = ref<boolean>(false)
const sseConnectionState = ref<SSEConnectionStateType>(SSE_CONNECTION_STATE.DISCONNECTED)
const activeTab = ref<string>('single')
const isExporting = ref<boolean>(false)
const inferenceStartTime = ref<number>(0)

// 步骤和日志状态
const inferenceSteps = ref<Array<{id: string, name: string, icon: string}>>([])
const inferenceLogs = ref<Array<{level: 'info' | 'warning' | 'error' | 'debug', message: string, timestamp: number, stage?: string}>>([])

let currentEventSource: EventSource | null = null
let lastHeartbeatTime = ref<number>(Date.now())
let heartbeatCheckInterval: ReturnType<typeof setInterval> | null = null
let reconnectAttempts = 0
let currentDiagnoseParams: { params: DiagnoseParams; imageUrl: string } | null = null

/**
 * 返回上一页
 * 导航回首页
 */
const goBack = (): void => {
  router.push('/')
}

/**
 * 重置推理进度状态
 * 将所有进度相关状态恢复到初始值
 * @returns {void}
 */
const resetProgressState = (): void => {
  inferenceProgress.value = 0
  inferenceStage.value = ''
  inferenceMessage.value = ''
  isInferenceComplete.value = false
  sseConnectionState.value = SSE_CONNECTION_STATE.DISCONNECTED
  inferenceSteps.value = []
  inferenceLogs.value = []
  inferenceStartTime.value = Date.now()
}

/**
 * 清空日志
 */
const clearLogs = (): void => {
  inferenceLogs.value = []
}

/**
 * 关闭当前 SSE 连接
 * 安全关闭 EventSource 并重置连接状态
 * @returns {void}
 */
const closeEventSource = (): void => {
  if (heartbeatCheckInterval) {
    clearInterval(heartbeatCheckInterval)
    heartbeatCheckInterval = null
  }
  if (currentEventSource) {
    currentEventSource.close()
    currentEventSource = null
  }
  sseConnectionState.value = SSE_CONNECTION_STATE.DISCONNECTED
}

/**
 * 启动心跳监控
 * 检测连接是否活跃，超时则触发重连
 */
const startHeartbeatMonitor = (): void => {
  lastHeartbeatTime.value = Date.now()
  
  if (heartbeatCheckInterval) {
    clearInterval(heartbeatCheckInterval)
  }
  
  heartbeatCheckInterval = setInterval(() => {
    const elapsed = Date.now() - lastHeartbeatTime.value
    if (elapsed > SSE_CONFIG.HEARTBEAT_TIMEOUT && sseConnectionState.value === SSE_CONNECTION_STATE.CONNECTED) {
      console.warn('SSE 心跳超时，尝试重连...')
      handleReconnect()
    }
  }, 5000)
}

/**
 * 处理 SSE 重连
 * 在连接中断时尝试自动重连
 */
const handleReconnect = async (): Promise<void> => {
  if (reconnectAttempts >= SSE_CONFIG.MAX_RECONNECT_ATTEMPTS) {
    ElMessage.error('连接重试次数已达上限，请重新开始诊断')
    closeEventSource()
    sseConnectionState.value = SSE_CONNECTION_STATE.ERROR
    reconnectAttempts = 0
    return
  }
  
  reconnectAttempts++
  
  closeEventSource()
  
  await new Promise(resolve => setTimeout(resolve, SSE_CONFIG.RECONNECT_DELAY))
  
  if (currentDiagnoseParams) {
    try {
      const p = currentDiagnoseParams as { params: DiagnoseParams; imageUrl: string }
      await startStreamingDiagnosis(p.params, p.imageUrl)
      reconnectAttempts = 0
    } catch (error) {
      console.error('重连失败:', error)
    }
  }
}

/**
 * 构建 SSE 连接的 URL 参数
 * @param {DiagnoseParams} params - 诊断参数
 * @returns {URLSearchParams} URL 查询参数对象
 */
const buildSSEParams = (params: DiagnoseParams): URLSearchParams => {
  const searchParams = new URLSearchParams()
  
  if (params.symptoms) {
    searchParams.append('symptoms', params.symptoms)
  }
  
  if (params.weather) {
    searchParams.append('weather', params.weather)
  }
  
  if (params.growthStage) {
    searchParams.append('growth_stage', params.growthStage)
  }
  
  if (params.affectedPart) {
    searchParams.append('affected_part', params.affectedPart)
  }
  
  searchParams.append('enable_thinking', String(params.enableThinking))
  searchParams.append('use_graph_rag', String(params.useGraphRag))
  
  return searchParams
}

/**
 * 启动 SSE 流式诊断连接
 * 
 * 建立 SSE 连接并监听以下事件：
 * - start: 诊断开始，初始化进度状态
 * - progress: 进度更新，显示当前阶段和进度
 * - heartbeat: 心跳事件，保持连接活跃
 * - complete: 诊断完成，处理最终结果
 * - error: 错误事件，处理诊断过程中的错误
 * 
 * @param {DiagnoseParams} params - 诊断参数
 * @param {string} imageUrl - 上传后的图片 URL
 * @returns {Promise<void>}
 */
const startStreamingDiagnosis = async (params: DiagnoseParams, imageUrl: string): Promise<void> => {
  return new Promise((resolve, reject) => {
    const searchParams = buildSSEParams(params)
    
    if (imageUrl) {
      searchParams.append('image_url', imageUrl)
    }
    
    // 添加用户 ID 参数，用于保存诊断记录
    const userStore = useUserStore()
    if (userStore.userInfo?.id) {
      searchParams.append('user_id', userStore.userInfo.id.toString())
    }
    
    const baseURL = import.meta.env.VITE_API_BASE_URL || ''
    const url = `${baseURL}/diagnosis/fusion/stream?${searchParams.toString()}`
    
    sseConnectionState.value = SSE_CONNECTION_STATE.CONNECTING
    currentEventSource = new EventSource(url, { withCredentials: true })
    
    /**
     * 启动心跳监控
     * 定期检查心跳超时，如果超时则尝试重连
     */
    const startHeartbeatMonitor = (): void => {
      if (heartbeatCheckInterval) {
        clearInterval(heartbeatCheckInterval)
      }
      
      lastHeartbeatTime.value = Date.now()
      
      heartbeatCheckInterval = setInterval(() => {
        const now = Date.now()
        const elapsed = now - lastHeartbeatTime.value
        
        if (elapsed > SSE_CONFIG.HEARTBEAT_TIMEOUT && sseConnectionState.value === SSE_CONNECTION_STATE.CONNECTED) {
          console.warn('心跳超时，尝试重连...')
          handleReconnect()
        }
      }, 5000)
    }
    
    /**
     * 处理重连逻辑
     * 最多尝试 MAX_RECONNECT_ATTEMPTS 次
     */
    const handleReconnect = (): void => {
      if (reconnectAttempts >= SSE_CONFIG.MAX_RECONNECT_ATTEMPTS) {
        console.error('重连次数已达上限')
        sseConnectionState.value = SSE_CONNECTION_STATE.ERROR
        ElMessage.error('连接不稳定，请重新开始诊断')
        closeEventSource()
        reject(new Error('连接不稳定'))
        return
      }
      
      reconnectAttempts++
      
      closeEventSource()
      
      setTimeout(() => {
        if (currentDiagnoseParams) {
          const p = currentDiagnoseParams as { params: DiagnoseParams; imageUrl: string }
          startStreamingDiagnosis(p.params, p.imageUrl)
            .then(resolve)
            .catch(reject)
        }
      }, SSE_CONFIG.RECONNECT_DELAY)
    }
    
    /**
     * 处理 start 事件
     * 诊断开始时初始化进度状态
     */
    currentEventSource.addEventListener('start', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        sseConnectionState.value = SSE_CONNECTION_STATE.CONNECTED
        inferenceProgress.value = data.progress || 0
        inferenceStage.value = data.stage || 'init'
        inferenceMessage.value = data.message || '开始诊断...'
        lastHeartbeatTime.value = Date.now()
        startHeartbeatMonitor()
      } catch (e) {
        console.error('解析 start 事件数据失败:', e)
      }
    })
    
    /**
     * 处理 steps 事件
     * 接收步骤定义并更新步骤指示器
     */
    currentEventSource.addEventListener('steps', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        if (data.steps && Array.isArray(data.steps)) {
          inferenceSteps.value = data.steps
        }
        lastHeartbeatTime.value = Date.now()
      } catch (e) {
        console.error('解析 steps 事件数据失败:', e)
      }
    })
    
    /**
     * 处理 log 事件
     * 接收推理日志并添加到日志流
     */
    currentEventSource.addEventListener('log', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        inferenceLogs.value.push({
          level: data.level || 'info',
          message: data.message || '',
          timestamp: data.timestamp || Date.now() / 1000,
          stage: data.stage
        })
        // 限制日志数量，保留最近 100 条
        if (inferenceLogs.value.length > 100) {
          inferenceLogs.value = inferenceLogs.value.slice(-100)
        }
        lastHeartbeatTime.value = Date.now()
      } catch (e) {
        console.error('解析 log 事件数据失败:', e)
      }
    })
    
    /**
     * 处理 progress 事件
     * 更新诊断进度和阶段信息
     */
    currentEventSource.addEventListener('progress', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        inferenceProgress.value = data.progress || 0
        inferenceStage.value = data.stage || ''
        inferenceMessage.value = data.message || ''
        lastHeartbeatTime.value = Date.now()
      } catch (e) {
        console.error('解析进度数据失败:', e)
      }
    })
    
    /**
     * 处理 heartbeat 事件
     * 更新心跳时间，保持连接活跃
     */
    currentEventSource.addEventListener('heartbeat', (event: MessageEvent) => {
      try {
        lastHeartbeatTime.value = Date.now()
      } catch (e) {
        console.error('处理心跳事件失败:', e)
      }
    })
    
    /**
     * 处理 complete 事件
     * 诊断完成，处理最终结果并关闭连接
     */
    currentEventSource.addEventListener('complete', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        
        inferenceProgress.value = 100
        isInferenceComplete.value = true
        sseConnectionState.value = SSE_CONNECTION_STATE.DISCONNECTED
        
        if (heartbeatCheckInterval) {
          clearInterval(heartbeatCheckInterval)
          heartbeatCheckInterval = null
        }
        
        if (data.success) {
          diagnosisResult.value = data.diagnosis
          reasoningChain.value = data.reasoning_chain || []
          ElMessage.success('融合诊断完成')
          multiModalInputRef.value?.reset()
        } else {
          console.error('[SSE] 诊断失败:', data.error)
          ElMessage.error(data.error || '诊断失败')
        }
        
        closeEventSource()
        resolve()
      } catch (e) {
        console.error('[SSE] 解析完成数据失败:', e)
        console.error('[SSE] 原始 event.data:', event.data)
        sseConnectionState.value = SSE_CONNECTION_STATE.ERROR
        if (heartbeatCheckInterval) {
          clearInterval(heartbeatCheckInterval)
          heartbeatCheckInterval = null
        }
        closeEventSource()
        reject(e)
      }
    })
    
    /**
     * 处理 error 事件
     * 服务器主动发送的错误事件
     */
    currentEventSource.addEventListener('error', (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)
        sseConnectionState.value = SSE_CONNECTION_STATE.ERROR
        
        if (heartbeatCheckInterval) {
          clearInterval(heartbeatCheckInterval)
          heartbeatCheckInterval = null
        }
        
        ElMessage.error(data.message || '诊断过程中发生错误')
        closeEventSource()
        reject(new Error(data.message || '诊断过程中发生错误'))
      } catch (e) {
        if (currentEventSource?.readyState === EventSource.CLOSED) {
          return
        }
        sseConnectionState.value = SSE_CONNECTION_STATE.ERROR
        
        if (heartbeatCheckInterval) {
          clearInterval(heartbeatCheckInterval)
          heartbeatCheckInterval = null
        }
        
        ElMessage.error('连接诊断服务失败')
        closeEventSource()
        reject(new Error('连接诊断服务失败'))
      }
    })
    
    /**
     * 处理 SSE 连接级别的错误
     * 网络中断或连接失败时触发
     */
    currentEventSource.onerror = (error: Event) => {
      console.error('SSE 连接错误:', error)
      if (currentEventSource?.readyState === EventSource.CLOSED) {
        return
      }
      sseConnectionState.value = SSE_CONNECTION_STATE.ERROR
      
      if (heartbeatCheckInterval) {
        clearInterval(heartbeatCheckInterval)
        heartbeatCheckInterval = null
      }
      
      ElMessage.error('诊断服务连接中断')
      closeEventSource()
      reject(new Error('诊断服务连接中断'))
    }
    
    /**
     * 连接成功打开时的回调
     */
    currentEventSource.onopen = () => {
      sseConnectionState.value = SSE_CONNECTION_STATE.CONNECTED
      lastHeartbeatTime.value = Date.now()
      reconnectAttempts = 0
    }
  })
}

/**
 * 处理导出诊断报告
 * @param {string} format - 报告格式: pdf / html / both
 * @returns {Promise<void>}
 */
const handleExportReport = async (format: string): Promise<void> => {
  if (!diagnosisResult.value) {
    ElMessage.warning('请先完成诊断')
    return
  }
  
  const imageFile = multiModalInputRef.value?.getImageFile()
  if (!imageFile) {
    ElMessage.warning('无法获取诊断图像，请重新上传')
    return
  }
  
  isExporting.value = true
  try {
    const symptoms = multiModalInputRef.value?.getSymptoms() || ''
    const result = await generateReport(imageFile, symptoms, format)
    
    if (result?.report_files) {
      const files = result.report_files
      const downloadedFormats: string[] = []
      
      if (files.pdf) {
        const pdfUrl = getReportDownloadUrl(files.pdf.split('/').pop() || files.pdf)
        window.open(pdfUrl, '_blank')
        downloadedFormats.push('PDF')
      }
      if (files.html) {
        const htmlUrl = getReportDownloadUrl(files.html.split('/').pop() || files.html)
        window.open(htmlUrl, '_blank')
        downloadedFormats.push('HTML')
      }
      
      if (downloadedFormats.length > 0) {
        ElMessage.success(`${downloadedFormats.join(' 和 ')} 报告已生成，正在下载...`)
      } else {
        ElMessage.warning('报告生成成功，但未找到可下载的文件')
      }
    } else {
      ElMessage.warning('报告生成返回数据异常')
    }
  } catch (error: unknown) {
    console.error('导出报告失败:', error)
    const msg = error instanceof Error ? error.message : '报告生成失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    isExporting.value = false
  }
}

/**
 * 处理诊断请求
 * @param {DiagnoseParams} params - 诊断参数
 * @returns {Promise<void>}
 */
const handleDiagnose = async (params: DiagnoseParams): Promise<void> => {
  isDiagnosing.value = true
  resetProgressState()
  
  if (uploadedImageUrl.value) {
    URL.revokeObjectURL(uploadedImageUrl.value)
    uploadedImageUrl.value = ''
  }
  
  if (params.image) {
    uploadedImageUrl.value = URL.createObjectURL(params.image)
  }
  
  try {
    let serverImageUrl = ''
    
    if (params.image) {
      const formData = new FormData()
      formData.append('file', params.image)
      
      const uploadResponse = await http.post('/upload/image', formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }) as any
      
      if (uploadResponse && uploadResponse.success) {
        serverImageUrl = uploadResponse.url
      }
    }
    
    await startStreamingDiagnosis(params, serverImageUrl)
  } catch (error: unknown) {
    console.error('[Diagnosis] 诊断失败:', error)
    const msg = error instanceof Error ? error.message : '诊断服务暂时不可用'
    ElMessage.error(msg)
  } finally {
    isDiagnosing.value = false
    isInferenceComplete.value = false
    multiModalInputRef.value?.setDiagnosing(false)
  }
}

onUnmounted(() => {
  closeEventSource()
  if (uploadedImageUrl.value) {
    URL.revokeObjectURL(uploadedImageUrl.value)
  }
})
</script>

<style scoped>
.diagnosis-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-title {
  font-size: 18px;
  font-weight: bold;
}

.diagnosis-tabs {
  margin-bottom: 20px;
}

.result-section {
  margin-top: 20px;
}

.export-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
  padding: 16px 0;
}
</style>
