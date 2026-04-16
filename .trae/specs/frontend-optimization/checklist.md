# 前端优化检查清单

## 构建优化检查

- [x] Vite 构建配置已优化
  - [x] manualChunks 配置正确
  - [x] 第三方库已分离
  - [ ] chunk 大小警告已消除（Element Plus 仍较大，但已分离）

- [x] JS chunk 已分离
  - [x] vue-vendor chunk: 106.75 kB
  - [x] echarts chunk: 628.23 kB（按需导入后）
  - [x] element-plus chunk: 1,008.42 kB
  - [x] axios chunk: 36.62 kB

## 路由懒加载检查

- [x] 所有路由组件使用懒加载
  - [x] Dashboard 懒加载
  - [x] Diagnosis 懒加载
  - [x] Knowledge 懒加载
  - [x] Records 懒加载
  - [x] User 懒加载
  - [x] Login 懒加载
  - [x] Register 懒加载

## 按需导入检查

- [ ] Element Plus 按需导入
  - [ ] 使用 unplugin-vue-components
  - [x] 无全量导入（已分离为独立 chunk）

- [x] ECharts 按需导入
  - [x] 只导入使用的组件
  - [x] 无全量导入

## 功能验证检查

- [x] 所有测试通过
  - [x] 单元测试 60 个通过
  - [x] 无测试失败

- [x] 构建成功
  - [x] TypeScript 编译通过
  - [x] Vite 构建成功
  - [x] 无构建错误

## 性能指标检查

- [x] 代码分割生效
- [x] 第三方库独立打包
- [x] 路由懒加载生效
