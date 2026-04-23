const PptxGenJS = require('pptxgenjs');

// 创建PPT实例
const pptx = new PptxGenJS();

// 设置默认字体
pptx.layout = 'LAYOUT_WIDE';
pptx.title = '基于多模态融合的小麦病害诊断系统';
pptx.author = '毕业设计';

// 主题颜色 - 绿色为主色调
const THEME = {
  PRIMARY: '4A7C59',     // 主色-深绿
  SECONDARY: '66BB6A',   // 辅助色-浅绿
  ACCENT: '2E7D32',      // 强调色-墨绿
  LIGHT: 'A5D6A7',       // 浅色-淡绿
  TEXT: '333333',        // 文本色
  WHITE: 'FFFFFF'
};

// 1. 封面幻灯片
let slide = pptx.addSlide();
// 添加背景形状
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: '100%', fill: { type: 'gradient', color: [{ color: THEME.PRIMARY }, { color: THEME.ACCENT }] } });
// 标题
slide.addText('基于多模态融合的小麦病害诊断系统', {
  x: 0.5, y: 2, w: '100%', h: 1.5,
  fontSize: 42, fontFace: 'Microsoft YaHei', align: 'center',
  bold: true, color: THEME.WHITE
});
// 副标题
slide.addText('Intelligent Wheat Disease Diagnosis System based on Multimodal Fusion', {
  x: 0.5, y: 3.8, w: '100%', h: 0.8,
  fontSize: 22, fontFace: 'Arial', align: 'center',
  color: THEME.LIGHT
});
// 毕业设计信息
slide.addText('毕业设计答辩', {
  x: 0.5, y: 5.2, w: '100%', h: 1,
  fontSize: 28, fontFace: 'Microsoft YaHei', align: 'center',
  color: THEME.WHITE
});
// 作者和日期
slide.addText('作者：毕业设计团队\n指导老师：\n日期：2026年', {
  x: 0.5, y: 6.5, w: '100%', h: 1.5,
  fontSize: 18, fontFace: 'Microsoft YaHei', align: 'center',
  color: THEME.LIGHT
});

// 2. 目录幻灯片
slide = pptx.addSlide();
// 添加装饰条
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: 0.5, fill: { type: 'solid', color: THEME.PRIMARY } });
// 标题
slide.addText('目录', {
  x: 0.5, y: 0.8, w: '100%', h: 0.8,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'left',
  bold: true, color: THEME.PRIMARY
});
// 目录内容
slide.addText('01  项目背景与研究意义\n02  技术架构设计\n03  关键实现过程\n04  系统功能展示\n05  测试与性能分析\n06  创新点与特色\n07  总结与展望\n08  致谢', {
  x: 1, y: 2, w: '80%', h: 5,
  fontSize: 20, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});

// 3. 项目背景与研究意义
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: 0.5, fill: { type: 'solid', color: THEME.PRIMARY } });
slide.addText('01  项目背景与研究意义', {
  x: 0.5, y: 0.8, w: '100%', h: 0.8,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'left',
  bold: true, color: THEME.PRIMARY
});
// 背景问题
slide.addText('项目背景', {
  x: 1, y: 2, w: 3, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('• 小麦是中国第一大粮食作物\n• 传统病害诊断依赖专家经验\n• 农技人员不足，诊断效率低\n• 主观性强，误诊率高', {
  x: 1, y: 2.7, w: 4.5, h: 2.5,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});
// 研究意义
slide.addText('研究意义', {
  x: 5.5, y: 2, w: 3, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('• 提高诊断效率和准确性\n• 降低对专家经验的依赖\n• 为农民提供便捷服务\n• 助力智慧农业发展', {
  x: 5.5, y: 2.7, w: 4, h: 2.5,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});

// 4. 技术架构设计
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: 0.5, fill: { type: 'solid', color: THEME.PRIMARY } });
slide.addText('02  技术架构设计', {
  x: 0.5, y: 0.8, w: '100%', h: 0.8,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'left',
  bold: true, color: THEME.PRIMARY
});
// 四层架构
slide.addText('四层分离架构', {
  x: 1, y: 2, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('交互层：Vue3 + TypeScript + Element Plus\n感知层：YOLOv8s + Qwen3-VL\n认知层：Neo4j知识图谱 + KAD-Former融合\n基础设施：JWT认证 + SSE推送 + Redis缓存', {
  x: 1, y: 2.8, w: 9, h: 2,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});
// 技术栈
slide.addText('核心技术栈', {
  x: 1, y: 5, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('Python / FastAPI / Vue3 / YOLOv8 / Qwen / Neo4j', {
  x: 1, y: 5.7, w: 9, h: 0.8,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});

// 5. 关键实现过程 - 视觉感知
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: 0.5, fill: { type: 'solid', color: THEME.PRIMARY } });
slide.addText('03  关键实现过程', {
  x: 0.5, y: 0.8, w: '100%', h: 0.8,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'left',
  bold: true, color: THEME.PRIMARY
});
// 视觉感知模块
slide.addText('视觉感知模块', {
  x: 1, y: 2, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('• 基于YOLOv8s的高精度目标检测\n• 支持17类小麦病害和虫害识别\n• FP16半精度推理，提升速度\n• LRU缓存机制，优化重复查询', {
  x: 1, y: 2.8, w: 9, h: 2,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});

// 6. 关键实现过程 - 多模态融合
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: 0.5, fill: { type: 'solid', color: THEME.PRIMARY } });
slide.addText('03  关键实现过程（续）', {
  x: 0.5, y: 0.8, w: '100%', h: 0.8,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'left',
  bold: true, color: THEME.PRIMARY
});
// 多模态融合
slide.addText('多模态融合机制', {
  x: 1, y: 2, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('• KAD-Former知识感知扩散融合\n• 视觉主导 + 文本辅助 + 知识仲裁\n• GraphRAG知识检索增强生成\n• 置信度校准与ROI可视化', {
  x: 1, y: 2.8, w: 9, h: 2,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});

// 7. 系统功能展示
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: 0.5, fill: { type: 'solid', color: THEME.PRIMARY } });
slide.addText('04  系统功能展示', {
  x: 0.5, y: 0.8, w: '100%', h: 0.8,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'left',
  bold: true, color: THEME.PRIMARY
});
// 核心功能
slide.addText('核心功能', {
  x: 1, y: 2, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('• 图像上传与病害检测\n• 实时流式诊断进度\n• 详细诊断报告与置信度\n• 科学防治建议\n• 历史诊断记录管理', {
  x: 1, y: 2.8, w: 9, h: 2,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});
// 用户角色
slide.addText('用户角色体系', {
  x: 1, y: 5, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('农民用户 / 农技人员 / 系统管理员', {
  x: 1, y: 5.7, w: 9, h: 0.8,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});

// 8. 测试与性能分析
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: 0.5, fill: { type: 'solid', color: THEME.PRIMARY } });
slide.addText('05  测试与性能分析', {
  x: 0.5, y: 0.8, w: '100%', h: 0.8,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'left',
  bold: true, color: THEME.PRIMARY
});
// 性能指标
slide.addText('关键性能指标', {
  x: 1, y: 2, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('• YOLO推理延迟：225ms (CPU)\n• SSE首事件延迟：0.01ms\n• Qwen显存占用：~2.6GB (INT4)\n• 知识覆盖率：100%\n• 测试覆盖：1448+用例，99%+通过率', {
  x: 1, y: 2.8, w: 9, h: 2.5,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});

// 9. 创新点与特色
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: 0.5, fill: { type: 'solid', color: THEME.PRIMARY } });
slide.addText('06  创新点与特色', {
  x: 0.5, y: 0.8, w: '100%', h: 0.8,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'left',
  bold: true, color: THEME.PRIMARY
});
// 创新点
slide.addText('主要创新点', {
  x: 1, y: 2, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('• KAD-Former多模态融合策略\n• GraphRAG知识增强生成\n• SSE实时流式交互\n• INT4量化显存优化\n• 完整安全防护体系', {
  x: 1, y: 2.8, w: 9, h: 2.5,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});

// 10. 总结与展望
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: 0.5, fill: { type: 'solid', color: THEME.PRIMARY } });
slide.addText('07  总结与展望', {
  x: 0.5, y: 0.8, w: '100%', h: 0.8,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'left',
  bold: true, color: THEME.PRIMARY
});
// 总结
slide.addText('项目总结', {
  x: 1, y: 2, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('• 成功构建多模态小麦病害诊断系统\n• 实现从感知到认知的完整闭环\n• 提供高效、准确、便捷的诊断服务', {
  x: 1, y: 2.8, w: 9, h: 1.5,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});
// 展望
slide.addText('未来展望', {
  x: 1, y: 4.8, w: 8, h: 0.6,
  fontSize: 22, fontFace: 'Microsoft YaHei',
  bold: true, color: THEME.ACCENT
});
slide.addText('• 扩展更多作物类型\n• 优化模型性能\n• 支持边缘设备部署\n• 构建农业智能生态', {
  x: 1, y: 5.6, w: 9, h: 1.5,
  fontSize: 16, fontFace: 'Microsoft YaHei',
  color: THEME.TEXT
});

// 11. 致谢
slide = pptx.addSlide();
slide.addShape(pptx.ShapeType.rect, { x: 0, y: 0, w: '100%', h: '100%', fill: { type: 'gradient', color: [{ color: THEME.PRIMARY }, { color: THEME.ACCENT }] } });
slide.addText('致谢', {
  x: 0.5, y: 2.5, w: '100%', h: 1.5,
  fontSize: 48, fontFace: 'Microsoft YaHei', align: 'center',
  bold: true, color: THEME.WHITE
});
slide.addText('感谢导师的悉心指导\n感谢团队成员的协作付出\n感谢所有支持本项目的人', {
  x: 0.5, y: 4.5, w: '100%', h: 2,
  fontSize: 24, fontFace: 'Microsoft YaHei', align: 'center',
  color: THEME.LIGHT
});
slide.addText('谢谢聆听！', {
  x: 0.5, y: 6.8, w: '100%', h: 1,
  fontSize: 32, fontFace: 'Microsoft YaHei', align: 'center',
  color: THEME.WHITE
});

// 生成PPT文件
pptx.writeFile({ fileName: '/workspace/ppt/graduation_presentation.pptx' })
  .then(() => {
    console.log('毕业设计PPT生成成功！');
    console.log('文件路径：/workspace/ppt/graduation_presentation.pptx');
  })
  .catch(err => {
    console.error('PPT生成失败：', err);
  });
