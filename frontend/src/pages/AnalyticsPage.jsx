import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  TrendingUp, AlertOctagon, GitBranch, Brain, Upload, ChevronDown, ChevronUp
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { getEDA } from '../utils/api'
import { useStore } from '../store'
import { StatCard, LoadingState, EmptyState, SectionHeader } from '../components/ui'

function OutlierCard({ colName, data }) {
  const iqr = data.iqr || {}
  const z = data.zscore || {}
  const [open, setOpen] = useState(false)
  return (
    <div className="card">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setOpen(!open)}
      >
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-amber-500/10 flex items-center justify-center flex-shrink-0">
            <AlertOctagon size={14} className="text-amber-400" />
          </div>
          <span className="font-medium text-surface-200">{colName}</span>
        </div>
        <div className="flex items-center gap-3">
          <span className={`badge ${iqr.outlier_count > 0 ? 'badge-warning' : 'badge-success'}`}>
            {iqr.outlier_count || 0} outliers
          </span>
          {open ? <ChevronUp size={14} className="text-surface-500" /> : <ChevronDown size={14} className="text-surface-500" />}
        </div>
      </div>
      {open && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          className="mt-4 pt-4 border-t border-surface-800 grid grid-cols-2 gap-4 text-sm"
        >
          <div>
            <p className="text-surface-500 text-xs mb-2 font-medium uppercase tracking-wider">IQR Method</p>
            <div className="space-y-1">
              <div className="flex justify-between"><span className="text-surface-400">Outliers</span><span className="text-white">{iqr.outlier_count}</span></div>
              <div className="flex justify-between"><span className="text-surface-400">Percentage</span><span className="text-white">{iqr.outlier_pct}%</span></div>
              <div className="flex justify-between"><span className="text-surface-400">Lower bound</span><span className="font-mono text-xs text-surface-300">{iqr.bounds?.lower?.toFixed(2)}</span></div>
              <div className="flex justify-between"><span className="text-surface-400">Upper bound</span><span className="font-mono text-xs text-surface-300">{iqr.bounds?.upper?.toFixed(2)}</span></div>
            </div>
          </div>
          <div>
            <p className="text-surface-500 text-xs mb-2 font-medium uppercase tracking-wider">Z-Score (σ=3)</p>
            <div className="space-y-1">
              <div className="flex justify-between"><span className="text-surface-400">Outliers</span><span className="text-white">{z.outlier_count}</span></div>
              <div className="flex justify-between"><span className="text-surface-400">Percentage</span><span className="text-white">{z.outlier_pct}%</span></div>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  )
}

function CorrBadge({ r }) {
  const abs = Math.abs(r)
  const color = abs >= 0.9 ? 'text-red-400' : abs >= 0.7 ? 'text-amber-400' : 'text-brand-400'
  return <span className={`font-mono text-sm font-bold ${color}`}>{r > 0 ? '+' : ''}{r.toFixed(3)}</span>
}

export default function AnalyticsPage() {
  const navigate = useNavigate()
  const currentDataset = useStore((s) => s.currentDataset)
  const getEdaResult = useStore((s) => s.getEdaResult)
  const setEdaResult = useStore((s) => s.setEdaResult)

  const [eda, setEda] = useState(null)
  const [loading, setLoading] = useState(true)
  const [insightExpanded, setInsightExpanded] = useState(false)

  useEffect(() => {
    if (!currentDataset) return
    load()
  }, [currentDataset])

  const load = async () => {
    setLoading(true)
    try {
      const cached = getEdaResult(currentDataset.id)
      if (cached) {
        setEda(cached)
      } else {
        const { data } = await getEDA(currentDataset.id)
        setEda(data)
        setEdaResult(currentDataset.id, data)
      }
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
        description="Upload a dataset to view analytics."
        action={<button onClick={() => navigate('/upload')} className="btn-primary">Upload Dataset</button>}
      />
    )
  }

  if (loading) return <LoadingState message="Loading analytics..." />

  const outliers = eda?.outlier_summary?.columns || {}
  const correlation = eda?.correlation || {}
  const strongPos = correlation.strong_positive || []
  const strongNeg = correlation.strong_negative || []
  const insights = eda?.ai_insights || ''
  const totalOutliers = eda?.outlier_summary?.total_outlier_cells || 0

  return (
    <div className="space-y-8 max-w-6xl mx-auto">
      <div className="page-header">
        <h1 className="page-title">Analytics Dashboard</h1>
        <p className="page-subtitle">Outlier detection, correlation analysis, and AI-generated insights</p>
      </div>

      {/* Summary KPIs */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <StatCard label="Total Outliers" value={totalOutliers.toLocaleString()} icon={AlertOctagon} color={totalOutliers > 0 ? 'amber' : 'green'} />
        <StatCard label="Numeric Columns Checked" value={eda?.outlier_summary?.numeric_columns_checked || 0} icon={TrendingUp} color="brand" />
        <StatCard label="Strong Correlations" value={strongPos.length + strongNeg.length} icon={GitBranch} color="blue" />
        <StatCard label="AI Insights" value={insights ? '✓ Ready' : 'Pending'} icon={Brain} color={insights ? 'green' : 'amber'} />
      </div>

      {/* AI Insights */}
      {insights && (
        <div className="card border-brand-500/20">
          <SectionHeader
            title="AI-Generated Insights"
            description="Gemini AI analyst narrative — patterns, trends, and recommendations"
            action={
              <button
                onClick={() => setInsightExpanded(!insightExpanded)}
                className="btn-ghost text-xs flex items-center gap-1"
              >
                {insightExpanded ? <><ChevronUp size={14} /> Collapse</> : <><ChevronDown size={14} /> Expand</>}
              </button>
            }
          />
          <div className={`prose-dark overflow-hidden transition-all duration-500 ${insightExpanded ? 'max-h-[2000px]' : 'max-h-48'}`}>
            <ReactMarkdown remarkPlugins={[remarkGfm]}>{insights}</ReactMarkdown>
          </div>
          {!insightExpanded && (
            <div className="relative">
              <div className="absolute inset-x-0 -top-16 h-16 bg-gradient-to-t from-surface-900/80 to-transparent pointer-events-none" />
              <button
                onClick={() => setInsightExpanded(true)}
                className="text-brand-400 text-xs hover:text-brand-300 mt-2 transition-colors"
              >
                Read full analysis →
              </button>
            </div>
          )}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Correlations */}
        <div className="card">
          <SectionHeader title="Correlation Findings" description="Pearson correlation between numeric columns" />
          {strongPos.length === 0 && strongNeg.length === 0 ? (
            <p className="text-surface-500 text-sm text-center py-6">No strong correlations (|r| ≥ 0.7) found.</p>
          ) : (
            <div className="space-y-5">
              {strongPos.length > 0 && (
                <div>
                  <p className="text-xs text-surface-500 uppercase tracking-wider mb-3 font-medium">
                    Strong Positive (r ≥ +0.7)
                  </p>
                  <div className="space-y-2">
                    {strongPos.slice(0, 8).map((c) => (
                      <div key={`${c.col1}-${c.col2}`} className="flex items-center justify-between py-2 border-b border-surface-800/50">
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-surface-300">{c.col1}</span>
                          <span className="text-surface-600">↔</span>
                          <span className="text-surface-300">{c.col2}</span>
                        </div>
                        <CorrBadge r={c.r} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {strongNeg.length > 0 && (
                <div>
                  <p className="text-xs text-surface-500 uppercase tracking-wider mb-3 font-medium">
                    Strong Negative (r ≤ −0.7)
                  </p>
                  <div className="space-y-2">
                    {strongNeg.slice(0, 8).map((c) => (
                      <div key={`${c.col1}-${c.col2}`} className="flex items-center justify-between py-2 border-b border-surface-800/50">
                        <div className="flex items-center gap-2 text-sm">
                          <span className="text-surface-300">{c.col1}</span>
                          <span className="text-surface-600">↔</span>
                          <span className="text-surface-300">{c.col2}</span>
                        </div>
                        <CorrBadge r={c.r} />
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Outliers summary */}
        <div className="card">
          <SectionHeader title="Outlier Summary" description="IQR and Z-score detection per column" />
          {Object.keys(outliers).length === 0 ? (
            <p className="text-surface-500 text-sm text-center py-6">No numeric columns to check.</p>
          ) : (
            <div className="space-y-3 max-h-[400px] overflow-y-auto">
              {Object.entries(outliers)
                .sort(([, a], [, b]) => (b.iqr?.outlier_count || 0) - (a.iqr?.outlier_count || 0))
                .map(([col, data]) => (
                  <OutlierCard key={col} colName={col} data={data} />
                ))}
            </div>
          )}
        </div>
      </div>

      {/* Correlation matrix table if small enough */}
      {correlation.columns && correlation.columns.length <= 10 && (
        <div className="card overflow-x-auto">
          <SectionHeader title="Correlation Matrix" description="Full Pearson correlation matrix" />
          <table className="text-xs font-mono">
            <thead>
              <tr>
                <th className="text-left p-2 text-surface-500">—</th>
                {correlation.columns.map((c) => (
                  <th key={c} className="p-2 text-surface-400 max-w-[80px] truncate" style={{ writingMode: 'vertical-rl', transform: 'rotate(180deg)', textAlign: 'left', height: 80 }}>
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {correlation.columns.map((row) => (
                <tr key={row} className="border-t border-surface-800/50">
                  <td className="p-2 text-surface-400 font-sans text-xs max-w-[100px] truncate">{row}</td>
                  {correlation.columns.map((col) => {
                    const val = correlation.matrix?.[row]?.[col]
                    const abs = Math.abs(val ?? 0)
                    const bg = val === null || val === undefined ? '' :
                      row === col ? 'bg-brand-500/20' :
                      abs >= 0.7 ? 'bg-amber-500/20' :
                      abs >= 0.4 ? 'bg-brand-500/10' : ''
                    return (
                      <td key={col} className={`p-2 text-center text-xs ${bg}`}>
                        {val != null ? (
                          <span className={Math.abs(val) >= 0.7 ? 'text-amber-400 font-bold' : 'text-surface-400'}>
                            {Number(val).toFixed(2)}
                          </span>
                        ) : '—'}
                      </td>
                    )
                  })}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
