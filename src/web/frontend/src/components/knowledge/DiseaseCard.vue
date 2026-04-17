<template>
  <div class="disease-card-container">
    <el-card
      class="disease-card"
      shadow="hover"
      :body-style="{ padding: '0' }"
      @click="handleClick"
    >
      <!-- 病害图片 -->
      <div class="card-image-wrapper">
        <el-image
          :src="imageUrl"
          :alt="diseaseName"
          fit="cover"
          class="card-image"
          :hide-on-click-modal="true"
          :preview-src-list="previewMode ? [imageUrl] : []"
        >
          <template #placeholder>
            <div class="image-loading">
              <el-icon><loading /></el-icon>
              <span>加载中...</span>
            </div>
          </template>
          <template #error>
            <div class="image-error">
              <el-icon><picture-filled /></el-icon>
              <span>图片加载失败</span>
            </div>
          </template>
        </el-image>
        
        <!-- 病害标签 -->
        <div class="disease-tag" :class="getSeverityClass(severity)">
          {{ getSeverityText(severity) }}
        </div>
      </div>

      <!-- 卡片内容 -->
      <div class="card-content">
        <div class="card-header">
          <h3 class="disease-name">{{ diseaseName }}</h3>
          <el-tag
            v-if="category"
            size="small"
            type="info"
            effect="plain"
          >
            {{ category }}
          </el-tag>
        </div>

        <p class="symptoms-brief">
          <el-icon><warning /></el-icon>
          {{ symptomsBrief }}
        </p>

        <!-- 症状标签 -->
        <div class="symptom-tags" v-if="symptoms && symptoms.length > 0">
          <el-tag
            v-for="(symptom, index) in symptoms"
            :key="index"
            size="small"
            type="warning"
            effect="plain"
            class="symptom-tag"
          >
            {{ symptom }}
          </el-tag>
        </div>

        <!-- 卡片底部信息 -->
        <div class="card-footer">
          <div class="footer-item">
            <el-icon><clock /></el-icon>
            <span>高发期：{{ highSeason }}</span>
          </div>
          <div class="footer-item">
            <el-icon><sunny /></el-icon>
            <span>适宜温度：{{ suitableTemp }}</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="card-actions">
          <el-button
            type="primary"
            size="small"
            @click.stop="handleViewDetail"
          >
            <el-icon><document /></el-icon>
            查看详情
          </el-button>
          <el-button
            size="small"
            @click.stop="handlePrevention"
          >
            <el-icon><circle-check /></el-icon>
            防治方法
          </el-button>
        </div>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import {
  Loading,
  PictureFilled,
  Warning,
  Clock,
  Sunny,
  Document,
  CircleCheck
} from '@element-plus/icons-vue'

/**
 * 病害卡片组件 Props
 * @property {string} imageUrl - 病害图片 URL
 * @property {string} diseaseName - 病害名称
 * @property {string} symptomsBrief - 症状简介
 * @property {string[]} symptoms - 详细症状列表
 * @property {string} category - 病害类别
 * @property {string} severity - 严重程度
 * @property {string} highSeason - 高发季节
 * @property {string} suitableTemp - 适宜温度
 * @property {boolean} previewMode - 是否开启预览模式
 * @property {number | string} id - 病害 ID
 */
interface Props {
  imageUrl?: string
  diseaseName: string
  symptomsBrief: string
  symptoms?: string[]
  category?: string
  severity?: 'low' | 'medium' | 'high'
  highSeason?: string
  suitableTemp?: string
  previewMode?: boolean
  id?: number | string
}

const props = withDefaults(defineProps<Props>(), {
  imageUrl: '',
  symptoms: () => [],
  category: '',
  severity: 'medium',
  highSeason: '全年',
  suitableTemp: '20-30°C',
  previewMode: false,
  id: 0
})

/**
 * 组件暴露的事件
 * @event click - 点击卡片时触发
 * @event viewDetail - 查看详情时触发
 * @event prevention - 查看防治方法时触发
 */
const emit = defineEmits<{
  'click': [id: number | string]
  'viewDetail': [id: number | string]
  'prevention': [id: number | string]
}>()

/**
 * 获取严重程度对应的样式类
 */
const getSeverityClass = (severity: string): string => {
  const severityMap: Record<string, string> = {
    low: 'severity-low',
    medium: 'severity-medium',
    high: 'severity-high'
  }
  return severityMap[severity] || 'severity-medium'
}

/**
 * 获取严重程度对应的文本
 */
const getSeverityText = (severity: string): string => {
  const severityMap: Record<string, string> = {
    low: '轻度',
    medium: '中度',
    high: '重度'
  }
  return severityMap[severity] || '中度'
}

/**
 * 处理卡片点击
 */
const handleClick = () => {
  emit('click', props.id)
}

/**
 * 处理查看详情
 */
const handleViewDetail = () => {
  emit('viewDetail', props.id)
}

/**
 * 处理防治方法
 */
const handlePrevention = () => {
  emit('prevention', props.id)
}
</script>

<style scoped>
.disease-card-container {
  width: 100%;
  padding: 10px;
}

.disease-card {
  width: 100%;
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
  cursor: pointer;
}

.disease-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
}

/* 图片区域 */
.card-image-wrapper {
  position: relative;
  width: 100%;
  height: 200px;
  overflow: hidden;
  background-color: #f5f7fa;
}

.card-image {
  width: 100%;
  height: 100%;
  transition: transform 0.3s;
}

.disease-card:hover .card-image {
  transform: scale(1.05);
}

.image-loading,
.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
}

.image-error {
  color: #f56c6c;
}

.image-loading .el-icon,
.image-error .el-icon {
  font-size: 40px;
  margin-bottom: 8px;
}

/* 严重程度标签 */
.disease-tag {
  position: absolute;
  top: 12px;
  right: 12px;
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.severity-low {
  background-color: #67c23a;
}

.severity-medium {
  background-color: #e6a23c;
}

.severity-high {
  background-color: #f56c6c;
}

/* 卡片内容区域 */
.card-content {
  padding: 16px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.disease-name {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #303133;
  flex: 1;
}

.symptoms-brief {
  display: flex;
  align-items: flex-start;
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #606266;
  line-height: 1.6;
}

.symptoms-brief .el-icon {
  margin-right: 6px;
  color: #e6a23c;
  flex-shrink: 0;
  margin-top: 2px;
}

/* 症状标签 */
.symptom-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.symptom-tag {
  margin-right: 0;
}

/* 卡片底部信息 */
.card-footer {
  display: flex;
  justify-content: space-between;
  padding: 12px 0;
  border-top: 1px solid #ebeef5;
  margin-bottom: 12px;
}

.footer-item {
  display: flex;
  align-items: center;
  font-size: 13px;
  color: #909399;
}

.footer-item .el-icon {
  margin-right: 6px;
  color: #409eff;
}

/* 操作按钮 */
.card-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.card-actions .el-button {
  flex: 1;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .card-image-wrapper {
    height: 180px;
  }
  
  .disease-name {
    font-size: 16px;
  }
  
  .card-footer {
    flex-direction: column;
    gap: 8px;
  }
}
</style>
