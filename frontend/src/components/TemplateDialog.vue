<script setup>
import { ref, reactive, computed, watch, nextTick } from 'vue'
import { uploadImage, uploadFile } from '../api/blocks'

const props = defineProps({
  modelValue: Boolean,
  templateType: { type: String, default: null }, // 'link' | 'image' | 'list' | 'todo'
  editBlock: { type: Object, default: null }, // block being edited (null = create mode)
})
const emit = defineEmits(['update:modelValue', 'save', 'switch-to-markdown'])

// --- Link form ---
const link = reactive({ url: '', title: '', description: '' })

// --- Image form ---
const imageUrl = ref('')
const imageAlt = ref('')
const uploading = ref(false)
const dragOver = ref(false)

// --- File form ---
const fileUrl = ref('')
const fileName = ref('')
const fileUploading = ref(false)
const fileDragOver = ref(false)
const fileErrorMsg = ref('')

const ALLOWED_FILE_EXTS = ['.pdf', '.docx', '.xlsx', '.pptx', '.txt', '.csv', '.md']
const MAX_FILE_SIZE = 20 * 1024 * 1024

// --- List / Todo form ---
const listItems = ref([])

const createTitles = {
  link: '新增連結',
  image: '新增圖片',
  list: '新增清單',
  todo: '新增待辦清單',
  file: '新增檔案',
}
const editTitles = {
  link: '編輯連結',
  image: '編輯圖片',
  list: '編輯清單',
  todo: '編輯待辦清單',
  file: '編輯檔案',
}
const titles = computed(() => props.editBlock ? editTitles : createTitles)

// --- Markdown-to-fields parsers ---
function parseLink(md) {
  // Match [title](url) optionally followed by description
  const m = md.match(/^\[([^\]]*)\]\(([^)]*)\)/)
  if (!m) return { url: '', title: '', description: '' }
  const rest = md.slice(m[0].length).replace(/^\n+/, '')
  return { url: m[2], title: m[1], description: rest }
}

function parseImage(md) {
  const m = md.match(/^!\[([^\]]*)\]\(([^)]*)\)/)
  if (!m) return { url: '', alt: '' }
  return { url: m[2], alt: m[1] }
}

function parseList(md) {
  return md.split('\n')
    .filter(line => line.match(/^- /))
    .map(line => line.replace(/^- /, ''))
}

function parseTodo(md) {
  return md.split('\n')
    .filter(line => line.match(/^- \[[ x]\] /))
    .map(line => ({
      text: line.replace(/^- \[[ x]\] /, ''),
      checked: line.startsWith('- [x] '),
    }))
}

function parseFile(md) {
  const m = md.match(/^\[([^\]]*)\]\(([^)]*)\)/)
  if (!m) return { name: '', url: '' }
  return { name: m[1], url: m[2] }
}

watch(() => props.modelValue, (open) => {
  if (!open) return

  const block = props.editBlock
  const md = block?.content?.text || ''

  // Reset common state
  uploading.value = false
  dragOver.value = false

  if (block && md) {
    // Edit mode: parse markdown back into fields
    if (props.templateType === 'link') {
      const parsed = parseLink(md)
      link.url = parsed.url
      link.title = parsed.title
      link.description = parsed.description
    } else if (props.templateType === 'image') {
      const parsed = parseImage(md)
      imageUrl.value = parsed.url
      imageAlt.value = parsed.alt
    } else if (props.templateType === 'list') {
      const items = parseList(md)
      listItems.value = items.length > 0 ? items : ['', '', '']
    } else if (props.templateType === 'todo') {
      const items = parseTodo(md)
      listItems.value = items.length > 0 ? items : [{ text: '', checked: false }, { text: '', checked: false }, { text: '', checked: false }]
    } else if (props.templateType === 'file') {
      const parsed = parseFile(md)
      fileUrl.value = parsed.url
      fileName.value = parsed.name
    }
  } else {
    // Create mode: reset forms
    link.url = ''
    link.title = ''
    link.description = ''
    imageUrl.value = ''
    imageAlt.value = ''
    fileUrl.value = ''
    fileName.value = ''
    fileUploading.value = false
    fileErrorMsg.value = ''
    fileDragOver.value = false
    if (props.templateType === 'list') {
      listItems.value = ['', '', '']
    } else if (props.templateType === 'todo') {
      listItems.value = [{ text: '', checked: false }, { text: '', checked: false }, { text: '', checked: false }]
    } else {
      listItems.value = []
    }
  }
})

// --- List helpers ---
function addItem() {
  listItems.value.push(props.templateType === 'todo' ? { text: '', checked: false } : '')
  nextTick(() => {
    const inputs = document.querySelectorAll('.template-list-input')
    inputs[inputs.length - 1]?.focus()
  })
}

function removeItem(index) {
  if (listItems.value.length <= 1) return
  listItems.value.splice(index, 1)
}

function getItemText(index) {
  const item = listItems.value[index]
  return typeof item === 'string' ? item : item.text
}

function onListKeydown(e, index) {
  if (e.key === 'Enter') {
    e.preventDefault()
    const newItem = props.templateType === 'todo' ? { text: '', checked: false } : ''
    listItems.value.splice(index + 1, 0, newItem)
    nextTick(() => {
      const inputs = document.querySelectorAll('.template-list-input')
      inputs[index + 1]?.focus()
    })
  } else if (e.key === 'Backspace' && getItemText(index) === '' && listItems.value.length > 1) {
    e.preventDefault()
    listItems.value.splice(index, 1)
    nextTick(() => {
      const inputs = document.querySelectorAll('.template-list-input')
      const focusIdx = Math.max(0, index - 1)
      inputs[focusIdx]?.focus()
    })
  }
}

// --- Image helpers ---
async function handleFiles(files) {
  if (!files || files.length === 0) return
  const file = files[0]
  if (!file.type.startsWith('image/')) return
  uploading.value = true
  try {
    const { url } = await uploadImage(file)
    imageUrl.value = url
    if (!imageAlt.value) imageAlt.value = file.name.replace(/\.[^.]+$/, '')
  } catch {
    // upload failed
  } finally {
    uploading.value = false
  }
}

function onFileSelect(e) {
  handleFiles(e.target.files)
}

function onDrop(e) {
  e.preventDefault()
  dragOver.value = false
  handleFiles(e.dataTransfer.files)
}

function onDragOver(e) {
  e.preventDefault()
  dragOver.value = true
}

function onDragLeave() {
  dragOver.value = false
}

function removeImage() {
  imageUrl.value = ''
}

// --- File helpers ---
function validateFile(file) {
  const ext = '.' + file.name.split('.').pop().toLowerCase()
  if (!ALLOWED_FILE_EXTS.includes(ext)) {
    return '不支援的檔案格式，允許：PDF、DOCX、XLSX、PPTX、TXT、CSV、MD'
  }
  if (file.size > MAX_FILE_SIZE) {
    return '檔案大小超過 20MB 限制'
  }
  return null
}

async function handleFileUpload(files) {
  if (!files || files.length === 0) return
  const file = files[0]
  fileErrorMsg.value = ''

  const err = validateFile(file)
  if (err) {
    fileErrorMsg.value = err
    return
  }

  fileUploading.value = true
  try {
    const { url, original_name } = await uploadFile(file)
    fileUrl.value = url
    fileName.value = original_name || file.name
  } catch (e) {
    fileErrorMsg.value = e.message
  } finally {
    fileUploading.value = false
  }
}

function onFileInputSelect(e) {
  handleFileUpload(e.target.files)
  e.target.value = ''
}

function onFileDrop(e) {
  e.preventDefault()
  fileDragOver.value = false
  handleFileUpload(e.dataTransfer.files)
}

function onFileDragOver(e) {
  e.preventDefault()
  fileDragOver.value = true
}

function onFileDragLeave() {
  fileDragOver.value = false
}

function removeFile() {
  fileUrl.value = ''
  fileName.value = ''
  fileErrorMsg.value = ''
}

// --- Switch to Markdown ---
function buildCurrentMarkdown() {
  if (props.templateType === 'link') {
    const title = link.title.trim() || link.url.trim() || ''
    const url = link.url.trim() || '#'
    let md = `[${title}](${url})`
    if (link.description.trim()) md += `\n\n${link.description.trim()}`
    return md
  } else if (props.templateType === 'image') {
    if (!imageUrl.value) return ''
    return `![${imageAlt.value.trim() || '圖片'}](${imageUrl.value})`
  } else if (props.templateType === 'list') {
    const items = listItems.value.filter(i => i.trim())
    return items.map(i => `- ${i.trim()}`).join('\n')
  } else if (props.templateType === 'todo') {
    const items = listItems.value.filter(i => i.text.trim())
    return items.map(i => `- [${i.checked ? 'x' : ' '}] ${i.text.trim()}`).join('\n')
  } else if (props.templateType === 'file') {
    if (!fileUrl.value) return ''
    return `[${fileName.value || '檔案'}](${fileUrl.value})`
  }
  return ''
}

function switchToMarkdown() {
  const md = buildCurrentMarkdown()
  emit('switch-to-markdown', md)
  close()
}

// --- Submit ---
function close() {
  emit('update:modelValue', false)
}

function submit() {
  let markdown = ''

  if (props.templateType === 'link') {
    if (!link.url.trim() && !link.title.trim()) return
    const title = link.title.trim() || link.url.trim()
    const url = link.url.trim() || '#'
    markdown = `[${title}](${url})`
    if (link.description.trim()) {
      markdown += `\n\n${link.description.trim()}`
    }
  } else if (props.templateType === 'image') {
    if (!imageUrl.value) return
    const alt = imageAlt.value.trim() || '圖片'
    markdown = `![${alt}](${imageUrl.value})`
  } else if (props.templateType === 'list') {
    const items = listItems.value.filter(i => i.trim())
    if (items.length === 0) return
    markdown = items.map(i => `- ${i.trim()}`).join('\n')
  } else if (props.templateType === 'todo') {
    const items = listItems.value.filter(i => i.text.trim())
    if (items.length === 0) return
    markdown = items.map(i => `- [${i.checked ? 'x' : ' '}] ${i.text.trim()}`).join('\n')
  } else if (props.templateType === 'file') {
    if (!fileUrl.value) return
    const name = fileName.value || '檔案'
    markdown = `[${name}](${fileUrl.value})`
  }

  emit('save', {
    block_type: 'markdown',
    content: { text: markdown },
    template_type: props.templateType,
  })
  close()
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="modelValue"
      class="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4"
      @mousedown.self="close"
    >
      <div class="bg-white rounded-2xl w-full max-w-lg shadow-xl flex flex-col max-h-[90vh]">
        <!-- Header -->
        <div class="flex items-center justify-between px-6 py-4 border-b border-gray-100">
          <h2 class="font-semibold text-gray-900">{{ titles[templateType] || (editBlock ? '編輯區塊' : '新增區塊') }}</h2>
          <button @click="close" class="text-gray-400 hover:text-gray-600 transition-colors">
            <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>

        <!-- Body -->
        <div class="overflow-y-auto flex-1 px-6 py-5">

          <!-- ===== Link Form ===== -->
          <div v-if="templateType === 'link'" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">連結網址</label>
              <input
                v-model="link.url"
                type="url"
                placeholder="https://example.com"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                @keydown.enter="$refs.linkTitle?.focus()"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">標題</label>
              <input
                ref="linkTitle"
                v-model="link.title"
                type="text"
                placeholder="連結標題"
                class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
              />
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">說明 <span class="text-gray-400 font-normal">(選填)</span></label>
              <textarea
                v-model="link.description"
                rows="3"
                placeholder="簡短描述這個連結..."
                class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent resize-none"
              />
            </div>
          </div>

          <!-- ===== Image Form ===== -->
          <div v-else-if="templateType === 'image'" class="space-y-4">
            <!-- Upload area -->
            <div
              v-if="!imageUrl"
              @drop="onDrop"
              @dragover="onDragOver"
              @dragleave="onDragLeave"
              class="border-2 border-dashed rounded-xl p-8 text-center transition-colors cursor-pointer"
              :class="dragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 hover:border-gray-400'"
              @click="$refs.fileInput.click()"
            >
              <input ref="fileInput" type="file" accept="image/*" class="hidden" @change="onFileSelect" />
              <div v-if="uploading" class="text-gray-500">
                <svg class="w-8 h-8 mx-auto mb-2 animate-spin text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <p class="text-sm">上傳中...</p>
              </div>
              <div v-else>
                <svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10 mx-auto mb-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
                <p class="text-sm text-gray-500">拖曳圖片到這裡，或點擊選擇檔案</p>
                <p class="text-xs text-gray-400 mt-1">支援 JPG, PNG, GIF, WebP</p>
              </div>
            </div>
            <!-- Preview -->
            <div v-else class="relative">
              <img :src="imageUrl" :alt="imageAlt" class="w-full rounded-lg border border-gray-200 max-h-60 object-contain bg-gray-50" />
              <button
                @click="removeImage"
                class="absolute top-2 right-2 p-1 bg-white/90 rounded-full shadow hover:bg-red-50 text-gray-500 hover:text-red-500 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-1">替代文字 <span class="text-gray-400 font-normal">(選填)</span></label>
              <input
                v-model="imageAlt"
                type="text"
                placeholder="描述這張圖片..."
                class="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
              />
            </div>
          </div>

          <!-- ===== List Form ===== -->
          <div v-else-if="templateType === 'list'" class="space-y-2">
            <label class="block text-sm font-medium text-gray-700 mb-2">清單項目</label>
            <div v-for="(item, index) in listItems" :key="index" class="flex items-center gap-2">
              <span class="text-gray-400 text-sm shrink-0 w-5 text-right">{{ index + 1 }}.</span>
              <input
                v-model="listItems[index]"
                class="template-list-input flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                :placeholder="`項目 ${index + 1}`"
                @keydown="onListKeydown($event, index)"
              />
              <button
                @click="removeItem(index)"
                :disabled="listItems.length <= 1"
                class="shrink-0 p-1 rounded text-gray-400 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
            <button
              @click="addItem"
              class="flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-700 mt-2 py-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
              </svg>
              新增項目
            </button>
            <p class="text-xs text-gray-400 mt-1">按 Enter 快速新增下一項，空白項目按 Backspace 刪除</p>
          </div>

          <!-- ===== Todo Form ===== -->
          <div v-else-if="templateType === 'todo'" class="space-y-2">
            <label class="block text-sm font-medium text-gray-700 mb-2">待辦事項</label>
            <div v-for="(item, index) in listItems" :key="index" class="flex items-center gap-2">
              <span class="shrink-0 w-5 flex justify-center">
                <input
                  type="checkbox"
                  v-model="listItems[index].checked"
                  class="w-4 h-4 rounded border-gray-300 text-indigo-600 focus:ring-indigo-400 cursor-pointer"
                />
              </span>
              <input
                v-model="listItems[index].text"
                class="template-list-input flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 focus:border-transparent"
                :class="{ 'line-through text-gray-400': listItems[index].checked }"
                :placeholder="`待辦事項 ${index + 1}`"
                @keydown="onListKeydown($event, index)"
              />
              <button
                @click="removeItem(index)"
                :disabled="listItems.length <= 1"
                class="shrink-0 p-1 rounded text-gray-400 hover:text-red-500 disabled:opacity-30 disabled:cursor-not-allowed transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
            <button
              @click="addItem"
              class="flex items-center gap-1.5 text-sm text-indigo-600 hover:text-indigo-700 mt-2 py-1"
            >
              <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
              </svg>
              新增待辦
            </button>
            <p class="text-xs text-gray-400 mt-1">按 Enter 快速新增下一項，空白項目按 Backspace 刪除</p>
          </div>

          <!-- ===== File Form ===== -->
          <div v-else-if="templateType === 'file'" class="space-y-4">
            <!-- Upload area -->
            <div
              v-if="!fileUrl"
              @drop="onFileDrop"
              @dragover="onFileDragOver"
              @dragleave="onFileDragLeave"
              class="border-2 border-dashed rounded-xl p-8 text-center transition-colors"
              :class="[
                fileUploading ? 'pointer-events-none opacity-60' : 'cursor-pointer',
                fileDragOver ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 hover:border-gray-400',
              ]"
              @click="!fileUploading && $refs.fileUploadInput.click()"
            >
              <input
                ref="fileUploadInput"
                type="file"
                :accept="ALLOWED_FILE_EXTS.join(',')"
                class="hidden"
                @change="onFileInputSelect"
              />
              <div v-if="fileUploading" class="text-gray-500">
                <svg class="w-8 h-8 mx-auto mb-2 animate-spin text-indigo-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
                  <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                </svg>
                <p class="text-sm">上傳中...</p>
              </div>
              <div v-else>
                <svg xmlns="http://www.w3.org/2000/svg" class="w-10 h-10 mx-auto mb-2 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" />
                </svg>
                <p class="text-sm text-gray-500">拖曳檔案到這裡，或點擊選擇檔案</p>
                <p class="text-xs text-gray-400 mt-1">支援 PDF、DOCX、XLSX、PPTX、TXT、CSV、MD（上限 20MB）</p>
              </div>
            </div>
            <!-- Error message -->
            <p v-if="fileErrorMsg" class="text-sm text-red-500">{{ fileErrorMsg }}</p>
            <!-- File preview -->
            <div v-if="fileUrl" class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg border border-gray-200">
              <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 text-indigo-500 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
              </svg>
              <span class="text-sm text-gray-700 truncate flex-1">{{ fileName }}</span>
              <button
                @click="removeFile"
                class="shrink-0 p-1 rounded text-gray-400 hover:text-red-500 transition-colors"
              >
                <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
                  <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
                </svg>
              </button>
            </div>
          </div>

        </div>

        <!-- Footer -->
        <div class="flex items-center px-6 py-4 border-t border-gray-100">
          <button
            @click="switchToMarkdown"
            type="button"
            class="flex items-center gap-1.5 px-3 py-2 text-sm text-gray-500 hover:text-indigo-600 rounded-lg hover:bg-gray-100 transition-colors"
            title="切換到 Markdown 編輯模式"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
            </svg>
            Markdown 編輯
          </button>
          <div class="flex gap-2 ml-auto">
            <button
              @click="close"
              type="button"
              class="px-4 py-2 text-sm text-gray-600 hover:text-gray-800 rounded-lg hover:bg-gray-100 transition-colors"
            >取消</button>
            <button
              @click="submit"
              type="button"
              class="px-4 py-2 text-sm bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors font-medium disabled:opacity-50"
              :disabled="uploading || fileUploading"
            >{{ editBlock ? '儲存' : '建立' }}</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
