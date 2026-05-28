import { useState, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Upload, FileText, CheckCircle, AlertCircle,
  X, ArrowRight, Database, Loader2
} from 'lucide-react'
import { uploadDataset, runEDA } from '../utils/api'
import { useStore } from '../store'
import { ProgressBar, StatCard } from '../components/ui'
import clsx from 'clsx'

const MAX_MB = 50
const ACCEPTED = { 'text/csv': ['.csv'], 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'] }

export default function UploadPage() {
  const navigate = useNavigate()
  const setCurrentDataset = useStore((s) => s.setCurrentDataset)
  const addToast = useStore((s) => s.addToast)

  const [file, setFile] = useState(null)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [status, setStatus] = useState('idle') // idle | uploading | processing | done | error
  const [error, setError] = useState('')
  const [dataset, setDataset] = useState(null)

  const onDrop = useCallback((accepted, rejected) => {
    if (rejected.length > 0) {
      setError(`File rejected: ${rejected[0].errors[0].message}`)
      return
    }
    if (accepted.length > 0) {
      const f = accepted[0]
      if (f.size > MAX_MB * 1024 * 1024) {
        setError(`File too large. Maximum size is ${MAX_MB} MB.`)
        return
      }
      setFile(f)
      setError('')
      setStatus('idle')
    }
  }, [])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: ACCEPTED,
    maxFiles: 1,
    multiple: false,
  })

  const handleUpload = async () => {
    if (!file) return
    setStatus('uploading')
    setError('')
    setUploadProgress(0)

    try {
      const { data: ds } = await uploadDataset(file, setUploadProgress)
      setDataset(ds)
      setCurrentDataset(ds)
      addToast(`"${ds.original_filename}" uploaded successfully.`, 'success')

      // Auto-trigger EDA
      setStatus('processing')
      await runEDA(ds.id)
      addToast('Analysis complete! Redirecting to dashboard...', 'success')
      setStatus('done')

      setTimeout(() => navigate('/overview'), 1200)
    } catch (err) {
      setStatus('error')
      setError(err.message || 'Upload failed. Please try again.')
      addToast(err.message || 'Upload failed', 'error')
    }
  }

  const reset = () => {
    setFile(null)
    setStatus('idle')
    setError('')
    setDataset(null)
    setUploadProgress(0)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="page-header">
        <h1 className="page-title">Upload Dataset</h1>
        <p className="page-subtitle">
          Drag and drop a CSV or XLSX file. The AI pipeline starts automatically.
        </p>
      </div>

      {/* Drop zone */}
      <AnimatePresence mode="wait">
        {status === 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0 }}
          >
            <div
              {...getRootProps()}
              className={clsx(
                'relative border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer transition-all duration-300',
                isDragActive
                  ? 'border-brand-500 bg-brand-500/10'
                  : file
                  ? 'border-emerald-500/50 bg-emerald-500/5'
                  : 'border-surface-700 hover:border-surface-500 bg-surface-900/50'
              )}
            >
              <input {...getInputProps()} />

              {file ? (
                <div className="space-y-3">
                  <div className="w-14 h-14 rounded-2xl bg-emerald-500/10 flex items-center justify-center mx-auto">
                    <FileText size={24} className="text-emerald-400" />
                  </div>
                  <p className="font-semibold text-white">{file.name}</p>
                  <p className="text-surface-400 text-sm">
                    {(file.size / 1024 / 1024).toFixed(2)} MB · {file.type || 'text/csv'}
                  </p>
                  <button
                    onClick={(e) => { e.stopPropagation(); reset() }}
                    className="text-surface-500 hover:text-red-400 transition-colors text-xs flex items-center gap-1 mx-auto"
                  >
                    <X size={12} /> Remove
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="w-16 h-16 rounded-2xl bg-brand-500/10 flex items-center justify-center mx-auto">
                    <Upload size={28} className={isDragActive ? 'text-brand-400 animate-bounce' : 'text-brand-500'} />
                  </div>
                  <div>
                    <p className="font-semibold text-white text-lg mb-1">
                      {isDragActive ? 'Drop your file here' : 'Drag & drop your dataset'}
                    </p>
                    <p className="text-surface-400 text-sm">
                      or <span className="text-brand-400 underline">browse files</span>
                    </p>
                  </div>
                  <div className="flex items-center justify-center gap-4 text-xs text-surface-500">
                    <span className="badge bg-surface-800 border-surface-700 text-surface-400">CSV</span>
                    <span className="badge bg-surface-800 border-surface-700 text-surface-400">XLSX</span>
                    <span>Max {MAX_MB} MB</span>
                  </div>
                </div>
              )}
            </div>
          </motion.div>
        )}

        {/* Uploading / Processing */}
        {(status === 'uploading' || status === 'processing') && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="card space-y-5 text-center"
          >
            <div className="w-16 h-16 rounded-2xl bg-brand-500/10 flex items-center justify-center mx-auto">
              <Loader2 size={28} className="text-brand-400 animate-spin" />
            </div>
            <div>
              <p className="font-semibold text-white text-lg mb-1">
                {status === 'uploading' ? 'Uploading file...' : 'Running AI Analysis Pipeline...'}
              </p>
              <p className="text-surface-400 text-sm">
                {status === 'uploading'
                  ? 'Transferring your dataset to the server'
                  : '8 agents are analysing your data — schema, EDA, outliers, correlations, insights...'}
              </p>
            </div>
            {status === 'uploading' && (
              <div className="space-y-2">
                <ProgressBar value={uploadProgress} max={100} color="brand" />
                <p className="text-xs text-surface-500">{uploadProgress}%</p>
              </div>
            )}
            {status === 'processing' && (
              <div className="grid grid-cols-4 gap-2">
                {['Schema', 'EDA', 'Outliers', 'Insights'].map((s, i) => (
                  <div key={s} className="text-center">
                    <div className="w-8 h-8 rounded-full bg-brand-500/20 border border-brand-500/40 flex items-center justify-center mx-auto mb-1 animate-pulse" style={{ animationDelay: `${i * 0.2}s` }}>
                      <div className="w-2 h-2 rounded-full bg-brand-400" />
                    </div>
                    <p className="text-xs text-surface-500">{s}</p>
                  </div>
                ))}
              </div>
            )}
          </motion.div>
        )}

        {/* Done */}
        {status === 'done' && dataset && (
          <motion.div
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            className="card space-y-5 text-center border-emerald-500/30"
          >
            <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 flex items-center justify-center mx-auto">
              <CheckCircle size={28} className="text-emerald-400" />
            </div>
            <div>
              <p className="font-semibold text-white text-lg mb-1">Analysis Complete!</p>
              <p className="text-surface-400 text-sm">Redirecting to your dashboard...</p>
            </div>
            <div className="grid grid-cols-3 gap-4 mt-2">
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{dataset.row_count?.toLocaleString()}</p>
                <p className="text-xs text-surface-500">Rows</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-white">{dataset.column_count}</p>
                <p className="text-xs text-surface-500">Columns</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-emerald-400">✓</p>
                <p className="text-xs text-surface-500">Ready</p>
              </div>
            </div>
          </motion.div>
        )}

        {/* Error */}
        {status === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="card border-red-500/30 space-y-4"
          >
            <div className="flex items-start gap-3">
              <AlertCircle size={20} className="text-red-400 flex-shrink-0 mt-0.5" />
              <div>
                <p className="font-semibold text-white">Upload failed</p>
                <p className="text-surface-400 text-sm mt-1">{error}</p>
              </div>
            </div>
            <button onClick={reset} className="btn-secondary text-sm">Try Again</button>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error below dropzone */}
      {error && status === 'idle' && (
        <p className="text-red-400 text-sm flex items-center gap-2">
          <AlertCircle size={14} /> {error}
        </p>
      )}

      {/* Upload button */}
      {file && status === 'idle' && (
        <motion.button
          initial={{ opacity: 0, y: 8 }}
          animate={{ opacity: 1, y: 0 }}
          onClick={handleUpload}
          className="btn-primary w-full flex items-center justify-center gap-2 py-3"
        >
          <Database size={16} />
          Analyse Dataset
          <ArrowRight size={16} />
        </motion.button>
      )}

      {/* Info */}
      {status === 'idle' && !file && (
        <div className="card bg-surface-900/30 border-surface-800">
          <p className="text-xs text-surface-500 font-medium mb-3 uppercase tracking-wider">What happens after upload</p>
          <ol className="space-y-2">
            {[
              'Schema Agent detects column types and data semantics',
              'EDA Agent computes full descriptive statistics',
              'Missing Value Agent recommends imputation strategies',
              'Outlier Agent runs IQR and Z-score detection',
              'Correlation Agent builds Pearson correlation matrix',
              'Insight Agent generates AI-powered analyst narrative',
              'Visualization Agent auto-selects and builds charts',
              'Report Agent assembles all findings for PDF export',
            ].map((step, i) => (
              <li key={i} className="flex items-start gap-3 text-xs text-surface-400">
                <span className="w-5 h-5 rounded-full bg-brand-500/20 text-brand-400 text-xs flex items-center justify-center flex-shrink-0 font-mono mt-0.5">
                  {i + 1}
                </span>
                {step}
              </li>
            ))}
          </ol>
        </div>
      )}
    </div>
  )
}
