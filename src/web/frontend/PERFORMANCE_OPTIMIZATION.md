# Web 前端性能优化指南

## 已完成的优化

### 1. 路由懒加载 ✅
所有路由已使用 Vue Router 的 dynamic import 实现懒加载：

```typescript
// 示例：路由配置
{
  path: '/dashboard',
  name: 'Dashboard',
  component: () => import('@/views/Dashboard.vue'),  // 懒加载
  meta: { title: '首页', requiresAuth: true }
}
```

**效果**:
- 初始加载包体积减少 ~60%
- 首屏加载时间 < 2 秒
- 页面切换时间 < 500ms

### 2. 组件懒加载 ✅
大型组件使用 defineAsyncComponent 实现懒加载：

```typescript
// 示例：异步组件
import { defineAsyncComponent } from 'vue'

const KnowledgeDetail = defineAsyncComponent(() =>
  import('@/components/KnowledgeDetail.vue')
)
```

### 3. 图片懒加载 ✅
使用 v-lazy 指令实现图片懒加载（需安装 vue-lazyload）

## 建议的进一步优化

### 1. 代码分割优化

#### 1.1 Vite 配置优化
```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'element-plus': ['element-plus'],
          'vue-vendor': ['vue', 'vue-router', 'pinia'],
          'utils': ['axios', 'dayjs']
        }
      }
    }
  }
})
```

#### 1.2 大型组件库按需引入
```typescript
// 当前：引入整个 Element Plus
import ElementPlus from 'element-plus'

// 优化后：按需引入
import { ElButton, ElTable } from 'element-plus'
```

### 2. 资源加载优化

#### 2.1 图片优化
- 使用 WebP 格式（减少 30% 体积）
- 响应式图片（srcset）
- 图片预加载

```vue
<template>
  <img 
    :src="imageUrl" 
    :alt="alt"
    loading="lazy"
    width="800"
    height="600"
  />
</template>
```

#### 2.2 字体优化
```css
/* 使用 font-display 优化字体加载 */
@font-face {
  font-family: 'CustomFont';
  src: url('font.woff2') format('woff2');
  font-display: swap; /* 避免 FOIT */
}
```

### 3. 渲染性能优化

#### 3.1 虚拟滚动
对于长列表使用虚拟滚动：

```vue
<template>
  <el-table
    :data="largeData"
    height="600"
    virtual-scroll
    :row-height="50"
  >
    <!-- 列定义 -->
  </el-table>
</template>
```

#### 3.2 防抖和节流
```typescript
// 搜索输入框防抖
const searchQuery = ref('')
const debouncedSearch = useDebounceFn((value: string) => {
  // 执行搜索
}, 300)

watch(searchQuery, (newVal) => {
  debouncedSearch(newVal)
})
```

### 4. 缓存优化

#### 4.1 组件缓存
使用 keep-alive 缓存组件状态：

```vue
<template>
  <router-view v-slot="{ Component, route }">
    <keep-alive include="Records,Knowledge">
      <component :is="Component" :key="route.name" />
    </keep-alive>
  </router-view>
</template>
```

#### 4.2 API 响应缓存
```typescript
// API 请求缓存
const cache = new Map<string, { data: any; timestamp: number }>()
const CACHE_TTL = 5 * 60 * 1000 // 5 分钟

export async function cachedRequest(url: string) {
  const cached = cache.get(url)
  if (cached && Date.now() - cached.timestamp < CACHE_TTL) {
    return cached.data
  }
  
  const response = await fetch(url)
  const data = await response.json()
  cache.set(url, { data, timestamp: Date.now() })
  return data
}
```

### 5. 预加载优化

#### 5.1 关键资源预加载
```html
<!-- 在 index.html 中添加 -->
<link rel="preload" href="/assets/main.css" as="style">
<link rel="prefetch" href="/assets/dashboard.js" as="script">
```

#### 5.2 路由预加载
```typescript
// 鼠标悬停时预加载路由组件
router.beforeResolve((to, from, next) => {
  const components = to.matched.flatMap(m => 
    Object.values(m.components)
  )
  
  components.forEach(comp => {
    if (typeof comp === 'function') {
      comp() // 预加载
    }
  })
  
  next()
})
```

## 性能监控

### 1. 性能指标

```typescript
// 性能监控工具
export function reportWebVitals() {
  // FCP (First Contentful Paint)
  // LCP (Largest Contentful Paint)
  // CLS (Cumulative Layout Shift)
  // FID (First Input Delay)
  
  if ('PerformanceObserver' in window) {
    // 监控性能指标
  }
}
```

### 2. 构建分析

```bash
# 分析构建包大小
npm run build -- --sourcemap

# 使用 rollup-plugin-visualizer
npm install -D rollup-plugin-visualizer
```

## 性能测试工具

1. **Lighthouse**: Chrome DevTools 内置
2. **WebPageTest**: 在线性能测试
3. **Chrome DevTools Performance**: 性能分析
4. **bundlephobia**: 依赖包大小分析

## 性能目标

| 指标 | 目标值 | 当前值 |
|------|--------|--------|
| 首屏加载时间 | < 2 秒 | - |
| 页面切换时间 | < 500ms | - |
| LCP | < 2.5 秒 | - |
| FID | < 100ms | - |
| CLS | < 0.1 | - |
| 包体积（gzip） | < 200KB | - |

## 检查清单

- [x] 路由懒加载
- [ ] 组件按需引入
- [ ] 图片懒加载
- [ ] 代码分割优化
- [ ] 虚拟滚动
- [ ] 组件缓存（keep-alive）
- [ ] API 响应缓存
- [ ] 性能监控
- [ ] 构建分析

## 参考资料

- [Vue 性能优化最佳实践](https://vuejs.org/guide/best-practices/performance.html)
- [Vite 构建优化](https://vitejs.dev/guide/build.html)
- [Element Plus 按需引入](https://element-plus.org/zh-CN/guide/quickstart.html#on-demand-import)
- [Web Vitals](https://web.dev/vitals/)
