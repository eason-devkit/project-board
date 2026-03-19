<script setup>
import { ref, computed, reactive, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import interact from 'interactjs'
import { useBlockStore } from '../stores/blocks'
import { getProjects } from '../api/projects'
import { getPages, createPage, updatePage, deletePage } from '../api/blocks'
import BlockCard from '../components/BlockCard.vue'
import BlockEditor from '../components/BlockEditor.vue'
import TemplateDialog from '../components/TemplateDialog.vue'

const props = defineProps({ id: [String, Number] })
const router = useRouter()
const blockStore = useBlockStore()

const project = ref(null)
const showEditor = ref(false)
const editingBlock = ref(null)
const isMobile = ref(window.innerWidth < 768)

// --- Pages ---
const pages = ref([])
const activePageId = ref(null)
const renamingPageId = ref(null)
const renameInput = ref('')

// --- Selection ---
const selectedIds = reactive(new Set())
const marquee = ref(null) // { startX, startY, currentX, currentY }
const blockRefs = new Map()

const GRID = 20
const DEFAULT_W = 280

// --- Template menu ---
const showTemplateMenu = ref(false)
const initialText = ref('')
const showTemplateDialog = ref(false)
const activeTemplateType = ref(null)

const TEMPLATES = [
  { label: '空白', type: 'blank' },
  { label: '連結', type: 'link' },
  { label: '圖片', type: 'image' },
  { label: '清單', type: 'list' },
  { label: '待辦', type: 'todo' },
  { label: '檔案', type: 'file' },
]

function openWithTemplate(tpl) {
  showTemplateMenu.value = false
  if (tpl.type === 'blank') {
    initialText.value = ''
    editingBlock.value = null
    showEditor.value = true
  } else {
    activeTemplateType.value = tpl.type
    editingBlock.value = null
    showTemplateDialog.value = true
  }
}

function onWindowResize() {
  isMobile.value = window.innerWidth < 768
}

// Canvas height
const canvasHeight = computed(() => {
  if (blockStore.blocks.length === 0) return 400
  const maxBottom = Math.max(...blockStore.blocks.map(b => (b.y || 0) + 260))
  return Math.max(400, maxBottom + 80)
})

// Mobile: sort by y then x
const sortedBlocks = computed(() => {
  return [...blockStore.blocks].sort((a, b) => (a.y || 0) - (b.y || 0) || (a.x || 0) - (b.x || 0))
})

// Marquee rect for rendering
const marqueeRect = computed(() => {
  if (!marquee.value) return null
  const { startX, startY, currentX, currentY } = marquee.value
  return {
    left: Math.min(startX, currentX),
    top: Math.min(startY, currentY),
    width: Math.abs(currentX - startX),
    height: Math.abs(currentY - startY),
  }
})

// --- Page management ---

async function loadPages() {
  pages.value = await getPages(Number(props.id))
  if (pages.value.length === 0) {
    const page = await createPage(Number(props.id), { name: '預設' })
    pages.value = [page]
  }
  activePageId.value = pages.value[0].id
}

async function switchPage(pageId) {
  activePageId.value = pageId
  selectedIds.clear()
  await blockStore.load(pageId)
  autoLayoutIfNeeded()
}

async function addPage() {
  const page = await createPage(Number(props.id))
  pages.value.push(page)
  await switchPage(page.id)
}

function startRename(page) {
  renamingPageId.value = page.id
  renameInput.value = page.name
}

async function finishRename(page) {
  const name = renameInput.value.trim()
  if (name && name !== page.name) {
    await updatePage(page.id, { name })
    page.name = name
  }
  renamingPageId.value = null
}

async function removePage(page) {
  if (pages.value.length <= 1) return
  if (!confirm(`確定要刪除分頁「${page.name}」及其所有區塊嗎？`)) return
  await deletePage(page.id)
  pages.value = pages.value.filter(p => p.id !== page.id)
  if (activePageId.value === page.id) {
    await switchPage(pages.value[0].id)
  }
}

// --- Auto layout ---

function autoLayoutIfNeeded() {
  const blocks = blockStore.blocks
  if (blocks.length === 0) return
  const allAtOrigin = blocks.every(b => !b.x && !b.y)
  if (!allAtOrigin) return

  const cols = Math.min(3, blocks.length)
  blocks.forEach((b, i) => {
    const col = i % cols
    const row = Math.floor(i / cols)
    b.x = col * (DEFAULT_W + GRID) + GRID
    b.y = row * (240 + GRID) + GRID
    b.w = b.w || DEFAULT_W
    blockStore.updateLayout(b.id, { x: b.x, y: b.y, w: b.w, h: b.h || 0 })
  })
}

function getNewBlockPosition() {
  const blocks = blockStore.blocks
  if (blocks.length === 0) return { x: GRID, y: GRID }
  const maxY = Math.max(...blocks.map(b => (b.y || 0) + 260))
  return { x: GRID, y: Math.round(maxY / GRID) * GRID }
}

// --- Project & Block CRUD ---

async function loadProject() {
  const projects = await getProjects()
  project.value = projects.find(p => p.id === Number(props.id))
  if (!project.value) {
    router.replace({ name: 'home' })
    return
  }
  await loadPages()
  await blockStore.load(activePageId.value)
  autoLayoutIfNeeded()
}

function openCreate() {
  showTemplateMenu.value = !showTemplateMenu.value
}

function openEdit(block) {
  showTemplateMenu.value = false
  const structuredTypes = ['link', 'image', 'list', 'todo', 'file']
  if (block.template_type && structuredTypes.includes(block.template_type)) {
    // Open structured template dialog for editing
    activeTemplateType.value = block.template_type
    editingBlock.value = block
    showTemplateDialog.value = true
  } else {
    // Open markdown editor for blank/null template_type
    activeTemplateType.value = null
    initialText.value = ''
    editingBlock.value = block
    showEditor.value = true
  }
}

// --- Switch between structured and markdown editing ---
function onSwitchToMarkdown(md) {
  // TemplateDialog → BlockEditor: carry over template_type and current markdown
  initialText.value = md
  showEditor.value = true
}

function onSwitchToStructured(md) {
  // BlockEditor → TemplateDialog: reopen structured dialog
  // editingBlock is already set; update its content temporarily for the dialog to parse
  if (editingBlock.value) {
    editingBlock.value = { ...editingBlock.value, content: { text: md } }
  }
  showTemplateDialog.value = true
}

async function handleSave(data) {
  if (editingBlock.value) {
    await blockStore.update(editingBlock.value.id, data)
  } else {
    const pos = getNewBlockPosition()
    await blockStore.create({ ...data, x: pos.x, y: pos.y, w: DEFAULT_W })
  }
}

async function handleDelete(block) {
  if (confirm('確定要刪除這個區塊嗎？')) {
    selectedIds.delete(block.id)
    await blockStore.remove(block.id)
  }
}

async function handleToggleCheck({ block, text }) {
  await blockStore.update(block.id, { content: { text } })
}

// --- Marquee selection ---

function onCanvasMouseDown(e) {
  // Only start marquee on empty canvas area
  if (e.target.closest('.block-item')) return
  if (e.button !== 0) return

  const canvas = e.currentTarget
  const rect = canvas.getBoundingClientRect()
  const x = e.clientX - rect.left + canvas.scrollLeft
  const y = e.clientY - rect.top + canvas.scrollTop

  if (!e.ctrlKey && !e.metaKey) {
    selectedIds.clear()
  }

  const prevSelected = new Set(selectedIds)
  marquee.value = { startX: x, startY: y, currentX: x, currentY: y }
  interacting.value = true

  function updateMarqueeSelection() {
    const mr = marqueeRect.value
    if (!mr) return
    // Reset to pre-marquee state, then add intersecting blocks
    selectedIds.clear()
    for (const id of prevSelected) selectedIds.add(id)
    if (mr.width > 3 || mr.height > 3) {
      for (const block of blockStore.blocks) {
        const bx = block.x || 0
        const by = block.y || 0
        const bw = block.w || DEFAULT_W
        const bh = blockRefs.get(block.id)?.offsetHeight || 200
        if (bx < mr.left + mr.width && bx + bw > mr.left &&
            by < mr.top + mr.height && by + bh > mr.top) {
          selectedIds.add(block.id)
        }
      }
    }
  }

  function onMouseMove(ev) {
    const cx = ev.clientX - rect.left + canvas.scrollLeft
    const cy = ev.clientY - rect.top + canvas.scrollTop
    marquee.value = { ...marquee.value, currentX: cx, currentY: cy }
    updateMarqueeSelection()
  }

  function onMouseUp() {
    marquee.value = null
    interacting.value = false
    window.removeEventListener('mousemove', onMouseMove)
    window.removeEventListener('mouseup', onMouseUp)
  }

  window.addEventListener('mousemove', onMouseMove)
  window.addEventListener('mouseup', onMouseUp)
}

function onBlockClick(e, block) {
  if (e.ctrlKey || e.metaKey) {
    e.preventDefault()
    if (selectedIds.has(block.id)) {
      selectedIds.delete(block.id)
    } else {
      selectedIds.add(block.id)
    }
  }
}

// --- interact.js ---

const interacting = ref(false)

function setupInteract(el, block) {
  interact(el)
    .on('dragstart resizestart', () => { interacting.value = true })
    .on('dragend resizeend', () => { interacting.value = false })
    .draggable({
      ignoreFrom: '.block-content, button',
      modifiers: [
        interact.modifiers.snap({
          targets: [interact.snappers.grid({ x: GRID, y: GRID })],
          range: Infinity,
          relativePoint: { x: 0, y: 0 },
          offset: 'startCoords',
        }),
      ],
      listeners: {
        move(event) {
          // Track raw accumulated position via data attributes (for snap accuracy)
          const prevX = parseFloat(el.getAttribute('data-x'))
          const prevY = parseFloat(el.getAttribute('data-y'))
          const x = (isNaN(prevX) ? (block.x || 0) : prevX) + event.dx
          const y = (isNaN(prevY) ? (block.y || 0) : prevY) + event.dy
          const nx = Math.max(0, x)
          const ny = Math.max(0, y)
          el.setAttribute('data-x', nx)
          el.setAttribute('data-y', ny)

          // Update dragged block reactively (Vue style binding handles DOM)
          block.x = nx
          block.y = ny

          // Move other selected blocks together
          if (selectedIds.has(block.id) && selectedIds.size > 1) {
            for (const otherId of selectedIds) {
              if (otherId === block.id) continue
              const other = blockStore.blocks.find(b => b.id === otherId)
              if (other) {
                other.x = Math.max(0, (other.x || 0) + event.dx)
                other.y = Math.max(0, (other.y || 0) + event.dy)
              }
            }
          }
        },
        end() {
          el.removeAttribute('data-x')
          el.removeAttribute('data-y')

          // Save all moved blocks
          if (selectedIds.has(block.id) && selectedIds.size > 1) {
            for (const id of selectedIds) {
              const b = blockStore.blocks.find(bl => bl.id === id)
              if (b) blockStore.updateLayout(b.id, { x: b.x, y: b.y, w: b.w, h: b.h || 0 })
            }
          } else {
            blockStore.updateLayout(block.id, { x: block.x, y: block.y, w: block.w, h: block.h || 0 })
          }
        },
      },
    })
    .resizable({
      edges: { right: true, bottom: true, left: false, top: false },
      modifiers: [
        interact.modifiers.snap({
          targets: [interact.snappers.grid({ x: GRID, y: GRID })],
          offset: 'startCoords',
        }),
        interact.modifiers.restrictSize({
          min: { width: 120, height: 50 },
        }),
      ],
      listeners: {
        move(event) {
          el.style.width = event.rect.width + 'px'
          el.style.height = event.rect.height + 'px'
        },
        end(event) {
          block.w = event.rect.width
          block.h = event.rect.height
          blockStore.updateLayout(block.id, { x: block.x, y: block.y, w: block.w, h: block.h })
        },
      },
    })
}

function setBlockRef(id, el) {
  if (el) blockRefs.set(id, el)
  else blockRefs.delete(id)
}

const vInteract = {
  mounted(el, binding) {
    if (!isMobile.value) {
      setupInteract(el, binding.value)
    }
  },
  unmounted(el) {
    try {
      interact(el).unset()
    } catch {
      // already unset
    }
  },
}

function onDocumentClick(e) {
  if (showTemplateMenu.value && !e.target.closest('.template-menu-wrapper')) {
    showTemplateMenu.value = false
  }
}

onMounted(() => {
  window.addEventListener('resize', onWindowResize)
  document.addEventListener('click', onDocumentClick, true)
  loadProject()
})

onUnmounted(() => {
  window.removeEventListener('resize', onWindowResize)
  document.removeEventListener('click', onDocumentClick, true)
})
</script>

<template>
  <div class="min-h-screen bg-gray-50 flex flex-col">
    <!-- Header -->
    <header class="bg-white border-b border-gray-200 sticky top-0 z-10">
      <div class="max-w-screen-2xl mx-auto px-6 py-3 flex items-center gap-4">
        <button
          @click="router.push({ name: 'home' })"
          class="shrink-0 p-1.5 rounded-lg hover:bg-gray-100 text-gray-500 hover:text-gray-700 transition-colors"
          title="返回"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M9.707 16.707a1 1 0 01-1.414 0l-6-6a1 1 0 010-1.414l6-6a1 1 0 011.414 1.414L5.414 9H17a1 1 0 110 2H5.414l4.293 4.293a1 1 0 010 1.414z" clip-rule="evenodd" />
          </svg>
        </button>

        <div v-if="project" class="flex items-center gap-3 min-w-0">
          <h1 class="text-lg font-bold text-gray-900 truncate">{{ project.name }}</h1>
          <div v-if="project.tags.length" class="flex gap-1 shrink-0">
            <span
              v-for="tag in project.tags"
              :key="tag.id"
              class="inline-block px-2 py-0.5 rounded-full text-xs bg-indigo-50 text-indigo-600"
            >
              {{ tag.name }}
            </span>
          </div>
        </div>

        <div class="ml-auto shrink-0 relative template-menu-wrapper">
          <button
            @click="openCreate"
            class="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-600 text-white rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
            </svg>
            新增區塊
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3 ml-0.5" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z" clip-rule="evenodd" />
            </svg>
          </button>
          <div
            v-if="showTemplateMenu"
            class="absolute right-0 top-full mt-1 bg-white rounded-xl shadow-lg border border-gray-200 py-1.5 z-30 min-w-[160px]"
          >
            <button
              v-for="tpl in TEMPLATES"
              :key="tpl.label"
              @click="openWithTemplate(tpl)"
              class="w-full text-left px-4 py-2.5 text-sm text-gray-700 hover:bg-indigo-50 hover:text-indigo-700 transition-colors flex items-center gap-2.5"
            >
              <!-- Blank -->
              <svg v-if="tpl.type === 'blank'" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
              <!-- Link -->
              <svg v-else-if="tpl.type === 'link'" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" /></svg>
              <!-- Image -->
              <svg v-else-if="tpl.type === 'image'" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
              <!-- List -->
              <svg v-else-if="tpl.type === 'list'" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 10h16M4 14h16M4 18h16" /></svg>
              <!-- Todo -->
              <svg v-else-if="tpl.type === 'todo'" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" /></svg>
              <!-- File -->
              <svg v-else-if="tpl.type === 'file'" xmlns="http://www.w3.org/2000/svg" class="w-4 h-4 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15.172 7l-6.586 6.586a2 2 0 102.828 2.828l6.414-6.586a4 4 0 00-5.656-5.656l-6.415 6.585a6 6 0 108.486 8.486L20.5 13" /></svg>
              {{ tpl.label }}
            </button>
          </div>
        </div>
      </div>
      <p v-if="project?.description" class="max-w-screen-2xl mx-auto px-6 pb-3 text-sm text-gray-500">
        {{ project.description }}
      </p>

      <!-- Tab bar -->
      <div class="max-w-screen-2xl mx-auto px-6 flex items-center gap-0.5 overflow-x-auto" v-if="pages.length">
        <div
          v-for="page in pages"
          :key="page.id"
          class="group flex items-center gap-1 shrink-0"
        >
          <!-- Rename input -->
          <div v-if="renamingPageId === page.id" class="flex items-center">
            <input
              v-model="renameInput"
              @keydown.enter="finishRename(page)"
              @blur="finishRename(page)"
              @keydown.escape="renamingPageId = null"
              ref="renameInputEl"
              class="px-3 py-1.5 text-sm border border-indigo-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-indigo-400 w-28"
              autofocus
            />
          </div>
          <!-- Tab button -->
          <button
            v-else
            @click="switchPage(page.id)"
            @dblclick.prevent="startRename(page)"
            class="px-3 py-2 text-sm whitespace-nowrap border-b-2 transition-colors"
            :class="activePageId === page.id
              ? 'border-indigo-600 text-indigo-600 font-medium'
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'"
          >
            {{ page.name }}
          </button>
          <!-- Delete page button -->
          <button
            v-if="pages.length > 1 && renamingPageId !== page.id"
            @click.stop="removePage(page)"
            class="p-0.5 rounded text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all"
            title="刪除分頁"
          >
            <svg xmlns="http://www.w3.org/2000/svg" class="w-3 h-3" viewBox="0 0 20 20" fill="currentColor">
              <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd" />
            </svg>
          </button>
        </div>
        <!-- Add page button -->
        <button
          @click="addPage"
          class="shrink-0 p-1.5 text-gray-400 hover:text-indigo-600 hover:bg-indigo-50 rounded-lg transition-colors ml-1"
          title="新增分頁"
        >
          <svg xmlns="http://www.w3.org/2000/svg" class="w-4 h-4" viewBox="0 0 20 20" fill="currentColor">
            <path fill-rule="evenodd" d="M10 3a1 1 0 011 1v5h5a1 1 0 110 2h-5v5a1 1 0 11-2 0v-5H4a1 1 0 110-2h5V4a1 1 0 011-1z" clip-rule="evenodd" />
          </svg>
        </button>
      </div>
    </header>

    <!-- Board content -->
    <main class="px-6 py-6 flex-1 flex flex-col">
      <!-- Empty state -->
      <div v-if="blockStore.blocks.length === 0" class="text-center py-20 text-gray-400">
        <svg xmlns="http://www.w3.org/2000/svg" class="w-12 h-12 mx-auto mb-3 opacity-40" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
        <p class="text-sm">還沒有任何區塊，點擊上方「新增區塊」開始吧！</p>
      </div>

      <!-- Desktop: Free canvas -->
      <div
        v-else-if="!isMobile"
        class="board-canvas relative flex-1"
        :class="{ 'select-none': interacting }"
        :style="{
          minHeight: canvasHeight + 'px',
          backgroundImage: 'radial-gradient(circle, #d1d5db 1px, transparent 1px)',
          backgroundSize: GRID + 'px ' + GRID + 'px',
        }"
        @mousedown="onCanvasMouseDown"
      >
        <div
          v-for="block in blockStore.blocks"
          :key="block.id"
          :ref="el => setBlockRef(block.id, el)"
          v-interact="block"
          class="block-item absolute touch-none group/block cursor-grab active:cursor-grabbing"
          :class="{ 'ring-2 ring-indigo-400/60 ring-offset-2 rounded-2xl': selectedIds.has(block.id) }"
          :style="{
            left: (block.x || 0) + 'px',
            top: (block.y || 0) + 'px',
            width: (block.w || DEFAULT_W) + 'px',
            height: block.h > 0 ? block.h + 'px' : undefined,
          }"
          @click="onBlockClick($event, block)"
        >
          <BlockCard
            :block="block"
            @edit="openEdit"
            @delete="handleDelete"
            @toggle-check="handleToggleCheck"
          />
          <!-- Resize handle (bottom-right corner) -->
          <div class="absolute bottom-0 right-0 w-4 h-4 opacity-0 group-hover/block:opacity-60 transition-opacity cursor-se-resize">
            <svg class="w-3 h-3 text-gray-400 absolute bottom-0.5 right-0.5" viewBox="0 0 6 6" fill="currentColor">
              <circle cx="5" cy="1" r="0.8"/><circle cx="5" cy="5" r="0.8"/><circle cx="1" cy="5" r="0.8"/>
            </svg>
          </div>
        </div>

        <!-- Marquee selection rectangle -->
        <div
          v-if="marqueeRect"
          class="absolute border border-indigo-300/60 bg-indigo-50/20 rounded pointer-events-none z-20"
          :style="{
            left: marqueeRect.left + 'px',
            top: marqueeRect.top + 'px',
            width: marqueeRect.width + 'px',
            height: marqueeRect.height + 'px',
          }"
        />
      </div>

      <!-- Mobile: Simple list -->
      <div v-else class="max-w-lg mx-auto flex flex-col gap-4">
        <BlockCard
          v-for="block in sortedBlocks"
          :key="block.id"
          :block="block"
          @edit="openEdit"
          @delete="handleDelete"
          @toggle-check="handleToggleCheck"
        />
      </div>
    </main>

    <BlockEditor
      v-model="showEditor"
      :block="editingBlock"
      :initialText="initialText"
      :templateType="activeTemplateType"
      @save="handleSave"
      @switch-to-structured="onSwitchToStructured"
    />

    <TemplateDialog
      v-model="showTemplateDialog"
      :templateType="activeTemplateType"
      :editBlock="editingBlock"
      @save="handleSave"
      @switch-to-markdown="onSwitchToMarkdown"
    />
  </div>
</template>
