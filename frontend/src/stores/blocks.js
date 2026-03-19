import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as api from '../api/blocks'

export const useBlockStore = defineStore('blocks', () => {
  const blocks = ref([])
  const pageId = ref(null)

  async function load(pid) {
    pageId.value = pid
    blocks.value = await api.getPageBlocks(pid)
  }

  async function create(data) {
    const block = await api.createPageBlock(pageId.value, data)
    blocks.value.push(block)
  }

  async function update(blockId, data) {
    const updated = await api.updateBlock(blockId, data)
    const existing = blocks.value.find(b => b.id === blockId)
    if (existing) Object.assign(existing, updated)
  }

  async function remove(blockId) {
    await api.deleteBlock(blockId)
    blocks.value = blocks.value.filter(b => b.id !== blockId)
  }

  async function updateLayout(blockId, layout) {
    const block = blocks.value.find(b => b.id === blockId)
    if (block) {
      block.x = layout.x
      block.y = layout.y
      block.w = layout.w
      if (layout.h !== undefined) block.h = layout.h
    }
    await api.updateBlockLayout(blockId, layout)
  }

  return { blocks, pageId, load, create, update, remove, updateLayout }
})
