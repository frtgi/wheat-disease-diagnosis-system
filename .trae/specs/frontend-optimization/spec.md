# 前端优化 Spec

## Why
前端构建成功但存在性能优化空间：部分 JS chunk 超过 500 kB（最大 1.1 MB），影响页面加载速度。需要优化代码分割、懒加载和资源利用率。

## What Changes
- 优化 Vite 构建配置，实现更细粒度的代码分割
- 实现路由级懒加载
- 优化 Element Plus 组件按需导入
- 添加图片懒加载
- 优化 ECharts 按需加载

## Impact
- Affected specs: 前端性能、用户体验
- Affected code: vite.config.ts, router/index.ts, main.ts, 组件文件

## ADDED Requirements

### Requirement: 代码分割优化
系统 SHALL 将大型 JS bundle 分割为更小的 chunk，每个 chunk 不超过 500 kB。

#### Scenario: 构建产物检查
- **WHEN** 执行 `npm run build`
- **THEN** 所有 JS chunk 文件大小不超过 500 kB（除第三方库合并 chunk 外）

### Requirement: 路由懒加载
系统 SHALL 对所有路由组件实现懒加载，减少首屏加载时间。

#### Scenario: 首屏加载
- **WHEN** 用户首次访问应用
- **THEN** 只加载首屏所需的代码，其他路由组件按需加载

### Requirement: 第三方库按需加载
系统 SHALL 对 Element Plus、ECharts 等大型第三方库实现按需加载。

#### Scenario: 组件导入
- **WHEN** 应用加载时
- **THEN** 只导入实际使用的组件和功能，而非整个库

## MODIFIED Requirements

### Requirement: 构建配置优化
Vite 配置 SHALL 包含 manualChunks 配置，将第三方库分离为独立 chunk。

## REMOVED Requirements
无
