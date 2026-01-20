import { createRouter, createWebHistory } from 'vue-router'

const routes = [
    {
        path: '/',
        name: 'Welcome',
        component: () => import('../views/WelcomePage.vue')
    },
    {
        path: '/explore',
        name: 'Explore',
        component: () => import('../views/ExplorePage.vue')
    },
    {
        path: '/complete',
        name: 'Complete',
        component: () => import('../views/CompletePage.vue')
    }
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

export default router
