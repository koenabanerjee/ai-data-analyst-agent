import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  FileDown, Loader2, CheckCircle, AlertCircle,
  Upload, FileText, Shield, BarChart3, Brain, Table2
} from 'lucide-react'
import { generateReport, getReportDownloadUrl } from '../utils/api'
import { useStore } from '../store'
import { EmptyState } from '../components/ui'

const REPORT_SECTIONS = [
  { icon: Shield, title: 'Executive Summary', desc: 'High-level overview of findings and key metrics' },
  { icon: Table2, title: 'Dataset Overview', desc: 'Schema, row/column counts, memory usage, datatypes' },
  { icon: BarChart3, title: 'Statistical Analysis', desc: 'Full descriptive stats, distributions, quartiles' },
  { icon: AlertCircle, title: 'Missing & Outlier Analysis', desc: 'Imputation recommendations and anomaly breakdown' },
  { icon: Brain, title: 'AI Insights & Recommendations', desc: 'Gemini-generated analyst narrative and action items' },
]

export default function ReportPage() {
  const navigate = useNavigate()
  const currentDataset = useStore((s) => s.currentDataset)
  const addToast = useStore((s) => s.addToast)

  const [status, setStatus] = useState('idle') // idle | generating | done | error
  const [error, setError] = useState('')
  const [reportId, setReportId] = useState(null)

  const handleGenerate = async () => {
    if (!currentDataset) return
    setStatus('generating')
    setError('')
    try {
      const { data } = await generateReport(currentDataset.id)
      setReportId(data.dataset_id)
      setStatus('done')
      addToast('PDF report generated successfully!', 'success')
    } catch (err) {
      setStatus('error')
      setError(err.message || 'Report generation failed')
      addToast(err.message || 'Report failed', 'error')
    }
  }

  const handleDownload = () => {
    const url = getReportDownloadUrl(currentDataset.id)
    const a = document.createElement('a')
    a.href = url
    a.download = `report_${currentDataset.original_filename?.replace(/\.[^.]+$/, '')}.pdf`
    a.click()
  }

  if (!currentDataset) {
    return (
      <EmptyState
        icon={Upload}
        title="No dataset selected"
        description="Upload and analyse a dataset to generate a report."
        action={<button onClick={() => navigate('/upload')} className="btn-primary">Upload Dataset</button>}
      />
    )
  }

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="page-header">
        <h1 className="page-title">Report Generator</h1>
        <p className="page-subtitle">Generate a professional PDF report with all analysis findings</p>
      </div>

      {/* Dataset info */}
      <div className="card flex items-center gap-4">
        <div className="w-12 h-12 rounded-2xl bg-brand-500/10 flex items-center justify-center flex-shrink-0">
          <FileText size={22} className="text-brand-400" />
        </div>
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-white truncate">{currentDataset.original_filename}</p>
          <p className="text-surface-400 text-sm">
            {currentDataset.row_count?.toLocaleString()} rows · {currentDataset.column_count} columns · {currentDataset.file_type?.toUpperCase()}
          </p>
        </div>
        <span className="badge-success">Ready</span>
      </div>

      {/* Report sections preview */}
      <div className="card space-y-4">
        <p className="font-semibold text-white">Report Contents</p>
        <div className="space-y-3">
          {REPORT_SECTIONS.map(({ icon: Icon, title, desc }) => (
            <div key={title} className="flex items-start gap-3">
              <div className="w-8 h-8 rounded-lg bg-brand-500/10 flex items-center justify-center flex-shrink-0">
                <Icon size={14} className="text-brand-400" />
              </div>
              <div>
                <p className="text-sm font-medium text-surface-200">{title}</p>
                <p className="text-xs text-surface-500">{desc}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Action area */}
      {status === 'idle' && (
        <motion.button
          whileHover={{ y: -1 }}
          whileTap={{ scale: 0.98 }}
          onClick={handleGenerate}
          className="btn-primary w-full flex items-center justify-center gap-2 py-4 text-base"
        >
          <FileDown size={18} />
          Generate PDF Report
        </motion.button>
      )}

      {status === 'generating' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card text-center space-y-4"
        >
          <Loader2 size={32} className="animate-spin text-brand-400 mx-auto" />
          <p className="font-semibold text-white">Generating your report...</p>
          <p className="text-surface-400 text-sm">
            Building PDF with executive summary, statistics, insights, and visualizations
          </p>
          <div className="flex justify-center gap-2 flex-wrap">
            {['Layout', 'Tables', 'Statistics', 'AI Insights'].map((s, i) => (
              <span
                key={s}
                className="badge-brand animate-pulse"
                style={{ animationDelay: `${i * 0.3}s` }}
              >
                {s}
              </span>
            ))}
          </div>
        </motion.div>
      )}

      {status === 'done' && (
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="card text-center space-y-4 border-emerald-500/30"
        >
          <CheckCircle size={40} className="text-emerald-400 mx-auto" />
          <div>
            <p className="font-semibold text-white text-lg">Report Ready!</p>
            <p className="text-surface-400 text-sm mt-1">Your professional PDF report has been generated.</p>
          </div>
          <div className="flex gap-3 justify-center">
            <button onClick={handleDownload} className="btn-primary flex items-center gap-2 px-6">
              <FileDown size={16} />
              Download PDF
            </button>
            <button onClick={() => setStatus('idle')} className="btn-secondary">
              Regenerate
            </button>
          </div>
        </motion.div>
      )}

      {status === 'error' && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="card border-red-500/30 space-y-3"
        >
          <div className="flex items-start gap-3">
            <AlertCircle size={18} className="text-red-400 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-semibold text-white">Generation failed</p>
              <p className="text-surface-400 text-sm mt-1">{error}</p>
              <p className="text-surface-500 text-xs mt-1">
                Make sure EDA has been completed first (go to Analytics and run analysis).
              </p>
            </div>
          </div>
          <button onClick={() => setStatus('idle')} className="btn-secondary text-sm">Try Again</button>
        </motion.div>
      )}
    </div>
  )
}
