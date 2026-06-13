<template>
  <el-container style="height:100vh">
    <el-aside width="220px" class="sidebar">
      <div class="logo">
        <span class="logo-icon">📊</span>
        <span class="logo-text">APS系统</span>
      </div>
      <el-menu :default-active="$route.path" router class="sidebar-menu" background-color="#1a1a2e" text-color="#adb5bd" active-text-color="#4fc3f7">
        <el-menu-item index="/dashboard"><el-icon><DataBoard /></el-icon>仪表盘</el-menu-item>
        <el-menu-item index="/orders"><el-icon><Document /></el-icon>客户订单</el-menu-item>
        <el-menu-item index="/inventory"><el-icon><Box /></el-icon>库存管理</el-menu-item>
        <el-menu-item index="/bom"><el-icon><Grid /></el-icon>BOM物料清单</el-menu-item>
        <el-menu-item index="/production"><el-icon><Setting /></el-icon>产线管理</el-menu-item>
        <el-menu-item index="/planning"><el-icon><Calendar /></el-icon>计划与RCCP</el-menu-item>
        <el-menu-item index="/scheduling"><el-icon><Timer /></el-icon>排程优化</el-menu-item>
        <el-menu-item index="/simulation"><el-icon><VideoPlay /></el-icon>算法演示</el-menu-item>
        <el-menu-item index="/reports"><el-icon><TrendCharts /></el-icon>报表与KPI</el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb>
            <el-breadcrumb-item>{{ pageTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tag type="success" size="small">{{ auth.user?.role }}</el-tag>
          <span class="username">{{ auth.user?.username }}</span>
          <el-button text @click="logout"><el-icon><SwitchButton /></el-icon>退出</el-button>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const route = useRoute()
const router = useRouter()
const auth = useAuthStore()

const titles = {
  '/dashboard': '仪表盘', '/orders': '客户订单', '/inventory': '库存管理',
  '/bom': 'BOM物料清单', '/production': '产线管理', '/planning': '计划与RCCP',
  '/scheduling': '排程优化', '/simulation': '算法演示', '/reports': '报表与KPI'
}
const pageTitle = computed(() => titles[route.path] || 'APS')

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<style scoped>
.sidebar { background: #1a1a2e; border-right: none; }
.logo {
  height: 64px; display: flex; align-items: center; justify-content: center;
  gap: 10px; border-bottom: 1px solid rgba(255,255,255,0.1);
}
.logo-icon { font-size: 24px; }
.logo-text { color: #4fc3f7; font-size: 18px; font-weight: 700; }
.sidebar-menu { border-right: none; }
.header {
  background: white; border-bottom: 1px solid #e4e7ed;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
}
.header-right { display: flex; align-items: center; gap: 12px; }
.username { color: #303133; font-weight: 500; }
.main-content { background: #f5f7fa; padding: 24px; overflow-y: auto; }
</style>
