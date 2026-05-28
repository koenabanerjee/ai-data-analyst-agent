import { useState, useRef, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Send, Bot, User, Upload, Loader2, BarChart2, Lightbulb
} from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { askQuestion } from '../utils/api'
import { useStore } from '../store'
import { EmptyState } from '../components/ui'
import PlotlyChart from '../components/charts/PlotlyChart'

const SUGGESTIONS = [
  'What are the main trends in this dataset?',
  'Which columns have the most outliers?',
  'What affects the target variable most?',
  'Are there any suspicious anomalies?',
  'Show me the distribution of the most important column.',
  'What patterns exist between numeric columns?',
  'What is the data quality like?',
]

function Message({ msg }) {
  const isUser = msg.role === 'user'
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div className={`w-8 h-8 rounded-xl flex items-center justify-center flex-shrink-0 mt-0.5 ${
        isUser ? 'bg-brand-500' : 'bg-surface-800 border border-surface-700'
      }`}>
        {isUser ? <User size={14} className="text-white" /> : <Bot size={14} className="text-brand-400" />}
      </div>

      {/* Bubble */}
      <div className={`max-w-[80%] space-y-3 ${isUser ? 'items-end' : 'items-start'} flex flex-col`}>
        <div className={`rounded-2xl px-4 py-3 text-sm ${
          isUser
            ? 'bg-brand-500 text-white rounded-tr-sm'
            : 'bg-surface-800 border border-surface-700 text-surface-200 rounded-tl-sm'
        }`}>
          {isUser ? (
            <p>{msg.content}</p>
          ) : msg.loading ? (
            <div className="flex items-center gap-2 text-surface-400">
              <Loader2 size={14} className="animate-spin" />
              <span>Thinking...</span>
            </div>
          ) : (
            <div className="prose-dark">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
            </div>
          )}
        </div>

        {/* Chart if available */}
        {msg.chart && (
          <div className="w-full max-w-2xl">
            <PlotlyChart
              plotlyJson={msg.chart.plotly_json}
              title={msg.chart.title}
              reason={msg.chart.reason}
            />
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function ChatPage() {
  const navigate = useNavigate()
  const currentDataset = useStore((s) => s.currentDataset)
  const addToast = useStore((s) => s.addToast)

  const [messages, setMessages] = useState([
    {
      id: 'welcome',
      role: 'assistant',
      content: "Hello! I'm your AI Data Analyst. Ask me anything about your dataset — I can identify trends, detect anomalies, explain patterns, and generate charts on demand.",
    },
  ])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const bottomRef = useRef(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  const send = async (question) => {
    const q = (question || input).trim()
    if (!q || sending || !currentDataset) return

    setInput('')
    setSending(true)

    const userMsg = { id: Date.now(), role: 'user', content: q }
    const loadingMsg = { id: Date.now() + 1, role: 'assistant', content: '', loading: true }
    setMessages((prev) => [...prev, userMsg, loadingMsg])

    try {
      const { data } = await askQuestion(currentDataset.id, q)
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, content: data.answer, chart: data.chart, loading: false }
            : m
        )
      )
    } catch (err) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === loadingMsg.id
            ? { ...m, content: `Error: ${err.message}`, loading: false }
            : m
        )
      )
      addToast(err.message, 'error')
    } finally {
      setSending(false)
    }
  }

  if (!currentDataset) {
    return (
      <EmptyState
        icon={Upload}
        title="No dataset selected"
        description="Upload a dataset to start chatting with the AI analyst."
        action={<button onClick={() => navigate('/upload')} className="btn-primary">Upload Dataset</button>}
      />
    )
  }

  return (
    <div className="max-w-4xl mx-auto flex flex-col h-[calc(100vh-9rem)]">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <div>
          <h1 className="page-title mb-1">AI Query Engine</h1>
          <p className="page-subtitle text-sm">Ask anything about <span className="text-brand-400">{currentDataset.original_filename}</span></p>
        </div>
        <div className="badge-brand">
          <BarChart2 size={12} />
          {currentDataset.row_count?.toLocaleString()} rows
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto space-y-5 pr-2 min-h-0">
        <AnimatePresence initial={false}>
          {messages.map((msg) => <Message key={msg.id} msg={msg} />)}
        </AnimatePresence>
        <div ref={bottomRef} />
      </div>

      {/* Suggestions */}
      {messages.length <= 1 && (
        <div className="flex-shrink-0 mt-4">
          <p className="text-xs text-surface-500 mb-2 flex items-center gap-1">
            <Lightbulb size={11} /> Suggested questions
          </p>
          <div className="flex flex-wrap gap-2">
            {SUGGESTIONS.slice(0, 4).map((s) => (
              <button
                key={s}
                onClick={() => send(s)}
                className="px-3 py-1.5 rounded-full bg-surface-800 border border-surface-700 text-xs text-surface-300 hover:text-white hover:border-brand-500/50 transition-all"
              >
                {s}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Input */}
      <div className="flex-shrink-0 mt-4">
        <div className="flex gap-3 items-end">
          <div className="flex-1 relative">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault()
                  send()
                }
              }}
              placeholder="Ask anything about your data... (Enter to send)"
              rows={2}
              className="input resize-none py-3 pr-12 text-sm"
              disabled={sending}
            />
          </div>
          <button
            onClick={() => send()}
            disabled={!input.trim() || sending}
            className="btn-primary h-12 w-12 flex items-center justify-center flex-shrink-0 p-0"
          >
            {sending ? <Loader2 size={16} className="animate-spin" /> : <Send size={16} />}
          </button>
        </div>
        <p className="text-xs text-surface-600 mt-1.5 text-right">Shift+Enter for new line · Enter to send</p>
      </div>
    </div>
  )
}
