# 快速开始指南

## 🎯 组件概览

本次实现了 4 个核心组件，用于构建小麦病害诊断系统的前端界面：

| 组件名称 | 路径 | 功能 |
|---------|------|------|
| ImageUploader | `components/diagnosis/ImageUploader.vue` | 图片上传、预览、验证 |
| DiagnosisResult | `components/diagnosis/DiagnosisResult.vue` | 诊断结果展示 |
| DiseaseChart | `components/dashboard/DiseaseChart.vue` | 病害统计图表 |
| DiseaseCard | `components/knowledge/DiseaseCard.vue` | 病害知识卡片 |

---

## 📦 安装依赖

确保已安装所有必需的依赖：

```bash
cd src/web/frontend
npm install
```

**核心依赖**:
- Vue 3.5.25+
- Element Plus 2.13.5+
- ECharts 6.0.0+
- TypeScript 5.9.3+

---

## 🚀 快速使用

### 1. 在诊断页面使用

诊断页面已经集成了 `ImageUploader` 和 `DiagnosisResult` 组件：

```vue
<!-- views/Diagnosis.vue -->
<template>
  <el-row :gutter="20">
    <!-- 左侧：图片上传 -->
    <el-col :span="10">
      <ImageUploader
        v-model:image-url="imageUrl"
        :token="token"
        @diagnose="handleDiagnose"
      />
    </el-col>
    
    <!-- 右侧：诊断结果 -->
    <el-col :span="14">
      <DiagnosisResult
        v-if="showResult"
        :disease-name="result.diseaseName"
        :confidence="result.confidence"
        :description="result.description"
        :suggestions="result.suggestions"
        :knowledge-links="result.knowledgeLinks"
        @save="handleSave"
        @newDiagnosis="handleNewDiagnosis"
      />
    </el-col>
  </el-row>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { ImageUploader, DiagnosisResult } from '@/components'

const imageUrl = ref('')
const showResult = ref(false)

const result = reactive({
  diseaseName: '',
  confidence: 0,
  description: '',
  suggestions: [],
  knowledgeLinks: []
})

const handleDiagnose = async (url: string) => {
  // TODO: 调用诊断 API
  showResult.value = true
}
</script>
```

### 2. 在仪表盘使用

仪表盘页面已经集成了 `DiseaseChart` 组件：

```vue
<!-- views/Dashboard.vue -->
<template>
  <div>
    <!-- 统计卡片 -->
    <el-row :gutter="20">
      <el-col :span="6">
        <el-statistic title="今日诊断" :value="156" />
      </el-col>
      <!-- 更多统计卡片... -->
    </el-row>
    
    <!-- 图表 -->
    <DiseaseChart
      :distribution-data="distributionData"
      :stats-data="statsData"
      :trend-data="trendData"
    />
  </div>
</template>

<script setup lang="ts">
import { DiseaseChart } from '@/components'
import type { DiseaseDistribution, DiagnosisStats } from '@/types'

const distributionData = ref<DiseaseDistribution[]>([
  { name: '锈病', value: 35 },
  { name: '白粉病', value: 25 }
])

const statsData = ref<DiagnosisStats[]>([
  { diseaseName: '锈病', count: 156 },
  { diseaseName: '白粉病', count: 98 }
])
</script>
```

### 3. 在知识库使用

知识库页面已经集成了 `DiseaseCard` 组件：

```vue
<!-- views/Knowledge.vue -->
<template>
  <div>
    <!-- 搜索栏 -->
    <el-card>
      <el-input v-model="keyword" placeholder="搜索病害" />
    </el-card>
    
    <!-- 病害卡片列表 -->
    <el-row :gutter="20">
      <el-col
        v-for="disease in diseaseList"
        :key="disease.id"
        :span="6"
      >
        <DiseaseCard
          :id="disease.id"
          :image-url="disease.imageUrl"
          :disease-name="disease.name"
          :symptoms-brief="disease.symptomsBrief"
          @viewDetail="handleViewDetail"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { DiseaseCard } from '@/components'
import type { Disease } from '@/types'

const diseaseList = ref<Disease[]>([
  {
    id: 1,
    name: '小麦锈病',
    imageUrl: '/images/rust.jpg',
    symptomsBrief: '叶片出现铁锈色粉末',
    symptoms: ['病斑', '孢子堆'],
    category: '真菌性病害',
    severity: 'high'
  }
])
</script>
```

---

## 🔧 自定义配置

### ImageUploader 自定义

```vue
<ImageUploader
  :upload-url="'/api/custom/upload'"
  :token="userToken"
  @upload="handleUpload"
  @success="handleSuccess"
  @error="handleError"
  @diagnose="handleDiagnose"
/>
```

### DiagnosisResult 自定义

```vue
<DiagnosisResult
  disease-name="小麦锈病"
  :confidence="92.5"
  description="详细的病害描述..."
  :suggestions="['建议 1', '建议 2']"
  :knowledge-links="[
    { title: '链接 1', url: 'https://...' }
  ]"
  :show-actions="true"
  @save="handleSave"
  @newDiagnosis="handleNew"
/>
```

### DiseaseChart 自定义

```vue
<DiseaseChart
  :distribution-data="[
    { name: '锈病', value: 35 },
    { name: '白粉病', value: 25 }
  ]"
  :stats-data="[
    { diseaseName: '锈病', count: 156 }
  ]"
  :trend-data="[
    { date: '2024-01-01', count: 15 }
  ]"
  :auto-resize="true"
  @timeRangeChange="handleChange"
/>
```

### DiseaseCard 自定义

```vue
<DiseaseCard
  :id="1"
  image-url="/images/rust.jpg"
  disease-name="小麦锈病"
  symptoms-brief="叶片出现病斑"
  :symptoms="['症状 1', '症状 2']"
  category="真菌性病害"
  severity="high"
  high-season="春季"
  suitable-temp="15-25°C"
  :preview-mode="true"
  @click="handleClick"
  @viewDetail="handleDetail"
  @prevention="handlePrevention"
/>
```

---

## 📱 响应式支持

所有组件都支持响应式布局：

```vue
<!-- 移动端：单列显示 -->
<el-col :xs="24">
  <DiseaseCard />
</el-col>

<!-- 平板：双列显示 -->
<el-col :sm="12">
  <DiseaseCard />
</el-col>

<!-- 桌面：四列显示 -->
<el-col :md="6" :lg="6">
  <DiseaseCard />
</el-col>
```

---

## 🎨 样式定制

### 使用 CSS 变量

```css
/* 全局样式变量 */
:root {
  --el-color-primary: #409eff;
  --el-card-border-color: #ebeef5;
}
```

### 覆盖组件样式

```vue
<style scoped>
:deep(.image-uploader .el-upload-dragger) {
  height: 400px;
}

:deep(.disease-card .el-card__header) {
  background-color: #f5f7fa;
}
</style>
```

---

## 🐛 常见问题

### 1. 组件未定义错误

**问题**: `Failed to resolve component`

**解决**: 确保正确导入组件
```typescript
import { ImageUploader } from '@/components'
```

### 2. 样式不生效

**问题**: 组件样式被覆盖或未生效

**解决**: 使用 `:deep()` 选择器
```vue
<style scoped>
:deep(.el-progress__text) {
  font-size: 16px;
}
</style>
```

### 3. TypeScript 类型错误

**问题**: 类型不匹配

**解决**: 检查 Props 类型定义
```typescript
// 查看类型定义
import type { Disease } from '@/types'
```

---

## 📚 学习资源

- [Vue 3 官方文档](https://vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [ECharts 文档](https://echarts.apache.org/)
- [TypeScript 文档](https://www.typescriptlang.org/)

---

## 🎯 下一步

1. **运行项目**:
   ```bash
   npm run dev
   ```

2. **查看效果**:
   - 访问 `/diagnosis` 查看诊断页面
   - 访问 `/dashboard` 查看仪表盘
   - 访问 `/knowledge` 查看知识库

3. **集成 API**:
   - 替换模拟数据为真实 API 调用
   - 使用 `request.ts` 中的 HTTP 方法

4. **添加功能**:
   - 实现图片上传后端接口
   - 实现诊断结果保存
   - 实现数据导出功能

---

## ✅ 检查清单

- [ ] 安装所有依赖
- [ ] 运行开发服务器
- [ ] 测试 ImageUploader 组件
- [ ] 测试 DiagnosisResult 组件
- [ ] 测试 DiseaseChart 组件
- [ ] 测试 DiseaseCard 组件
- [ ] 检查响应式布局
- [ ] 集成后端 API
- [ ] 进行功能测试

---

**祝使用愉快！** 🎉
