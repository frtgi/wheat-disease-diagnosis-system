<template>
  <div class="image-uploader-container">
    <el-card class="uploader-card">
      <template #header>
        <div class="card-header">
          <span class="title">上传图片</span>
          <span class="subtitle">支持 JPG、PNG 格式，最大 5MB</span>
        </div>
      </template>

      <el-upload
        ref="uploadRef"
        class="image-uploader"
        drag
        :action="uploadUrl"
        :headers="headers"
        :on-success="handleSuccess"
        :on-error="handleError"
        :on-progress="handleProgress"
        :before-upload="beforeUpload"
        :on-change="handleChange"
        :file-list="fileList"
        :limit="1"
        :accept="acceptFormats"
      >
        <el-icon class="el-icon--upload">
          <upload-filled />
        </el-icon>
        <div class="el-upload__text">
          将图片拖到此处，或<em>点击上传</em>
        </div>
        <template #tip>
          <div class="el-upload__tip">
            支持 JPG/PNG 格式，图片大小不超过 5MB
          </div>
        </template>
      </el-upload>

      <!-- 图片预览区域 -->
      <div v-if="imagePreviewUrl" class="preview-container">
        <el-image
          :src="imagePreviewUrl"
          fit="contain"
          class="preview-image"
          :preview-src-list="[imagePreviewUrl]"
        >
          <template #placeholder>
            <div class="image-loading">
              <el-icon><loading /></el-icon>
              <span>加载中...</span>
            </div>
          </template>
        </el-image>
        
        <!-- 上传进度显示 -->
        <div v-if="uploading" class="progress-overlay">
          <el-progress
            type="circle"
            :percentage="uploadProgress"
            :stroke-width="10"
            :color="customColors"
          />
          <span class="progress-text">上传中...</span>
        </div>

        <!-- 操作按钮 -->
        <div class="preview-actions">
          <el-button
            type="danger"
            size="small"
            @click="handleRemove"
            :disabled="uploading"
          >
            <el-icon><delete /></el-icon>
            删除
          </el-button>
          <el-button
            type="primary"
            size="small"
            @click="handleDiagnose"
            :loading="uploading"
            :disabled="!imagePreviewUrl"
          >
            <el-icon><circle-check /></el-icon>
            开始诊断
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled, Loading, Delete, CircleCheck } from '@element-plus/icons-vue'
import type { UploadUserFile, UploadProgressEvent, UploadRequestOptions } from 'element-plus'

/**
 * 图片上传组件 Props
 * @property {string} uploadUrl - 上传接口地址
 * @property {string} token - 认证 Token
 */
interface Props {
  uploadUrl?: string
  token?: string
}

const props = withDefaults(defineProps<Props>(), {
  uploadUrl: '/api/v1/diagnosis/upload',
  token: ''
})

/**
 * 组件暴露的事件
 * @event update:imageUrl - 图片 URL 变化时触发
 * @event upload - 开始上传时触发
 * @event success - 上传成功时触发
 * @event error - 上传失败时触发
 */
const emit = defineEmits<{
  'update:imageUrl': [url: string]
  'upload': [file: File]
  'success': [response: any, file: File]
  'error': [error: Error, file: File]
  'diagnose': [imageUrl: string]
}>()

// 上传组件引用
const uploadRef = ref()

// 文件列表
const fileList = ref<UploadUserFile[]>([])

// 图片预览 URL
const imagePreviewUrl = ref<string>('')

// 上传状态
const uploading = ref<boolean>(false)

// 上传进度
const uploadProgress = ref<number>(0)

// 允许的文件格式
const acceptFormats = '.jpg,.jpeg,.png,image/jpeg,image/png'

// 最大文件大小（5MB）
const MAX_FILE_SIZE = 5 * 1024 * 1024

// 请求头配置
const headers = computed(() => ({
  Authorization: props.token ? `Bearer ${props.token}` : ''
}))

// 进度条颜色配置
const customColors = [
  { color: '#f56c6c', percentage: 20 },
  { color: '#e6a23c', percentage: 40 },
  { color: '#5cb87a', percentage: 60 },
  { color: '#1989fa', percentage: 80 },
  { color: '#6f7ad3', percentage: 100 }
]

/**
 * 上传前验证
 * 验证文件格式和大小
 */
const beforeUpload = (file: File): boolean => {
  // 验证文件类型
  const isValidType = file.type === 'image/jpeg' || 
                      file.type === 'image/png' ||
                      file.name.endsWith('.jpg') ||
                      file.name.endsWith('.jpeg') ||
                      file.name.endsWith('.png')
  
  if (!isValidType) {
    ElMessage.error('只能上传 JPG/PNG 格式的图片！')
    return false
  }

  // 验证文件大小
  const isLt5M = file.size <= MAX_FILE_SIZE
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB！')
    return false
  }

  return true
}

/**
 * 文件变化处理
 * 生成预览 URL
 */
const handleChange = (uploadFile: UploadUserFile) => {
  if (uploadFile.raw) {
    // 生成预览 URL
    imagePreviewUrl.value = URL.createObjectURL(uploadFile.raw)
    // 触发自定义上传事件
    emit('upload', uploadFile.raw)
  }
}

/**
 * 上传进度处理
 */
const handleProgress = (event: UploadProgressEvent) => {
  uploading.value = true
  uploadProgress.value = Math.round(event.percent)
}

/**
 * 上传成功处理
 */
const handleSuccess = (response: any, uploadFile: UploadUserFile) => {
  uploading.value = false
  uploadProgress.value = 0
  
  ElMessage.success('上传成功！')
  
  // 如果返回了图片 URL，更新预览
  if (response.data && response.data.imageUrl) {
    emit('update:imageUrl', response.data.imageUrl)
  } else if (response.data && response.data.url) {
    emit('update:imageUrl', response.data.url)
  }
  
  // 触发成功事件
  emit('success', response, uploadFile.raw as File)
}

/**
 * 上传失败处理
 */
const handleError = (error: Error, uploadFile: UploadUserFile) => {
  uploading.value = false
  uploadProgress.value = 0
  
  ElMessage.error('上传失败，请重试')
  
  // 触发错误事件
  emit('error', error, uploadFile.raw as File)
}

/**
 * 删除图片处理
 */
const handleRemove = () => {
  // 清除预览 URL
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
    imagePreviewUrl.value = ''
  }
  
  // 清空文件列表
  fileList.value = []
  uploadRef.value?.clearFiles()
  
  // 通知父组件清除 URL
  emit('update:imageUrl', '')
}

/**
 * 开始诊断
 */
const handleDiagnose = () => {
  if (imagePreviewUrl.value) {
    emit('diagnose', imagePreviewUrl.value)
  }
}

// 组件卸载时清理资源
defineExpose({
  clearFiles: () => {
    handleRemove()
  },
  getPreviewUrl: () => imagePreviewUrl.value
})
</script>

<style scoped>
.image-uploader-container {
  width: 100%;
  padding: 20px;
}

.uploader-card {
  max-width: 800px;
  margin: 0 auto;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.subtitle {
  font-size: 12px;
  color: #909399;
}

.image-uploader {
  width: 100%;
}

.image-uploader :deep(.el-upload) {
  width: 100%;
}

.image-uploader :deep(.el-upload-dragger) {
  width: 100%;
  height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.el-icon--upload {
  font-size: 67px;
  color: #8c939d;
  margin-bottom: 16px;
}

.el-upload__text {
  color: #606266;
  font-size: 14px;
}

.el-upload__text em {
  color: #409eff;
  font-style: normal;
}

.el-upload__tip {
  text-align: center;
  color: #909399;
  font-size: 12px;
  margin-top: 8px;
}

/* 预览区域样式 */
.preview-container {
  position: relative;
  margin-top: 20px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 500px;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
}

.image-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #909399;
}

.image-loading .el-icon {
  font-size: 40px;
  margin-bottom: 10px;
}

/* 进度遮罩层 */
.progress-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border-radius: 8px;
}

.progress-text {
  margin-top: 16px;
  font-size: 14px;
  color: #606266;
}

/* 操作按钮 */
.preview-actions {
  margin-top: 16px;
  display: flex;
  justify-content: center;
  gap: 12px;
}
</style>
