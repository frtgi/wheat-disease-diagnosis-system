# PPT 结构设计

## 1. 封面
- 标题：基于多模态融合的小麦病害诊断系统
- 副标题：Intelligent Wheat Disease Diagnosis System based on Multimodal Fusion
- 作者：项目团队
- 日期：2024

## 2. 目录
- 项目简介
- 核心功能
- 技术架构
- 性能指标
- 创新点
- 应用场景
- 未来展望
- 致谢

## 3. 项目简介
- 项目背景：传统农业诊断依赖专家经验，难以标准化
- 项目目标：构建智能小麦病害诊断系统
- 核心优势：多模态融合、智能推理、实时交互、高效检测、安全可靠

## 4. 核心功能
- 视觉感知模块：YOLOv8s目标检测，17类病害识别
- 多模态理解模块：Qwen3-VL图文联合理解
- 知识图谱模块：Neo4j知识存储与推理
- 多模态融合模块：KAD-Former融合决策
- Web交互系统：Vue3前端 + FastAPI后端

## 5. 技术架构
- 交互层：Vue3 Web前端、FastAPI REST API + SSE流式推送
- 感知层：VisionAgent (YOLOv8s)、LanguageAgent (Qwen3-VL)
- 认知层：KnowledgeAgent (Neo4j+TransE)、FusionAgent (KAD-Former)
- 基础设施层：JWT认证、SSE推送、并发限流、Redis缓存

## 6. 性能指标
- YOLO推理延迟：225ms (CPU)
- SSE首事件延迟：0.01ms
- 完整诊断延迟：185.8ms (YOLO-only)
- Qwen显存占用：~2.6GB (INT4)
- 知识覆盖率：100%

## 7. 创新点
- 多模态融合策略：KAD-Former (Knowledge-Aware Diffusion Fusion)
- 知识增强生成：GraphRAG机制
- 实时交互：SSE流式推送 + 心跳保活
- 高效检测：YOLOv8s FP16推理
- 安全可靠：JWT双令牌认证、RBAC权限控制

## 8. 应用场景
- 农田现场诊断
- 农业技术推广
- 病虫害监测
- 智能农业决策支持

## 9. 未来展望
- 模型优化：进一步提升诊断 accuracy
- 扩展作物：支持更多作物病害
- 边缘部署：支持边缘设备实时诊断
- 生态系统：构建完整的农业智能诊断生态

## 10. 致谢
- 项目团队成员
- 技术支持
- 参考文献

## 设计风格
- 配色方案：绿色为主色调，象征农业和科技
- 字体：无衬线字体，清晰易读
- 布局：简洁明了，重点突出
- 动画：适当的过渡效果，增强演示效果