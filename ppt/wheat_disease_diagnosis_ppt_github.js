const PptxGenJS = require('pptxgenjs');

// 创建PPT实例
const pptx = new PptxGenJS();

// 设置主题和样式
// pptx.setDefaultFont({ name: 'Arial' }); // 移除不存在的方法

// 颜色方案
const colors = {
  primary: '#2C5F2D',    // 森林绿
  secondary: '#97BC62',  //  moss绿
  accent: '#F5F5F5',     // 奶油色
  text: '#333333',       // 深灰色
  lightText: '#666666'   // 浅灰色
};

// 1. 封面
const slide1 = pptx.addSlide();
slide1.addText('基于多模态融合的小麦病害诊断系统', {
  x: 1, y: 1, w: 8, h: 1.5,
  fontSize: 36,
  bold: true,
  color: colors.primary,
  align: 'center'
});
slide1.addText('Intelligent Wheat Disease Diagnosis System based on Multimodal Fusion', {
  x: 1, y: 2.5, w: 8, h: 1,
  fontSize: 20,
  color: colors.lightText,
  align: 'center'
});
slide1.addText('项目团队', {
  x: 1, y: 4, w: 8, h: 0.75,
  fontSize: 16,
  color: colors.text,
  align: 'center'
});
slide1.addText('2024', {
  x: 1, y: 4.75, w: 8, h: 0.75,
  fontSize: 16,
  color: colors.lightText,
  align: 'center'
});

// 2. 目录
const slide2 = pptx.addSlide();
slide2.addText('目录', {
  x: 1, y: 0.5, w: 8, h: 1,
  fontSize: 32,
  bold: true,
  color: colors.primary,
  align: 'center'
});

const tableOfContents = [
  '项目简介',
  '核心功能',
  '技术架构',
  '性能指标',
  '创新点',
  '应用场景',
  '未来展望',
  '致谢'
];

tableOfContents.forEach((item, index) => {
  slide2.addText(`${index + 1}. ${item}`, {
    x: 2, y: 1.75 + index * 0.5,
    fontSize: 16,
    color: colors.text
  });
});

// 3. 项目简介
const slide3 = pptx.addSlide();
slide3.addText('项目简介', {
  x: 1, y: 0.5, w: 8, h: 0.75,
  fontSize: 28,
  bold: true,
  color: colors.primary,
  align: 'center'
});

// 添加项目相关图片
try {
  slide3.addImage({
    path: '/workspace/mmexport1776920706492.jpg',
    x: 5, y: 1.5, w: 4, h: 3
  });
} catch (error) {
  console.log('图片添加失败:', error.message);
}

slide3.addText('项目背景', {
  x: 1, y: 1.5, w: 4, h: 0.5,
  fontSize: 18,
  bold: true,
  color: colors.secondary
});
slide3.addText('传统农业诊断依赖专家经验，难以标准化', {
  x: 1, y: 2, w: 4, h: 0.5,
  fontSize: 14,
  color: colors.text
});

slide3.addText('项目目标', {
  x: 1, y: 2.75, w: 4, h: 0.5,
  fontSize: 18,
  bold: true,
  color: colors.secondary
});
slide3.addText('构建智能小麦病害诊断系统，实现从"感知"到"认知"再到"行动"的完整闭环', {
  x: 1, y: 3.25, w: 4, h: 0.75,
  fontSize: 14,
  color: colors.text
});

slide3.addText('核心优势', {
  x: 1, y: 4.25, w: 4, h: 0.5,
  fontSize: 18,
  bold: true,
  color: colors.secondary
});
const advantages = [
  '多模态融合：结合图像视觉特征、文本语义描述和结构化知识图谱',
  '智能推理：基于知识图谱的 GraphRAG 机制，提供科学的防治建议',
  '实时交互：基于 SSE 流式推送的实时诊断进度',
  '高效检测：基于 YOLOv8s 的 FP16 推理，支持 17 类小麦病害识别',
  '安全可靠：JWT 双令牌认证、XSS 防护、RBAC 权限控制'
];

advantages.forEach((adv, index) => {
  slide3.addText(`• ${adv}`, {
    x: 1, y: 4.75 + index * 0.4,
    w: 4,
    fontSize: 12,
    color: colors.text
  });
});

// 4. 核心功能
const slide4 = pptx.addSlide();
slide4.addText('核心功能', {
  x: 1, y: 0.5, w: 8, h: 0.75,
  fontSize: 28,
  bold: true,
  color: colors.primary,
  align: 'center'
});

const features = [
  {
    title: '视觉感知模块',
    content: '基于 YOLOv8s 的高精度目标检测（FP16 推理）\n支持 17 类小麦病害和虫害识别\n自动定位病灶区域并绘制可视化结果\nLRU 推理缓存（64 条）+ SHA-256 图像哈希匹配'
  },
  {
    title: '多模态理解模块',
    content: '基于 Qwen3-VL-2B-Instruct 的图文联合理解（INT4 量化）\n支持 Thinking 推理链模式，提供详细诊断依据\n多语言文本嵌入与检索'
  },
  {
    title: '知识图谱模块',
    content: '基于 Neo4j 的农业知识图谱\nGraphRAG 知识检索增强生成机制\nTransE 知识嵌入 + 多跳推理\n包含病害成因、预防措施、治疗药剂等完整知识体系'
  },
  {
    title: '多模态融合模块',
    content: 'KAD-Former (Knowledge-Aware Diffusion Fusion) 融合策略\n决策级融合：视觉主导 + 文本辅助 + 知识仲裁\n提供详细的推理过程和置信度评估\nFusionAnnotator 知识增强标注 + ROI 可视化'
  },
  {
    title: 'Web 交互系统',
    content: 'Vue 3 + TypeScript + Element Plus 前端界面\nFastAPI 后端服务，四层分离架构\nSSE 流式响应：实时诊断进度推送，6 种事件类型\nJWT 双令牌认证 + RBAC 权限控制'
  }
];

features.forEach((feature, index) => {
  const yPos = 1.5 + Math.floor(index / 2) * 2;
  const xPos = index % 2 === 0 ? 1 : 5;
  slide4.addText(feature.title, {
    x: xPos, y: yPos, w: 3.5, h: 0.5,
    fontSize: 16,
    bold: true,
    color: colors.secondary
  });
  slide4.addText(feature.content, {
    x: xPos + 0.25, y: yPos + 0.5, w: 3, h: 1.25,
    fontSize: 12,
    color: colors.text,
    lineSpacing: 1.2
  });
});

// 5. 技术架构
const slide5 = pptx.addSlide();
slide5.addText('技术架构', {
  x: 1, y: 0.5, w: 8, h: 0.75,
  fontSize: 28,
  bold: true,
  color: colors.primary,
  align: 'center'
});

// 架构图描述
slide5.addText('系统架构层次', {
  x: 1, y: 1.5, w: 8, h: 0.5,
  fontSize: 18,
  bold: true,
  color: colors.secondary
});

const architecture = [
  '交互层 (Interaction Layer):\n  - Vue3 Web 前端 (Element Plus + ECharts)\n  - FastAPI REST API + SSE 流式推送',
  '感知层 (Perception Layer):\n  - VisionAgent (YOLOv8s FP16) - 图像检测与定位\n  - LanguageAgent (Qwen3-VL) - 多模态语义理解',
  '认知层 (Cognition Layer):\n  - KnowledgeAgent (Neo4j+TransE) - 知识图谱推理\n  - FusionAgent (KAD-Former) - 多模态融合决策',
  '基础设施层 (Infrastructure Layer):\n  - JWT双令牌认证 + RBAC权限\n  - SSE流式推送 + 心跳保活\n  - 并发限流 + GPU监控\n  - Redis缓存 + Token黑名单'
];

architecture.forEach((layer, index) => {
  slide5.addText(layer, {
    x: 1.5, y: 2.25 + index * 1.1,
    fontSize: 12,
    color: colors.text,
    lineSpacing: 1.2
  });
});

// 6. 性能指标
const slide6 = pptx.addSlide();
slide6.addText('性能指标', {
  x: 1, y: 0.5, w: 8, h: 0.75,
  fontSize: 28,
  bold: true,
  color: colors.primary,
  align: 'center'
});

// 添加性能指标图表
slide6.addImage({
  data: 'https://trae-api-cn.mchost.guru/api/ide/v1/text_to_image?prompt=A%20professional%20bar%20chart%20showing%20system%20performance%20metrics%20with%20green%20color%20scheme&image_size=landscape_16_9',
  x: 1, y: 1.5, w: 8, h: 4
});

// 7. 创新点
const slide7 = pptx.addSlide();
slide7.addText('创新点', {
  x: 1, y: 0.5, w: 8, h: 0.75,
  fontSize: 28,
  bold: true,
  color: colors.primary,
  align: 'center'
});

const innovations = [
  {
    title: '多模态融合策略',
    content: 'KAD-Former (Knowledge-Aware Diffusion Fusion) 融合策略，实现视觉、文本和知识的深度融合'
  },
  {
    title: '知识增强生成',
    content: 'GraphRAG 知识检索增强生成机制，提供科学的防治建议'
  },
  {
    title: '实时交互',
    content: 'SSE 流式推送 + 心跳保活，提供实时诊断进度反馈'
  },
  {
    title: '高效检测',
    content: 'YOLOv8s FP16 推理，支持 17 类小麦病害识别'
  },
  {
    title: '安全可靠',
    content: 'JWT 双令牌认证、RBAC 权限控制、并发限流等多重安全保障'
  }
];

innovations.forEach((innovation, index) => {
  const yPos = 1.5 + Math.floor(index / 2) * 1.5;
  const xPos = index % 2 === 0 ? 1 : 5;
  slide7.addText(innovation.title, {
    x: xPos, y: yPos, w: 3.5, h: 0.5,
    fontSize: 16,
    bold: true,
    color: colors.secondary
  });
  slide7.addText(innovation.content, {
    x: xPos + 0.25, y: yPos + 0.5, w: 3, h: 0.75,
    fontSize: 12,
    color: colors.text,
    lineSpacing: 1.2
  });
});

// 8. 应用场景
const slide8 = pptx.addSlide();
slide8.addText('应用场景', {
  x: 1, y: 0.5, w: 8, h: 0.75,
  fontSize: 28,
  bold: true,
  color: colors.primary,
  align: 'center'
});

const scenarios = [
  {
    title: '农田现场诊断',
    content: '农民在田间通过手机拍摄小麦叶片，实时获取病害诊断结果和防治建议'
  },
  {
    title: '农业技术推广',
    content: '农业技术人员使用系统进行病害识别培训，提高基层农技人员的诊断能力'
  },
  {
    title: '病虫害监测',
    content: '通过无人机或固定摄像头采集小麦田图像，系统自动分析病虫害发生情况'
  },
  {
    title: '智能农业决策支持',
    content: '基于诊断数据，为农场管理提供智能化的病虫害防治决策支持'
  }
];

scenarios.forEach((scenario, index) => {
  const yPos = 1.5 + index * 1.25;
  slide8.addText(scenario.title, {
    x: 1, y: yPos, w: 8, h: 0.5,
    fontSize: 16,
    bold: true,
    color: colors.secondary
  });
  slide8.addText(scenario.content, {
    x: 1.5, y: yPos + 0.5, w: 7, h: 0.5,
    fontSize: 14,
    color: colors.text
  });
});

// 9. 未来展望
const slide9 = pptx.addSlide();
slide9.addText('未来展望', {
  x: 1, y: 0.5, w: 8, h: 0.75,
  fontSize: 28,
  bold: true,
  color: colors.primary,
  align: 'center'
});

const future = [
  {
    title: '模型优化',
    content: '进一步提升诊断 accuracy，优化模型推理速度'
  },
  {
    title: '扩展作物',
    content: '支持更多作物病害的识别和诊断'
  },
  {
    title: '边缘部署',
    content: '支持边缘设备实时诊断，减少云端依赖'
  },
  {
    title: '生态系统',
    content: '构建完整的农业智能诊断生态，集成更多农业管理功能'
  }
];

future.forEach((item, index) => {
  const yPos = 1.5 + Math.floor(index / 2) * 1.5;
  const xPos = index % 2 === 0 ? 1 : 5;
  slide9.addText(item.title, {
    x: xPos, y: yPos, w: 3.5, h: 0.5,
    fontSize: 16,
    bold: true,
    color: colors.secondary
  });
  slide9.addText(item.content, {
    x: xPos + 0.25, y: yPos + 0.5, w: 3, h: 0.75,
    fontSize: 12,
    color: colors.text,
    lineSpacing: 1.2
  });
});

// 10. 致谢
const slide10 = pptx.addSlide();
slide10.addText('致谢', {
  x: 1, y: 0.5, w: 8, h: 1,
  fontSize: 32,
  bold: true,
  color: colors.primary,
  align: 'center'
});

slide10.addText('项目团队成员', {
  x: 1, y: 2, w: 8, h: 0.75,
  fontSize: 18,
  color: colors.text,
  align: 'center'
});

slide10.addText('技术支持', {
  x: 1, y: 3, w: 8, h: 0.75,
  fontSize: 18,
  color: colors.text,
  align: 'center'
});

slide10.addText('参考文献', {
  x: 1, y: 4, w: 8, h: 0.75,
  fontSize: 18,
  color: colors.text,
  align: 'center'
});

// 生成PPT文件
pptx.writeFile({ fileName: 'wheat_disease_diagnosis_ppt_github.pptx' });
console.log('PPT生成成功！文件：wheat_disease_diagnosis_ppt_github.pptx');
