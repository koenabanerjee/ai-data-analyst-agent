import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Table2, Rows, Columns, AlertTriangle,
  Copy, Hash, RefreshCw, Upload
} from 'lucide-react'
import { getEDA, getDatasetPreview } from '../utils/api'
import { useStore } from '../store'
import { StatCard, LoadingState, EmptyState, Badge, ProgressBar } from '../components/ui'
import clsx from 'clsx'

export default function OverviewPage() {
  const navigate = useNavigate()
  const currentDataset = useStore((s) => s.currentDataset)
  const setEdaResult = useStore((s) => s.setEdaResult)
  const getEdaResult = useStore((s) => s.getEdaResult)

  const [eda, setEda] = useState(null)
  const [preview, setPreview] = useState(null)
  const [loading, setLoading] = useState(true)
  const [activeTab, setActiveTab] = useState('overview')

  useEffect(() => {
    if (!currentDataset) return
    load()
  }, [currentDataset])

  const load = async () => {
    setLoading(true)
    try {
      const cached = getEdaResult(currentDataset.id)
      const [edaRes, previewRes] = await Promise.all([
        cached ? Promise.resolve({ data: cached }) : getEDA(currentDataset.id),
        getDatasetPreview(currentDataset.id, 100),
      ])
      const edaData = edaRes.data
      setEda(edaData)
      setEdaResult(currentDataset.id, edaData)
      setPreview(previewRes.data)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  if (!currentDataset) {
    return (
      <EmptyState
        icon={Upload}
        title="No dataset selected"
        description="Upload a dataset to see its overview."
        action={<button onClick={() => navigate('/upload')} className="btn-primary">Upload Dataset</button>}
      />
    )
  }

  if (loading) return <LoadingState message="Loading dataset overview..." />

  const overview = eda?.overview || {}
  const colStats = eda?.column_stats || []
  const missingRecs = eda?.missing_recommendations || []

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <div className="page-header">
        <h1 className="page-title">{currentDataset.original_filename}</h1>
        <p className="page-subtitle">Dataset overview, schema, and column statistics</p>
      </div>

      {/* KPI cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Rows" value={overview.row_count?.toLocaleString()} icon={Rows} color="brand" />
        <StatCard label="Columns" value={overview.column_count} icon={Columns} color="blue" />
        <StatCard label="Missing Values" value={`${overview.null_pct?.toFixed(1)}%`} icon={AlertTriangle} color={overview.null_pct > 10 ? 'amber' : 'green'} sub={`${overview.total_nulls?.toLocaleString()} cells`} />
        <StatCard label="Duplicate Rows" value={overview.duplicate_rows?.toLocaleString()} icon={Copy} color={overview.duplicate_rows > 0 ? 'amber' : 'green'} />
      </div>

      {/* Column type breakdown */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: 'Numeric', cols: overview.numeric_columns || [], color: 'brand' },
          { label: 'Categorical', cols: overview.categorical_columns || [], color: 'blue' },
          { label: 'Datetime', cols: overview.datetime_columns || [], color: 'green' },
        ].map(({ label, cols, color }) => (
          <div key={label} className="card">
            <div className="flex items-center justify-between mb-3">
              <p className="text-sm font-semibold text-surface-200">{label} Columns</p>
              <span className={`badge badge-${color === 'brand' ? 'brand' : color === 'green' ? 'success' : 'brand'}`}>{cols.length}</span>
            </div>
            <div className="flex flex-wrap gap-1.5">
              {cols.slice(0, 8).map((c) => (
                <span key={c} className="px-2 py-0.5 rounded-md bg-surface-800 text-xs text-surface-300 border border-surface-700">
                  {c}
                </span>
              ))}
              {cols.length > 8 && <span className="text-xs text-surface-500">+{cols.length - 8} more</span>}
              {cols.length === 0 && <span className="text-xs text-surface-600">None detected</span>}
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 border-b border-surface-800 pb-0">
        {['overview', 'columns', 'missing', 'preview'].map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={clsx(
              'px-4 py-2 text-sm font-medium capitalize transition-all border-b-2 -mb-px',
              activeTab === tab
                ? 'text-brand-400 border-brand-500'
                : 'text-surface-400 border-transparent hover:text-surface-200'
            )}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Tab: Column statistics */}
      {activeTab === 'columns' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-surface-800">
                {['Column', 'Type', 'Null %', 'Unique', 'Mean', 'Median', 'Std Dev', 'Min', 'Max', 'Skew'].map((h) => (
                  <th key={h} className="text-left py-3 px-3 text-xs font-medium text-surface-400 uppercase tracking-wider">
                    {h}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {colStats.map((cs, i) => (
                <tr key={cs.name} className={clsx('border-b border-surface-800/50', i % 2 === 0 ? 'bg-surface-900/20' : '')}>
                  <td className="py-3 px-3 font-medium text-surface-200 max-w-[140px] truncate">{cs.name}</td>
                  <td className="py-3 px-3">
                    <span className="badge-brand text-xs">{cs.dtype}</span>
                  </td>
                  <td className="py-3 px-3">
                    <div className="flex items-center gap-2">
                      <span className={cs.null_pct > 20 ? 'text-amber-400' : 'text-surface-300'}>{cs.null_pct}%</span>
                    </div>
                  </td>
                  <td className="py-3 px-3 text-surface-400">{cs.unique_count?.toLocaleString()}</td>
                  <td className="py-3 px-3 text-surface-300 font-mono text-xs">{cs.mean?.toFixed(2) ?? '—'}</td>
                  <td className="py-3 px-3 text-surface-300 font-mono text-xs">{cs.median?.toFixed(2) ?? '—'}</td>
                  <td className="py-3 px-3 text-surface-300 font-mono text-xs">{cs.std?.toFixed(2) ?? '—'}</td>
                  <td className="py-3 px-3 text-surface-300 font-mono text-xs">{cs.min?.toFixed(2) ?? '—'}</td>
                  <td className="py-3 px-3 text-surface-300 font-mono text-xs">{cs.max?.toFixed(2) ?? '—'}</td>
                  <td className="py-3 px-3">
                    {cs.skewness != null && (
                      <span className={clsx('font-mono text-xs', Math.abs(cs.skewness) > 1 ? 'text-amber-400' : 'text-surface-400')}>
                        {cs.skewness?.toFixed(2)}
                      </span>
                    )}
                    {cs.skewness == null && <span className="text-surface-600">—</span>}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      )}

      {/* Tab: Missing values */}
      {activeTab === 'missing' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="space-y-4">
          {missingRecs.length === 0 ? (
            <div className="card text-center py-10">
              <p className="text-emerald-400 font-semibold text-lg mb-1">✓ No missing values</p>
              <p className="text-surface-500 text-sm">This dataset is complete.</p>
            </div>
          ) : (
            missingRecs.map((rec) => (
              <div key={rec.column} className="card flex items-start gap-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
                  <AlertTriangle size={16} className="text-amber-400" />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-3 mb-1">
                    <p className="font-semibold text-surface-200">{rec.column}</p>
                    <span className="badge-warning">{rec.null_pct}% missing</span>
                    <span className="badge-brand capitalize">{rec.recommendation?.replace(/_/g, ' ')}</span>
                  </div>
                  <p className="text-sm text-surface-400">{rec.reason}</p>
                  <ProgressBar value={rec.null_pct} max={100} color={rec.null_pct > 50 ? 'red' : 'amber'} />
                </div>
              </div>
            ))
          )}
        </motion.div>
      )}

      {/* Tab: Data preview */}
      {activeTab === 'preview' && preview && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="overflow-x-auto">
          <p className="text-xs text-surface-500 mb-3">Showing first {preview.preview_rows?.length} rows</p>
          <table className="w-full text-xs min-w-max">
            <thead>
              <tr className="border-b border-surface-800">
                {preview.columns?.map((col) => (
                  <th key={col} className="text-left py-2.5 px-3 text-surface-400 font-medium whitespace-nowrap max-w-[160px] truncate">
                    <div>
                      <span className="text-surface-200">{col}</span>
                      <br />
                      <span className="text-surface-600 font-normal">{preview.dtypes?.[col]}</span>
                    </div>
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.preview_rows?.slice(0, 50).map((row, i) => (
                <tr key={i} className={clsx('border-b border-surface-800/40', i % 2 === 0 ? '' : 'bg-surface-900/30')}>
                  {preview.columns?.map((col) => (
                    <td key={col} className="py-2 px-3 text-surface-300 max-w-[160px] truncate whitespace-nowrap">
                      {row[col] == null ? <span className="text-surface-600 italic">null</span> : String(row[col])}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </motion.div>
      )}

      {/* Tab: Overview (default) */}
      {activeTab === 'overview' && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="card space-y-3">
            <p className="font-semibold text-white mb-3">Dataset Summary</p>
            {[
              ['File', currentDataset.original_filename],
              ['Format', currentDataset.file_type?.toUpperCase()],
              ['Size', `${(currentDataset.file_size / 1024 / 1024).toFixed(2)} MB`],
              ['Memory', `${overview.memory_usage_kb?.toFixed(1)} KB`],
              ['Status', currentDataset.status],
            ].map(([label, value]) => (
              <div key={label} className="flex justify-between items-center py-1.5 border-b border-surface-800/50">
                <span className="text-surface-400 text-sm">{label}</span>
                <span className="text-surface-200 text-sm font-medium">{value}</span>
              </div>
            ))}
          </div>

          <div className="card">
            <p className="font-semibold text-white mb-4">Missing Values by Column</p>
            <div className="space-y-2.5 max-h-60 overflow-y-auto">
              {colStats
                .filter((cs) => cs.null_pct > 0)
                .sort((a, b) => b.null_pct - a.null_pct)
                .map((cs) => (
                  <div key={cs.name}>
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-surface-400 truncate max-w-[160px]">{cs.name}</span>
                      <span className="text-surface-300">{cs.null_pct}%</span>
                    </div>
                    <ProgressBar value={cs.null_pct} max={100} color={cs.null_pct > 50 ? 'red' : cs.null_pct > 20 ? 'amber' : 'brand'} />
                  </div>
                ))}
              {colStats.every((cs) => cs.null_pct === 0) && (
                <p className="text-emerald-400 text-sm text-center py-4">✓ No missing values</p>
              )}
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}
