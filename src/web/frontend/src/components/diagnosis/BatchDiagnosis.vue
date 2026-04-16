<template>
  <div class="batch-diagnosis-container">
    <el-card class="upload-card">
      <template #header>
        <div class="card-header">
          <el-icon><UploadFilled /></el-icon>
          <span>批量图像上传</span>
          <el-tag type="info" size="small">最多 10 张</el-tag>
        </div>
      </template>

      <el-upload
        ref="batchUploadRef"
        class="batch-uploader"
        drag
        multiple
        :auto-upload="false"
        :on-change="handleFileChange"
        :on-remove="handleFileRemove"
        :file-list="fileList"
        :limit="10"
        :on-exceed="handleExceed"
        accept=".jpg,.jpeg,.png,image/jpeg,image/png"
        list-type="picture-card"
      >
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">
          拖拽图片到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 JPG/PNG 格式，单张最大 5MB，最多 10 张
          </div>
        </template>
      </el-upload>

      <el-form :model="batchForm" label-width="100px" class="batch-form">
        <el-form-item label="症状描述">
          <el-input
            v-model="batchForm.symptoms"
            type="textarea"
            :rows="3"
            placeholder="可选：描述共同症状，将应用于所有图像"
            resize="none"
          />
        </el-form-item>
        <el-form-item label="增强选项">
          <el-checkbox v-model="batchForm.thinkingMode" label="Thinking 推理链" />
          <el-checkbox v-model="batchForm.useGraphRag" label="GraphRAG 知识增强" />
        </el-form-item>
      </el-form>

      <div class="batch-actions">
        <el-button
          type="primary"
          size="large"
          :loading="isBatching"
          :disabled="!canBatchDiagnose"
          @click="handleBatchDiagnose"
        >
          <el-icon><CircleCheck /></el-icon>
          开始批量诊断（{{ validFileCount }} 张）
        </el-button>
      </div>
    </el-card>

    <el-card v-if="isBatching" class="progress-card">
      <template #header>
        <div class="card-header">
          <el-icon class="rotating"><Loading /></el-icon>
          <span>批量诊断进行中...</span>
        </div>
      </template>
      <el-progress
        :percentage="batchProgress"
        :stroke-width="16"
        striped
        striped-flow
        :format="() => `${completedCount} / ${totalBatchCount}`"
      />
      <p class="progress-hint">请耐心等待，批量诊断可能需要较长时间</p>
    </el-card>

    <el-card v-if="batchResult" class="result-card">
      <template #header>
        <div class="card-header">
          <el-icon><DataAnalysis /></el-icon>
          <span>批量诊断结果</span>
        </div>
      </template>

      <el-row :gutter="16" class="summary-row">
        <el-col :span="6">
          <el-statistic title="总图像数" :value="batchResult.summary.total_images" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="成功数" :value="batchResult.summary.success_count">
            <template #suffix>
              <el-tag type="success" size="small">{{ batchResult.summary.success_rate }}%</el-tag>
            </template>
          </el-statistic>
        </el-col>
        <el-col :span="6">
          <el-statistic title="失败数" :value="batchResult.summary.failed_count" />
        </el-col>
        <el-col :span="6">
          <el-statistic title="缓存命中" :value="batchResult.summary.cache_hits">
            <template #suffix>
              <el-tag type="warning" size="small">{{ batchResult.summary.cache_hit_rate }}%</el-tag>
            </template>
          </el-statistic>
        </el-col>
      </el-row>

      <el-descriptions :column="2" border size="small" class="perf-desc">
        <el-descriptions-item label="总耗时">
          {{ formatTime(batchResult.performance.total_time_ms) }}
        </el-descriptions-item>
        <el-descriptions-item label="平均每张耗时">
          {{ formatTime(batchResult.performance.avg_time_per_image_ms) }}
        </el-descriptions-item>
      </el-descriptions>

      <el-table :data="batchResult.results" stripe border class="result-table">
        <el-table-column type="index" label="序号" width="60" />
        <el-table-column prop="filename" label="文件名" width="180" show-overflow-tooltip />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.success ? 'success' : 'danger'" size="small">
              {{ row.success ? '成功' : '失败' }}
            </el-tag>
            <el-tag v-if="row.cache_hit" type="warning" size="small" style="margin-left: 4px">
              缓存
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="诊断结果">
          <template #default="{ row }">
            <template v-if="row.success && row.diagnosis">
              <div class="diagnosis-brief">
                <el-tag type="primary" size="small">{{ row.diagnosis.disease_name || '未知' }}</el-tag>
                <span v-if="row.diagnosis.confidence" class="confidence-text">
                  置信度: {{ Math.round(row.diagnosis.confidence * 100) }}%
                </span>
              </div>
            </template>
            <template v-else-if="row.error">
              <el-text type="danger" size="small">{{ row.error }}</el-text>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  UploadFilled,
  CircleCheck,
  Loading,
  DataAnalysis
} from '@element-plus/icons-vue'
import type { UploadUserFile, UploadFile } from 'element-plus'
import { diagnoseBatch } from '@/api/diagnosis'
import type { BatchDiagnosisResponse } from '@/api/diagnosis'

/**
 * 批量诊断组件
 * 支持多图上传、进度显示和结果汇总
 */

const MAX_FILE_SIZE = 5 * 1024 * 1024
const MAX_FILES = 10

const batchUploadRef = ref()
const fileList = ref<UploadUserFile[]>([])
const imageFiles = ref<File[]>([])

const batchForm = ref({
  symptoms: '',
  thinkingMode: false,
  useGraphRag: false
})

const isBatching = ref(false)
const batchProgress = ref(0)
const completedCount = ref(0)
const totalBatchCount = ref(0)
const batchResult = ref<BatchDiagnosisResponse | null>(null)

/**
 * 有效文件数量
 */
const validFileCount = computed(() => imageFiles.value.length)

/**
 * 是否可以开始批量诊断
 */
const canBatchDiagnose = computed(() => imageFiles.value.length > 0 && !isBatching.value)

/**
 * 处理文件选择变化
 */
const handleFileChange = (uploadFile: UploadFile) => {
  if (!uploadFile.raw) return

  if (!validateFile(uploadFile.raw)) {
    fileList.value = fileList.value.filter(f => f.uid !== uploadFile.uid)
    return
  }

  if (imageFiles.value.length >= MAX_FILES) {
    ElMessage.warning(`最多支持 ${MAX_FILES} 张图像`)
    fileList.value = fileList.value.filter(f => f.uid !== uploadFile.uid)
    return
  }

  imageFiles.value.push(uploadFile.raw)
}

/**
 * 处理文件移除
 */
const handleFileRemove = (uploadFile: UploadFile) => {
  const index = imageFiles.value.findIndex(
    (_, i) => fileList.value[i]?.uid === uploadFile.uid
  )
  if (index > -1) {
    imageFiles.value.splice(index, 1)
  }
}

/**
 * 处理超出限制
 */
const handleExceed = () => {
  ElMessage.warning(`最多支持 ${MAX_FILES} 张图像`)
}

/**
 * 验证文件格式和大小
 */
const validateFile = (file: File): boolean => {
  const isValidType = file.type === 'image/jpeg' ||
    file.type === 'image/png' ||
    file.name.endsWith('.jpg') ||
    file.name.endsWith('.jpeg') ||
    file.name.endsWith('.png')

  if (!isValidType) {
    ElMessage.error('只能上传 JPG/PNG 格式的图片！')
    return false
  }

  if (file.size > MAX_FILE_SIZE) {
    ElMessage.error('图片大小不能超过 5MB！')
    return false
  }

  return true
}

/**
 * 处理批量诊断
 */
const handleBatchDiagnose = async () => {
  if (!canBatchDiagnose.value) return

  isBatching.value = true
  batchProgress.value = 0
  completedCount.value = 0
  totalBatchCount.value = imageFiles.value.length
  batchResult.value = null

  const progressInterval = setInterval(() => {
    if (batchProgress.value < 90) {
      batchProgress.value += Math.random() * 3
      completedCount.value = Math.min(
        Math.floor(batchProgress.value / 100 * totalBatchCount.value),
        totalBatchCount.value - 1
      )
    }
  }, 2000)

  try {
    const result = await diagnoseBatch(
      imageFiles.value,
      batchForm.value.symptoms,
      batchForm.value.thinkingMode,
      batchForm.value.useGraphRag
    )

    batchProgress.value = 100
    completedCount.value = result.summary.total_images
    batchResult.value = result

    ElMessage.success(result.message || '批量诊断完成')
  } catch (error: unknown) {
    console.error('批量诊断失败:', error)
    const msg = error instanceof Error ? error.message : '批量诊断失败，请稍后重试'
    ElMessage.error(msg)
  } finally {
    clearInterval(progressInterval)
    isBatching.value = false
  }
}

/**
 * 格式化时间显示
 */
const formatTime = (ms: number): string => {
  if (ms < 1000) return `${Math.round(ms)} ms`
  const seconds = ms / 1000
  if (seconds < 60) return `${seconds.toFixed(1)} 秒`
  const minutes = Math.floor(seconds / 60)
  const remainSeconds = Math.round(seconds % 60)
  return `${minutes} 分 ${remainSeconds} 秒`
}
</script>

<style scoped>
.batch-diagnosis-container {
  width: 100%;
}

.upload-card,
.progress-card,
.result-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  color: #303133;
}

.batch-uploader :deep(.el-upload-dragger) {
  width: 100%;
  padding: 20px;
}

.batch-form {
  margin-top: 16px;
}

.batch-actions {
  display: flex;
  justify-content: center;
  padding: 16px 0;
}

.progress-card .rotating {
  animation: rotate 1.5s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.progress-hint {
  margin: 12px 0 0;
  text-align: center;
  color: #909399;
  font-size: 13px;
}

.summary-row {
  margin-bottom: 20px;
  padding: 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.perf-desc {
  margin-bottom: 16px;
}

.result-table {
  margin-top: 16px;
}

.diagnosis-brief {
  display: flex;
  align-items: center;
  gap: 8px;
}

.confidence-text {
  font-size: 12px;
  color: #909399;
}
</style>
