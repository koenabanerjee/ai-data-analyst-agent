import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 120000, // 2 min — AI calls can take time
})

// ── Interceptors ──────────────────────────────────────────────────────────────
api.interceptors.response.use(
  (res) => res,
  (err) => {
    const msg = err.response?.data?.detail || err.response?.data?.error || err.message
    console.error('[API Error]', msg, err.config?.url)
    return Promise.reject(new Error(msg))
  }
)

// ── Dataset APIs ──────────────────────────────────────────────────────────────
export const uploadDataset = (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      if (onProgress) onProgress(Math.round((e.loaded / e.total) * 100))
    },
  })
}

export const listDatasets = () => api.get('/datasets')
export const getDatasetPreview = (id, n = 50) => api.get(`/datasets/${id}/preview?n_rows=${n}`)
export const deleteDataset = (id) => api.delete(`/datasets/${id}`)

// ── Analysis APIs ─────────────────────────────────────────────────────────────
export const runEDA = (id) => api.post(`/analysis/${id}/run-sync`)
export const getEDA = (id) => api.get(`/analysis/${id}/eda`)
export const getVisualizations = (id) => api.get(`/analysis/${id}/visualizations`)
export const getInsights = (id) => api.get(`/analysis/${id}/insights`)

// ── Query API ─────────────────────────────────────────────────────────────────
export const askQuestion = (id, question) => api.post(`/query/${id}`, { question })
export const getQueryHistory = (id) => api.get(`/query/${id}/history`)

// ── Report API ────────────────────────────────────────────────────────────────
export const generateReport = (id) => api.post(`/report/${id}/generate`)
export const getReportDownloadUrl = (id) => `${BASE_URL}/report/${id}/download`
