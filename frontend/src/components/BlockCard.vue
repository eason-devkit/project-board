<script setup>
import { computed, ref, watch } from 'vue'
import { marked } from 'marked'

const props = defineProps({ block: Object })
const emit = defineEmits(['edit', 'delete', 'toggle-check'])

// --- Link card detection ---
const isLinkCard = computed(() => props.block.template_type === 'link')

// --- File card detection ---
const isFileCard = computed(() => props.block.template_type === 'file')

const fileData = computed(() => {
  if (!isFileCard.value) return null
  const text = props.block.content?.text || ''
  const m = text.match(/^\[([^\]]*)\]\(([^)]*)\)/)
  if (!m) return null
  return { name: m[1], url: m[2] }
})

const fileExtension = computed(() => {
  if (!fileData.value) return ''
  const name = fileData.value.name
  const dot = name.lastIndexOf('.')
  return dot >= 0 ? name.slice(dot + 1).toUpperCase() : ''
})

const fileMissing = ref(false)

async function checkFileExists(url) {
  try {
    const res = await fetch(url, { method: 'HEAD' })
    fileMissing.value = !res.ok
  } catch {
    fileMissing.value = true
  }
}

// Check file existence when file card is detected
watch(() => fileData.value?.url, (url) => {
  if (url) {
    fileMissing.value = false
    checkFileExists(url)
  }
}, { immediate: true })

const linkData = computed(() => {
  if (!isLinkCard.value) return null
  const text = props.block.content?.text || ''
  const m = text.match(/^\[([^\]]*)\]\(([^)]*)\)/)
  if (!m) return null
  const rest = text.slice(m[0].length).replace(/^\n+/, '')
  return { title: m[1], url: m[2], description: rest }
})

function linkDomain(url) {
  try {
    return new URL(url).hostname.replace(/^www\./, '')
  } catch {
    return url
  }
}

function faviconUrl(url) {
  try {
    const origin = new URL(url).origin
    return `${origin}/favicon.ico`
  } catch {
    return null
  }
}

// Custom renderer to enable checkboxes
const renderer = new marked.Renderer()
renderer.listitem = function (token) {
  // In marked v17, token is a full token object; render inner tokens to HTML
  const rendered = this.parser.parseInline(token.tokens)
  if (token.task) {
    const checkbox = `<input type="checkbox" ${token.checked ? 'checked' : ''} class="md-checkbox rounded border-gray-300 text-indigo-600 focus:ring-indigo-400 w-4 h-4 cursor-pointer mr-2 align-middle" />`
    const cleanText = rendered.replace(/^<input.*?>\s*/, '')
    return `<li class="task-list-item flex items-center gap-1" style="list-style:none">${checkbox}<span${token.checked ? ' class="line-through text-gray-400"' : ''}>${cleanText}</span></li>\n`
  }
  return `<li>${rendered}</li>\n`
}

marked.setOptions({
  breaks: true,
  gfm: true,
  renderer,
})

const renderedHtml = computed(() => {
  const text = props.block.content?.text
  if (!text) return ''
  return marked.parse(text)
})

function onContentClick(e) {
  const checkbox = e.target.closest('input.md-checkbox')
  if (!checkbox) return

  e.preventDefault()
  e.stopPropagation()

  const text = props.block.content?.text
  if (!text) return

  // Find all checkbox lines and determine which one was clicked
  const listItems = e.currentTarget.querySelectorAll('input.md-checkbox')
  const clickedIndex = Array.from(listItems).indexOf(checkbox)
  if (clickedIndex === -1) return

  // Toggle the corresponding line in markdown source
  const lines = text.split('\n')
  let checkboxCount = 0
  for (let i = 0; i < lines.length; i++) {
    const unchecked = /^(\s*- )\[ \](.*)$/
    const checked = /^(\s*- )\[x\](.*)$/i
    if (unchecked.test(lines[i]) || checked.test(lines[i])) {
      if (checkboxCount === clickedIndex) {
        if (unchecked.test(lines[i])) {
          lines[i] = lines[i].replace(unchecked, '$1[x]$2')
        } else {
          lines[i] = lines[i].replace(checked, '$1[ ]$2')
        }
        break
      }
      checkboxCount++
    }
  }

  emit('toggle-check', { block: props.block, text: lines.join('\n') })
}
</script>

<template>
  <div class="bg-amber-50 border-amber-200 rounded-xl border p-4 flex flex-col gap-2 hover:shadow-md transition-shadow group h-full overflow-auto">
    <!-- Header row -->
    <div class="flex items-center justify-between">
      <div class="flex items-center gap-1.5">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3 text-gray-300 shrink-0" viewBox="0 0 16 16" fill="currentColor">
          <circle cx="4" cy="3" r="1.5"/><circle cx="4" cy="8" r="1.5"/><circle cx="4" cy="13" r="1.5"/>
          <circle cx="10" cy="3" r="1.5"/><circle cx="10" cy="8" r="1.5"/><circle cx="10" cy="13" r="1.5"/>
        </svg>
      </div>
      <div class="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
        <button
          @click="emit('edit', block)"
          class="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-gray-600 transition-colors"
          title="編輯"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path d="M13.586 3.586a2 2 0 112.828 2.828l-.793.793-2.828-2.828.793-.793zM11.379 5.793L3 14.172V17h2.828l8.38-8.379-2.83-2.828z" />
          </svg>
        </button>
        <button
          @click="emit('delete', block)"
          class="p-1 rounded hover:bg-gray-100 text-gray-400 hover:text-red-500 transition-colors"
          title="刪除"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-3.5 h-3.5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </div>

    <!-- Content area -->
    <!-- Link card rendering -->
    <a
      v-if="isLinkCard && linkData"
      :href="linkData.url"
      target="_blank"
      rel="noopener noreferrer"
      class="block-content link-card block rounded-lg border border-gray-200 bg-white hover:border-indigo-300 hover:shadow transition-all overflow-hidden no-underline cursor-pointer"
      @click.stop
    >
      <div class="px-4 py-3">
        <div class="flex items-start gap-3">
          <img
            :src="faviconUrl(linkData.url)"
            class="w-5 h-5 mt-0.5 rounded shrink-0"
            @error="$event.target.style.display='none'"
          />
          <div class="min-w-0 flex-1">
            <div class="text-sm font-medium text-gray-900 truncate">{{ linkData.title }}</div>
            <div class="text-xs text-indigo-500 truncate mt-0.5">{{ linkDomain(linkData.url) }}</div>
          </div>
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-300 shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
          </svg>
        </div>
        <p v-if="linkData.description" class="text-xs text-gray-500 mt-2 line-clamp-2">{{ linkData.description }}</p>
      </div>
      <div class="h-1 bg-gradient-to-r from-indigo-400 to-purple-400"></div>
    </a>
    <!-- File card rendering -->
    <div v-else-if="isFileCard && fileData" class="block-content file-card rounded-lg border border-gray-200 bg-white p-4">
      <div v-if="fileMissing" class="flex items-center gap-3 text-gray-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-8 h-8 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
        <div class="min-w-0 flex-1">
          <div class="text-sm text-red-400 font-medium">檔案不存在</div>
          <div class="text-xs text-gray-400 truncate mt-0.5">{{ fileData.name }}</div>
        </div>
      </div>
      <a
        v-else
        :href="fileData.url"
        :download="fileData.name"
        class="flex items-center gap-3 no-underline hover:bg-gray-50 -m-2 p-2 rounded-lg transition-colors"
        @click.stop
      >
        <div class="w-10 h-10 rounded-lg bg-indigo-50 border border-indigo-100 flex items-center justify-center shrink-0">
          <span class="text-[10px] font-bold text-indigo-500 leading-none">{{ fileExtension }}</span>
        </div>
        <div class="min-w-0 flex-1">
          <div class="text-sm font-medium text-gray-900 truncate">{{ fileData.name }}</div>
          <div class="text-xs text-gray-400 mt-0.5">點擊下載</div>
        </div>
        <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-300 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
        </svg>
      </a>
    </div>
    <!-- Default markdown rendering -->
    <div v-else class="block-content cursor-text" @click="onContentClick">
      <div class="text-sm text-gray-700 leading-relaxed prose prose-sm max-w-none block-prose" v-html="renderedHtml"></div>
    </div>
  </div>
</template>

<style scoped>
.block-prose :deep(a) {
  color: #4f46e5;
  text-decoration: underline;
  text-underline-offset: 2px;
}
.block-prose :deep(a:hover) {
  color: #3730a3;
}
.link-card {
  text-decoration: none !important;
}
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
