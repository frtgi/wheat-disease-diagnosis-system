<template>
  <el-container class="layout-container">
    <el-header class="layout-header">
      <div class="header-content">
        <h1 class="logo">小麦病害诊断系统</h1>
        <el-menu
          mode="horizontal"
          :default-active="activeMenu"
          router
          class="header-menu"
        >
          <el-menu-item index="/">
            <el-icon><home-filled /></el-icon>
            <span>首页</span>
          </el-menu-item>
          <el-menu-item index="/diagnosis">
            <el-icon><picture /></el-icon>
            <span>诊断</span>
          </el-menu-item>
          <el-menu-item index="/records">
            <el-icon><document /></el-icon>
            <span>记录</span>
          </el-menu-item>
          <el-menu-item index="/knowledge">
            <el-icon><reading /></el-icon>
            <span>知识库</span>
          </el-menu-item>
          <el-menu-item index="/user">
            <el-icon><user /></el-icon>
            <span>用户中心</span>
          </el-menu-item>
          <el-menu-item v-if="isAdmin" index="/admin">
            <el-icon><setting /></el-icon>
            <span>管理后台</span>
          </el-menu-item>
        </el-menu>
        <div class="header-actions">
          <template v-if="isLoggedIn">
            <el-dropdown @command="handleCommand">
              <span class="user-info">
                <el-avatar :size="32" :src="userInfo.avatar">
                  {{ userInfo.username.charAt(0) }}
                </el-avatar>
                <span class="username">{{ userInfo.username }}</span>
              </span>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="profile">个人中心</el-dropdown-item>
                  <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </template>
          <template v-else>
            <el-button type="primary" @click="$router.push('/login')">
              登录
            </el-button>
          </template>
        </div>
      </div>
    </el-header>

    <el-main class="layout-main">
      <router-view />
    </el-main>

    <el-footer class="layout-footer">
      <p>© 2024 小麦病害诊断系统。All rights reserved.</p>
    </el-footer>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 计算属性
const activeMenu = computed(() => route.path)
const isLoggedIn = computed(() => userStore.isLoggedIn)
const userInfo = computed(() => userStore.userInfo)
const isAdmin = computed(() => {
  try {
    const userInfo = JSON.parse(localStorage.getItem('userInfo') || '{}')
    return userInfo.role === 'admin'
  } catch {
    return false
  }
})

// 处理下拉菜单命令
const handleCommand = (command: string) => {
  if (command === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (command === 'profile') {
    router.push('/user')
  }
}
</script>

<style scoped>
.layout-container {
  min-height: 100vh;
}

.layout-header {
  background-color: #fff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  padding: 0;
}

.header-content {
  display: flex;
  align-items: center;
  height: 100%;
  padding: 0 20px;
}

.logo {
  font-size: 20px;
  font-weight: bold;
  color: #409eff;
  margin: 0 40px 0 0;
}

.header-menu {
  flex: 1;
  border-bottom: none;
}

.header-actions {
  display: flex;
  align-items: center;
}

.user-info {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.username {
  margin-left: 8px;
  color: #606266;
}

.layout-main {
  background-color: #f5f7fa;
  min-height: calc(100vh - 120px);
}

.layout-footer {
  background-color: #fff;
  text-align: center;
  padding: 20px;
  color: #909399;
  font-size: 14px;
}
</style>
