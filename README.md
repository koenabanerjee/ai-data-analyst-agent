# AI Data Analyst Agent

> Autonomous AI system for automated exploratory data analysis, statistical insights, and professional reporting.

**Tech:** Python · FastAPI · LangGraph · Gemini AI · React · Tailwind · Plotly · ReportLab

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                      FRONTEND                        │
│  React + Tailwind · 7 pages · Plotly charts          │
│  Zustand state · Framer Motion animations            │
└─────────────────────┬────────────────────────────────┘
                      │ HTTP / REST
┌─────────────────────▼───────────────────────────────-┐
│                       BACKEND                        │
│  FastAPI · Async · Pydantic v2 · SQLAlchemy async    │
│                                                      │
│  ┌────────────────────────────────────────────────┐  │
│  │              LANGGRAPH PIPELINE                │  │
│  │  SchemaAgent → EDAAgent → MissingValueAgent    │  │
│  │    → OutlierAgent → CorrelationAgent           │  │
│  │      → InsightAgent → VisualizationAgent       │  │
│  │        → ReportAgent                           │  │
│  └────────────────────────────────────────────────┘  │
│                                                      │
│  QueryAgent (NL queries)                             │
│  ReportService (ReportLab PDF)                       │
│  SQLite / PostgreSQL (SQLAlchemy async)              │
└──────────────────────────────────────────────────────┘
```

## Features

- **Smart Upload** — CSV/XLSX, drag-and-drop, schema detection, duplicate detection, file validation
- **8-Agent EDA Pipeline** — LangGraph StateGraph with full agent orchestration
- **Statistical Analysis** — mean, median, mode, std, variance, quartiles, skewness, kurtosis
- **Missing Value Analysis** — automated imputation recommendations with reasoning
- **Outlier Detection** — IQR and Z-score methods with bounds and counts
- **Correlation Analysis** — Pearson matrix with strong correlation identification
- **AI Insights** — Gemini-powered human-like analyst narratives
- **Interactive Charts** — 8 chart types auto-selected by Visualization Agent
- **NL Query Engine** — plain English questions with chart responses
- **PDF Reports** — professional ReportLab reports with all findings

---



