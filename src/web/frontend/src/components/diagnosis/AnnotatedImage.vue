<template>
  <div class="annotated-image-container">
    <div class="image-wrapper">
      <el-image
        v-if="annotatedImage"
        :src="annotatedImage"
        fit="contain"
        class="annotated-image"
        :preview-src-list="[annotatedImage]"
        :z-index="9999"
      >
        <template #error>
          <div class="image-error">
            <el-icon><picture-filled /></el-icon>
            <span>标注图像加载失败</span>
          </div>
        </template>
        <template #placeholder>
          <div class="image-loading">
            <el-icon class="is-loading"><loading /></el-icon>
            <span>加载中...</span>
          </div>
        </template>
      </el-image>
      
      <div v-else-if="imageSrc && detections.length" class="canvas-container">
        <canvas
          ref="canvasRef"
          class="detection-canvas"
          @mousemove="handleMouseMove"
          @mouseleave="hideTooltip"
        ></canvas>
        <div
          v-if="tooltipVisible"
          class="detection-tooltip"
          :style="tooltipStyle"
        >
          <div class="tooltip-title">{{ tooltipData.class_name }}</div>
          <div class="tooltip-confidence">
            置信度: {{ Math.round(tooltipData.confidence * 100) }}%
          </div>
          <div v-if="tooltipData.box && tooltipData.box.length > 0" class="tooltip-box">
            位置: [{{ tooltipData.box.map(v => Math.round(v)).join(', ') }}]
          </div>
        </div>
      </div>
      
      <el-empty
        v-else
        description="暂无图像数据"
        :image-size="100"
      />
    </div>
    
    <div v-if="detections.length" class="detection-list">
      <div class="detection-header">
        <el-icon><location /></el-icon>
        <span>检测到 {{ detections.length }} 个病灶区域</span>
      </div>
      <div class="detection-tags">
        <el-tag
          v-for="(det, idx) in detections"
          :key="idx"
          :type="getTagType(det.confidence)"
          class="detection-tag"
          effect="plain"
          @mouseenter="highlightDetection(idx)"
          @mouseleave="unhighlightDetection"
        >
          <el-icon><aim /></el-icon>
          {{ det.class_name }} ({{ Math.round(det.confidence * 100) }}%)
        </el-tag>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import {
  PictureFilled,
  Loading,
  Location,
  Aim
} from '@element-plus/icons-vue'

/**
 * 检测结果数据结构
 */
interface Detection {
  class_name: string
  confidence: number
  box?: number[]
}

/**
 * AnnotatedImage 组件 Props
 * @property {string} imageSrc - 原始图像 URL 或 Base64
 * @property {string} annotatedImage - 标注图像 Base64
 * @property {Detection[]} detections - 检测结果数组
 */
interface Props {
  imageSrc?: string
  annotatedImage?: string
  detections?: Detection[]
}

const props = withDefaults(defineProps<Props>(), {
  imageSrc: '',
  annotatedImage: '',
  detections: () => []
})

const canvasRef = ref<HTMLCanvasElement | null>(null)
const tooltipVisible = ref(false)
const tooltipStyle = ref<Record<string, string>>({})
const tooltipData = ref<Detection>({
  class_name: '',
  confidence: 0,
  box: []
})

const highlightedIndex = ref<number | null>(null)

const BOX_COLORS: string[] = [
  '#f56c6c',
  '#e6a23c',
  '#409eff',
  '#67c23a',
  '#909399',
  '#b37feb'
]

/**
 * 获取置信度对应的标签类型
 * @param confidence - 置信度值 (0-1)
 * @returns Element Plus 标签类型
 */
const getTagType = (confidence: number): 'success' | 'warning' | 'danger' | 'info' => {
  if (confidence >= 0.8) return 'success'
  if (confidence >= 0.6) return 'warning'
  if (confidence >= 0.4) return 'danger'
  return 'info'
}

/**
 * 获取检测框颜色
 * @param index - 检测框索引
 * @returns 颜色字符串
 */
const getBoxColor = (index: number): string => {
  return BOX_COLORS[index % BOX_COLORS.length] || '#f56c6c'
}

/**
 * 在 Canvas 上绘制检测框
 */
const drawDetections = async () => {
  if (!canvasRef.value || !props.imageSrc || !props.detections.length) {
    return
  }

  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const img = new Image()
  img.crossOrigin = 'anonymous'
  
  img.onload = () => {
    const maxWidth = 800
    const maxHeight = 600
    let width = img.width
    let height = img.height

    if (width > maxWidth) {
      height = (maxWidth / width) * height
      width = maxWidth
    }
    if (height > maxHeight) {
      width = (maxHeight / height) * width
      height = maxHeight
    }

    canvas.width = width
    canvas.height = height

    ctx.drawImage(img, 0, 0, width, height)

    const scaleX = width / img.width
    const scaleY = height / img.height

    props.detections.forEach((det, idx) => {
      if (det.box && det.box.length >= 4) {
        const x1 = det.box[0] ?? 0
        const y1 = det.box[1] ?? 0
        const x2 = det.box[2] ?? 0
        const y2 = det.box[3] ?? 0
        
        const boxX = x1 * scaleX
        const boxY = y1 * scaleY
        const boxW = (x2 - x1) * scaleX
        const boxH = (y2 - y1) * scaleY

        const color = getBoxColor(idx)
        const isHighlighted = highlightedIndex.value === idx
        const lineWidth = isHighlighted ? 4 : 2

        ctx.strokeStyle = color
        ctx.lineWidth = lineWidth
        ctx.strokeRect(boxX, boxY, boxW, boxH)

        if (isHighlighted) {
          ctx.fillStyle = color + '20'
          ctx.fillRect(boxX, boxY, boxW, boxH)
        }

        const label = `${det.class_name} ${Math.round(det.confidence * 100)}%`
        ctx.font = 'bold 14px Arial'
        const textWidth = ctx.measureText(label).width
        const labelHeight = 22

        ctx.fillStyle = color
        ctx.fillRect(boxX, boxY - labelHeight, textWidth + 10, labelHeight)

        ctx.fillStyle = '#ffffff'
        ctx.fillText(label, boxX + 5, boxY - 6)
      }
    })
  }

  img.onerror = () => {
    console.error('图像加载失败')
  }

  img.src = props.imageSrc
}

/**
 * 处理鼠标移动事件
 * @param event - 鼠标事件
 */
const handleMouseMove = (event: MouseEvent) => {
  if (!canvasRef.value || !props.detections.length) return

  const canvas = canvasRef.value
  const rect = canvas.getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  const scaleX = canvas.width / rect.width
  const scaleY = canvas.height / rect.height
  const canvasX = x * scaleX
  const canvasY = y * scaleY

  for (let i = 0; i < props.detections.length; i++) {
    const det = props.detections[i]
    if (det && det.box && det.box.length >= 4) {
      const x1 = det.box[0] ?? 0
      const y1 = det.box[1] ?? 0
      const x2 = det.box[2] ?? 0
      const y2 = det.box[3] ?? 0
      
      const img = new Image()
      img.src = props.imageSrc || ''
      
      const scaleXBox = canvas.width / (img.width || canvas.width)
      const scaleYBox = canvas.height / (img.height || canvas.height)
      
      const boxX = x1 * scaleXBox
      const boxY = y1 * scaleYBox
      const boxW = (x2 - x1) * scaleXBox
      const boxH = (y2 - y1) * scaleYBox

      if (canvasX >= boxX && canvasX <= boxX + boxW &&
          canvasY >= boxY && canvasY <= boxY + boxH) {
        tooltipData.value = { ...det }
        tooltipVisible.value = true
        tooltipStyle.value = {
          left: `${event.clientX - rect.left + 10}px`,
          top: `${event.clientY - rect.top + 10}px`
        }
        return
      }
    }
  }

  tooltipVisible.value = false
}

/**
 * 隐藏工具提示
 */
const hideTooltip = () => {
  tooltipVisible.value = false
}

/**
 * 高亮显示检测框
 * @param index - 检测框索引
 */
const highlightDetection = (index: number) => {
  highlightedIndex.value = index
  drawDetections()
}

/**
 * 取消高亮显示
 */
const unhighlightDetection = () => {
  highlightedIndex.value = null
  drawDetections()
}

watch(() => [props.imageSrc, props.detections, props.annotatedImage], () => {
  nextTick(() => {
    if (!props.annotatedImage && props.imageSrc && props.detections.length) {
      drawDetections()
    }
  })
}, { deep: true })

onMounted(() => {
  if (!props.annotatedImage && props.imageSrc && props.detections.length) {
    nextTick(() => {
      drawDetections()
    })
  }
})
</script>

<style scoped>
.annotated-image-container {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.image-wrapper {
  position: relative;
  width: 100%;
  min-height: 200px;
  background-color: #f5f7fa;
  border-radius: 8px;
  overflow: hidden;
  display: flex;
  justify-content: center;
  align-items: center;
}

.annotated-image {
  max-width: 100%;
  max-height: 500px;
}

.canvas-container {
  position: relative;
  width: 100%;
  display: flex;
  justify-content: center;
}

.detection-canvas {
  max-width: 100%;
  max-height: 500px;
  border-radius: 8px;
  cursor: crosshair;
}

.detection-tooltip {
  position: absolute;
  background-color: rgba(0, 0, 0, 0.85);
  color: #ffffff;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
  pointer-events: none;
  z-index: 100;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.15);
}

.tooltip-title {
  font-weight: bold;
  margin-bottom: 4px;
  font-size: 14px;
}

.tooltip-confidence {
  color: #67c23a;
}

.tooltip-box {
  color: #909399;
  font-size: 12px;
  margin-top: 4px;
}

.image-error,
.image-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  color: #909399;
  padding: 40px;
}

.image-error .el-icon,
.image-loading .el-icon {
  font-size: 48px;
}

.detection-list {
  background-color: #fafafa;
  border-radius: 8px;
  padding: 16px;
}

.detection-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
  font-weight: 600;
  color: #303133;
}

.detection-header .el-icon {
  color: #409eff;
  font-size: 18px;
}

.detection-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.detection-tag {
  cursor: pointer;
  transition: all 0.3s;
  padding: 6px 12px;
  font-size: 13px;
}

.detection-tag:hover {
  transform: translateY(-2px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.detection-tag .el-icon {
  margin-right: 4px;
}
</style>
