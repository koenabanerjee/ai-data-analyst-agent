import clsx from 'clsx'
import { motion } from 'framer-motion'

// ── Spinner ───────────────────────────────────────────────────────────────────
export function Spinner({ size = 'md', className = '' }) {
  const sz = { sm: 'w-4 h-4', md: 'w-8 h-8', lg: 'w-12 h-12' }[size]
  return (
    <div className={clsx('relative', sz, className)}>
      <div className={clsx('absolute inset-0 rounded-full border-2 border-surface-700')} />
      <div className={clsx('absolute inset-0 rounded-full border-2 border-transparent border-t-brand-500 animate-spin')} />
    </div>
  )
}

// ── Loading overlay ───────────────────────────────────────────────────────────
export function LoadingState({ message = 'Processing...' }) {
  return (
    <div className="flex flex-col items-center justify-center py-20 gap-4">
      <Spinner size="lg" />
      <p className="text-surface-400 text-sm animate-pulse">{message}</p>
    </div>
  )
}

// ── Shimmer skeleton ──────────────────────────────────────────────────────────
export function Skeleton({ className = '' }) {
  return <div className={clsx('shimmer rounded-lg', className)} />
}

// ── Stat card ─────────────────────────────────────────────────────────────────
export function StatCard({ label, value, icon: Icon, color = 'brand', sub }) {
  const colorMap = {
    brand: 'text-brand-400 bg-brand-500/10',
    green: 'text-emerald-400 bg-emerald-500/10',
    amber: 'text-amber-400 bg-amber-500/10',
    red: 'text-red-400 bg-red-500/10',
    blue: 'text-blue-400 bg-blue-500/10',
  }
  return (
    <motion.div
      whileHover={{ y: -2 }}
      className="stat-card"
    >
      <div className="flex items-start justify-between mb-3">
        <div className={clsx('p-2.5 rounded-xl', colorMap[color])}>
          {Icon && <Icon size={18} className={colorMap[color].split(' ')[0]} />}
        </div>
      </div>
      <p className="text-2xl font-display font-bold text-white mb-1">{value ?? '—'}</p>
      <p className="text-sm text-surface-400">{label}</p>
      {sub && <p className="text-xs text-surface-500 mt-1">{sub}</p>}
    </motion.div>
  )
}

// ── Empty state ───────────────────────────────────────────────────────────────
export function EmptyState({ icon: Icon, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center py-16 px-6 text-center">
      {Icon && (
        <div className="w-16 h-16 rounded-2xl bg-surface-800 flex items-center justify-center mb-4">
          <Icon size={28} className="text-surface-500" />
        </div>
      )}
      <h3 className="text-lg font-display font-semibold text-surface-200 mb-2">{title}</h3>
      {description && <p className="text-surface-500 text-sm max-w-sm mb-6">{description}</p>}
      {action}
    </div>
  )
}

// ── Section header ────────────────────────────────────────────────────────────
export function SectionHeader({ title, description, action }) {
  return (
    <div className="flex items-start justify-between mb-6">
      <div>
        <h2 className="text-xl font-display font-semibold text-white">{title}</h2>
        {description && <p className="text-surface-400 text-sm mt-1">{description}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  )
}

// ── Badge ─────────────────────────────────────────────────────────────────────
export function Badge({ children, variant = 'brand' }) {
  const v = {
    brand: 'badge-brand',
    success: 'badge-success',
    warning: 'badge-warning',
    danger: 'badge-danger',
  }[variant] || 'badge-brand'
  return <span className={v}>{children}</span>
}

// ── Progress bar ──────────────────────────────────────────────────────────────
export function ProgressBar({ value, max = 100, color = 'brand' }) {
  const pct = Math.min(100, (value / max) * 100)
  const colorMap = {
    brand: 'bg-brand-500',
    green: 'bg-emerald-500',
    amber: 'bg-amber-500',
    red: 'bg-red-500',
  }
  return (
    <div className="w-full bg-surface-800 rounded-full h-1.5">
      <motion.div
        className={clsx('h-1.5 rounded-full', colorMap[color] || colorMap.brand)}
        initial={{ width: 0 }}
        animate={{ width: `${pct}%` }}
        transition={{ duration: 0.6, ease: 'easeOut' }}
      />
    </div>
  )
}
