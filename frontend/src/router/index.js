import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import RepoRag from '../views/RepoRag.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView
    },
    {
      path: '/:owner/:repo',
      name: 'repoRag',
      component: RepoRag,
      props: true
    }
  ]
})

export default router