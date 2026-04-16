# Tasks

- [x] Task 1: 优化 Vite 构建配置 - 代码分割
  - [x] 1.1: 配置 manualChunks 分离第三方库
  - [x] 1.2: 配置 Element Plus 单独 chunk
  - [x] 1.3: 配置 ECharts 单独 chunk
  - [x] 1.4: 配置 Vue 生态库单独 chunk

- [x] Task 2: 实现路由懒加载
  - [x] 2.1: 修改 router/index.ts 使用动态导入
  - [x] 2.2: 添加路由加载状态组件
  - [x] 2.3: 配置路由预加载策略

- [ ] Task 3: 优化 Element Plus 按需导入
  - [ ] 3.1: 检查当前导入方式
  - [ ] 3.2: 配置 unplugin-vue-components 自动导入
  - [ ] 3.3: 移除全局全量导入

- [x] Task 4: 优化 ECharts 按需加载
  - [x] 4.1: 检查 DiseaseChart.vue 的 ECharts 导入
  - [x] 4.2: 实现按需导入 ECharts 组件
  - [x] 4.3: 封装 ECharts 初始化逻辑

- [ ] Task 5: 添加图片懒加载
  - [ ] 5.1: 创建图片懒加载指令
  - [ ] 5.2: 在图片组件中应用懒加载

- [x] Task 6: 验证优化效果
  - [x] 6.1: 运行构建检查 chunk 大小
  - [x] 6.2: 运行测试确保功能正常
  - [x] 6.3: 对比优化前后构建产物大小

# Task Dependencies
- [Task 2] 可与 [Task 1] 并行执行
- [Task 3] 可与 [Task 4] 并行执行
- [Task 6] 依赖 [Task 1] - [Task 5] 全部完成
