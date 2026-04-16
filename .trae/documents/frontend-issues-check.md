# 前端问题检查报告

## 概述

对 `src/web/frontend` 目录下的前端代码进行了全面检查，发现了以下几类问题：

---

## 1. 依赖配置问题

### 1.1 缺少必要依赖
**文件**: [package.json](file:///D:/Project/wheatagent/src/web/frontend/package.json)

| 问题 | 描述 |
|------|------|
| 缺少 `@element-plus/icons-vue` | [main.ts:10](file:///D:/Project/wheatagent/src/web/frontend/src/main.ts#L10) 和多个组件中使用了该依赖，但 `package.json` 中未声明 |
| 缺少 `terser` | [vite.config.ts:35](file:///D:/Project/wheatagent/src/web/frontend/vite.config.ts#L35) 配置了 `minify: 'terser'`，但未安装 terser 依赖 |

**修复方案**:
```json
{
  "devDependencies": {
    "@element-plus/icons-vue": "^2.3.1",
    "terser": "^5.31.0"
  }
}
```

---

## 2. API 导入问题

### 2.1 导入方式不匹配
**文件**: 
- [src/api/user.ts:5](file:///D:/Project/wheatagent/src/web/frontend/src/api/user.ts#L5)
- [src/api/diagnosis.ts:5](file:///D:/Project/wheatagent/src/web/frontend/src/api/diagnosis.ts#L5)
- [src/api/knowledge.ts:5](file:///D:/Project/wheatagent/src/web/frontend/src/api/knowledge.ts#L5)

**问题**: API 文件中使用 `import { http } from '@/utils/request'`，但 [request.ts:225](file:///D:/Project/wheatagent/src/web/frontend/src/utils/request.ts#L225) 导出的是 `export const http = {...}`，需要确认导入导出一致性。

**修复方案**: 确认 `request.ts` 中正确导出 `http` 对象。

---

## 3. 路由与代理配置问题

### 3.1 API 代理路径配置
**文件**: [vite.config.ts:20-26](file:///D:/Project/wheatagent/src/web/frontend/vite.config.ts#L20-L26)

**问题**: 
- 代理配置将 `/api` 重写为空 (`rewrite: (path) => path.replace(/^\/api/, '')`)
- 但 [request.ts:12](file:///D:/Project/wheatagent/src/web/frontend/src/utils/request.ts#L12) 中 baseURL 是 `http://localhost:8000/api/v1`
- 这会导致实际请求路径不正确

**修复方案**:
```typescript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
    // 移除 rewrite，保留 /api 前缀
  }
}
```

---

## 4. 组件逻辑问题

### 4.1 User.vue 硬编码数据
**文件**: [src/views/User.vue:95-109](file:///D:/Project/wheatagent/src/web/frontend/src/views/User.vue#L95-L109)

**问题**: 用户信息和统计数据是硬编码的，没有从 API 获取实际数据。

**修复方案**: 添加 API 调用获取用户信息和使用统计。

### 4.2 Records.vue 分页逻辑错误
**文件**: [src/views/Records.vue:102-114](file:///D:/Project/wheatagent/src/web/frontend/src/views/Records.vue#L102-L114)

**问题**: 
- `total` 计算使用的是当前页数据长度，而非总记录数
- 后端 API 没有返回 total 字段

**修复方案**: 修改 API 返回分页信息，或调整前端分页逻辑。

### 4.3 Knowledge.vue 重复筛选
**文件**: [src/views/Knowledge.vue:97-154](file:///D:/Project/wheatagent/src/web/frontend/src/views/Knowledge.vue#L97-L154)

**问题**: 
- 同时在前端 (`filteredDiseases`) 和后端 (`searchDiseases`) 进行筛选
- 可能导致数据不一致

**修复方案**: 统一使用后端筛选或前端筛选。

---

## 5. 测试文件问题

### 5.1 测试组件与实际不匹配
**文件**: [tests/Diagnosis.test.ts](file:///D:/Project/wheatagent/src/web/frontend/tests/Diagnosis.test.ts)

**问题**: 
- 测试模拟的是 `ImageUploader` 和 `DiagnosisResult` 组件
- 但实际 [Diagnosis.vue](file:///D:/Project/wheatagent/src/web/frontend/src/views/Diagnosis.vue) 使用的是 `MultiModalInput` 和 `FusionResult` 组件

**修复方案**: 更新测试文件以匹配实际组件结构。

---

## 6. 安全问题

### 6.1 退出登录清理不完整
**文件**: [src/views/User.vue:130-144](file:///D:/Project/wheatagent/src/web/frontend/src/views/User.vue#L130-L144)

**问题**: 退出登录时只清除了 `token`，没有清除 `refresh_token` 和 `user` 信息。

**修复方案**:
```typescript
localStorage.removeItem('token')
localStorage.removeItem('refresh_token')
localStorage.removeItem('user')
```

### 6.2 缺少 CSRF 保护
**问题**: HTTP 请求没有实现 CSRF Token 保护机制。

---

## 7. 代码质量问题

### 7.1 循环依赖风险
**文件**: [src/utils/request.ts:8](file:///D:/Project/wheatagent/src/web/frontend/src/utils/request.ts#L8)

**问题**: 导入了 `router`，可能导致循环依赖。

**修复方案**: 使用动态导入或事件总线替代。

### 7.2 Dashboard.vue 统计计算问题
**文件**: [src/views/Dashboard.vue:89-148](file:///D:/Project/wheatagent/src/web/frontend/src/views/Dashboard.vue#L89-L148)

**问题**: 
- 用户数是模拟计算 (`Math.floor(records.length / 3)`)
- 准确率计算使用置信度平均值，语义不准确

---

## 8. 性能问题

### 8.1 ECharts 实例销毁
**文件**: [src/components/dashboard/DiseaseChart.vue:333-346](file:///D:/Project/wheatagent/src/web/frontend/src/components/dashboard/DiseaseChart.vue#L333-L346)

**问题**: 虽然有销毁逻辑，但 `ResizeObserver` 未在 `onBeforeUnmount` 中断开连接。

**修复方案**:
```typescript
onBeforeUnmount(() => {
  if (resizeObserver.value) {
    resizeObserver.value.disconnect()
  }
  // ... 其他清理
})
```

### 8.2 缺少图片懒加载
**问题**: 图片组件没有实现懒加载，可能影响页面加载性能。

---

## 9. 类型定义问题

### 9.1 类型定义重复
**文件**: 
- [src/types/index.ts](file:///D:/Project/wheatagent/src/web/frontend/src/types/index.ts)
- [src/api/diagnosis.ts:13-22](file:///D:/Project/wheatagent/src/web/frontend/src/api/diagnosis.ts#L13-L22)
- [src/api/user.ts:13-23](file:///D:/Project/wheatagent/src/web/frontend/src/api/user.ts#L13-L23)

**问题**: `DiagnosisResult`、`UserInfo` 等类型在多处重复定义。

**修复方案**: 统一在 `types/index.ts` 中定义，其他文件从该处导入。

---

## 10. 其他问题

### 10.1 环境变量未定义
**问题**: [request.ts:12](file:///D:/Project/wheatagent/src/web/frontend/src/utils/request.ts#L12) 使用 `import.meta.env.VITE_API_BASE_URL`，但没有 `.env` 文件定义该变量。

### 10.2 缺少 ForgotPassword.vue 实现
**文件**: [src/views/ForgotPassword.vue](file:///D:/Project/wheatagent/src/web/frontend/src/views/ForgotPassword.vue)

**问题**: 文件存在但需要确认是否有完整实现。

---

## 修复优先级

| 优先级 | 问题类型 | 数量 |
|--------|----------|------|
| 高 | 依赖配置问题 | 2 |
| 高 | API 导入问题 | 1 |
| 高 | 安全问题 | 2 |
| 中 | 组件逻辑问题 | 3 |
| 中 | 测试文件问题 | 1 |
| 低 | 代码质量问题 | 2 |
| 低 | 性能问题 | 2 |
| 低 | 类型定义问题 | 1 |

---

## 下一步行动

1. 首先修复依赖配置问题，确保项目可以正常构建
2. 修复 API 导入和代理配置问题
3. 修复安全问题
4. 更新测试文件以匹配实际组件
5. 优化组件逻辑和性能
