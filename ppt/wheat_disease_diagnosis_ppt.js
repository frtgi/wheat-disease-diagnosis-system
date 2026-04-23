const PptxGenJS = require('pptxgenjs');
const { LAYOUT_WIDE, ALIGN_CENTER, FONT_HELVETICA, FONT_HELVETICA_BOLD, FONT_HELVETICA_ITALIC } = PptxGenJS;

// 创建PPT实例
const pptx = new PptxGenJS();

// 标题幻灯片
let slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('基于多模态融合的小麦病害诊断系统', {
  x: 0, y: 1, w: '100%', h: 2,
  fontSize: 36, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});
slide.addText('毕业设计答辩', {
  x: 0, y: 3, w: '100%', h: 1.5,
  fontSize: 24, fontFace: FONT_HELVETICA, align: ALIGN_CENTER,
  color: '548235'
});
slide.addText('IWDDA Team', {
  x: 0, y: 5, w: '100%', h: 1,
  fontSize: 18, fontFace: FONT_HELVETICA_ITALIC, align: ALIGN_CENTER,
  color: '7030A0'
});

// 项目简介
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('项目简介', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});
slide.addText('IWDDA（Intelligent Wheat Disease Diagnosis Agent）是一个基于多模态特征融合的小麦病害诊断智能体，旨在解决传统农业诊断中依赖专家经验、难以标准化的问题。', {
  x: 1, y: 2, w: 8, h: 2,
  fontSize: 18, fontFace: FONT_HELVETICA,
  color: '333333'
});
slide.addText('核心优势：', {
  x: 1, y: 4, w: 2, h: 1,
  fontSize: 20, fontFace: FONT_HELVETICA_BOLD,
  color: '366092'
});
slide.addText('• 多模态融合：结合图像视觉特征、文本语义描述和结构化知识图谱\n• 智能推理：基于知识图谱的 GraphRAG 机制，提供科学的防治建议\n• 实时交互：基于 SSE 流式推送的实时诊断进度\n• 高效检测：基于 YOLOv8s 的 FP16 推理，支持 17 类小麦病害识别\n• 安全可靠：JWT 双令牌认证、XSS 防护、RBAC 权限控制', {
  x: 1, y: 4.8, w: 8, h: 3,
  fontSize: 16, fontFace: FONT_HELVETICA,
  color: '333333'
});

// 系统架构
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('系统架构', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
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
  fontSize: 14, fontFace: FONT_HELVETICA,
  color: '333333'
});

// 核心功能模块
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('核心功能模块', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});

// 视觉感知模块
slide.addText('1. 视觉感知模块 (Vision Agent)', {
  x: 1, y: 2, w: 8, h: 0.8,
  fontSize: 20, fontFace: FONT_HELVETICA_BOLD,
  color: '548235'
});
slide.addText('• 基于 YOLOv8s 的高精度目标检测（FP16 推理）\n• 支持 17类 小麦病害和虫害识别\n• 自动定位病灶区域并绘制可视化结果\n• LRU 推理缓存（64 条）+ SHA-256 图像哈希匹配', {
  x: 1.5, y: 2.8, w: 7.5, h: 1.5,
  fontSize: 16, fontFace: FONT_HELVETICA,
  color: '333333'
});

// 多模态理解模块
slide.addText('2. 多模态理解模块 (Language Agent)', {
  x: 1, y: 4.5, w: 8, h: 0.8,
  fontSize: 20, fontFace: FONT_HELVETICA_BOLD,
  color: '548235'
});
slide.addText('• 基于 Qwen3-VL-2B-Instruct 的图文联合理解（INT4 量化）\n• 支持 Thinking 推理链模式，提供详细诊断依据\n• 多语言文本嵌入与检索', {
  x: 1.5, y: 5.3, w: 7.5, h: 1.2,
  fontSize: 16, fontFace: FONT_HELVETICA,
  color: '333333'
});

// 知识图谱模块
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('核心功能模块（续）', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});

// 知识图谱模块
slide.addText('3. 知识图谱模块 (Knowledge Agent)', {
  x: 1, y: 2, w: 8, h: 0.8,
  fontSize: 20, fontFace: FONT_HELVETICA_BOLD,
  color: '548235'
});
slide.addText('• 基于 Neo4j 的农业知识图谱\n• GraphRAG 知识检索增强生成机制\n• TransE 知识嵌入 + 多跳推理\n• 包含病害成因、预防措施、治疗药剂等完整知识体系', {
  x: 1.5, y: 2.8, w: 7.5, h: 1.5,
  fontSize: 16, fontFace: FONT_HELVETICA,
  color: '333333'
});

// 多模态融合模块
slide.addText('4. 多模态融合模块 (Fusion Agent)', {
  x: 1, y: 4.5, w: 8, h: 0.8,
  fontSize: 20, fontFace: FONT_HELVETICA_BOLD,
  color: '548235'
});
slide.addText('• KAD-Former (Knowledge-Aware Diffusion Fusion) 融合策略\n• 决策级融合：视觉主导 + 文本辅助 + 知识仲裁\n• 提供详细的推理过程和置信度评估\n• FusionAnnotator 知识增强标注 + ROI 可视化', {
  x: 1.5, y: 5.3, w: 7.5, h: 1.5,
  fontSize: 16, fontFace: FONT_HELVETICA,
  color: '333333'
});

// Web 交互系统
slide.addText('5. Web 交互系统', {
  x: 1, y: 7, w: 8, h: 0.8,
  fontSize: 20, fontFace: FONT_HELVETICA_BOLD,
  color: '548235'
});
slide.addText('• Vue 3 + TypeScript + Element Plus 前端界面\n• FastAPI 后端服务，四层分离架构\n• SSE 流式响应：实时诊断进度推送，6 种事件类型\n• JWT 双令牌认证：Access 30min + Refresh 7days\n• RBAC 权限控制：farmer / technician / admin 三级角色', {
  x: 1.5, y: 7.8, w: 7.5, h: 2,
  fontSize: 16, fontFace: FONT_HELVETICA,
  color: '333333'
});

// 技术栈
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('技术栈', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});

const techStacks = [
  ['视觉检测', 'YOLOv8s (Ultralytics)', '目标检测与定位（FP16）'],
  ['多模态理解', 'Qwen3-VL-2B-Instruct (INT4)', '图文联合理解与推理'],
  ['知识图谱', 'Neo4j + TransE', '结构化知识存储与推理'],
  ['知识增强', 'GraphRAG', '知识检索增强生成'],
  ['融合引擎', 'KAD-Former', '多模态特征融合决策'],
  ['后端框架', 'FastAPI + SQLAlchemy', 'REST API + 异步ORM'],
  ['前端框架', 'Vue 3 + TypeScript + Element Plus', 'Web 交互界面'],
  ['数据可视化', 'ECharts', '病害分布图表'],
  ['数据库', 'MySQL 8.0 + Redis 7.2', '数据存储 + 缓存'],
  ['认证安全', 'JWT + bcrypt + SHA-256', '双令牌认证 + 密码安全']
];

let yPos = 2;
techStacks.forEach((stack, index) => {
  slide.addText(`${index + 1}. ${stack[0]}: ${stack[1]}`, {
    x: 1, y: yPos, w: 4, h: 0.6,
    fontSize: 16, fontFace: FONT_HELVETICA_BOLD,
    color: '333333'
  });
  slide.addText(`用途: ${stack[2]}`, {
    x: 5, y: yPos, w: 4, h: 0.6,
    fontSize: 16, fontFace: FONT_HELVETICA,
    color: '666666'
  });
  yPos += 0.8;
});

// 支持的病害类别
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('支持的病害类别', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});

const diseaseCategories = [
  ['0', '蚜虫', 'Aphids', '昆虫'],
  ['1', '螨虫', 'Mites', '昆虫'],
  ['2', '茎蝇', 'Stem Fly', '昆虫'],
  ['3', '锈病', 'Rust', '真菌'],
  ['4', '茎锈病', 'Stem Rust', '真菌'],
  ['5', '叶锈病', 'Leaf Rust', '真菌'],
  ['6', '条锈病', 'Stripe Rust', '真菌'],
  ['7', '黑粉病', 'Smuts', '真菌'],
  ['8', '根腐病', 'Common Root Rot', '真菌'],
  ['9', '叶斑病', 'Spot Blotch', '真菌'],
  ['10', '小麦爆发病', 'Wheat Blast', '真菌'],
  ['11', '赤霉病', 'Fusarium Head Blight', '真菌'],
  ['12', '壳针孢叶斑病', 'Septoria Leaf Blotch', '真菌'],
  ['13', '斑点叶斑病', 'Speckled Leaf Blotch', '真菌'],
  ['14', '褐斑病', 'Brown Spot', '真菌'],
  ['15', '白粉病', 'Powdery Mildew', '真菌'],
  ['16', '健康', 'Healthy', '正常']
];

// 添加表头
slide.addText('ID', {
  x: 1, y: 1.8, w: 0.8, h: 0.6,
  fontSize: 14, fontFace: FONT_HELVETICA_BOLD,
  color: '333333',
  fill: { color: 'E2E2E2' }
});
slide.addText('中文名称', {
  x: 1.8, y: 1.8, w: 2, h: 0.6,
  fontSize: 14, fontFace: FONT_HELVETICA_BOLD,
  color: '333333',
  fill: { color: 'E2E2E2' }
});
slide.addText('英文名称', {
  x: 3.8, y: 1.8, w: 2.5, h: 0.6,
  fontSize: 14, fontFace: FONT_HELVETICA_BOLD,
  color: '333333',
  fill: { color: 'E2E2E2' }
});
slide.addText('类型', {
  x: 6.3, y: 1.8, w: 1.7, h: 0.6,
  fontSize: 14, fontFace: FONT_HELVETICA_BOLD,
  color: '333333',
  fill: { color: 'E2E2E2' }
});

// 添加数据
let rowY = 2.4;
diseaseCategories.forEach(disease => {
  slide.addText(disease[0], {
    x: 1, y: rowY, w: 0.8, h: 0.5,
    fontSize: 14, fontFace: FONT_HELVETICA,
    color: '333333'
  });
  slide.addText(disease[1], {
    x: 1.8, y: rowY, w: 2, h: 0.5,
    fontSize: 14, fontFace: FONT_HELVETICA,
    color: '333333'
  });
  slide.addText(disease[2], {
    x: 3.8, y: rowY, w: 2.5, h: 0.5,
    fontSize: 14, fontFace: FONT_HELVETICA,
    color: '333333'
  });
  slide.addText(disease[3], {
    x: 6.3, y: rowY, w: 1.7, h: 0.5,
    fontSize: 14, fontFace: FONT_HELVETICA,
    color: '333333'
  });
  rowY += 0.5;
});

// 性能指标
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('性能指标', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});

const performanceMetrics = [
  ['YOLO 推理延迟', '≤150ms', '225ms (CPU)'],
  ['SSE 首事件延迟', '≤500ms', '0.01ms'],
  ['完整诊断延迟', '≤40s', '185.8ms (YOLO-only)'],
  ['Qwen 显存占用', '≤4GB', '~2.6GB (INT4)'],
  ['知识覆盖率', '≥95%', '100%']
];

// 添加表头
slide.addText('指标', {
  x: 1, y: 2, w: 3, h: 0.8,
  fontSize: 16, fontFace: FONT_HELVETICA_BOLD,
  color: '333333',
  fill: { color: 'E2E2E2' }
});
slide.addText('目标值', {
  x: 4, y: 2, w: 2, h: 0.8,
  fontSize: 16, fontFace: FONT_HELVETICA_BOLD,
  color: '333333',
  fill: { color: 'E2E2E2' }
});
slide.addText('实测值', {
  x: 6, y: 2, w: 2, h: 0.8,
  fontSize: 16, fontFace: FONT_HELVETICA_BOLD,
  color: '333333',
  fill: { color: 'E2E2E2' }
});

// 添加数据
let metricY = 2.8;
performanceMetrics.forEach(metric => {
  slide.addText(metric[0], {
    x: 1, y: metricY, w: 3, h: 0.8,
    fontSize: 16, fontFace: FONT_HELVETICA,
    color: '333333'
  });
  slide.addText(metric[1], {
    x: 4, y: metricY, w: 2, h: 0.8,
    fontSize: 16, fontFace: FONT_HELVETICA,
    color: '333333'
  });
  slide.addText(metric[2], {
    x: 6, y: metricY, w: 2, h: 0.8,
    fontSize: 16, fontFace: FONT_HELVETICA,
    color: '333333'
  });
  metricY += 0.8;
});

// 安全设计
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('安全设计', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});

const securityFeatures = [
  ['JWT 双令牌', 'Access 30min + Refresh 7days'],
  ['Token 黑名单', 'Redis Set + TTL 自动过期'],
  ['密码安全', 'bcrypt 哈希存储 + 72 字节截断'],
  ['密码重置', 'SHA-256 令牌哈希 + 1 小时有效期'],
  ['XSS 防护', 'html.escape 转义 + CSP 安全头 + 用户名正则验证'],
  ['开放重定向防护', '登录 redirect 参数验证'],
  ['速率限制', 'SlowAPI 频率限流'],
  ['并发限流', 'DiagnosisRateLimiter（≤3 并发）'],
  ['GPU 保护', '显存≥90% 返回 503'],
  ['CORS', '可配置白名单'],
  ['输入验证', 'Pydantic V2 Schema 校验'],
  ['账户锁定', '连续 5 次失败锁定 30 分钟'],
  ['Cookie 安全', 'httpOnly + secure + samesite=lax']
];

let secY = 2;
securityFeatures.forEach((feature, index) => {
  slide.addText(`${index + 1}. ${feature[0]}: ${feature[1]}`, {
    x: 1, y: secY, w: 8, h: 0.6,
    fontSize: 16, fontFace: FONT_HELVETICA,
    color: '333333'
  });
  secY += 0.6;
});

// 创新点
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('创新点', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});

slide.addText('• 多模态融合架构：首次将视觉检测、多模态理解和知识图谱有机结合\n• KAD-Former 融合策略：创新的知识感知扩散融合机制，提高诊断准确性\n• GraphRAG 知识增强：利用知识图谱进行检索增强生成，提供科学的防治建议\n• 实时流式响应：基于 SSE 的实时诊断进度推送，提升用户体验\n• INT4 量化优化：Qwen3-VL 模型的 INT4 量化，降低显存占用至 2.6GB\n• 完整安全体系：JWT 双令牌认证、XSS 防护、RBAC 权限控制等多重安全措施\n• 可扩展性设计：模块化架构，支持模型升级和功能扩展\n• 边缘部署支持：优化的模型和推理引擎，支持在边缘设备上部署', {
  x: 1, y: 2, w: 8, h: 5,
  fontSize: 16, fontFace: FONT_HELVETICA,
  color: '333333'
});

// 项目结构
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('项目结构', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});

slide.addText(`WheatAgent/
├── src/                           # 核心源码
│   ├── web/                       # Web 前后端
│   │   ├── frontend/              # Vue3 前端
│   │   │   ├── src/
│   │   │   │   ├── api/           # API 接口层
│   │   │   │   ├── components/    # 组件（诊断/知识/仪表盘）
│   │   │   │   ├── views/         # 页面视图
│   │   │   │   ├── router/        # Vue Router 路由
│   │   │   │   ├── stores/        # Pinia 状态管理
│   │   │   │   ├── utils/         # 工具函数
│   │   │   │   └── types/         # TypeScript 类型
│   │   └── backend/               # FastAPI 后端
│   │       └── app/
│   │           ├── api/v1/        # API 路由层
│   │           ├── services/      # 业务服务层
│   │           ├── core/          # 核心组件层
│   │           ├── models/        # 数据模型层
│   │           ├── schemas/       # Pydantic 数据校验
│   │           └── utils/         # 工具函数
│   ├── vision/                    # 视觉引擎（YOLOv8增强）
│   ├── perception/                # 感知模块（YOLO/Qwen-VL）
│   ├── fusion/                    # 融合引擎（KAD-Former/GraphRAG）
│   ├── graph/                     # 图引擎（GNN/知识图谱）
│   ├── text/                      # 文本引擎（遗留，已被Qwen3-VL替代）
│   └── cognition/                 # 认知引擎
├── configs/                       # 训练与模型配置
├── scripts/                       # 工具脚本
├── deploy/                        # 部署配置
├── docs/                          # 项目文档
├── data/                          # 数据目录
└── runs/                          # 训练输出目录`, {
  x: 1, y: 2, w: 8, h: 4,
  fontSize: 14, fontFace: FONT_HELVETICA,
  color: '333333'
});

// 总结与展望
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('总结与展望', {
  x: 0, y: 0.5, w: '100%', h: 1,
  fontSize: 28, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});

slide.addText('项目总结：', {
  x: 1, y: 2, w: 2, h: 1,
  fontSize: 20, fontFace: FONT_HELVETICA_BOLD,
  color: '366092'
});
slide.addText('成功实现了一个基于多模态融合的小麦病害诊断系统，整合了计算机视觉、大语言模型和知识图谱技术，实现了从"感知"到"认知"再到"行动"的完整闭环。系统支持17类小麦病害识别，提供实时诊断和科学的防治建议。', {
  x: 1, y: 3, w: 8, h: 2,
  fontSize: 16, fontFace: FONT_HELVETICA,
  color: '333333'
});

slide.addText('未来展望：', {
  x: 1, y: 5.5, w: 2, h: 1,
  fontSize: 20, fontFace: FONT_HELVETICA_BOLD,
  color: '366092'
});
slide.addText('• 扩展支持更多作物类型和病害种类\n• 优化模型性能，进一步降低推理延迟\n• 增加移动端应用，支持离线诊断\n• 引入联邦学习，保护用户数据隐私\n• 与农业物联网设备集成，实现智能监测\n• 开发专家系统，提供更精准的农业决策支持', {
  x: 1, y: 6.3, w: 8, h: 3,
  fontSize: 16, fontFace: FONT_HELVETICA,
  color: '333333'
});

// 致谢
slide = pptx.addSlide({ layout: 'LAYOUT_WIDE' });
slide.addText('致谢', {
  x: 0, y: 2, w: '100%', h: 1.5,
  fontSize: 32, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '366092'
});
slide.addText('感谢导师的悉心指导\n感谢团队成员的协作\n感谢所有支持本项目的人', {
  x: 0, y: 4, w: '100%', h: 2,
  fontSize: 20, fontFace: FONT_HELVETICA, align: ALIGN_CENTER,
  color: '333333'
});
slide.addText('谢谢聆听！', {
  x: 0, y: 6.5, w: '100%', h: 1,
  fontSize: 24, fontFace: FONT_HELVETICA_BOLD, align: ALIGN_CENTER,
  color: '548235'
});

// 生成PPT文件
pptx.writeFile({ fileName: 'wheat_disease_diagnosis_ppt.pptx' });
console.log('PPT generated successfully!');
