<template>
  <div class="fusion-result-container">
    <el-card v-if="result" class="result-card">
      <template #header>
        <div class="result-header">
          <div class="header-left">
            <el-icon class="result-icon" :class="confidenceClass">
              <circle-check-filled v-if="confidenceLevel === 'high'" />
              <warning-filled v-else-if="confidenceLevel === 'medium'" />
              <circle-close-filled v-else />
            </el-icon>
            <div class="header-info">
              <h3 class="disease-name">
                {{ result.disease_name || '未知病害' }}
                <span v-if="result.disease_name_en" class="disease-name-en">
                  ({{ result.disease_name_en }})
                </span>
              </h3>
              <span class="confidence-text">
                综合置信度: {{ formatConfidence(result.confidence) }}
                <el-tag v-if="result.severity" :type="getSeverityTagType(result.severity)" size="small" class="severity-tag">
                  {{ getSeverityLabel(result.severity) }}
                </el-tag>
              </span>
            </div>
          </div>
          <el-tag :type="confidenceTagType" size="large">
            {{ confidenceLabel }}
          </el-tag>
        </div>
      </template>
      
      <el-tabs v-model="activeTab" class="result-tabs">
        <el-tab-pane label="诊断概览" name="overview">
          <div class="overview-section">
            <div class="confidence-grid">
              <div class="confidence-item">
                <div class="confidence-header">
                  <span class="confidence-label">综合置信度</span>
                  <el-tag :type="getConfidenceTagType(result.confidence)" size="small">
                    {{ getConfidenceLevelLabel(result.confidence) }}
                  </el-tag>
                </div>
                <el-progress
                  :percentage="Math.round((result.confidence || 0) * 100)"
                  :color="confidenceColor"
                  :stroke-width="12"
                  striped
                  striped-flow
                />
              </div>
              <div class="confidence-item">
                <div class="confidence-header">
                  <span class="confidence-label">视觉置信度</span>
                  <el-tag type="success" size="small">
                    {{ getConfidenceLevelLabel(result.visual_confidence) }}
                  </el-tag>
                </div>
                <el-progress
                  :percentage="Math.round((result.visual_confidence || 0) * 100)"
                  color="#67c23a"
                  :stroke-width="12"
                  striped
                  striped-flow
                />
              </div>
              <div class="confidence-item">
                <div class="confidence-header">
                  <span class="confidence-label">文本置信度</span>
                  <el-tag type="primary" size="small">
                    {{ getConfidenceLevelLabel(result.textual_confidence) }}
                  </el-tag>
                </div>
                <el-progress
                  :percentage="Math.round((result.textual_confidence || 0) * 100)"
                  color="#409eff"
                  :stroke-width="12"
                  striped
                  striped-flow
                />
              </div>
              <div class="confidence-item" v-if="result.knowledge_confidence">
                <div class="confidence-header">
                  <span class="confidence-label">知识置信度</span>
                  <el-tag type="warning" size="small">
                    {{ getConfidenceLevelLabel(result.knowledge_confidence) }}
                  </el-tag>
                </div>
                <el-progress
                  :percentage="Math.round((result.knowledge_confidence || 0) * 100)"
                  color="#e6a23c"
                  :stroke-width="12"
                  striped
                  striped-flow
                />
              </div>
            </div>
            
            <el-descriptions :column="2" border class="info-descriptions">
              <el-descriptions-item label="推理时间">
                {{ result.inference_time_ms || 0 }} ms
              </el-descriptions-item>
            </el-descriptions>
            
            <div class="description-section" v-if="result.description">
              <h4><el-icon><document /></el-icon> 病害描述</h4>
              <p class="description-text">{{ result.description }}</p>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="视觉检测" name="visual" v-if="hasVisualDetection">
          <div class="visual-section">
            <AnnotatedImage
              :annotated-image="result.annotated_image"
              :image-src="imageSrc"
              :detections="roiBoxes"
            />
            
            <div v-if="roiBoxes.length > 0" class="detection-summary">
              <el-divider content-position="left">
                <el-icon><data-analysis /></el-icon>
                检测结果详情
              </el-divider>
              <el-table :data="roiBoxes" stripe border size="small">
                <el-table-column type="index" label="序号" width="60" />
                <el-table-column prop="class_name" label="病害类型" width="150">
                  <template #default="{ row }">
                    <el-tag :type="getRoiTagType(row.confidence)" size="small">
                      {{ row.class_name }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="confidence" label="置信度" width="180">
                  <template #default="{ row }">
                    <el-progress
                      :percentage="Math.round(row.confidence * 100)"
                      :color="getConfidenceColor(row.confidence)"
                      :stroke-width="16"
                    />
                  </template>
                </el-table-column>
                <el-table-column prop="box" label="边界框坐标">
                  <template #default="{ row }">
                    <span v-if="row.box && row.box.length >= 4" class="box-coords">
                      [{{ row.box.map((v: number) => Math.round(v)).join(', ') }}]
                    </span>
                    <span v-else class="no-box">-</span>
                  </template>
                </el-table-column>
              </el-table>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="推理链" name="reasoning" v-if="reasoningChain && reasoningChain.length > 0">
          <div class="reasoning-section">
            <div class="reasoning-header">
              <el-checkbox v-model="expandAll">展开全部</el-checkbox>
              <span class="reasoning-count">共 {{ reasoningChain.length }} 步</span>
            </div>
            <el-timeline>
              <el-timeline-item
                v-for="(step, index) in reasoningChain"
                :key="index"
                :type="getTimelineType(index)"
                :hollow="index < reasoningChain.length - 1"
                placement="top"
              >
                <el-card class="reasoning-card" shadow="hover">
                  <template #header>
                    <div class="reasoning-card-header">
                      <span class="reasoning-step-title">步骤 {{ index + 1 }}</span>
                      <el-button 
                        type="primary" 
                        link 
                        @click="toggleStep(index)"
                      >
                        {{ expandedSteps[index] ? '收起' : '展开' }}
                      </el-button>
                    </div>
                  </template>
                  <div class="reasoning-step" :class="{ 'expanded': expandedSteps[index] }">
                    {{ step.length > 100 && !expandedSteps[index] ? step.substring(0, 100) + '...' : step }}
                  </div>
                </el-card>
              </el-timeline-item>
            </el-timeline>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="症状特征" name="symptoms" v-if="symptoms && symptoms.length > 0">
          <div class="symptoms-section">
            <el-alert type="info" :closable="false" class="section-alert">
              <template #title>
                <el-icon><warning-filled /></el-icon>
                病害症状识别
              </template>
            </el-alert>
            <div class="symptoms-list">
              <div v-for="(symptom, index) in symptoms" :key="index" class="symptom-item">
                <el-icon class="symptom-icon"><circle-check-filled /></el-icon>
                <span class="symptom-text">{{ symptom }}</span>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="发病原因" name="causes" v-if="causes && causes.length > 0">
          <div class="causes-section">
            <el-alert type="warning" :closable="false" class="section-alert">
              <template #title>
                <el-icon><warning-filled /></el-icon>
                病害成因分析
              </template>
            </el-alert>
            <div class="causes-list">
              <div v-for="(cause, index) in causes" :key="index" class="cause-item">
                <el-tag type="warning" size="small" effect="plain">{{ index + 1 }}</el-tag>
                <span class="cause-text">{{ cause }}</span>
              </div>
            </div>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="治疗方法" name="treatment" v-if="treatment && treatment.length > 0">
          <div class="treatment-section">
            <el-alert type="success" :closable="false" class="section-alert">
              <template #title>
                <el-icon><first-aid-kit /></el-icon>
                专业治疗方案
              </template>
            </el-alert>
            <el-steps direction="vertical" :space="60">
              <el-step v-for="(step, index) in treatment" :key="index" :status="'success'">
                <template #title>
                  <span class="treatment-step-title">步骤 {{ index + 1 }}</span>
                </template>
                <template #description>
                  <p class="treatment-step-desc">{{ step }}</p>
                </template>
              </el-step>
            </el-steps>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="用药指导" name="medicines" v-if="medicines && medicines.length > 0">
          <div class="medicines-section">
            <el-alert type="error" :closable="false" class="section-alert medicine-alert">
              <template #title>
                <el-icon><first-aid-kit /></el-icon>
                推荐用药方案（请在专业指导下使用）
              </template>
            </el-alert>
            <el-table :data="medicines" stripe border class="medicine-table">
              <el-table-column prop="name" label="药物名称" width="150">
                <template #default="{ row }">
                  <div class="medicine-name">
                    <span class="name-cn">{{ row.name }}</span>
                    <span v-if="row.name_en" class="name-en">({{ row.name_en }})</span>
                  </div>
                </template>
              </el-table-column>
              <el-table-column prop="concentration" label="浓度" width="120">
                <template #default="{ row }">
                  {{ row.concentration || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="dosage" label="用量" width="120">
                <template #default="{ row }">
                  {{ row.dosage || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="method" label="使用方法" width="150">
                <template #default="{ row }">
                  {{ row.method || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="frequency" label="使用频率" width="120">
                <template #default="{ row }">
                  {{ row.frequency || '-' }}
                </template>
              </el-table-column>
              <el-table-column prop="safety_period" label="安全间隔期">
                <template #default="{ row }">
                  <el-tag v-if="row.safety_period" type="warning" size="small">
                    {{ row.safety_period }}
                  </el-tag>
                  <span v-else>-</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="防治建议" name="recommendations" v-if="recommendations && recommendations.length > 0">
          <div class="recommendations-section">
            <el-alert type="info" :closable="false" class="section-alert">
              <template #title>
                <el-icon><first-aid-kit /></el-icon>
                综合防治建议
              </template>
            </el-alert>
            <el-row :gutter="16">
              <el-col :span="12" v-for="(rec, index) in recommendations" :key="index">
                <el-card class="recommendation-card" shadow="hover">
                  <div class="recommendation-icon">
                    <el-icon><first-aid-kit /></el-icon>
                  </div>
                  <div class="recommendation-content">
                    {{ rec }}
                  </div>
                </el-card>
              </el-col>
            </el-row>
          </div>
        </el-tab-pane>
        
        <el-tab-pane label="知识引用" name="knowledge" v-if="knowledgeReferences && knowledgeReferences.length > 0">
          <div class="knowledge-section">
            <el-table :data="knowledgeReferences" stripe border @row-click="handleKnowledgeClick">
              <el-table-column prop="entity_name" label="实体" width="150">
                <template #default="{ row }">
                  <el-link type="primary">{{ row.entity_name }}</el-link>
                </template>
              </el-table-column>
              <el-table-column prop="relation" label="关系" width="120">
                <template #default="{ row }">
                  <el-tag size="small">{{ row.relation }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="tail" label="值" />
              <el-table-column prop="source" label="来源" width="180">
                <template #default="{ row }">
                  <el-tag size="small" type="info">{{ row.source }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="confidence" label="置信度" width="120">
                <template #default="{ row }">
                  <el-progress
                    :percentage="Math.round(row.confidence * 100)"
                    :color="getConfidenceColor(row.confidence)"
                    :stroke-width="6"
                    style="width: 80px"
                  />
                </template>
              </el-table-column>
            </el-table>
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
    
    <el-empty v-else description="暂无诊断结果" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import {
  CircleCheckFilled,
  WarningFilled,
  CircleCloseFilled,
  Document,
  FirstAidKit,
  DataAnalysis
} from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import AnnotatedImage from './AnnotatedImage.vue'
import type { FusionDiagnosisResult, Detection, KnowledgeReference } from '@/types'

/**
 * 融合诊断结果展示组件
 * 展示病害诊断结果、推理链、知识引用和防治建议
 */

interface Props {
  result: FusionDiagnosisResult | null
  reasoningChain?: string[]
  imageSrc?: string
}

const props = withDefaults(defineProps<Props>(), {
  result: null,
  reasoningChain: () => [],
  imageSrc: ''
})

const emit = defineEmits<{
  (e: 'knowledge-click', row: any): void
}>()

const activeTab = ref<string>('overview')
const expandAll = ref<boolean>(false)
const expandedSteps = ref<Record<number, boolean>>({})

watch(expandAll, (newVal) => {
  if (props.reasoningChain) {
    props.reasoningChain.forEach((_, index) => {
      expandedSteps.value[index] = newVal
    })
  }
})

watch(() => props.reasoningChain, (newChain) => {
  if (newChain) {
    expandedSteps.value = {}
    newChain.forEach((_, index) => {
      expandedSteps.value[index] = false
    })
  }
}, { immediate: true })

const confidenceLevel = computed(() => {
  const conf = props.result?.confidence || 0
  if (conf >= 0.8) return 'high'
  if (conf >= 0.5) return 'medium'
  return 'low'
})

const confidenceClass = computed(() => {
  return `confidence-${confidenceLevel.value}`
})

const confidenceTagType = computed((): 'success' | 'warning' | 'danger' | 'info' | 'primary' => {
  const types: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    high: 'success',
    medium: 'warning',
    low: 'danger'
  }
  return types[confidenceLevel.value] || 'info'
})

const confidenceLabel = computed(() => {
  const labels: Record<string, string> = {
    high: '高置信度',
    medium: '中等置信度',
    low: '低置信度'
  }
  return labels[confidenceLevel.value]
})

const confidenceColor = computed(() => {
  const colors: Record<string, string> = {
    high: '#67c23a',
    medium: '#e6a23c',
    low: '#f56c6c'
  }
  return colors[confidenceLevel.value]
})

const recommendations = computed(() => props.result?.recommendations || [])
const knowledgeReferences = computed(() => props.result?.knowledge_references || [])
const roiBoxes = computed(() => props.result?.roi_boxes || [])
const reasoningChain = computed(() => props.reasoningChain || [])
const symptoms = computed(() => props.result?.symptoms || [])
const causes = computed(() => props.result?.causes || [])
const treatment = computed(() => props.result?.treatment || [])
const medicines = computed(() => props.result?.medicines || [])

const hasVisualDetection = computed(() => {
  return !!(props.result?.annotated_image || (props.result?.roi_boxes && props.result.roi_boxes.length > 0))
})

/**
 * 格式化置信度显示
 * @param confidence - 置信度值 (0-1)
 * @returns 格式化后的置信度字符串
 */
const formatConfidence = (confidence: number | undefined): string => {
  if (confidence === undefined) return 'N/A'
  return `${Math.round(confidence * 100)}%`
}

/**
 * 获取置信度等级标签
 * @param confidence - 置信度值 (0-1)
 * @returns 置信度等级标签文本
 */
const getConfidenceLevelLabel = (confidence: number | undefined): string => {
  if (confidence === undefined) return 'N/A'
  if (confidence >= 0.8) return '高'
  if (confidence >= 0.5) return '中'
  return '低'
}

/**
 * 获取置信度对应的 Tag 类型
 * @param confidence - 置信度值 (0-1)
 * @returns Element Plus Tag 类型
 */
const getConfidenceTagType = (confidence: number | undefined): 'success' | 'warning' | 'danger' | 'info' | 'primary' => {
  if (confidence === undefined) return 'info'
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.5) return 'warning'
  return 'danger'
}

/**
 * 获取置信度对应的颜色
 * @param confidence - 置信度值 (0-1)
 * @returns 颜色值
 */
const getConfidenceColor = (confidence: number): string => {
  if (confidence >= 0.8) return '#67c23a'
  if (confidence >= 0.5) return '#e6a23c'
  return '#f56c6c'
}

/**
 * 获取时间线节点类型
 * @param index - 步骤索引
 * @returns Element Plus Timeline 类型
 */
const getTimelineType = (index: number): '' | 'success' | 'warning' | 'danger' | 'info' | 'primary' => {
  const types: Array<'' | 'success' | 'warning' | 'danger' | 'info' | 'primary'> = ['primary', 'success', 'warning', 'danger', 'info']
  return types[index % types.length] || 'primary'
}

/**
 * 获取 ROI 标签类型
 * @param confidence - 置信度值 (0-1)
 * @returns Element Plus Tag 类型
 */
const getRoiTagType = (confidence: number): 'success' | 'warning' | 'danger' | 'info' | 'primary' => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.5) return 'warning'
  return 'danger'
}

/**
 * 获取严重程度对应的 Tag 类型
 * @param severity - 严重程度 (low/medium/high/critical)
 * @returns Element Plus Tag 类型
 */
const getSeverityTagType = (severity: string): 'success' | 'warning' | 'danger' | 'info' | 'primary' => {
  const types: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'primary'> = {
    low: 'success',
    medium: 'warning',
    high: 'danger',
    critical: 'danger'
  }
  return types[severity] || 'info'
}

/**
 * 获取严重程度的中文标签
 * @param severity - 严重程度 (low/medium/high/critical)
 * @returns 严重程度中文标签
 */
const getSeverityLabel = (severity: string): string => {
  const labels: Record<string, string> = {
    low: '轻度',
    medium: '中度',
    high: '重度',
    critical: '严重'
  }
  return labels[severity] || '未知'
}

/**
 * 切换推理步骤的展开/折叠状态
 * @param index - 步骤索引
 */
const toggleStep = (index: number): void => {
  expandedSteps.value[index] = !expandedSteps.value[index]
}

/**
 * 处理知识引用行点击事件
 * @param row - 点击的知识引用数据行
 */
const handleKnowledgeClick = (row: any): void => {
  emit('knowledge-click', row)
  ElMessage.info(`查看知识详情: ${row.entity_name}`)
}
</script>

<style scoped>
.fusion-result-container {
  width: 100%;
}

.result-card {
  margin-top: 20px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.result-icon {
  font-size: 48px;
}

.result-icon.confidence-high {
  color: #67c23a;
}

.result-icon.confidence-medium {
  color: #e6a23c;
}

.result-icon.confidence-low {
  color: #f56c6c;
}

.header-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.disease-name {
  margin: 0;
  font-size: 20px;
  color: #303133;
}

.confidence-text {
  font-size: 14px;
  color: #909399;
}

.result-tabs {
  margin-top: 20px;
}

.overview-section {
  padding: 10px 0;
}

.confidence-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.confidence-item {
  background: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
}

.confidence-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.confidence-label {
  font-weight: 500;
  color: #303133;
}

.info-descriptions {
  margin-top: 16px;
}

.description-section {
  margin-top: 20px;
}

.description-section h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  color: #303133;
}

.description-text {
  line-height: 1.8;
  color: #606266;
  background-color: #f5f7fa;
  padding: 16px;
  border-radius: 8px;
}

.visual-section {
  padding: 10px 0;
}

.detection-summary {
  margin-top: 20px;
}

.box-coords {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  color: #606266;
  background-color: #f5f7fa;
  padding: 4px 8px;
  border-radius: 4px;
}

.no-box {
  color: #c0c4cc;
}

.reasoning-section {
  padding: 10px 0;
}

.reasoning-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #f5f7fa;
  border-radius: 8px;
}

.reasoning-count {
  color: #909399;
  font-size: 14px;
}

.reasoning-card {
  margin-bottom: 0;
}

.reasoning-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.reasoning-step-title {
  font-weight: 500;
  color: #303133;
}

.reasoning-step {
  line-height: 1.6;
  color: #606266;
  transition: all 0.3s ease;
}

.reasoning-step.expanded {
  white-space: pre-wrap;
}

.recommendations-section {
  padding: 10px 0;
}

.recommendation-card {
  margin-bottom: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.recommendation-icon {
  font-size: 24px;
  color: #409eff;
}

.recommendation-content {
  flex: 1;
  line-height: 1.6;
  color: #606266;
}

.knowledge-section {
  padding: 10px 0;
}

.knowledge-section :deep(.el-table__row) {
  cursor: pointer;
}

.knowledge-section :deep(.el-table__row:hover) {
  background-color: #ecf5ff;
}

.section-alert {
  margin-bottom: 16px;
}

.section-alert :deep(.el-alert__title) {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.symptoms-section {
  padding: 10px 0;
}

.symptoms-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.symptom-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: #f0f9eb;
  border-radius: 8px;
  border-left: 4px solid #67c23a;
}

.symptom-icon {
  color: #67c23a;
  font-size: 18px;
  margin-top: 2px;
}

.symptom-text {
  line-height: 1.6;
  color: #606266;
}

.causes-section {
  padding: 10px 0;
}

.causes-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.cause-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  background: #fdf6ec;
  border-radius: 8px;
  border-left: 4px solid #e6a23c;
}

.cause-text {
  line-height: 1.6;
  color: #606266;
  flex: 1;
}

.treatment-section {
  padding: 10px 0;
}

.treatment-step-title {
  font-weight: 500;
  color: #303133;
}

.treatment-step-desc {
  margin: 8px 0 0;
  line-height: 1.6;
  color: #606266;
}

.medicines-section {
  padding: 10px 0;
}

.medicine-alert {
  margin-bottom: 16px;
}

.medicine-table {
  margin-top: 8px;
}

.medicine-name {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.medicine-name .name-cn {
  font-weight: 500;
  color: #303133;
}

.medicine-name .name-en {
  font-size: 12px;
  color: #909399;
}

.severity-tag {
  margin-left: 8px;
}

.disease-name-en {
  font-size: 14px;
  color: #909399;
  font-weight: normal;
}

@media (max-width: 768px) {
  .confidence-grid {
    grid-template-columns: 1fr;
  }
}
</style>
