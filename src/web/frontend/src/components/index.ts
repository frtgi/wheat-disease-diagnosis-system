/**
 * 组件统一导出文件
 * 方便在项目中导入和使用所有核心组件
 */

// ==================== 通用组件 ====================

/**
 * ErrorBoundary - 错误边界组件
 * 功能：
 * - 捕获子组件 JavaScript 错误
 * - 错误类型分类（渲染/异步/网络/未知）
 * - 友好的错误提示界面
 * - 重试、返回上页、返回首页功能
 * - 错误详情展示（可折叠）
 * - 错误日志本地存储
 * - 错误上报功能
 * - 最大重试次数限制
 */
export { default as ErrorBoundary } from './common/ErrorBoundary.vue'

// ==================== 诊断模块组件 ====================

/**
 * ImageUploader - 图片上传组件
 * 功能：
 * - 支持拖拽上传和点击上传
 * - 图像预览功能
 * - 图像格式验证（JPG、PNG）
 * - 图像大小限制（最大 5MB）
 * - 上传进度显示
 */
export { default as ImageUploader } from './diagnosis/ImageUploader.vue'

/**
 * DiagnosisResult - 诊断结果展示组件
 * 功能：
 * - 展示病害名称
 * - 展示置信度（进度条或百分比）
 * - 展示病害描述
 * - 展示防治建议（列表形式）
 * - 展示相关知识链接
 */
export { default as DiagnosisResult } from './diagnosis/DiagnosisResult.vue'

/**
 * MultiModalInput - 多模态输入组件
 * 功能：
 * - 支持图像上传和文本症状描述同时输入
 * - 环境因素选择（天气、生长阶段、发病部位）
 * - Thinking 推理链模式开关
 * - GraphRAG 知识增强开关
 */
export { default as MultiModalInput } from './diagnosis/MultiModalInput.vue'

/**
 * FusionResult - 融合诊断结果展示组件
 * 功能：
 * - 展示病害名称和综合置信度
 * - 展示视觉/文本/知识置信度分解
 * - 展示推理链（Thinking 模式）
 * - 展示防治建议列表
 * - 展示知识引用溯源
 * - 展示检测区域（ROI）
 */
export { default as FusionResult } from './diagnosis/FusionResult.vue'

// ==================== 仪表盘模块组件 ====================

/**
 * DiseaseChart - 病害统计图表组件
 * 功能：
 * - 使用 ECharts 展示病害统计
 * - 饼图：病害类型分布
 * - 柱状图：诊断次数统计
 * - 折线图：诊断趋势分析
 * - 响应式图表
 */
export { default as DiseaseChart } from './dashboard/DiseaseChart.vue'

// ==================== 知识库模块组件 ====================

/**
 * DiseaseCard - 病害知识卡片组件
 * 功能：
 * - 病害卡片展示
 * - 包含病害图片、名称、症状简介
 * - 点击查看详情
 * - 严重程度标签
 */
export { default as DiseaseCard } from './knowledge/DiseaseCard.vue'
