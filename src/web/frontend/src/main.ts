/**
 * 应用入口文件
 * 负责初始化 Vue 应用，注册全局组件和插件
 * 
 * Element Plus 使用按需导入，由 unplugin-vue-components 自动处理
 * 图标仅全局注册通过模板 kebab-case 或 prefix-icon 字符串引用的图标，
 * 其余图标由各组件自行显式导入
 */
import { createApp, type Component } from 'vue'
import { createPinia } from 'pinia'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import {
  HomeFilled,
  Picture,
  Document,
  Reading,
  User,
  Search
} from '@element-plus/icons-vue'

import App from './App.vue'
import router from './router'

const app = createApp(App)

const pinia = createPinia()

app.use(pinia)
app.use(router)

app.config.globalProperties.$ELEMENT = {
  locale: zhCn
}

/**
 * 全局注册图标组件
 * 仅注册通过模板 kebab-case 或 prefix-icon 字符串引用的图标
 * 其他图标由各组件按需显式导入
 */
const globallyUsedIcons: Record<string, Component> = {
  HomeFilled,
  Picture,
  Document,
  Reading,
  User,
  Search
}

for (const [key, component] of Object.entries(globallyUsedIcons)) {
  app.component(key, component)
}

app.mount('#app')
