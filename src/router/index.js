import { createRouter, createWebHashHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/home',
    children: [
      {
        path: 'home',
        name: 'Home',
        component: () => import('@/views/Home.vue'),
        meta: { title: '首页' }
      },
      {
        path: 'bidding',
        name: 'Bidding',
        component: () => import('@/views/Bidding.vue'),
        meta: { title: '招投标信息' }
      },
      {
        path: 'policy',
        name: 'Policy',
        component: () => import('@/views/Policy.vue'),
        meta: { title: '政策动态' }
      },
      {
        path: 'solutions',
        name: 'Solutions',
        component: () => import('@/views/Solutions.vue'),
        meta: { title: '解决方案' }
      },
      {
        path: 'ecosystem',
        name: 'Ecosystem',
        component: () => import('@/views/Ecosystem.vue'),
        meta: { title: '生态图谱' }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
  scrollBehavior() {
    return { top: 0 }
  }
})

router.afterEach((to) => {
  const baseTitle = '教育行业知识服务平台'
  document.title = to.meta?.title ? `${to.meta.title} - ${baseTitle}` : baseTitle
})

export default router
