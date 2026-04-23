# 基于多模态融合的小麦病害诊断系统 - PPT设计需求文档

## Overview
- **Summary**: 基于GitHub项目实际代码和图片内容，使用pptx和gh-cli技能设计一个专业的毕业设计答辩PPT，展示小麦病害诊断系统的核心功能、技术架构和创新点。
- **Purpose**: 为毕业设计答辩提供一个清晰、专业的演示文档，帮助评审老师理解项目的技术价值和创新之处。
- **Target Users**: 毕业设计评审老师、项目团队成员、潜在的合作伙伴。

## Goals
- 展示项目的核心功能和技术架构
- 突出系统的创新点和技术优势
- 提供清晰的项目实施路径和成果展示
- 设计专业、美观的PPT界面
- 包含数据可视化图表，展示系统性能和效果
- 基于GitHub项目实际代码内容生成PPT

## Non-Goals (Out of Scope)
- 不包含详细的代码实现细节
- 不包含完整的用户操作手册
- 不包含系统部署的详细步骤

## Background & Context
- 项目是一个基于多模态融合的小麦病害诊断系统，整合了计算机视觉、大语言模型和知识图谱技术
- 系统支持17类小麦病害和虫害的识别
- 项目使用了YOLOv8s、Qwen3-VL、Neo4j等先进技术
- 项目已经完成了核心功能的开发和测试
- 项目代码存储在GitHub仓库中，包含完整的前后端实现

## Functional Requirements
- **FR-1**: PPT应包含项目简介、核心功能、技术架构、性能指标等内容
- **FR-2**: PPT应包含数据可视化图表，展示系统性能和诊断效果
- **FR-3**: PPT应包含系统的创新点和技术优势
- **FR-4**: PPT应设计专业、美观的界面，符合学术答辩的风格
- **FR-5**: PPT应包含项目的实际应用场景和未来展望
- **FR-6**: PPT应基于GitHub项目的实际代码内容生成，反映项目的真实状态

## Non-Functional Requirements
- **NFR-1**: PPT设计应简洁明了，重点突出
- **NFR-2**: PPT应使用专业的配色方案和字体
- **NFR-3**: PPT应包含适当的动画效果，增强演示效果
- **NFR-4**: PPT应兼容常见的PPT播放器
- **NFR-5**: PPT应使用pptx技能生成，确保专业质量
- **NFR-6**: PPT应利用gh-cli技能获取GitHub项目的实际代码信息

## Constraints
- **Technical**: 使用PPTXGenJS库和pptx技能生成PPT，使用gh-cli技能获取GitHub项目信息
- **Business**: 符合毕业设计答辩的时间要求（通常15-20分钟）
- **Dependencies**: 依赖项目的代码和文档内容，依赖GitHub仓库的实际代码

## Assumptions
- 项目代码和文档内容是完整的
- 图片内容与项目相关，可用于PPT设计
- PPT将用于正式的毕业设计答辩
- GitHub项目代码可以通过gh-cli访问

## Acceptance Criteria

### AC-1: PPT内容完整性
- **Given**: 评审老师查看PPT
- **When**: 浏览所有幻灯片
- **Then**: PPT应包含项目简介、核心功能、技术架构、性能指标、创新点等完整内容
- **Verification**: `human-judgment`

### AC-2: 数据可视化效果
- **Given**: 评审老师查看PPT中的图表
- **When**: 查看性能指标和诊断效果图表
- **Then**: 图表应清晰展示系统性能和诊断效果
- **Verification**: `human-judgment`

### AC-3: 界面设计质量
- **Given**: 评审老师查看PPT界面
- **When**: 浏览PPT的设计风格和布局
- **Then**: PPT应设计专业、美观，符合学术答辩的风格
- **Verification**: `human-judgment`

### AC-4: 技术创新展示
- **Given**: 评审老师查看PPT中的创新点部分
- **When**: 了解系统的技术创新
- **Then**: PPT应清晰展示系统的技术创新和优势
- **Verification**: `human-judgment`

### AC-5: 演示效果
- **Given**: 答辩人使用PPT进行演示
- **When**: 进行15-20分钟的答辩
- **Then**: PPT应支持流畅的演示，重点突出
- **Verification**: `human-judgment`

### AC-6: 基于实际代码
- **Given**: 查看PPT内容
- **When**: 对比GitHub项目实际代码
- **Then**: PPT内容应准确反映项目的实际代码结构和功能
- **Verification**: `human-judgment`

## Open Questions
- [ ] 图片内容的具体内容是什么？如何在PPT中使用？
- [ ] 答辩的具体时间要求是什么？
- [ ] 是否需要包含系统的实际运行演示视频？
- [ ] GitHub仓库的具体地址是什么？