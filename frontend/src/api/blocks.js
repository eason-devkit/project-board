import { api } from './projects'

// Page-level block operations
export const getPageBlocks = (pageId) =>
  api.get(`/pages/${pageId}/blocks`).then(r => r.data)

export const createPageBlock = (pageId, data) =>
  api.post(`/pages/${pageId}/blocks`, data).then(r => r.data)

// Legacy project-level (kept for compat)
export const getBlocks = (projectId) =>
  api.get(`/projects/${projectId}/blocks`).then(r => r.data)

export const createBlock = (projectId, data) =>
  api.post(`/projects/${projectId}/blocks`, data).then(r => r.data)

export const updateBlock = (blockId, data) =>
  api.put(`/blocks/${blockId}`, data).then(r => r.data)

export const deleteBlock = (blockId) =>
  api.delete(`/blocks/${blockId}`)

export const updateBlockLayout = (blockId, layout) =>
  api.put(`/blocks/${blockId}/layout`, layout).then(r => r.data)

export const reorderBlocks = (projectId, items) =>
  api.put(`/projects/${projectId}/blocks/reorder`, { items })

export const uploadImage = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload', form).then(r => r.data)
}

export const uploadFile = async (file) => {
  const form = new FormData()
  form.append('file', file)
  try {
    const r = await api.post('/upload', form)
    return r.data
  } catch (err) {
    if (err.response) {
      const detail = err.response.data?.detail
      throw new Error(detail || `上傳失敗（HTTP ${err.response.status}）`)
    }
    throw new Error('網路連線異常，請檢查後重試')
  }
}

// Page operations
export const getPages = (projectId) =>
  api.get(`/projects/${projectId}/pages`).then(r => r.data)

export const createPage = (projectId, data = {}) =>
  api.post(`/projects/${projectId}/pages`, data).then(r => r.data)

export const updatePage = (pageId, data) =>
  api.put(`/pages/${pageId}`, data).then(r => r.data)

export const deletePage = (pageId) =>
  api.delete(`/pages/${pageId}`)
