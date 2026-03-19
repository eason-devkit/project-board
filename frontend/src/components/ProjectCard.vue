<script setup>
const props = defineProps({ project: Object })
const emit = defineEmits(['edit', 'delete'])
</script>

<template>
  <div class="bg-white rounded-xl border border-gray-200 p-4 flex flex-col gap-3 hover:shadow-md transition-shadow cursor-pointer">
    <!-- Header -->
    <div class="flex items-start justify-between gap-2">
      <h3 class="font-semibold text-gray-900 text-base leading-tight">{{ project.name }}</h3>
      <div class="flex items-center gap-1 shrink-0" @click.stop>
        <button
          @click="emit('edit', project)"
          class="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
          title="編輯"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
          </svg>
        </button>
        <button
          @click="emit('delete', project)"
          class="p-1 rounded hover:bg-red-50 text-gray-400 hover:text-red-500 transition-colors"
          title="刪除"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm5-1a1 1 0 00-1 1v6a1 1 0 102 0V8a1 1 0 00-1-1z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Tags -->
    <div v-if="project.tags.length" class="flex flex-wrap gap-1.5 items-center">
      <span
        v-for="tag in project.tags"
        :key="tag.id"
        class="inline-block px-2 py-0.5 rounded-full text-xs bg-indigo-50 text-indigo-600"
      >
        {{ tag.name }}
      </span>
    </div>

    <!-- Description -->
    <p v-if="project.description" class="text-sm text-gray-500 line-clamp-2 leading-relaxed">
      {{ project.description }}
    </p>

    <!-- Block count -->
    <div class="mt-auto pt-1 text-xs text-gray-400 flex items-center gap-1">
      <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
        <path d="M7 3a1 1 0 000 2h6a1 1 0 100-2H7zM4 7a1 1 0 011-1h10a1 1 0 110 2H5a1 1 0 01-1-1zM2 11a2 2 0 012-2h12a2 2 0 012 2v4a2 2 0 01-2 2H4a2 2 0 01-2-2v-4z" />
      </svg>
      {{ project.block_count || 0 }} 個區塊
    </div>
  </div>
</template>
