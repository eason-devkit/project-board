<script setup>
import { ref, computed, watch } from 'vue'
import { MdEditor } from 'md-editor-v3'
import 'md-editor-v3/lib/style.css'
import { uploadImage } from '../api/blocks'

const props = defineProps({
  modelValue: Boolean,
  block: Object,
  initialText: { type: String, default: '' },
  templateType: { type: String, default: null },
})
const emit = defineEmits(['update:modelValue', 'save', 'switch-to-structured'])

const text = ref('')

watch(() => props.modelValue, (open) => {
  if (!open) return
  if (props.block) {
    text.value = props.block.content?.text || ''
  } else {
    text.value = props.initialText
  }
}, { immediate: true })

async function onUploadImg(files, callback) {
  const results = []
  for (const file of files) {
    try {
      const { url } = await uploadImage(file)
      results.push({ url, alt: file.name, title: file.name })
    } catch {
      // skip failed uploads
    }
  }
  callback(results)
}

// --- Format validation for switching back to structured mode ---
const FORMAT_VALIDATORS = {
  link: /^\[([^\]]*)\]\(([^)]*)\)(\n\n[\s\S]*)?$/,
  image: /^!\[([^\]]*)\]\(([^)]*)\)$/,
  list: /^(- .+\n?)+$/,
  todo: /^(- \[[ x]\] .+\n?)+$/,
  file: /^\[([^\]]*)\]\(([^)]*)\)$/,
}

const canSwitchToStructured = computed(() => {
  if (!props.templateType) return false
  const validator = FORMAT_VALIDATORS[props.templateType]
  if (!validator) return false
  return validator.test(text.value.trim())
})

function switchToStructured() {
  if (!canSwitchToStructured.value) return
  emit('switch-to-structured', text.value)
  close()
}

function close() {
  emit('update:modelValue', false)
}

function submit() {
  if (!text.value.trim()) return
  const data = {
    block_type: 'markdown',
    content: { text: text.value },
  }
  // If content no longer matches template format, clear template_type
  if (props.templateType) {
    const validator = FORMAT_VALIDATORS[props.templateType]
    if (validator && validator.test(text.value.trim())) {
      data.template_type = props.templateType
    } else {
      data.template_type = null
    }
  }
  emit('save', data)
  close()
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
    >
      <div class="bg-white rounded-2xl w-full max-w-3xl shadow-xl flex flex-col max-h-[90vh]">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-900">{{ block ? '編輯區塊' : '新增區塊' }}</h2>
          <button @click="close" class="text-gray-400 hover:text-gray-600 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="overflow-y-auto flex-1 px-6 py-4">
          <MdEditor
            v-model="text"
            language="en-US"
            :preview="false"
            :toolbarsExclude="['github', 'save', 'htmlPreview', 'catalog', 'fullscreen']"
            @onUploadImg="onUploadImg"
            style="height: 400px"
          />
        </div>

        <!-- Footer -->
        <div class="flex items-center px-6 py-4 border-t border-gray-100">
          <div v-if="templateType" class="flex items-center gap-2">
            <button
              v-if="canSwitchToStructured"
              @click="switchToStructured"
              type="button"
              class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 hover:text-indigo-600 rounded-lg hover:bg-gray-100 transition-colors"
              title="切換到結構化編輯模式"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" />
              </svg>
              結構化編輯
            </button>
            <span v-else class="text-xs text-gray-400 px-2">
              內容格式已變更，無法切換回結構化編輯
            </span>
          </div>
          <div class="flex gap-2 ml-auto">
            <button
              @click="close"
              type="button"
              class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 rounded-lg hover:bg-gray-100 transition-colors"
            >取消</button>
            <button
              @click="submit"
              type="button"
              class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium"
            >儲存</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
