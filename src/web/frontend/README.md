# WheatAgent 前端

基于 Vue 3 + TypeScript + Vite 构建的小麦病害诊断系统前端应用。

## 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript 超集
- **Vite** - 下一代前端构建工具
- **Element Plus** - Vue 3 组件库
- **Pinia** - Vue 状态管理
- **Vue Router** - 路由管理
- **Axios** - HTTP 客户端
- **ECharts** - 数据可视化

## 环境要求

- Node.js >= 18.0.0
- npm >= 9.0.0 或 pnpm >= 8.0.0

## 快速开始

### 安装依赖

```bash
# 使用 npm
npm install

# 或使用 pnpm（推荐）
pnpm install
```

### 开发模式

```bash
# 启动开发服务器
npm run dev

# 或
pnpm dev
```

开发服务器默认运行在 `http://localhost:5173`

### 生产构建

```bash
# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

## 项目结构

```
frontend/
├── src/
│   ├── components/     # 可复用组件
│   ├── views/          # 页面视图
│   ├── router/         # 路由配置
│   ├── stores/         # Pinia 状态管理
│   ├── api/            # API 接口
│   ├── assets/         # 静态资源
│   └── main.ts         # 入口文件
├── public/             # 公共静态资源
├── index.html          # HTML 模板
├── vite.config.ts      # Vite 配置
└── tsconfig.json       # TypeScript 配置
```

## 可用脚本

| 命令 | 说明 |
|------|------|
| `npm run dev` | 启动开发服务器 |
| `npm run build` | 构建生产版本 |
| `npm run preview` | 预览生产构建 |
| `npm run test` | 运行测试（监听模式） |
| `npm run test:run` | 运行测试（单次） |
| `npm run test:coverage` | 运行测试并生成覆盖率报告 |

## 配置后端 API

前端默认连接到 `http://localhost:8000` 的后端服务。如需修改，请编辑 `src/api/config.ts` 或设置环境变量：

```env
VITE_API_BASE_URL=http://your-backend-url:port
```

## 测试

项目使用 Vitest 进行单元测试：

```bash
# 运行测试
npm run test

# 运行测试并生成覆盖率报告
npm run test:coverage
```

## 相关文档

- [Vue 3 文档](https://vuejs.org/)
- [Vite 文档](https://vitejs.dev/)
- [Element Plus 文档](https://element-plus.org/)
- [TypeScript 指南](https://www.typescriptlang.org/docs/)
