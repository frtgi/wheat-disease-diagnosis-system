# Web 端开发检查清单

## 前端开发检查

- [ ] Vue3 项目框架搭建完成（Vite + TypeScript）
- [ ] Element Plus UI 组件库安装和配置完成
- [ ] Vue Router 路由配置完成（7 个页面路由）
- [ ] Pinia 状态管理配置完成
- [ ] Axios API 拦截器配置完成（JWT Token 自动携带）
- [ ] ImageUploader 组件实现（支持拖拽和点击上传）
- [ ] DiagnosisResult 组件实现（展示病害名称、置信度、防治建议）
- [ ] Dashboard 页面实现（ECharts 图表展示）
- [ ] 病害诊断页面实现（`/diagnosis`）
- [ ] 诊断记录页面实现（`/records`）
- [ ] 农业知识库页面实现（`/knowledge`）
- [ ] 用户中心页面实现（`/user`）
- [ ] 登录/注册页面实现
- [ ] 前端响应式布局适配（PC 端和移动端）

## 后端开发检查

- [ ] FastAPI 项目框架搭建完成
- [ ] 数据库连接配置完成（MySQL 8.0+）
- [ ] Redis 缓存配置完成（7.2+）
- [ ] CORS 配置完成（允许前端跨域访问）
- [ ] JWT 认证配置完成（24 小时有效期）
- [ ] User 模型创建完成（包含角色字段）
- [ ] Disease 模型创建完成（包含症状、防治方法）
- [ ] DiagnosisRecord 模型创建完成（包含外键关联）
- [ ] KnowledgeGraph 模型创建完成（包含实体、关系）
- [ ] 用户注册接口实现（POST /api/v1/user/register）
- [ ] 用户登录接口实现（POST /api/v1/user/login）
- [ ] 用户信息接口实现（GET/PUT /api/v1/user/me）
- [ ] 图像诊断接口实现（POST /api/v1/diagnosis/image）
- [ ] 文本诊断接口实现（POST /api/v1/diagnosis/text）
- [ ] 诊断记录查询接口实现（GET /api/v1/diagnosis/records）
- [ ] 诊断详情接口实现（GET /api/v1/diagnosis/{id}）
- [ ] 诊断报告导出接口实现（GET /api/v1/diagnosis/{id}/export）
- [ ] 病害列表接口实现（GET /api/v1/knowledge/diseases）
- [ ] 病害详情接口实现（GET /api/v1/knowledge/diseases/{id}）
- [ ] 知识搜索接口实现（GET /api/v1/knowledge/search）
- [ ] 统计概览接口实现（GET /api/v1/stats/overview）
- [ ] 诊断趋势接口实现（GET /api/v1/stats/trends）
- [ ] 病害分布接口实现（GET /api/v1/stats/diseases）

## AI 集成检查

- [ ] YOLOv8 视觉引擎集成完成
- [ ] Qwen3-VL 认知引擎集成完成
- [ ] 多模态融合引擎集成完成
- [ ] 图像预处理流程实现（缩放、归一化）
- [ ] 诊断结果解析和格式化实现
- [ ] 错误处理和异常捕获实现
- [ ] 诊断超时处理实现（> 30 秒超时）

## 数据库检查

- [ ] MySQL 数据库创建完成
- [ ] users 表创建完成（包含索引）
- [ ] diseases 表创建完成（包含索引）
- [ ] diagnosis_records 表创建完成（包含索引和外键）
- [ ] knowledge_graph 表创建完成（包含索引）
- [ ] 数据库迁移脚本创建完成
- [ ] 病害知识种子数据导入完成（至少 10 种常见病害）
- [ ] Redis 缓存键设计实现
- [ ] 缓存失效策略实现

## 对象存储检查

- [ ] MinIO 服务配置完成
- [ ] 图像上传到 MinIO 实现
- [ ] 图像 URL 生成实现
- [ ] 图像删除功能实现
- [ ] 图像访问权限控制实现

## 异步任务检查

- [ ] Celery 配置完成（Redis Broker）
- [ ] 异步诊断任务实现
- [ ] 任务状态查询接口实现
- [ ] 任务结果回调实现
- [ ] 任务超时处理实现

## 安全检查

- [ ] JWT Token 认证实现（Header 携带）
- [ ] 密码哈希实现（bcrypt）
- [ ] API 限流实现（按接口类型）
- [ ] SQL 注入防护实现（参数化查询）
- [ ] XSS 防护实现（输入过滤）
- [ ] CORS 配置正确（仅允许信任域名）
- [ ] HTTPS 配置（生产环境）

## 性能检查

- [ ] 前端路由懒加载实现
- [ ] 前端组件懒加载实现
- [ ] 前端图片压缩实现
- [ ] 后端 Redis 缓存实现（诊断结果缓存）
- [ ] 数据库索引优化（查询字段）
- [ ] API 响应时间 < 500ms（不含 AI 推理）
- [ ] 诊断响应时间 < 5s（包含 AI 推理）
- [ ] 页面加载时间 < 2s

## 测试检查

- [ ] 后端单元测试编写完成（pytest）
- [ ] 后端集成测试编写完成
- [ ] 前端组件测试编写完成（Vitest）
- [ ] 端到端测试编写完成（Playwright/Cypress）
- [ ] 性能测试完成（负载测试、压力测试）
- [ ] 测试覆盖率 > 80%

## 部署检查

- [ ] 前端 Dockerfile 编写完成
- [ ] 后端 Dockerfile 编写完成
- [ ] Docker Compose 配置编写完成
- [ ] Kubernetes 部署配置编写完成
- [ ] 环境变量配置完成
- [ ] 密钥管理配置完成
- [ ] 日志记录配置完成
- [ ] 监控告警配置完成

## 文档检查

- [ ] API 文档生成（FastAPI 自动文档）
- [ ] 前端组件文档编写
- [ ] 部署文档编写
- [ ] 用户手册编写
- [ ] 开发文档编写

## 性能指标验证

- [ ] 页面加载时间 < 2s ✅
- [ ] API 响应时间 < 500ms ✅
- [ ] 诊断响应时间 < 5s ✅
- [ ] 并发用户数 > 1000 ✅
- [ ] 系统可用性 > 99.9% ✅

## 功能验收

- [ ] 用户可以成功注册和登录
- [ ] 用户可以上传小麦病害图像
- [ ] 系统可以返回准确的诊断结果（置信度 > 0.8）
- [ ] 系统可以保存诊断记录
- [ ] 用户可以查看历史诊断记录
- [ ] 用户可以浏览农业知识库
- [ ] 用户可以查看 Dashboard 统计图表
- [ ] 系统支持 RBAC 权限控制（不同角色不同权限）
