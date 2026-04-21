<template>
  <div class="records-container">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>诊断记录</span>
          <el-input
            v-model="searchQuery"
            placeholder="搜索记录"
            style="width: 200px"
            clearable
          />
        </div>
      </template>

      <el-table :data="filteredRecords" stripe style="width: 100%" v-loading="isLoading">
        <template #empty>
          <div class="empty-state">
            <el-empty description="">
              <template #image>
                <el-icon :size="64" color="#c0c4cc"><Document /></el-icon>
              </template>
              <div class="empty-content">
                <h3>暂无诊断记录</h3>
                <p>完成首次病害诊断后，记录将显示在此处</p>
                <el-button type="primary" @click="$router.push('/diagnosis')">开始诊断</el-button>
              </div>
            </el-empty>
          </div>
        </template>
        <el-table-column prop="created_at" label="诊断时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="diagnosis_result" label="病害类型" width="150">
          <template #default="{ row }">
            <el-tag :type="getDiseaseType(row.confidence)">
              {{ row.diagnosis_result || '未知' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="confidence" label="置信度" width="120">
          <template #default="{ row }">
            <el-progress v-if="row.confidence" :percentage="row.confidence * 100" :stroke-width="10" />
            <span v-else>-</span>
          </template>
        </el-table-column>
        <el-table-column prop="symptoms" label="症状描述" show-overflow-tooltip>
          <template #default="{ row }">
            {{ row.description || row.symptoms || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleViewDetail(row)">
              查看详情
            </el-button>
            <el-button link type="warning" @click="handleExportReport(row)">
              导出报告
            </el-button>
            <el-button link type="danger" @click="handleDelete(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :total="total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        class="pagination"
        @current-change="handlePageChange"
      />
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, h } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Document } from '@element-plus/icons-vue'
import {
  getDiagnosisRecords as apiGetRecords,
  deleteDiagnosis as apiDeleteDiagnosis,
  type DiagnosisRecordItem
} from '@/api/diagnosis'
import { generateReportFromRecord, downloadReport } from '@/api/report'

const searchQuery = ref('')

const currentPage = ref(1)
const pageSize = ref(10)
const totalRecords = ref(0)

const records = ref<DiagnosisRecordItem[]>([])
const allRecords = ref<DiagnosisRecordItem[]>([])

const isLoading = ref(false)

/**
 * 加载所有诊断记录（用于本地搜索和统计）
 */
const loadAllRecords = async () => {
  try {
    const response = await apiGetRecords(0, 1000)
    allRecords.value = response.records
    totalRecords.value = response.total
  } catch (error: unknown) {
    console.error('加载全部记录失败:', error)
  }
}

/**
 * 加载当前页诊断记录
 */
const loadRecords = async () => {
  isLoading.value = true
  try {
    const skip = (currentPage.value - 1) * pageSize.value
    const response = await apiGetRecords(skip, pageSize.value)
    records.value = response.records
    totalRecords.value = response.total
    if (allRecords.value.length === 0) {
      await loadAllRecords()
    }
  } catch (error: unknown) {
    console.error('加载记录失败:', error)
    const msg = error instanceof Error ? error.message : '加载记录失败'
    ElMessage.error(msg)
  } finally {
    isLoading.value = false
  }
}

onMounted(() => {
  loadRecords()
})

watch(pageSize, () => {
  currentPage.value = 1
  loadRecords()
})

const filteredRecords = computed(() => {
  if (!searchQuery.value) {
    return records.value
  }
  return allRecords.value.filter(record =>
    (record.diagnosis_result && record.diagnosis_result.includes(searchQuery.value)) ||
    (record.symptoms && record.symptoms.includes(searchQuery.value))
  )
})

const total = computed(() => {
  if (searchQuery.value) {
    return filteredRecords.value.length
  }
  return totalRecords.value
})

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

const getDiseaseType = (confidence: number) => {
  if (confidence >= 0.9) return 'success'
  if (confidence >= 0.7) return 'warning'
  return 'danger'
}

const handleViewDetail = (row: DiagnosisRecordItem) => {
  ElMessageBox.alert(
    h('div', null, [
      h('p', null, [`病害名称：${row.diagnosis_result || '未知'}`]),
      h('p', null, [`置信度：${row.confidence ? (row.confidence * 100).toFixed(2) + '%' : '未知'}`]),
      h('p', null, [`状态：${row.status || '未知'}`]),
      h('p', null, [`症状描述：${row.symptoms || '无'}`]),
      h('p', null, [`防治建议：${row.suggestions || '无'}`])
    ]),
    '诊断详情',
    {
      confirmButtonText: '确定'
    }
  )
}

const handleDelete = async (row: DiagnosisRecordItem) => {
  ElMessageBox.confirm('确定要删除这条记录吗？', '提示', {
    confirmButtonText: '确定',
    cancelButtonText: '取消',
    type: 'warning'
  }).then(async () => {
    try {
      await apiDeleteDiagnosis(String(row.id))
      ElMessage.success('删除成功')
      allRecords.value = []
      loadRecords()
    } catch (error: unknown) {
      console.error('删除失败:', error)
      const msg = error instanceof Error ? error.message : '删除失败'
      ElMessage.error(msg)
    }
  }).catch(() => {
  })
}

/**
 * 导出诊断报告
 */
const handleExportReport = async (row: DiagnosisRecordItem) => {
  try {
    const result = await generateReportFromRecord(row.id, 'both')
    if (result.report_files) {
      ElMessage.success(`报告生成成功${result.has_image ? '（含诊断图像）' : '（无诊断图像）'}`)
      const firstFile = Object.values(result.report_files)[0]
      if (firstFile) {
        const filename = String(firstFile).split(/[/\\]/).pop()
        if (filename) {
          await downloadReport(filename)
        }
      }
    }
  } catch (error: unknown) {
    console.error('导出报告失败:', error)
    ElMessage.error('导出报告失败')
  }
}

const handlePageChange = () => {
  loadRecords()
}

const handleSearch = () => {
  if (searchQuery.value) {
    currentPage.value = 1
  }
}
</script>

<style scoped>
.records-container {
  padding: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination {
  margin-top: 20px;
  justify-content: center;
}

.empty-state {
  padding: 40px 0;
}

.empty-content {
  text-align: center;
}

.empty-content h3 {
  margin: 0 0 8px;
  font-size: 16px;
  color: #303133;
}

.empty-content p {
  margin: 0 0 16px;
  font-size: 14px;
  color: #909399;
}
</style>
