import { useEffect, useRef } from 'react'
import { motion } from 'framer-motion'

// Dynamic import of Plotly to keep initial bundle lean
let Plotly = null
async function getPlotly() {
  if (!Plotly) {
    Plotly = (await import('plotly.js-dist-min')).default
  }
  return Plotly
}

export default function PlotlyChart({ plotlyJson, title, reason, className = '' }) {
  const divRef = useRef(null)

  useEffect(() => {
    if (!plotlyJson || !divRef.current) return
    let mounted = true

    getPlotly().then((P) => {
      if (!mounted || !divRef.current) return
      const layout = {
        ...plotlyJson.layout,
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)',
        font: { color: '#cbd5e1', family: 'DM Sans' },
        margin: { t: 40, b: 40, l: 50, r: 20 },
        xaxis: { ...plotlyJson.layout?.xaxis, gridcolor: '#1e293b', linecolor: '#334155', color: '#94a3b8' },
        yaxis: { ...plotlyJson.layout?.yaxis, gridcolor: '#1e293b', linecolor: '#334155', color: '#94a3b8' },
        colorway: ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#06b6d4', '#8b5cf6', '#f97316'],
      }
      P.newPlot(divRef.current, plotlyJson.data, layout, {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['sendDataToCloud', 'editInChartStudio'],
        toImageButtonOptions: { format: 'png', scale: 2 },
      })
    })

    return () => {
      mounted = false
      if (divRef.current && Plotly) {
        try { Plotly.purge(divRef.current) } catch (_) {}
      }
    }
  }, [plotlyJson])

  if (!plotlyJson) return null

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      className={`card ${className}`}
    >
      {title && <h3 className="text-sm font-semibold text-surface-200 mb-1">{title}</h3>}
      {reason && <p className="text-xs text-surface-500 mb-3 italic">{reason}</p>}
      <div ref={divRef} className="w-full min-h-[360px]" />
    </motion.div>
  )
}
