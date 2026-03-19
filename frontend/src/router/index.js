import { createRouter, createWebHistory } from 'vue-router'
import ProjectList from '../pages/ProjectList.vue'
import ProjectBoard from '../pages/ProjectBoard.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', name: 'home', component: ProjectList },
    { path: '/projects/:id', name: 'board', component: ProjectBoard, props: true },
  ],
})

export default router
