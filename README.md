# AI Data Analyst Agent

> Autonomous AI system for automated exploratory data analysis, statistical insights, and professional reporting.

**Tech:** Python · FastAPI · LangGraph · Gemini AI · React · Tailwind · Plotly · ReportLab

---

## Architecture

```
┌──────────────────────────────────────────────────────┐
│                      FRONTEND                         │
│  React + Tailwind · 7 pages · Plotly charts          │
│  Zustand state · Framer Motion animations             │
└─────────────────────┬────────────────────────────────┘
                      │ HTTP / REST
┌─────────────────────▼────────────────────────────────┐
│                       BACKEND                         │
│  FastAPI · Async · Pydantic v2 · SQLAlchemy async    │
│                                                        │
│  ┌────────────────────────────────────────────────┐  │
│  │              LANGGRAPH PIPELINE                 │  │
│  │  SchemaAgent → EDAAgent → MissingValueAgent    │  │
│  │    → OutlierAgent → CorrelationAgent           │  │
│  │      → InsightAgent → VisualizationAgent       │  │
│  │        → ReportAgent                           │  │
│  └────────────────────────────────────────────────┘  │
│                                                        │
│  QueryAgent (on-demand NL queries)                    │
│  ReportService (ReportLab PDF)                        │
│  SQLite / PostgreSQL (SQLAlchemy async)               │
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

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- A Gemini API key (or OpenAI API key)

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env — add your GOOGLE_API_KEY

# Run
uvicorn app.main:app --reload --port 8000
```

Backend runs at: http://localhost:8000  
API docs: http://localhost:8000/docs

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# VITE_API_URL=http://localhost:8000/api/v1

# Run
npm run dev
```

Frontend runs at: http://localhost:3000

---

## API Reference

### Upload
```
POST   /api/v1/upload                    Upload CSV/XLSX
```

### Datasets
```
GET    /api/v1/datasets                  List all datasets
GET    /api/v1/datasets/{id}/preview     Preview rows and schema
DELETE /api/v1/datasets/{id}             Delete dataset
```

### Analysis
```
POST   /api/v1/analysis/{id}/run-sync    Run full EDA pipeline (sync)
POST   /api/v1/analysis/{id}/run         Run EDA in background
GET    /api/v1/analysis/{id}/eda         Get cached EDA result
GET    /api/v1/analysis/{id}/visualizations  Get charts only
GET    /api/v1/analysis/{id}/insights    Get AI insights only
```

### Query
```
POST   /api/v1/query/{id}               Ask a natural language question
GET    /api/v1/query/{id}/history       Get query history
```

### Report
```
POST   /api/v1/report/{id}/generate     Generate PDF report
GET    /api/v1/report/{id}/download     Download PDF
```

---

## Deployment

### Backend → Render

1. Push to GitHub
2. Create new **Web Service** on [render.com](https://render.com)
3. Set:
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables from `.env.example`

### Frontend → Vercel

```bash
cd frontend
npm run build

# Deploy with Vercel CLI
npx vercel --prod

# Or connect GitHub repo in Vercel dashboard
# Set VITE_API_URL to your Render backend URL
```

### Database → PostgreSQL

Replace SQLite with PostgreSQL by changing `.env`:
```
DATABASE_URL=postgresql+asyncpg://user:pass@host/dbname
```

Add to requirements.txt:
```
asyncpg==0.29.0
```

---

## Project Structure

```
ai-data-analyst/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   │   └── workflow.py          # LangGraph 8-agent pipeline
│   │   ├── models/
│   │   │   ├── database.py          # SQLAlchemy async models
│   │   │   └── schemas.py           # Pydantic v2 schemas
│   │   ├── routes/
│   │   │   ├── upload.py            # File upload endpoint
│   │   │   ├── datasets.py          # Dataset CRUD
│   │   │   ├── analysis.py          # EDA trigger/retrieve
│   │   │   ├── query.py             # NL query endpoint
│   │   │   └── report.py            # PDF generation/download
│   │   ├── services/
│   │   │   ├── dataset_service.py   # Dataset business logic
│   │   │   └── report_service.py    # ReportLab PDF builder
│   │   ├── utils/
│   │   │   ├── ai_client.py         # Gemini/OpenAI wrapper
│   │   │   ├── data_utils.py        # Pandas/NumPy helpers
│   │   │   ├── viz_utils.py         # Plotly chart builders
│   │   │   └── logging.py           # Structured logging
│   │   ├── config.py                # Pydantic settings
│   │   └── main.py                  # FastAPI app entry
│   ├── requirements.txt
│   └── .env.example
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── charts/PlotlyChart.jsx
    │   │   ├── layout/Layout.jsx
    │   │   └── ui/                  # Reusable UI components
    │   ├── pages/
    │   │   ├── HomePage.jsx
    │   │   ├── UploadPage.jsx
    │   │   ├── OverviewPage.jsx
    │   │   ├── AnalyticsPage.jsx
    │   │   ├── VisualizePage.jsx
    │   │   ├── ChatPage.jsx
    │   │   └── ReportPage.jsx
    │   ├── store/index.js            # Zustand global state
    │   ├── utils/api.js              # Axios API client
    │   ├── App.jsx                   # React Router
    │   └── main.jsx
    ├── package.json
    ├── vite.config.js
    ├── tailwind.config.js
    └── .env.example
```

---

## Environment Variables

### Backend (.env)
| Variable | Description |
|----------|-------------|
| `GOOGLE_API_KEY` | Gemini API key (primary AI provider) |
| `OPENAI_API_KEY` | OpenAI key (optional fallback) |
| `AI_PROVIDER` | `gemini` or `openai` |
| `DATABASE_URL` | SQLite or PostgreSQL connection string |
| `UPLOAD_DIR` | Directory for uploaded files |
| `MAX_UPLOAD_SIZE_MB` | Max file size (default: 50) |
| `CORS_ORIGINS` | Comma-separated allowed origins |

### Frontend (.env)
| Variable | Description |
|----------|-------------|
| `VITE_API_URL` | Backend API base URL |

---

Built with ❤️ — AI/ML + SWE production project
