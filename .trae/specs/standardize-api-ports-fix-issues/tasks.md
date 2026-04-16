# Tasks

## Phase 1: 接口标准化

- [x] Task 1.1: 创建 API 响应格式标准化模块
  - [x] 创建 `app/core/response.py` 统一响应格式
  - [x] 定义 `success_response()` 和 `error_response()` 函数
  - [x] 添加响应中间件自动包装

- [x] Task 1.2: 完善错误码体系
  - [x] 创建 `app/core/error_codes.py` 错误码定义
  - [x] 定义系统错误码 (SYS_XXX)
  - [x] 定义数据库错误码 (DB_XXX)
  - [x] 定义 AI 服务错误码 (AI_XXX)
  - [x] 更新现有错误码 (AUTH_XXX, DIAG_XXX, USER_XXX)

- [x] Task 1.3: 更新 API 文档
  - [x] 修正 API_REFERENCE.md 中的路径错误
  - [x] 添加完整的错误码说明
  - [x] 添加请求/响应示例

## Phase 2: 端口标准化

- [x] Task 2.1: 创建端口分配文档
  - [x] 创建 `docs/PORT_ALLOCATION.md`
  - [x] 定义各服务端口范围
  - [x] 添加端口冲突解决方案

- [ ] Task 2.2: 更新配置文件
  - [ ] 更新 `app/core/config.py` 端口配置
  - [ ] 更新 docker-compose.yml 端口映射
  - [ ] 更新前端 API 配置

## Phase 3: 问题修复

- [x] Task 3.1: 修复 P001 - 用户注册接口 500 错误
  - [x] 分析注册流程代码
  - [x] 检查 bcrypt 密码哈希
  - [x] 检查数据库约束
  - [x] 添加详细错误日志
  - [x] 编写单元测试验证

- [x] Task 3.2: 修复 P002 - 重复注册错误处理
  - [x] 添加邮箱唯一性预检查
  - [x] 添加用户名唯一性预检查
  - [x] 返回正确的 409 状态码
  - [x] 编写单元测试验证

- [x] Task 3.3: 修复 P003 - 后端服务连接不稳定
  - [x] 优化数据库连接池配置
  - [x] 添加请求重试中间件
  - [x] 优化 uvicorn 配置
  - [x] 添加健康检查端点
  - [x] 编写并发测试验证

- [x] Task 3.4: 解决 P004 - 诊断服务集成
  - [x] 创建诊断服务 Mock
  - [x] 或配置真实 AI 服务
  - [x] 编写集成测试

- [x] Task 3.5: 解决 P005 - 前端服务配置
  - [x] 更新前端启动文档
  - [x] 配置前端测试环境

- [x] Task 3.6: 改进 P006 - 测试覆盖率
  - [x] 添加测试 Fixture
  - [x] 添加服务健康检查
  - [x] 配置 pytest-cov

## Phase 4: 验证与文档

- [x] Task 4.1: 运行完整测试
  - [x] 运行单元测试
  - [x] 运行集成测试
  - [x] 生成测试报告

- [x] Task 4.2: 更新文档
  - [x] 更新 API_REFERENCE.md
  - [x] 创建 PORT_ALLOCATION.md
  - [x] 创建问题解决报告

# Task Dependencies
- [Task 1.1] 和 [Task 2.1] 可并行
- [Task 1.2] depends on [Task 1.1]
- [Task 1.3] depends on [Task 1.2]
- [Task 2.2] depends on [Task 2.1]
- [Task 3.1], [Task 3.2], [Task 3.3] 可并行
- [Task 3.4], [Task 3.5], [Task 3.6] 可并行
- [Task 4.1] depends on [Task 3.1, Task 3.2, Task 3.3]
- [Task 4.2] depends on [Task 4.1]
