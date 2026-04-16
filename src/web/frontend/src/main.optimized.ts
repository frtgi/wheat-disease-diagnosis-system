/**
 * 优化版应用入口文件
 * 负责初始化 Vue 应用，注册全局组件和插件
 * 包含性能优化和懒加载配置
 */

import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'

// 按需引入常用图标，避免引入全部图标
import {
  Download,
  Refresh,
  WarningFilled,
  DataLine,
  Document,
  CircleCheckFilled,
  Check,
  Link,
  DocumentCopy,
  User,
  Avatar,
  Lock,
  Picture,
  Upload,
  Search,
  Setting,
  InfoFilled,
  SuccessFilled,
  WarningFilled as WarningFilledIcon,
  QuestionFilled,
  Close,
  CircleCheck,
  Clock,
  Edit,
  Delete,
  Plus,
  Minus,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  More,
  Star,
  Collection,
  Tickets,
  Message,
  Position,
  Location,
  OfficeBuilding,
  Phone,
  Monitor,
  DataAnalysis,
  Histogram,
  Menu,
  HomeFilled,
  UserFilled,
  Guide,
  Notebook
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

// 创建 Vue 应用实例
const app = createApp(App)

// 创建 Pinia 实例
const pinia = createPinia()

// 使用插件
app.use(pinia)
app.use(router)
app.use(ElementPlus, {
  locale: zhCn
})

// 注册按需引入的图标
const icons: Record<string, any> = {
  Download,
  Refresh,
  WarningFilled,
  DataLine,
  Document,
  CircleCheckFilled,
  Check,
  Link,
  DocumentCopy,
  User,
  Avatar,
  Lock,
  Picture,
  Upload,
  Search,
  Setting,
  InfoFilled,
  SuccessFilled,
  WarningFilledIcon,
  QuestionFilled,
  Close,
  CircleCheck,
  Clock,
  Edit,
  Delete,
  Plus,
  Minus,
  ArrowLeft,
  ArrowRight,
  ArrowUp,
  ArrowDown,
  More,
  Star,
  Collection,
  Tickets,
  Message,
  Position,
  Location,
  OfficeBuilding,
  Phone,
  Monitor,
  DataAnalysis,
  Histogram,
  Menu,
  HomeFilled,
  UserFilled,
  Guide,
  Notebook
}

Object.keys(icons).forEach(key => {
  app.component(key, icons[key])
})

// 挂载应用
app.mount('#app')

// 性能监控
if (import.meta.env.PROD) {
  window.addEventListener('load', () => {
    if ('performance' in window) {
      setTimeout(() => {
        const perfEntries = performance.getEntriesByType('navigation')
        if (perfEntries.length > 0) {
          const perfData = perfEntries[0] as PerformanceNavigationTiming
          if (perfData) {
            console.log('页面加载时间:', perfData.loadEventEnd - perfData.fetchStart, 'ms')
          }
        }
      }, 0)
    }
  })
}

export { app, pinia, router }