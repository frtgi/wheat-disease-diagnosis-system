<template>
  <div class="knowledge-container">
    <!-- 搜索栏 -->
    <el-card class="search-card">
      <div class="search-header">
        <h2>病害知识库</h2>
        <div class="search-box">
          <el-input
            v-model="searchKeyword"
            @input="handleSearchChange"
            placeholder="搜索病害名称或症状"
            clearable
            prefix-icon="Search"
            class="search-input"
          />
          <el-select
            v-model="selectedCategory"
            @change="loadDiseases"
            placeholder="病害类别"
            clearable
            class="category-select"
          >
            <el-option
              v-for="cat in categoryOptions"
              :key="cat.value"
              :label="cat.label"
              :value="cat.value"
            />
          </el-select>
        </div>
      </div>
    </el-card>

    <!-- 病害卡片列表 -->
    <el-row :gutter="20" class="disease-list" v-loading="isLoading">
      <el-col
        v-for="disease in filteredDiseases"
        :key="disease.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
      >
        <DiseaseCard
          :id="disease.id"
          :disease-name="disease.name"
          :symptoms-brief="(disease.symptoms || '').substring(0, 50) + '...'"
          :symptoms="(disease.symptoms || '').split('。').slice(0, 3)"
          :category="disease.category"
          :severity="getSeverityLevel(disease.severity)"
          @click="handleClick"
          @viewDetail="handleViewDetail"
          @prevention="handlePrevention"
        />
      </el-col>
    </el-row>

    <!-- 病害详情弹窗 -->
    <el-dialog
      v-model="detailDialogVisible"
      :title="currentDisease?.name || '病害详情'"
      width="700px"
      destroy-on-close
    >
      <el-descriptions :column="2" border v-if="currentDisease">
        <el-descriptions-item label="病害名称">{{ currentDisease.name }}</el-descriptions-item>
        <el-descriptions-item label="分类">
          <el-tag size="small">{{ getCategoryLabel(currentDisease.category) }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="严重程度">
          <el-tag :type="getSeverityTagType(currentDisease.severity)" size="small">
            {{ getSeverityLevel(currentDisease.severity) }}
          </el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="编码">{{ currentDisease.code || '-' }}</el-descriptions-item>
        <el-descriptions-item label="症状描述" :span="2">{{ currentDisease.symptoms || '暂无描述' }}</el-descriptions-item>
        <el-descriptions-item label="病因" :span="2">{{ currentDisease.causes || '暂无描述' }}</el-descriptions-item>
        <el-descriptions-item label="预防措施" :span="2">
          <template v-if="currentDisease.prevention">
            <div v-if="Array.isArray(currentDisease.prevention)">
              <p v-for="(item, idx) in currentDisease.prevention" :key="idx">• {{ item }}</p>
            </div>
            <span v-else>{{ currentDisease.prevention }}</span>
          </template>
          <span v-else>暂无</span>
        </el-descriptions-item>
        <el-descriptions-item label="治疗方法" :span="2">
          <template v-if="currentDisease.treatments">
            <div v-if="Array.isArray(currentDisease.treatments)">
              <p v-for="(item, idx) in currentDisease.treatments" :key="idx">• {{ item }}</p>
            </div>
            <span v-else>{{ currentDisease.treatments }}</span>
          </template>
          <span v-else>暂无</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>

    <!-- 空状态 -->
    <el-empty
      v-if="!isLoading && filteredDiseases.length === 0"
      description="未找到相关病害信息"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import DiseaseCard from '@/components/knowledge/DiseaseCard.vue'
import { getDiseaseKnowledge, searchDiseaseKnowledge, getDiseaseDetail } from '@/api/knowledge'
import type { DiseaseKnowledge } from '@/api/knowledge'

/**
 * 根据后端 severity 数值（0-1）转换为前端严重程度级别
 * @param severityValue 后端返回的 severity 值（0-1 浮点数）
 * @returns 严重程度级别
 */
const getSeverityLevel = (severityValue?: number | null): 'low' | 'medium' | 'high' => {
  if (severityValue === null || severityValue === undefined) {
    return 'medium'
  }
  if (severityValue >= 0.7) return 'high'
  if (severityValue >= 0.3) return 'medium'
  return 'low'
}

// 搜索关键词
const searchKeyword = ref<string>('')

// 选中的类别
const selectedCategory = ref<string>('')

// 病害列表数据
const diseaseList = ref<DiseaseKnowledge[]>([])

// 加载状态
const isLoading = ref(false)

// 详情弹窗状态
const detailDialogVisible = ref(false)
const currentDisease = ref<DiseaseKnowledge | null>(null)

/**
 * 获取病害分类的中文标签
 * @param category 分类英文标识
 * @returns 分类中文名称
 */
const getCategoryLabel = (category: string | undefined): string => {
  const map: Record<string, string> = {
    fungal: '真菌性病害', bacterial: '细菌性病害', viral: '病毒性病害',
    pest: '虫害', nutritional: '营养性病害'
  }
  return map[category || ''] || category || '未知'
}

/**
 * 根据严重程度获取标签类型
 * @param severity 严重程度值（0-1）
 * @returns Element Plus 标签类型
 */
const getSeverityTagType = (severity: number | undefined): string => {
  if (!severity) return 'info'
  if (severity >= 0.7) return 'danger'
  if (severity >= 0.3) return 'warning'
  return 'success'
}

// 类别选项
const categoryOptions = ref([
  { label: '真菌性病害', value: 'fungal' },
  { label: '细菌性病害', value: 'bacterial' },
  { label: '病毒性病害', value: 'viral' },
  { label: '虫害', value: 'pest' },
  { label: '营养性病害', value: 'nutritional' }
])

// 加载病害知识
const loadDiseases = async () => {
  isLoading.value = true
  try {
    const response = await getDiseaseKnowledge(
      selectedCategory.value || undefined,
      0,
      100
    )
    diseaseList.value = response
  } catch (error: unknown) {
    console.error('加载病害知识失败:', error)
    const msg = error instanceof Error ? error.message : '加载失败'
    ElMessage.error(msg)
  } finally {
    isLoading.value = false
  }
}

// 搜索病害
const searchDiseases = async () => {
  if (!searchKeyword.value) {
    loadDiseases()
    return
  }
  
  isLoading.value = true
  try {
    const response = await searchDiseaseKnowledge(searchKeyword.value)
    diseaseList.value = response
  } catch (error: unknown) {
    console.error('搜索失败:', error)
    const msg = error instanceof Error ? error.message : '搜索失败'
    ElMessage.error(msg)
  } finally {
    isLoading.value = false
  }
}

// 生命周期钩子：组件挂载时加载数据
onMounted(() => {
  loadDiseases()
})

// 计算属性：直接返回病害列表（筛选已由后端处理）
const filteredDiseases = computed<DiseaseKnowledge[]>(() => {
  return diseaseList.value
})

// 监听搜索关键词变化
let searchTimeout: any
const handleSearchChange = () => {
  clearTimeout(searchTimeout)
  searchTimeout = setTimeout(() => {
    searchDiseases()
  }, 500)
}

/**
 * 处理卡片点击
 */
const handleClick = (id: string | number) => {
}

/**
 * 处理查看详情
 */
const handleViewDetail = async (id: string | number) => {
  try {
    const diseaseId = typeof id === 'string' ? parseInt(id, 10) : id
    const disease = await getDiseaseDetail(diseaseId)
    currentDisease.value = disease
    detailDialogVisible.value = true
  } catch (error: unknown) {
    ElMessage.error('加载详情失败')
  }
}

/**
 * 处理防治方法
 */
const handlePrevention = (id: string | number) => {
  const diseaseId = typeof id === 'string' ? parseInt(id, 10) : id
  const disease = diseaseList.value.find(d => d.id === diseaseId)
  if (disease) {
    ElMessage.info(`${disease.name}的防治方法：${disease.prevention || '暂无'}`)
  }
}
</script>

<style scoped>
.knowledge-container {
  padding: 20px;
}

.search-card {
  margin-bottom: 20px;
}

.search-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.search-header h2 {
  margin: 0;
  color: #303133;
}

.search-box {
  display: flex;
  gap: 12px;
  flex: 1;
  max-width: 600px;
}

.search-input {
  flex: 1;
}

.category-select {
  width: 150px;
}

.disease-list {
  margin-top: 10px;
}

@media (max-width: 768px) {
  .search-header {
    flex-direction: column;
  }
  
  .search-box {
    width: 100%;
    max-width: none;
  }
}
</style>
