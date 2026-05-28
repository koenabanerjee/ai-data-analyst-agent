import { NavLink, useLocation } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  LayoutDashboard, Upload, Table2, BarChart3,
  LineChart, MessageSquare, FileDown, Zap, ChevronRight,
} from 'lucide-react'
import { useStore } from '../../store'
import Toast from '../ui/Toast'
import clsx from 'clsx'

const NAV = [
  { to: '/', icon: Zap, label: 'Home' },
  { to: '/upload', icon: Upload, label: 'Upload' },
  { to: '/overview', icon: Table2, label: 'Dataset' },
  { to: '/analytics', icon: BarChart3, label: 'Analytics' },
  { to: '/visualize', icon: LineChart, label: 'Visualize' },
  { to: '/chat', icon: MessageSquare, label: 'AI Chat' },
  { to: '/report', icon: FileDown, label: 'Report' },
]

export default function Layout({ children }) {
  const currentDataset = useStore((s) => s.currentDataset)
  const toasts = useStore((s) => s.toasts)
  const removeToast = useStore((s) => s.removeToast)
  const location = useLocation()

  return (
    <div className="flex h-screen overflow-hidden bg-surface-950">
      {/* Sidebar */}
      <aside className="w-20 lg:w-64 flex-shrink-0 flex flex-col glass-dark border-r border-surface-800 z-20">
        {/* Logo */}
        <div className="h-16 flex items-center px-4 lg:px-6 border-b border-surface-800 gap-3">
          <div className="w-8 h-8 rounded-xl bg-brand-500 flex items-center justify-center flex-shrink-0">
            <Zap size={16} className="text-white" />
          </div>
          <span className="hidden lg:block font-display font-bold text-white text-sm leading-tight">
            AI Data<br />Analyst
          </span>
        </div>

        {/* Nav links */}
        <nav className="flex-1 px-2 py-4 space-y-1 overflow-y-auto">
          {NAV.map(({ to, icon: Icon, label }) => (
            <NavLink
              key={to}
              to={to}
              end={to === '/'}
              className={({ isActive }) =>
                clsx(
                  'flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group',
                  isActive
                    ? 'bg-brand-500/20 text-brand-300 border border-brand-500/30'
                    : 'text-surface-400 hover:text-surface-100 hover:bg-surface-800'
                )
              }
            >
              {({ isActive }) => (
                <>
                  <Icon size={18} className={isActive ? 'text-brand-400' : 'text-current'} />
                  <span className="hidden lg:block text-sm font-medium">{label}</span>
                  {isActive && (
                    <ChevronRight size={14} className="hidden lg:block ml-auto text-brand-400" />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        {/* Dataset indicator */}
        {currentDataset && (
          <div className="hidden lg:block px-4 py-3 border-t border-surface-800">
            <p className="text-xs text-surface-500 mb-1">Active Dataset</p>
            <p className="text-xs text-surface-300 truncate font-medium">
              {currentDataset.original_filename}
            </p>
            <p className="text-xs text-surface-500">
              {currentDataset.row_count?.toLocaleString()} rows
            </p>
          </div>
        )}
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Top bar */}
        <header className="h-16 flex items-center px-6 border-b border-surface-800 glass-dark flex-shrink-0 gap-4">
          <div className="flex-1">
            <h2 className="font-display font-semibold text-surface-100 capitalize text-sm">
              {location.pathname === '/' ? 'Home' :
               location.pathname.replace('/', '').replace('-', ' ')}
            </h2>
          </div>
          {currentDataset && (
            <div className="badge-brand">
              <span className="w-1.5 h-1.5 rounded-full bg-brand-400 animate-pulse" />
              {currentDataset.original_filename}
            </div>
          )}
        </header>

        {/* Page */}
        <div className="flex-1 overflow-y-auto p-6">
          <AnimatePresence mode="wait">
            <motion.div
              key={location.pathname}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </div>
      </main>

      {/* Toast container */}
      <div className="fixed bottom-6 right-6 z-50 space-y-2">
        <AnimatePresence>
          {toasts.map((t) => (
            <Toast key={t.id} toast={t} onClose={() => removeToast(t.id)} />
          ))}
        </AnimatePresence>
      </div>
    </div>
  )
}
