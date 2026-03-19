<script setup>
import { ref, watch } from 'vue'

const props = defineProps({ modelValue: Boolean, project: Object })
const emit = defineEmits(['update:modelValue', 'save'])

const empty = () => ({ name: '', description: '', tags: [] })
const form = ref(empty())
const tagInput = ref('')

watch(() => props.project, (p) => {
  if (p) {
    form.value = {
      name: p.name,
      description: p.description,
      tags: p.tags.map(t => t.name),
    }
  } else {
    form.value = empty()
  }
}, { immediate: true })

function addTag() {
  const t = tagInput.value.trim()
  if (t && !form.value.tags.includes(t)) {
    form.value.tags.push(t)
  }
  tagInput.value = ''
}

function removeTag(t) {
  form.value.tags = form.value.tags.filter(x => x !== t)
}

function handleTagKeydown(e) {
  if (e.key === 'Enter') {
    e.preventDefault()
    addTag()
  }
}

function close() {
  emit('update:modelValue', false)
}

function submit() {
  if (!form.value.name.trim()) return
  emit('save', { ...form.value })
  close()
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      @click.self="close"
    >
      <div class="bg-white rounded-2xl w-full max-w-lg shadow-xl flex flex-col max-h-[90vh]">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-900">{{ project ? '編輯專案' : '新增專案' }}</h2>
          <button @click="close" class="text-gray-400 hover:text-gray-600 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="overflow-y-auto flex-1 px-6 py-4 flex flex-col gap-4">
          <!-- Name -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">專案名稱 <span class="text-red-500">*</span></label>
            <input
              v-model="form.name"
              type="text"
              placeholder="e.g. My Awesome Project"
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
            />
          </div>

          <!-- Description -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">備註</label>
            <textarea
              v-model="form.description"
              rows="3"
              placeholder="專案說明、備忘錄..."
              class="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 resize-none"
            />
          </div>

          <!-- Tags -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">標籤</label>
            <div class="flex gap-2 mb-2">
              <input
                v-model="tagInput"
                type="text"
                placeholder="輸入標籤後按 Enter"
                @keydown="handleTagKeydown"
                class="flex-1 border border-gray-300 rounded-lg px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400"
              />
              <button
                @click="addTag"
                type="button"
                class="px-3 py-1.5 bg-indigo-50 text-indigo-600 rounded-lg text-sm font-medium hover:bg-indigo-100 transition-colors"
              >新增</button>
            </div>
            <div class="flex flex-wrap gap-1.5">
              <span
                v-for="tag in form.tags"
                :key="tag"
                class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs bg-indigo-50 text-indigo-600"
              >
                {{ tag }}
                <button @click="removeTag(tag)" class="hover:text-indigo-900">&times;</button>
              </span>
            </div>
          </div>
        </div>

        <!-- Footer -->
        <div class="flex gap-2 justify-end px-6 py-4 border-t border-gray-100">
          <button
            @click="close"
            type="button"
            class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 rounded-lg hover:bg-gray-100 transition-colors"
          >取消</button>
          <button
            @click="submit"
            type="button"
            class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50"
            :disabled="!form.name.trim()"
          >儲存</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>
