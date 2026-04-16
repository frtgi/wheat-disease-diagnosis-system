<template>
  <div class="multimodal-input-container">
    <el-row :gutter="20">
      <el-col :span="12">
        <el-card class="input-card image-card">
          <template #header>
            <div class="card-header">
              <el-icon><picture-filled /></el-icon>
              <span>图像上传</span>
            </div>
          </template>
          
          <el-upload
            ref="uploadRef"
            class="image-uploader"
            drag
            :auto-upload="false"
            :on-change="handleImageChange"
            :on-remove="handleImageRemove"
            :file-list="fileList"
            :limit="1"
            accept=".jpg,.jpeg,.png,image/jpeg,image/png"
          >
            <el-icon class="el-icon--upload"><upload-filled /></el-icon>
            <div class="el-upload__text">
              拖拽图片到此处，或<em>点击上传</em>
            </div>
            <template #tip>
              <div class="el-upload__tip">
                支持 JPG/PNG 格式，最大 5MB
              </div>
            </template>
          </el-upload>
          
          <div v-if="imagePreviewUrl" class="preview-container">
            <el-image
              :src="imagePreviewUrl"
              fit="contain"
              class="preview-image"
              :preview-src-list="[imagePreviewUrl]"
            />
          </div>
        </el-card>
      </el-col>
      
      <el-col :span="12">
        <el-card class="input-card text-card">
          <template #header>
            <div class="card-header">
              <el-icon><document /></el-icon>
              <span>症状描述</span>
            </div>
          </template>
          
          <el-input
            v-model="symptomsText"
            type="textarea"
            :rows="6"
            placeholder="请描述病害症状，如：叶片出现黄色条纹状病斑，边缘有红色孢子堆..."
            resize="none"
          />
        </el-card>
      </el-col>
    </el-row>
    
    <el-card class="input-card env-card">
      <template #header>
        <div class="card-header">
          <el-icon><setting /></el-icon>
          <span>环境因素（可选）</span>
        </div>
      </template>
      
      <el-form :model="envForm" label-width="100px" class="env-form">
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="天气条件">
              <el-select v-model="envForm.weather" placeholder="选择天气" clearable>
                <el-option label="晴朗" value="sunny" />
                <el-option label="阴天" value="cloudy" />
                <el-option label="阴雨" value="rainy" />
                <el-option label="高温高湿" value="hot_humid" />
                <el-option label="低温干燥" value="cold_dry" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="生长阶段">
              <el-select v-model="envForm.growthStage" placeholder="选择阶段" clearable>
                <el-option label="苗期" value="seedling" />
                <el-option label="分蘖期" value="tillering" />
                <el-option label="拔节期" value="jointing" />
                <el-option label="抽穗期" value="heading" />
                <el-option label="灌浆期" value="filling" />
                <el-option label="成熟期" value="maturity" />
              </el-select>
            </el-form-item>
          </el-col>
          
          <el-col :span="8">
            <el-form-item label="发病部位">
              <el-select v-model="envForm.affectedPart" placeholder="选择部位" clearable>
                <el-option label="叶片" value="leaf" />
                <el-option label="茎秆" value="stem" />
                <el-option label="穗部" value="spike" />
                <el-option label="根部" value="root" />
                <el-option label="叶鞘" value="sheath" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
    </el-card>
    
    <div class="action-bar">
      <el-checkbox v-model="enableThinking" label="启用 Thinking 推理链" />
      <el-checkbox v-model="useGraphRag" label="启用 GraphRAG 知识增强" />
      
      <el-button
        type="primary"
        size="large"
        :loading="diagnosing"
        :disabled="!canDiagnose"
        @click="handleDiagnose"
      >
        <el-icon><circle-check /></el-icon>
        开始融合诊断
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import {
  PictureFilled,
  Document,
  Setting,
  UploadFilled,
  CircleCheck
} from '@element-plus/icons-vue'
import type { UploadUserFile, UploadFile } from 'element-plus'

/**
 * 多模态输入组件
 * 支持图像上传和文本症状描述同时输入
 */

interface EnvForm {
  weather: string
  growthStage: string
  affectedPart: string
}

interface DiagnoseParams {
  image: File | null
  symptoms: string
  weather: string
  growthStage: string
  affectedPart: string
  enableThinking: boolean
  useGraphRag: boolean
}

const emit = defineEmits<{
  'diagnose': [params: DiagnoseParams]
}>()

const uploadRef = ref()
const fileList = ref<UploadUserFile[]>([])
const imagePreviewUrl = ref<string>('')
const imageFile = ref<File | null>(null)

const symptomsText = ref<string>('')

const envForm = ref<EnvForm>({
  weather: '',
  growthStage: '',
  affectedPart: ''
})

const enableThinking = ref<boolean>(true)
const useGraphRag = ref<boolean>(true)
const diagnosing = ref<boolean>(false)

const MAX_FILE_SIZE = 5 * 1024 * 1024

const canDiagnose = computed(() => {
  return imageFile.value !== null || symptomsText.value.trim() !== ''
})

const handleImageChange = (uploadFile: UploadFile) => {
  if (!uploadFile.raw) return
  
  if (!validateFile(uploadFile.raw)) return
  
  imageFile.value = uploadFile.raw
  
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
  }
  imagePreviewUrl.value = URL.createObjectURL(uploadFile.raw)
}

const handleImageRemove = () => {
  imageFile.value = null
  if (imagePreviewUrl.value) {
    URL.revokeObjectURL(imagePreviewUrl.value)
    imagePreviewUrl.value = ''
  }
}

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

  const isLt5M = file.size <= MAX_FILE_SIZE
  if (!isLt5M) {
    ElMessage.error('图片大小不能超过 5MB！')
    return false
  }

  return true
}

const handleDiagnose = () => {
  if (!canDiagnose.value) {
    ElMessage.warning('请至少提供图像或症状描述中的一种输入')
    return
  }
  
  diagnosing.value = true
  
  emit('diagnose', {
    image: imageFile.value,
    symptoms: symptomsText.value,
    weather: envForm.value.weather,
    growthStage: envForm.value.growthStage,
    affectedPart: envForm.value.affectedPart,
    enableThinking: enableThinking.value,
    useGraphRag: useGraphRag.value
  })
}

const setDiagnosing = (value: boolean) => {
  diagnosing.value = value
}

const reset = () => {
  handleImageRemove()
  symptomsText.value = ''
  envForm.value = {
    weather: '',
    growthStage: '',
    affectedPart: ''
  }
  fileList.value = []
  uploadRef.value?.clearFiles()
}

defineExpose({
  setDiagnosing,
  reset,
  getImageFile: () => imageFile.value,
  getSymptoms: () => symptomsText.value
})
</script>

<style scoped>
.multimodal-input-container {
  width: 100%;
}

.input-card {
  margin-bottom: 20px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: bold;
  color: #303133;
}

.image-uploader {
  width: 100%;
}

.image-uploader :deep(.el-upload) {
  width: 100%;
}

.image-uploader :deep(.el-upload-dragger) {
  width: 100%;
  height: 200px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  transition: all 0.3s;
}

.image-uploader :deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

.el-icon--upload {
  font-size: 48px;
  color: #8c939d;
  margin-bottom: 12px;
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

.preview-container {
  margin-top: 16px;
  text-align: center;
}

.preview-image {
  max-width: 100%;
  max-height: 200px;
  border-radius: 8px;
}

.env-form {
  margin-top: 10px;
}

.env-form :deep(.el-select) {
  width: 100%;
}

.action-bar {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 24px;
  padding: 20px;
  background-color: #f5f7fa;
  border-radius: 8px;
}
</style>
