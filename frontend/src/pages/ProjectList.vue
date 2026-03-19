<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useProjectStore } from '../stores/projects'
import ProjectCard from '../components/ProjectCard.vue'
import ProjectForm from '../components/ProjectForm.vue'

const router = useRouter()
const store = useProjectStore()

const showForm = ref(false)
const editingProject = ref(null)

const allTags = computed(() => {
  const set = new Set()
  store.projects.forEach(p => p.tags.forEach(t => set.add(t.name)))
  return [...set].sort()
})

function openCreate() {
  editingProject.value = null
  showForm.value = true
}

function openEdit(project) {
  editingProject.value = project
  showForm.value = true
}

async function handleSave(data) {
  if (editingProject.value) {
    await store.update(editingProject.value.id, data)
  } else {
    await store.create(data)
  }
}

async function handleDelete(project) {
  if (confirm(`確定要刪除「${project.name}」嗎？`)) {
    await store.remove(project.id)
  }
}

function openBoard(project) {
  router.push({ name: 'board', params: { id: project.id } })
}

onMounted(() => store.load())
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Top bar -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-6xl mx-auto px-6 py-3 flex items-center gap-4">
        <h1 class="text-lg font-bold text-gray-900 shrink-0">Project Board</h1>

        <!-- Search -->
        <div class="relative flex-1 max-w-sm">
          <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M8 4a4 4 0 100 8 4 4 0 000-8zM2 8a6 6 0 1110.89 3.476l4.817 4.817a1 1 0 01-1.414 1.414l-4.816-4.816A6 6 0 012 8z" clip-rule="evenodd" />
          </svg>
          <input
            v-model="store.searchQuery"
            type="text"
            placeholder="搜尋專案..."
            class="w-full pl-9 pr-3 py-1.5 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
          />
        </div>

        <button
          @click="openCreate"
          class="ml-auto shrink-0 flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
          </svg>
          新增專案
        </button>
      </div>

      <!-- Tag filter -->
      <div v-if="allTags.length" class="max-w-6xl mx-auto px-6 pb-3 flex items-center gap-4 flex-wrap">
        <div class="flex gap-1 flex-wrap">
          <button
            v-for="tag in allTags"
            :key="tag"
            @click="store.filterTag = store.filterTag === tag ? '' : tag"
            class="px-2.5 py-1 rounded-full text-xs font-medium transition-colors"
            :class="store.filterTag === tag
              ? 'bg-indigo-100 text-indigo-700 ring-1 ring-indigo-400'
              : 'bg-gray-100 text-gray-600 hover:bg-gray-200'"
          >
            {{ tag }}
          </button>
        </div>
      </div>
    </header>

    <!-- Main content -->
    <main class="max-w-6xl mx-auto px-6 py-6">
      <!-- Empty state -->
      <div v-if="store.filtered.length === 0" class="text-center py-20 text-gray-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <p class="text-sm">{{ store.searchQuery || store.filterTag ? '找不到符合的專案' : '還沒有任何專案，新增一個吧！' }}</p>
      </div>

      <!-- Cards grid -->
      <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <ProjectCard
          v-for="project in store.filtered"
          :key="project.id"
          :project="project"
          @click="openBoard(project)"
          @edit="openEdit"
          @delete="handleDelete"
        />
      </div>
    </main>

    <ProjectForm
      v-model="showForm"
      :project="editingProject"
      @save="handleSave"
    />
  </div>
</template>
