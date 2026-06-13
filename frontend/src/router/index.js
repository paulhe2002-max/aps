import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/login', component: () => import('../views/Login.vue'), meta: { public: true } },
  {
    path: '/',
    component: () => import('../views/Layout.vue'),
    redirect: '/dashboard',
    children: [
      { path: 'dashboard', component: () => import('../views/Dashboard.vue') },
      { path: 'orders', component: () => import('../views/Orders.vue') },
      { path: 'inventory', component: () => import('../views/Inventory.vue') },
      { path: 'bom', component: () => import('../views/BOM.vue') },
      { path: 'production', component: () => import('../views/Production.vue') },
      { path: 'planning', component: () => import('../views/Planning.vue') },
      { path: 'scheduling', component: () => import('../views/Scheduling.vue') },
      { path: 'simulation', component: () => import('../views/Simulation.vue') },
      { path: 'reports', component: () => import('../views/Reports.vue') },
    ]
  }
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) return '/login'
})

export default router
