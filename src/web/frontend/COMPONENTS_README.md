# 核心组件使用说明

本文档介绍小麦病害诊断系统的四个核心组件的使用方法。

## 组件列表

### 1. ImageUploader - 图片上传组件

**位置**: `src/components/diagnosis/ImageUploader.vue`

**功能特性**:
- ✅ 支持拖拽上传和点击上传
- ✅ 图像预览功能
- ✅ 图像格式验证（JPG、PNG）
- ✅ 图像大小限制（最大 5MB）
- ✅ 上传进度显示
- ✅ 使用 Element Plus 的 Upload 组件

**Props**:
```typescript
interface Props {
  uploadUrl?: string      // 上传接口地址，默认：'/api/v1/diagnosis/upload'
  token?: string          // 认证 Token，默认：''
}
```

**Events**:
```typescript
const emit = defineEmits<{
  'update:imageUrl': [url: string]   // 图片 URL 变化时触发
  'upload': [file: File]             // 开始上传时触发
  'success': [response: any, file: File]  // 上传成功时触发
  'error': [error: Error, file: File]     // 上传失败时触发
  'diagnose': [imageUrl: string]     // 开始诊断时触发
}>()
```

**使用示例**:
```vue
<template>
  <ImageUploader
    v-model:image-url="imageUrl"
    :token="token"
    @success="handleUploadSuccess"
    @error="handleUploadError"
    @diagnose="handleDiagnose"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { ImageUploader } from '@/components'

const imageUrl = ref<string>('')
const token = ref<string>(localStorage.getItem('token') || '')

const handleUploadSuccess = (response: any, file: File) => {
  console.log('上传成功:', response)
}

const handleUploadError = (error: Error, file: File) => {
  console.error('上传失败:', error)
}

const handleDiagnose = (url: string) => {
  console.log('开始诊断:', url)
  // 调用诊断 API
}
</script>
```

---

### 2. DiagnosisResult - 诊断结果展示组件

**位置**: `src/components/diagnosis/DiagnosisResult.vue`

**功能特性**:
- ✅ 展示病害名称
- ✅ 展示置信度（进度条或百分比）
- ✅ 展示病害描述
- ✅ 展示防治建议（列表形式）
- ✅ 展示相关知识链接
- ✅ 使用 Element Plus 的 Card、Progress、Tag 组件

**Props**:
```typescript
interface Props {
  diseaseName?: string        // 病害名称
  confidence?: number         // 置信度（0-100）
  description?: string        // 病害描述
  suggestions?: string[]      // 防治建议列表
  knowledgeLinks?: {          // 相关知识链接
    title: string
    url: string
  }[]
  showActions?: boolean       // 是否显示操作按钮
}
```

**Events**:
```typescript
const emit = defineEmits<{
  'save': []                  // 保存结果时触发
  'newDiagnosis': []          // 重新诊断时触发
}>()
```

**使用示例**:
```vue
<template>
  <DiagnosisResult
    :disease-name="result.diseaseName"
    :confidence="result.confidence"
    :description="result.description"
    :suggestions="result.suggestions"
    :knowledge-links="result.knowledgeLinks"
    @save="handleSave"
    @newDiagnosis="handleNewDiagnosis"
  />
</template>

<script setup lang="ts">
import { reactive } from 'vue'
import { DiagnosisResult } from '@/components'

const result = reactive({
  diseaseName: '小麦锈病',
  confidence: 92.5,
  description: '小麦锈病是由锈菌引起的一种真菌性病害...',
  suggestions: [
    '选用抗病品种，合理密植',
    '及时清除病残体',
    '发病初期喷洒杀菌剂'
  ],
  knowledgeLinks: [
    { title: '防治指南', url: 'https://example.com/guide' },
    { title: '发生规律', url: 'https://example.com/research' }
  ]
})

const handleSave = () => {
  console.log('保存诊断结果')
}

const handleNewDiagnosis = () => {
  console.log('重新诊断')
}
</script>
```

---

### 3. DiseaseChart - 病害统计图表组件

**位置**: `src/components/dashboard/DiseaseChart.vue`

**功能特性**:
- ✅ 使用 ECharts 展示病害统计
- ✅ 饼图：病害类型分布
- ✅ 柱状图：诊断次数统计
- ✅ 折线图：诊断趋势分析
- ✅ 响应式图表

**Props**:
```typescript
interface Props {
  distributionData?: {      // 病害分布数据（饼图）
    name: string
    value: number
  }[]
  statsData?: {             // 统计数据（柱状图）
    diseaseName: string
    count: number
  }[]
  trendData?: {             // 趋势数据（折线图）
    date: string
    count: number
  }[]
  autoResize?: boolean      // 是否自动调整大小
}
```

**Events**:
```typescript
const emit = defineEmits<{
  'timeRangeChange': [range: string]  // 时间范围变化时触发
}>()
```

**使用示例**:
```vue
<template>
  <DiseaseChart
    :distribution-data="distributionData"
    :stats-data="statsData"
    :trend-data="trendData"
    @timeRangeChange="handleTimeRangeChange"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { DiseaseChart } from '@/components'

const distributionData = ref([
  { name: '锈病', value: 35 },
  { name: '白粉病', value: 25 },
  { name: '赤霉病', value: 20 },
  { name: '纹枯病', value: 15 },
  { name: '其他', value: 5 }
])

const statsData = ref([
  { diseaseName: '锈病', count: 156 },
  { diseaseName: '白粉病', count: 98 },
  { diseaseName: '赤霉病', count: 87 }
])

const trendData = ref([
  { date: '2024-01-01', count: 15 },
  { date: '2024-01-02', count: 23 },
  { date: '2024-01-03', count: 18 }
])

const handleTimeRangeChange = (range: string) => {
  console.log('时间范围变化:', range)
  // 根据时间范围重新加载数据
}
</script>
```

---

### 4. DiseaseCard - 病害知识卡片组件

**位置**: `src/components/knowledge/DiseaseCard.vue`

**功能特性**:
- ✅ 病害卡片展示
- ✅ 包含病害图片、名称、症状简介
- ✅ 点击查看详情
- ✅ 使用 Element Plus 的 Card 组件
- ✅ 严重程度标签
- ✅ 症状标签展示

**Props**:
```typescript
interface Props {
  imageUrl?: string         // 病害图片 URL
  diseaseName: string       // 病害名称
  symptomsBrief: string     // 症状简介
  symptoms?: string[]       // 详细症状列表
  category?: string         // 病害类别
  severity?: 'low' | 'medium' | 'high'  // 严重程度
  highSeason?: string       // 高发季节
  suitableTemp?: string     // 适宜温度
  previewMode?: boolean     // 是否开启预览模式
  id?: number | string      // 病害 ID
}
```

**Events**:
```typescript
const emit = defineEmits<{
  'click': [id: number | string]      // 点击卡片时触发
  'viewDetail': [id: number | string] // 查看详情时触发
  'prevention': [id: number | string] // 查看防治方法时触发
}>()
```

**使用示例**:
```vue
<template>
  <div class="disease-list">
    <DiseaseCard
      v-for="disease in diseaseList"
      :key="disease.id"
      :id="disease.id"
      :image-url="disease.imageUrl"
      :disease-name="disease.name"
      :symptoms-brief="disease.symptomsBrief"
      :symptoms="disease.symptoms"
      :category="disease.category"
      :severity="disease.severity"
      :high-season="disease.highSeason"
      :suitable-temp="disease.suitableTemp"
      @click="handleClick"
      @viewDetail="handleViewDetail"
      @prevention="handlePrevention"
    />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { DiseaseCard } from '@/components'

const diseaseList = ref([
  {
    id: 1,
    name: '小麦锈病',
    imageUrl: '/images/diseases/rust.jpg',
    symptomsBrief: '叶片出现铁锈色粉末状孢子堆',
    symptoms: ['叶片病斑', '铁锈色孢子堆', '后期黑色病斑'],
    category: '真菌性病害',
    severity: 'high',
    highSeason: '春季和秋季',
    suitableTemp: '15-25°C'
  },
  {
    id: 2,
    name: '小麦白粉病',
    imageUrl: '/images/diseases/powdery-mildew.jpg',
    symptomsBrief: '叶片表面覆盖白色粉状物',
    symptoms: ['白色粉状病斑', '叶片褪绿'],
    category: '真菌性病害',
    severity: 'medium',
    highSeason: '春季',
    suitableTemp: '15-20°C'
  }
])

const handleClick = (id: number) => {
  console.log('点击卡片:', id)
}

const handleViewDetail = (id: number) => {
  console.log('查看详情:', id)
}

const handlePrevention = (id: number) => {
  console.log('查看防治方法:', id)
}
</script>
```

---

## 统一导入方式

所有组件可以通过统一入口导入：

```typescript
// 导入单个组件
import { ImageUploader } from '@/components'
import { DiagnosisResult } from '@/components'
import { DiseaseChart } from '@/components'
import { DiseaseCard } from '@/components'

// 或者导入所有组件
import * as Components from '@/components'
```

## TypeScript 类型支持

组件相关的类型定义位于 `src/types/index.ts`，已自动包含：

```typescript
// 病害信息
export interface Disease {
  id: number
  name: string
  imageUrl: string
  symptomsBrief: string
  symptoms: string[]
  category: string
  severity: 'low' | 'medium' | 'high'
  highSeason: string
  suitableTemp: string
  description: string
  prevention: string[]
}

// 病害分布数据
export interface DiseaseDistribution {
  name: string
  value: number
}

// 知识链接
export interface KnowledgeLink {
  id: number
  title: string
  url: string
  type: string
}
```

## 注意事项

1. **Element Plus**: 确保项目已安装 Element Plus
2. **ECharts**: DiseaseChart 组件需要安装 ECharts
3. **TypeScript**: 所有组件都使用 TypeScript 编写，提供完整的类型支持
4. **Vue 3**: 所有组件都使用 Vue 3 Composition API 风格
5. **响应式**: 所有组件都支持响应式布局

## 依赖版本

```json
{
  "vue": "^3.5.25",
  "element-plus": "^2.13.5",
  "echarts": "^6.0.0",
  "typescript": "~5.9.3"
}
```
