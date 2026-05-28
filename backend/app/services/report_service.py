"""
app/services/report_service.py — Professional PDF report generation with ReportLab
"""
from __future__ import annotations

import io
import os
import time
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm, mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from app.config import get_settings
from app.utils.logging import get_logger

logger = get_logger(__name__)
settings = get_settings()

# Color palette
DARK_BG = colors.HexColor("#0F172A")
ACCENT = colors.HexColor("#6366F1")
ACCENT_LIGHT = colors.HexColor("#818CF8")
TEXT = colors.HexColor("#1E293B")
TEXT_MUTED = colors.HexColor("#64748B")
SURFACE = colors.HexColor("#F1F5F9")
SUCCESS = colors.HexColor("#10B981")
WARNING = colors.HexColor("#F59E0B")
DANGER = colors.HexColor("#EF4444")


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle("cover_title", fontSize=32, textColor=colors.white,
                                       alignment=TA_CENTER, spaceAfter=10, fontName="Helvetica-Bold"),
        "cover_sub": ParagraphStyle("cover_sub", fontSize=14, textColor=colors.HexColor("#CBD5E1"),
                                     alignment=TA_CENTER, spaceAfter=6),
        "h1": ParagraphStyle("h1", fontSize=20, textColor=ACCENT, fontName="Helvetica-Bold",
                              spaceBefore=16, spaceAfter=8),
        "h2": ParagraphStyle("h2", fontSize=14, textColor=TEXT, fontName="Helvetica-Bold",
                              spaceBefore=12, spaceAfter=6),
        "body": ParagraphStyle("body", fontSize=10, textColor=TEXT, leading=15, spaceAfter=6),
        "muted": ParagraphStyle("muted", fontSize=9, textColor=TEXT_MUTED, leading=13, spaceAfter=4),
        "label": ParagraphStyle("label", fontSize=9, textColor=ACCENT, fontName="Helvetica-Bold"),
        "insight": ParagraphStyle("insight", fontSize=10, textColor=TEXT, leading=16,
                                   leftIndent=12, rightIndent=12, spaceAfter=8,
                                   backColor=SURFACE, borderPadding=(6, 6, 6, 6)),
    }


def _overview_table(overview: dict[str, Any]) -> Table:
    data = [
        ["Metric", "Value"],
        ["Total Rows", f"{overview.get('row_count', 0):,}"],
        ["Total Columns", f"{overview.get('column_count', 0)}"],
        ["Total Missing Values", f"{overview.get('total_nulls', 0):,}"],
        ["Missing Value %", f"{overview.get('null_pct', 0):.2f}%"],
        ["Duplicate Rows", f"{overview.get('duplicate_rows', 0):,}"],
        ["Memory Usage", f"{overview.get('memory_usage_kb', 0):.1f} KB"],
        ["Numeric Columns", f"{len(overview.get('numeric_columns', []))}"],
        ["Categorical Columns", f"{len(overview.get('categorical_columns', []))}"],
        ["Datetime Columns", f"{len(overview.get('datetime_columns', []))}"],
    ]
    t = Table(data, colWidths=[8 * cm, 8 * cm])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE]),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ("ALIGN", (1, 0), (1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING", (0, 0), (-1, -1), 10),
        ])
    )
    return t


def _stats_table(col_stats: list[dict[str, Any]], max_rows: int = 20) -> Table:
    headers = ["Column", "Type", "Nulls %", "Mean", "Median", "Std", "Min", "Max", "Skew"]
    data = [headers]
    for cs in col_stats[:max_rows]:
        if cs.get("mean") is not None:
            row = [
                cs["name"][:20],
                cs["dtype"][:10],
                f"{cs['null_pct']}%",
                f"{cs['mean']:.3f}" if cs.get("mean") is not None else "—",
                f"{cs['median']:.3f}" if cs.get("median") is not None else "—",
                f"{cs['std']:.3f}" if cs.get("std") is not None else "—",
                f"{cs['min']:.3f}" if cs.get("min") is not None else "—",
                f"{cs['max']:.3f}" if cs.get("max") is not None else "—",
                f"{cs['skewness']:.3f}" if cs.get("skewness") is not None else "—",
            ]
            data.append(row)
    if len(data) == 1:
        return Paragraph("No numeric columns found.", _styles()["muted"])  # type: ignore[return-value]
    col_widths = [4.5 * cm, 2.2 * cm, 2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2.2 * cm, 2 * cm]
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("ALIGN", (2, 1), (-1, -1), "RIGHT"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("OVERFLOW", (0, 0), (-1, -1), "TRUNCATE"),
        ])
    )
    return t


def _missing_table(recs: list[dict[str, Any]]) -> Table | Paragraph:
    if not recs:
        return Paragraph("✓ No missing values detected in this dataset.", _styles()["muted"])  # type: ignore[return-value]
    data = [["Column", "Missing %", "Recommendation", "Reason"]]
    for r in recs[:25]:
        data.append([
            r.get("column", "")[:20],
            f"{r.get('null_pct', 0):.1f}%",
            r.get("recommendation", "").replace("_", " ").title(),
            r.get("reason", "")[:80],
        ])
    t = Table(data, colWidths=[4 * cm, 2.5 * cm, 4 * cm, 8.5 * cm])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ])
    )
    return t


def _outlier_table(outlier_summary: dict[str, Any]) -> Table | Paragraph:
    columns_data = outlier_summary.get("columns", {})
    if not columns_data:
        return Paragraph("No outlier data available.", _styles()["muted"])  # type: ignore[return-value]
    data = [["Column", "IQR Outliers", "IQR %", "Z-Score Outliers", "Z-Score %"]]
    for col, info in list(columns_data.items())[:20]:
        iqr = info.get("iqr", {})
        z = info.get("zscore", {})
        data.append([
            col[:22],
            str(iqr.get("outlier_count", 0)),
            f"{iqr.get('outlier_pct', 0):.1f}%",
            str(z.get("outlier_count", 0)),
            f"{z.get('outlier_pct', 0):.1f}%",
        ])
    t = Table(data, colWidths=[5 * cm, 3.5 * cm, 2.5 * cm, 4 * cm, 3 * cm])
    t.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), DARK_BG),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, SURFACE]),
            ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#E2E8F0")),
            ("ALIGN", (1, 1), (-1, -1), "CENTER"),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ])
    )
    return t


async def generate_pdf_report(sections: dict[str, Any], dataset_id: str) -> str:
    """
    Generate a professional PDF report. Returns the file path.
    """
    reports_dir = Path(settings.upload_dir) / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    output_path = str(reports_dir / f"report_{dataset_id}.pdf")

    styles = _styles()
    story = []

    # ── Cover page ────────────────────────────────────────────────────────────
    story.append(Spacer(1, 3 * cm))

    # Dark header block
    cover_data = [[Paragraph("AI DATA ANALYST", styles["cover_title"]),],
                  [Paragraph("Automated Exploratory Data Analysis Report", styles["cover_sub"])],
                  [Paragraph(f"Dataset: {sections.get('dataset_name', 'Unknown')}", styles["cover_sub"])],
                  [Paragraph(f"Generated: {time.strftime('%B %d, %Y at %H:%M UTC')}", styles["cover_sub"])],
    ]
    cover_table = Table(cover_data, colWidths=[17 * cm])
    cover_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), DARK_BG),
        ("TOPPADDING", (0, 0), (-1, -1), 14),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 14),
        ("LEFTPADDING", (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    story.append(cover_table)
    story.append(Spacer(1, 1 * cm))

    # Key stats summary boxes
    overview = sections.get("overview", {})
    kpi_data = [[
        _kpi_cell("Total Rows", f"{overview.get('row_count', 0):,}"),
        _kpi_cell("Columns", str(overview.get("column_count", 0))),
        _kpi_cell("Missing %", f"{overview.get('null_pct', 0):.1f}%"),
        _kpi_cell("Duplicates", f"{overview.get('duplicate_rows', 0):,}"),
    ]]
    kpi_table = Table(kpi_data, colWidths=[4.2 * cm, 4.2 * cm, 4.2 * cm, 4.4 * cm])
    kpi_table.setStyle(TableStyle([
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("GRID", (0, 0), (-1, -1), 1, ACCENT),
    ]))
    story.append(kpi_table)
    story.append(PageBreak())

    # ── Section 1: Dataset Overview ───────────────────────────────────────────
    story.append(Paragraph("1. Dataset Overview", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 6))
    story.append(_overview_table(overview))
    story.append(Spacer(1, 12))

    nc = overview.get("numeric_columns", [])
    cc = overview.get("categorical_columns", [])
    if nc:
        story.append(Paragraph(f"<b>Numeric Columns ({len(nc)}):</b> {', '.join(nc)}", styles["muted"]))
    if cc:
        story.append(Paragraph(f"<b>Categorical Columns ({len(cc)}):</b> {', '.join(cc[:20])}", styles["muted"]))

    story.append(PageBreak())

    # ── Section 2: Statistical Analysis ──────────────────────────────────────
    story.append(Paragraph("2. Statistical Analysis", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 6))
    story.append(_stats_table(sections.get("column_stats", [])))
    story.append(PageBreak())

    # ── Section 3: Missing Values ─────────────────────────────────────────────
    story.append(Paragraph("3. Missing Value Analysis", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "The system automatically recommends the optimal imputation strategy per column based on distribution characteristics.",
        styles["body"]
    ))
    story.append(Spacer(1, 6))
    story.append(_missing_table(sections.get("missing_recommendations", [])))
    story.append(PageBreak())

    # ── Section 4: Outlier Analysis ───────────────────────────────────────────
    story.append(Paragraph("4. Outlier Analysis", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 6))
    story.append(Paragraph(
        "Outliers detected using two complementary methods: IQR (Interquartile Range) and Z-Score (threshold = 3σ).",
        styles["body"]
    ))
    story.append(Spacer(1, 6))
    story.append(_outlier_table(sections.get("outlier_summary", {})))

    corr = sections.get("correlation", {})
    sp = corr.get("strong_positive", [])
    sn = corr.get("strong_negative", [])
    if sp or sn:
        story.append(PageBreak())
        story.append(Paragraph("5. Correlation Findings", styles["h1"]))
        story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
        story.append(Spacer(1, 6))
        if sp:
            story.append(Paragraph("<b>Strong Positive Correlations (r ≥ 0.7):</b>", styles["h2"]))
            for c in sp[:8]:
                story.append(Paragraph(f"• <b>{c['col1']}</b> ↔ <b>{c['col2']}</b>: r = {c['r']:.3f}", styles["body"]))
        if sn:
            story.append(Paragraph("<b>Strong Negative Correlations (r ≤ −0.7):</b>", styles["h2"]))
            for c in sn[:8]:
                story.append(Paragraph(f"• <b>{c['col1']}</b> ↔ <b>{c['col2']}</b>: r = {c['r']:.3f}", styles["body"]))

    # ── Section 5: AI Insights ────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Paragraph("6. AI-Generated Insights", styles["h1"]))
    story.append(HRFlowable(width="100%", thickness=1, color=ACCENT))
    story.append(Spacer(1, 8))

    insights_raw = sections.get("ai_insights", "No insights available.")
    # Convert markdown to simple paragraphs
    for line in insights_raw.split("\n"):
        line = line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue
        if line.startswith("## "):
            story.append(Paragraph(line[3:], styles["h2"]))
        elif line.startswith("### "):
            story.append(Paragraph(f"<b>{line[4:]}</b>", styles["body"]))
        elif line.startswith("- ") or line.startswith("* "):
            story.append(Paragraph(f"• {line[2:]}", styles["body"]))
        else:
            story.append(Paragraph(line, styles["body"]))

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(PageBreak())
    story.append(Spacer(1, 3 * cm))
    story.append(Paragraph("Generated by AI Data Analyst Agent", styles["muted"]))
    story.append(Paragraph("Powered by Gemini AI · LangGraph · FastAPI", styles["muted"]))

    # ── Build ─────────────────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="AI Data Analyst Report",
        author="AI Data Analyst Agent",
    )

    doc.build(story, onFirstPage=_add_page_number, onLaterPages=_add_page_number)
    logger.info("PDF report generated: %s", output_path)
    return output_path


def _kpi_cell(label: str, value: str) -> Table:
    inner = Table(
        [[Paragraph(value, ParagraphStyle("kv", fontSize=18, fontName="Helvetica-Bold",
                                           textColor=ACCENT, alignment=TA_CENTER))],
         [Paragraph(label, ParagraphStyle("kl", fontSize=8, textColor=TEXT_MUTED, alignment=TA_CENTER))]],
    )
    inner.setStyle(TableStyle([("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]))
    return inner


def _add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(TEXT_MUTED)
    page_num = canvas.getPageNumber()
    canvas.drawRightString(A4[0] - 2 * cm, 1.2 * cm, f"Page {page_num}")
    canvas.drawString(2 * cm, 1.2 * cm, "AI Data Analyst Agent — Confidential")
    canvas.restoreState()
