const PptxGenJS = require('pptxgenjs');

// 创建PPT实例
const pptx = new PptxGenJS();

// 图表URLs
const chartUrls = {
  performance: 'https://mdn.alipayobjects.com/one_clip/afts/img/EWjNSI8D4P4AAAAAQmAAAAgAoEACAQFr/original',
  diseaseDistribution: 'https://mdn.alipayobjects.com/one_clip/afts/img/j2aGTL93D-wAAAAAQnAAAAgAoEACAQFr/original'
};

// 封面幻灯片
let slide = pptx.addSlide();
slide.addText('基于多模态融合的小麦病害诊断系统', {
  x: 0, y: 1, w: '100%', h: 2,
  fontSize: 36, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('Wheat Disease Diagnosis System based on Multimodal Fusion', {
  x: 0, y: 3, w: '100%', h: 1.5,
  fontSize: 20, fontFace: 'Arial', align: 'center',
  color: '548235'
});
slide.addText('毕业设计答辩', {
  x: 0, y: 4.5, w: '100%', h: 1,
  fontSize: 24, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('IWDDA Team', {
  x: 0, y: 6, w: '100%', h: 1,
  fontSize: 18, fontFace: 'Arial', align: 'center',
  color: '7030A0'
});

// 目录幻灯片
slide = pptx.addSlide();
slide.addText('目录', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('1. 项目简介\n2. 核心功能\n3. 技术架构\n4. 性能指标\n5. 创新点\n6. 应用场景\n7. 未来展望\n8. 致谢', {
  x: 2, y: 2, w: 6, h: 5,
  fontSize: 20, fontFace: 'Arial',
  color: '333333'
});

// 项目简介幻灯片
slide = pptx.addSlide();
slide.addText('项目简介', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('IWDDA（Intelligent Wheat Disease Diagnosis Agent）是一个基于多模态特征融合的小麦病害诊断智能体，旨在解决传统农业诊断中依赖专家经验、难以标准化的问题。该系统通过整合计算机视觉、大语言模型和知识图谱技术，实现了从"感知"到"认知"再到"行动"的完整闭环。', {
  x: 1, y: 2, w: 8, h: 3,
  fontSize: 16, fontFace: 'Arial',
  color: '333333'
});
slide.addText('核心优势：', {
  x: 1, y: 5, w: 2, h: 0.8,
  fontSize: 18, fontFace: 'Arial',
  color: '366092'
});
slide.addText('• 多模态融合：结合图像视觉特征、文本语义描述和结构化知识图谱\n• 智能推理：基于知识图谱的 GraphRAG 机制，提供科学的防治建议\n• 实时交互：基于 SSE 流式推送的实时诊断进度\n• 高效检测：基于 YOLOv8s 的 FP16 推理，支持 17 类小麦病害识别\n• 安全可靠：JWT 双令牌认证、XSS 防护、RBAC 权限控制', {
  x: 1, y: 5.8, w: 8, h: 2.5,
  fontSize: 14, fontFace: 'Arial',
  color: '333333'
});

// 核心功能幻灯片
slide = pptx.addSlide();
slide.addText('核心功能', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});

// 视觉感知模块
slide.addText('1. 视觉感知模块 (Vision Agent)', {
  x: 1, y: 2, w: 8, h: 0.8,
  fontSize: 18, fontFace: 'Arial',
  color: '548235'
});
slide.addText('• 基于 YOLOv8s 的高精度目标检测（FP16 推理）\n• 支持 17类 小麦病害和虫害识别\n• 自动定位病灶区域并绘制可视化结果\n• LRU 推理缓存（64 条）+ SHA-256 图像哈希匹配', {
  x: 1.5, y: 2.8, w: 7.5, h: 1.5,
  fontSize: 14, fontFace: 'Arial',
  color: '333333'
});

// 多模态理解模块
slide.addText('2. 多模态理解模块 (Language Agent)', {
  x: 1, y: 4.5, w: 8, h: 0.8,
  fontSize: 18, fontFace: 'Arial',
  color: '548235'
});
slide.addText('• 基于 Qwen3-VL-2B-Instruct 的图文联合理解（INT4 量化）\n• 支持 Thinking 推理链模式，提供详细诊断依据\n• 多语言文本嵌入与检索', {
  x: 1.5, y: 5.3, w: 7.5, h: 1.2,
  fontSize: 14, fontFace: 'Arial',
  color: '333333'
});

// 知识图谱模块
slide = pptx.addSlide();
slide.addText('核心功能（续）', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});

// 知识图谱模块
slide.addText('3. 知识图谱模块 (Knowledge Agent)', {
  x: 1, y: 2, w: 8, h: 0.8,
  fontSize: 18, fontFace: 'Arial',
  color: '548235'
});
slide.addText('• 基于 Neo4j 的农业知识图谱\n• GraphRAG 知识检索增强生成机制\n• TransE 知识嵌入 + 多跳推理\n• 包含病害成因、预防措施、治疗药剂等完整知识体系', {
  x: 1.5, y: 2.8, w: 7.5, h: 1.5,
  fontSize: 14, fontFace: 'Arial',
  color: '333333'
});

// 多模态融合模块
slide.addText('4. 多模态融合模块 (Fusion Agent)', {
  x: 1, y: 4.5, w: 8, h: 0.8,
  fontSize: 18, fontFace: 'Arial',
  color: '548235'
});
slide.addText('• KAD-Former (Knowledge-Aware Diffusion Fusion) 融合策略\n• 决策级融合：视觉主导 + 文本辅助 + 知识仲裁\n• 提供详细的推理过程和置信度评估\n• FusionAnnotator 知识增强标注 + ROI 可视化', {
  x: 1.5, y: 5.3, w: 7.5, h: 1.5,
  fontSize: 14, fontFace: 'Arial',
  color: '333333'
});

// Web 交互系统
slide.addText('5. Web 交互系统', {
  x: 1, y: 7, w: 8, h: 0.8,
  fontSize: 18, fontFace: 'Arial',
  color: '548235'
});
slide.addText('• Vue 3 + TypeScript + Element Plus 前端界面\n• FastAPI 后端服务，四层分离架构\n• SSE 流式响应：实时诊断进度推送，6 种事件类型\n• JWT 双令牌认证：Access 30min + Refresh 7days\n• RBAC 权限控制：farmer / technician / admin 三级角色', {
  x: 1.5, y: 7.8, w: 7.5, h: 2,
  fontSize: 14, fontFace: 'Arial',
  color: '333333'
});

// 技术架构幻灯片
slide = pptx.addSlide();
slide.addText('技术架构', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText(`IWDDA System
├── 交互层 (Interaction Layer)
│   ├── Vue3 Web 前端 (Element Plus + ECharts)
│   └── FastAPI REST API + SSE 流式推送
├── 感知层 (Perception Layer)
│   ├── VisionAgent (YOLOv8s FP16)   - 图像检测与定位
│   └── LanguageAgent (Qwen3-VL)     - 多模态语义理解
├── 认知层 (Cognition Layer)
│   ├── KnowledgeAgent (Neo4j+TransE) - 知识图谱推理
│   └── FusionAgent (KAD-Former)      - 多模态融合决策
└── 基础设施层 (Infrastructure Layer)
    ├── JWT双令牌认证 + RBAC权限
    ├── SSE流式推送 + 心跳保活
    ├── 并发限流 + GPU监控
    └── Redis缓存 + Token黑名单`, {
  x: 1, y: 2, w: 8, h: 4,
  fontSize: 14, fontFace: 'Courier New',
  color: '333333'
});

// 性能指标幻灯片
slide = pptx.addSlide();
slide.addText('性能指标', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('• YOLO 推理延迟: 225ms (目标: ≤150ms)\n• SSE 首事件延迟: 0.01ms (目标: ≤500ms)\n• 完整诊断延迟: 185.8ms (目标: ≤40s)\n• Qwen 显存占用: ~2.6GB (目标: ≤4GB)\n• 知识覆盖率: 100% (目标: ≥95%)', {
  x: 1, y: 2, w: 8, h: 5,
  fontSize: 16, fontFace: 'Arial',
  color: '333333'
});

// 病害类别分布幻灯片
slide = pptx.addSlide();
slide.addText('病害类别分布', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('• 昆虫: 3类 (蚜虫、螨虫、茎蝇)\n• 真菌: 13类 (锈病、茎锈病、叶锈病、条锈病、黑粉病、根腐病、叶斑病、小麦爆发病、赤霉病、壳针孢叶斑病、斑点叶斑病、褐斑病、白粉病)\n• 正常: 1类 (健康)', {
  x: 1, y: 2, w: 8, h: 5,
  fontSize: 16, fontFace: 'Arial',
  color: '333333'
});

// 创新点幻灯片
slide = pptx.addSlide();
slide.addText('创新点', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('• 多模态融合架构：首次将视觉检测、多模态理解和知识图谱有机结合\n• KAD-Former 融合策略：创新的知识感知扩散融合机制，提高诊断准确性\n• GraphRAG 知识增强：利用知识图谱进行检索增强生成，提供科学的防治建议\n• 实时流式响应：基于 SSE 的实时诊断进度推送，提升用户体验\n• INT4 量化优化：Qwen3-VL 模型的 INT4 量化，降低显存占用至 2.6GB\n• 完整安全体系：JWT 双令牌认证、XSS 防护、RBAC 权限控制等多重安全措施\n• 可扩展性设计：模块化架构，支持模型升级和功能扩展\n• 边缘部署支持：优化的模型和推理引擎，支持在边缘设备上部署', {
  x: 1, y: 2, w: 8, h: 5,
  fontSize: 14, fontFace: 'Arial',
  color: '333333'
});

// 应用场景幻灯片
slide = pptx.addSlide();
slide.addText('应用场景', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('• 农业生产：实时监测小麦病害，及时采取防治措施\n• 农业科研：收集和分析病害数据，支持科研研究\n• 农业教育：作为教学工具，帮助学生了解小麦病害\n• 智能农场：与物联网设备集成，实现自动化监测\n• 农业咨询：为农民提供专业的病害诊断和防治建议', {
  x: 1, y: 2, w: 8, h: 3,
  fontSize: 16, fontFace: 'Arial',
  color: '333333'
});
slide.addText('图片说明：由于图片读取失败，此处应为小麦病害示例图片或系统界面截图，展示系统的实际应用效果。', {
  x: 1, y: 5, w: 8, h: 1.5,
  fontSize: 14, fontFace: 'Arial', align: 'center',
  color: '666666'
});

// 未来展望幻灯片
slide = pptx.addSlide();
slide.addText('未来展望', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('• 扩展支持更多作物类型和病害种类\n• 优化模型性能，进一步降低推理延迟\n• 增加移动端应用，支持离线诊断\n• 引入联邦学习，保护用户数据隐私\n• 与农业物联网设备集成，实现智能监测\n• 开发专家系统，提供更精准的农业决策支持', {
  x: 1, y: 2, w: 8, h: 4,
  fontSize: 16, fontFace: 'Arial',
  color: '333333'
});

// 致谢幻灯片
slide = pptx.addSlide();
slide.addText('致谢', {
  x: 0, y: 2, w: '100%', h: 1.5,
  fontSize: 32, fontFace: 'Arial', align: 'center',
  color: '366092'
});
slide.addText('感谢导师的悉心指导\n感谢团队成员的协作\n感谢所有支持本项目的人', {
  x: 0, y: 4, w: '100%', h: 2,
  fontSize: 20, fontFace: 'Arial', align: 'center',
  color: '333333'
});
slide.addText('谢谢聆听！', {
  x: 0, y: 6.5, w: '100%', h: 1,
  fontSize: 24, fontFace: 'Arial', align: 'center',
  color: '548235'
});

// 生成PPT文件
pptx.writeFile({ fileName: 'wheat_disease_diagnosis_ppt_enhanced.pptx' });
console.log('PPT generated successfully!');
