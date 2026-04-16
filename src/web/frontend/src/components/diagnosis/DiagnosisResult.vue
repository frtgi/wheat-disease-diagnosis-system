<template>
  <div class="diagnosis-result-container">
    <el-card v-if="result" class="result-card" shadow="hover">
      <template #header>
        <div class="result-header">
          <span class="title">诊断结果</span>
          <el-tag :type="getConfidenceType(confidence)" size="large">
            置信度：{{ confidence.toFixed(1) }}%
          </el-tag>
        </div>
      </template>

      <div class="result-content">
        <!-- 病害名称 -->
        <div class="result-section">
          <div class="section-title">
            <el-icon><warning-filled /></el-icon>
            <span>病害名称</span>
          </div>
          <div class="disease-name">
            {{ diseaseName }}
          </div>
        </div>

        <!-- 置信度进度条 -->
        <div class="result-section">
          <div class="section-title">
            <el-icon><data-line /></el-icon>
            <span>置信度</span>
          </div>
          <el-progress
            :percentage="confidence"
            :stroke-width="20"
            :color="getProgressColor(confidence)"
            :format="formatProgress"
          />
        </div>

        <!-- 病害描述 -->
        <div class="result-section">
          <div class="section-title">
            <el-icon><document /></el-icon>
            <span>病害描述</span>
          </div>
          <el-alert
            :title="description"
            type="info"
            :closable="false"
            show-icon
          />
        </div>

        <!-- 防治建议 -->
        <div class="result-section">
          <div class="section-title">
            <el-icon><circle-check-filled /></el-icon>
            <span>防治建议</span>
          </div>
          <ul class="suggestion-list">
            <li
              v-for="(item, index) in suggestions"
              :key="index"
              class="suggestion-item"
            >
              <el-icon class="suggestion-icon"><check /></el-icon>
              <span>{{ item }}</span>
            </li>
          </ul>
        </div>

        <!-- 相关知识链接 -->
        <div class="result-section">
          <div class="section-title">
            <el-icon><link /></el-icon>
            <span>相关知识</span>
          </div>
          <div class="knowledge-links">
            <el-tag
              v-for="(link, index) in knowledgeLinks"
              :key="index"
              class="knowledge-tag"
              type="info"
              effect="plain"
              @click="handleLinkClick(link.url)"
            >
              <el-icon><document-copy /></el-icon>
              {{ link.title }}
            </el-tag>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="result-actions">
          <el-button @click="handleSave">
            <el-icon><download /></el-icon>
            保存结果
          </el-button>
          <el-button @click="handleNewDiagnosis" type="primary">
            <el-icon><refresh /></el-icon>
            重新诊断
          </el-button>
        </div>
      </div>
    </el-card>

    <!-- 空状态 -->
    <el-empty v-else description="暂无诊断结果，请先上传图片进行诊断" />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { ElMessage } from 'element-plus'
import {
  WarningFilled,
  DataLine,
  Document,
  CircleCheckFilled,
  Check,
  Link,
  DocumentCopy,
  Download,
  Refresh
} from '@element-plus/icons-vue'

/**
 * 知识链接类型
 */
interface KnowledgeLink {
  title: string
  url: string
}

/**
 * 诊断结果组件 Props
 * @property {string} diseaseName - 病害名称
 * @property {number} confidence - 置信度（0-100）
 * @property {string} description - 病害描述
 * @property {string[]} suggestions - 防治建议列表
 * @property {KnowledgeLink[]} knowledgeLinks - 相关知识链接
 * @property {boolean} showActions - 是否显示操作按钮
 */
interface Props {
  diseaseName?: string
  confidence?: number
  description?: string
  suggestions?: string[]
  knowledgeLinks?: KnowledgeLink[]
  showActions?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  diseaseName: '',
  confidence: 0,
  description: '',
  suggestions: () => [],
  knowledgeLinks: () => [],
  showActions: true
})

/**
 * 组件暴露的事件
 * @event save - 保存结果时触发
 * @event newDiagnosis - 重新诊断时触发
 */
const emit = defineEmits<{
  'save': []
  'newDiagnosis': []
}>()

// 计算属性：是否有结果
const result = computed(() => !!props.diseaseName)

// 格式化进度条显示
const formatProgress = (percentage: number) => {
  return percentage >= 90 ? '非常可靠' : 
         percentage >= 75 ? '可靠' : 
         percentage >= 60 ? '较可靠' : '仅供参考'
}

/**
 * 获取置信度对应的标签类型
 */
const getConfidenceType = (percentage: number): 'success' | 'warning' | 'danger' => {
  if (percentage >= 90) return 'success'
  if (percentage >= 75) return 'warning'
  return 'danger'
}

/**
 * 获取进度条颜色
 */
const getProgressColor = (percentage: number): string => {
  if (percentage >= 90) return '#67c23a' // 绿色
  if (percentage >= 75) return '#e6a23c' // 橙色
  if (percentage >= 60) return '#f56c6c' // 红色
  return '#909399' // 灰色
}

/**
 * 处理链接点击
 */
const handleLinkClick = (url: string) => {
  if (url) {
    window.open(url, '_blank')
  }
}

/**
 * 处理保存结果
 */
const handleSave = () => {
  ElMessage.success('结果已保存')
  emit('save')
}

/**
 * 处理重新诊断
 */
const handleNewDiagnosis = () => {
  emit('newDiagnosis')
}

// 暴露方法供父组件调用
defineExpose({
  reset: () => {
    // 重置组件状态（由父组件通过 props 控制）
  }
})
</script>

<style scoped>
.diagnosis-result-container {
  width: 100%;
  padding: 20px;
}

.result-card {
  max-width: 900px;
  margin: 0 auto;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title {
  font-size: 18px;
  font-weight: bold;
  color: #303133;
}

.result-content {
  padding: 10px 0;
}

.result-section {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #606266;
}

.section-title .el-icon {
  margin-right: 8px;
  font-size: 18px;
  color: #409eff;
}

.disease-name {
  font-size: 24px;
  font-weight: bold;
  color: #303133;
  padding: 16px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 8px;
  color: #fff;
  text-align: center;
}

.suggestion-list {
  list-style: none;
  padding: 0;
  margin: 0;
  background-color: #f5f7fa;
  border-radius: 8px;
  padding: 16px;
}

.suggestion-item {
  display: flex;
  align-items: flex-start;
  padding: 12px 0;
  border-bottom: 1px solid #ebeef5;
}

.suggestion-item:last-child {
  border-bottom: none;
}

.suggestion-icon {
  color: #67c23a;
  margin-right: 12px;
  margin-top: 2px;
  flex-shrink: 0;
}

.suggestion-item span {
  color: #606266;
  line-height: 1.6;
}

.knowledge-links {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}

.knowledge-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.knowledge-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.knowledge-tag .el-icon {
  margin-right: 4px;
}

.result-actions {
  display: flex;
  justify-content: center;
  gap: 16px;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}
</style>
