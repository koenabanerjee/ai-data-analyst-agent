import { create } from 'zustand'

export const useStore = create((set, get) => ({
  // Current active dataset
  currentDataset: null,
  setCurrentDataset: (ds) => set({ currentDataset: ds }),

  // EDA result cache
  edaResults: {},
  setEdaResult: (datasetId, result) =>
    set((s) => ({ edaResults: { ...s.edaResults, [datasetId]: result } })),
  getEdaResult: (datasetId) => get().edaResults[datasetId] || null,

  // Datasets list
  datasets: [],
  setDatasets: (datasets) => set({ datasets }),

  // Loading states
  loading: {},
  setLoading: (key, val) =>
    set((s) => ({ loading: { ...s.loading, [key]: val } })),
  isLoading: (key) => get().loading[key] || false,

  // Toast notifications
  toasts: [],
  addToast: (msg, type = 'info') => {
    const id = Date.now()
    set((s) => ({ toasts: [...s.toasts, { id, msg, type }] }))
    setTimeout(() => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })), 4000)
  },
  removeToast: (id) => set((s) => ({ toasts: s.toasts.filter((t) => t.id !== id) })),
}))
