import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as api from '../api/projects'

export const useProjectStore = defineStore('projects', () => {
  const projects = ref([])
  const searchQuery = ref('')
  const filterTag = ref('')

  const filtered = computed(() => {
    const q = searchQuery.value.toLowerCase()
    return projects.value.filter(p => {
      const matchSearch =
        !q ||
        p.name.toLowerCase().includes(q) ||
        p.description.toLowerCase().includes(q) ||
        p.tags.some(t => t.name.toLowerCase().includes(q))
      const matchTag = !filterTag.value || p.tags.some(t => t.name === filterTag.value)
      return matchSearch && matchTag
    })
  })

  async function load() {
    projects.value = await api.getProjects()
  }

  async function create(data) {
    const project = await api.createProject(data)
    projects.value.unshift(project)
  }

  async function update(id, data) {
    const project = await api.updateProject(id, data)
    const idx = projects.value.findIndex(p => p.id === id)
    if (idx !== -1) projects.value[idx] = project
  }

  async function remove(id) {
    await api.deleteProject(id)
    projects.value = projects.value.filter(p => p.id !== id)
  }

  return { projects, searchQuery, filterTag, filtered, load, create, update, remove }
})
