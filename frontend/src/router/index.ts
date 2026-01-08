import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/',
      name: 'dashboard',
      component: () => import('@/views/Dashboard.vue'),
    },
    {
      path: '/stocks',
      name: 'stocks',
      component: () => import('@/views/Stocks.vue'),
    },
    {
      path: '/stocks/:ticker',
      name: 'stock-detail',
      component: () => import('@/views/StockDetail.vue'),
    },
    {
      path: '/portfolio',
      name: 'portfolio',
      component: () => import('@/views/Portfolio.vue'),
    },
    {
      path: '/alerts',
      name: 'alerts',
      component: () => import('@/views/Alerts.vue'),
    },
    {
      path: '/dividends',
      name: 'dividends',
      component: () => import('@/views/DividendCalendar.vue'),
    },
  ],
})

export default router
