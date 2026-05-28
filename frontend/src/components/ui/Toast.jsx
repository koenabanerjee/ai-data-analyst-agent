import { motion } from 'framer-motion'
import { X, CheckCircle, AlertCircle, Info, AlertTriangle } from 'lucide-react'
import clsx from 'clsx'

const icons = {
  success: <CheckCircle size={16} className="text-emerald-400" />,
  error: <AlertCircle size={16} className="text-red-400" />,
  warning: <AlertTriangle size={16} className="text-amber-400" />,
  info: <Info size={16} className="text-brand-400" />,
}

const borders = {
  success: 'border-emerald-500/30',
  error: 'border-red-500/30',
  warning: 'border-amber-500/30',
  info: 'border-brand-500/30',
}

export default function Toast({ toast, onClose }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: 60, scale: 0.9 }}
      animate={{ opacity: 1, x: 0, scale: 1 }}
      exit={{ opacity: 0, x: 60, scale: 0.9 }}
      className={clsx(
        'flex items-start gap-3 px-4 py-3 rounded-xl glass-dark border max-w-sm shadow-2xl',
        borders[toast.type] || borders.info
      )}
    >
      <span className="mt-0.5 flex-shrink-0">{icons[toast.type] || icons.info}</span>
      <p className="text-sm text-surface-200 flex-1">{toast.msg}</p>
      <button onClick={onClose} className="text-surface-500 hover:text-surface-300 flex-shrink-0">
        <X size={14} />
      </button>
    </motion.div>
  )
}
