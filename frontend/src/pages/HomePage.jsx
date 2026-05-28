import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  Zap, BarChart3, Brain, FileDown, MessageSquare,
  ArrowRight, Database, TrendingUp, Shield
} from 'lucide-react'

const FEATURES = [
  { icon: Database, title: 'Smart Upload', desc: 'CSV & XLSX with automatic schema detection, datatype inference, and duplicate detection.' },
  { icon: BarChart3, title: 'Autonomous EDA', desc: '8-agent LangGraph pipeline runs full statistical analysis — overview, outliers, correlations, and more.' },
  { icon: Brain, title: 'AI Insights', desc: 'Gemini AI generates human-like analyst narratives — trends, anomalies, patterns, and recommendations.' },
  { icon: TrendingUp, title: 'Smart Visualizations', desc: 'Plotly charts auto-selected based on data semantics — histograms, scatter, heatmaps, violin plots.' },
  { icon: MessageSquare, title: 'NL Query Engine', desc: 'Ask questions in plain English. The Query Agent interprets intent and answers with charts when helpful.' },
  { icon: FileDown, title: 'PDF Reports', desc: 'Download premium professional PDF reports with executive summary, stats, visualizations, and insights.' },
]

const STACK = ['Python', 'FastAPI', 'LangGraph', 'Gemini AI', 'React', 'Tailwind', 'Plotly', 'ReportLab']

const stagger = {
  container: { hidden: {}, show: { transition: { staggerChildren: 0.08 } } },
  item: { hidden: { opacity: 0, y: 24 }, show: { opacity: 1, y: 0 } },
}

export default function HomePage() {
  return (
    <div className="max-w-5xl mx-auto space-y-16 py-4">
      {/* Hero */}
      <motion.section
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="text-center space-y-6"
      >
        <div className="inline-flex items-center gap-2 badge-brand text-sm px-4 py-1.5 mb-2">
          <Zap size={13} />
          Agentic AI · LangGraph · 8 Agents
        </div>
        <h1 className="text-5xl lg:text-6xl font-display font-bold text-white leading-tight">
          AI Data Analyst
          <br />
          <span className="text-brand-400">Agent</span>
        </h1>
        <p className="text-surface-400 text-lg max-w-2xl mx-auto">
          Upload any dataset and watch an autonomous AI pipeline perform full exploratory data analysis,
          generate professional insights, and produce downloadable reports — in seconds.
        </p>
        <div className="flex items-center justify-center gap-4 flex-wrap">
          <Link to="/upload" className="btn-primary flex items-center gap-2 text-base px-8 py-3">
            Get Started <ArrowRight size={16} />
          </Link>
          <Link to="/analytics" className="btn-secondary flex items-center gap-2 text-base">
            View Demo
          </Link>
        </div>
      </motion.section>

      {/* Tech stack */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="flex flex-wrap gap-2 justify-center"
      >
        {STACK.map((s) => (
          <span key={s} className="px-3 py-1 rounded-full text-xs font-medium bg-surface-800 text-surface-300 border border-surface-700">
            {s}
          </span>
        ))}
      </motion.section>

      {/* Features grid */}
      <section>
        <h2 className="text-2xl font-display font-bold text-white text-center mb-8">
          Everything you need, autonomously
        </h2>
        <motion.div
          variants={stagger.container}
          initial="hidden"
          animate="show"
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5"
        >
          {FEATURES.map(({ icon: Icon, title, desc }) => (
            <motion.div key={title} variants={stagger.item} className="card group hover:border-brand-500/30 transition-all duration-300">
              <div className="w-10 h-10 rounded-xl bg-brand-500/10 flex items-center justify-center mb-4 group-hover:bg-brand-500/20 transition-colors">
                <Icon size={18} className="text-brand-400" />
              </div>
              <h3 className="font-display font-semibold text-white mb-2">{title}</h3>
              <p className="text-surface-400 text-sm leading-relaxed">{desc}</p>
            </motion.div>
          ))}
        </motion.div>
      </section>

      {/* Agent pipeline visual */}
      <section className="card">
        <h2 className="text-xl font-display font-bold text-white mb-6 text-center">
          Agentic Workflow Pipeline
        </h2>
        <div className="flex flex-wrap items-center justify-center gap-2">
          {['Schema', 'EDA', 'Missing Values', 'Outliers', 'Correlation', 'Insights', 'Visualization', 'Report'].map((agent, i, arr) => (
            <div key={agent} className="flex items-center gap-2">
              <div className="flex flex-col items-center">
                <div className="px-3 py-2 rounded-xl bg-brand-500/10 border border-brand-500/30 text-brand-300 text-xs font-medium">
                  {agent}
                </div>
                <span className="text-xs text-surface-600 mt-1">Agent</span>
              </div>
              {i < arr.length - 1 && <ArrowRight size={14} className="text-surface-600 flex-shrink-0" />}
            </div>
          ))}
        </div>
        <p className="text-center text-surface-500 text-xs mt-4">
          Each agent enriches shared state via LangGraph StateGraph — modular, extensible, production-ready
        </p>
      </section>

      {/* CTA */}
      <motion.section
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.5 }}
        className="text-center"
      >
        <div className="card bg-gradient-to-br from-brand-900/40 to-surface-900 border-brand-500/20">
          <Shield size={32} className="text-brand-400 mx-auto mb-4" />
          <h2 className="text-2xl font-display font-bold text-white mb-3">Ready to analyse your data?</h2>
          <p className="text-surface-400 mb-6">Upload CSV or XLSX — results in under 60 seconds.</p>
          <Link to="/upload" className="btn-primary inline-flex items-center gap-2 px-8 py-3 text-base">
            Upload Dataset <ArrowRight size={16} />
          </Link>
        </div>
      </motion.section>
    </div>
  )
}
