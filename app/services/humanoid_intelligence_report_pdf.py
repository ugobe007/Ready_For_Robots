"""Generate downloadable PDF for the humanoid intelligence report."""
from __future__ import annotations

import html
import io
import re
from datetime import datetime, timezone
from typing import Any, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.humanoid_deployment_report import TIER_LABELS
from app.services.humanoid_scraper import HEIF_DIMS

TEAL = colors.HexColor("#0d9488")
PURPLE = colors.HexColor("#6d28d9")
MUTED = colors.HexColor("#64748b")


def _esc(text: Any) -> str:
    if text is None:
        return "—"
    return html.escape(str(text))


def _table(data: List[List[Any]], col_widths: List[float] | None = None) -> Table:
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), TEAL),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, 0), 8),
                ("FONTSIZE", (0, 1), (-1, -1), 7),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    return t


def _pdf_filename(report: dict) -> str:
    title = report.get("title") or "Humanoid_Intelligence_Report"
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
    return f"{slug}.pdf"


def build_humanoid_intelligence_report_pdf(payload: dict) -> tuple[bytes, str]:
    """
    Build PDF bytes from build_humanoid_intelligence_report_payload() result.
    Returns (pdf_bytes, suggested_filename).
    """
    report = payload.get("report")
    if not report:
        raise ValueError("Report payload is empty")

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "RptTitle",
        parent=styles["Heading1"],
        fontSize=20,
        textColor=PURPLE,
        spaceAfter=8,
        alignment=TA_CENTER,
    )
    subtitle_style = ParagraphStyle(
        "RptSub",
        parent=styles["Normal"],
        fontSize=10,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=16,
    )
    h2 = ParagraphStyle(
        "RptH2",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=TEAL,
        spaceBefore=14,
        spaceAfter=8,
    )
    body = ParagraphStyle(
        "RptBody",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        spaceAfter=6,
    )
    bullet = ParagraphStyle(
        "RptBullet",
        parent=body,
        leftIndent=12,
        bulletIndent=0,
        spaceAfter=4,
    )

    story: list[Any] = []
    generated = payload.get("generated_at") or datetime.now(timezone.utc).isoformat()

    story.append(Spacer(1, 0.4 * inch))
    story.append(Paragraph(_esc(report.get("title")), title_style))
    story.append(Paragraph("Ready For Robots · HEIR 2026 / HEIF methodology", subtitle_style))
    story.append(Paragraph(f"Generated {generated[:10]} · readyforrobots.com/robots", subtitle_style))
    story.append(Spacer(1, 12))
    story.append(Paragraph(_esc(report.get("framework")), body))
    story.append(Spacer(1, 8))

    story.append(Paragraph("Executive summary", h2))
    for line in report.get("executive_summary") or []:
        story.append(Paragraph(f"• {_esc(line)}", bullet))

    metrics = report.get("adoption_metrics") or {}
    story.append(Paragraph("Market adoption metrics (full fleet)", h2))
    metric_rows = [
        ["Metric", "Value"],
        ["Robots in index", _esc(metrics.get("fleet_total_robots") or report.get("total_robots"))],
        ["PoC-or-better evidence", _esc(f"{metrics.get('fleet_poc_or_better_count')} ({metrics.get('fleet_poc_or_better_pct')}%)")],
        ["Commercial / fleet signals", _esc(metrics.get("fleet_deployment_signal_count"))],
        ["With deployment-news sources", _esc(metrics.get("fleet_with_news_sources"))],
        ["Capability-only (no field evidence)", _esc(metrics.get("fleet_capability_only_count"))],
        ["Top-12 trial/PoC headlines", _esc(metrics.get("news_trial_headlines_top_slice"))],
        ["Top-12 deployment headlines", _esc(metrics.get("news_deployment_headlines_top_slice"))],
        ["Top-12 named customers in press", _esc(metrics.get("robots_with_named_customers_top_slice"))],
    ]
    story.append(_table(metric_rows, [2.8 * inch, 3.5 * inch]))

    comparisons = report.get("comparisons") or {}
    tier_breakdown = comparisons.get("fleet_deployment_tier_breakdown") or {}
    if tier_breakdown:
        story.append(Paragraph("Deployment tier breakdown (all robots)", h2))
        tier_rows = [["Tier", "Count"]]
        for tier, count in tier_breakdown.items():
            if count:
                label = TIER_LABELS.get(tier, tier)
                tier_rows.append([_esc(label), _esc(count)])
        story.append(_table(tier_rows, [4.2 * inch, 1.2 * inch]))

    vendors = comparisons.get("vendor_leaderboard") or []
    if vendors:
        story.append(Paragraph("Vendor comparison — deployment signals", h2))
        vrows = [["Vendor", "Robots", "PoC+", "Commercial", "Deployments"]]
        for v in vendors[:12]:
            vrows.append([
                _esc(v.get("vendor")),
                _esc(v.get("robot_count")),
                _esc(f"{v.get('poc_or_deployment')} ({v.get('poc_or_deployment_pct')}%)"),
                _esc(v.get("deployment_signal")),
                _esc(v.get("total_deployments")),
            ])
        story.append(_table(vrows, [1.6 * inch, 0.7 * inch, 1.1 * inch, 1.0 * inch, 1.0 * inch]))

    leaders = comparisons.get("dimension_leaders") or []
    if leaders:
        story.append(Paragraph("HEIF dimension leaders (who wins each category)", h2))
        lrows = [["Dimension", "Robot", "Vendor", "HEIF", "Index"]]
        for entry in leaders:
            lrows.append([
                _esc(entry.get("dimension")),
                _esc(entry.get("name")),
                _esc(entry.get("vendor")),
                _esc(entry.get("heif")),
                _esc(entry.get("index_score")),
            ])
        story.append(_table(lrows, [1.2 * inch, 1.5 * inch, 1.3 * inch, 0.6 * inch, 0.6 * inch]))

    idx_dep = comparisons.get("index_vs_deployment") or []
    if idx_dep:
        story.append(PageBreak())
        story.append(Paragraph("Top robots: capability vs deployment evidence", h2))
        irows = [["#", "Robot", "Index", "HEIF", "Tier", "Depl.", "News", "Gap?"]]
        for row in idx_dep:
            news = f"T{row.get('news_trial_headlines', 0)}/D{row.get('news_deployment_headlines', 0)}"
            irows.append([
                _esc(row.get("rank")),
                _esc(row.get("name")),
                _esc(row.get("score_total")),
                _esc(row.get("heif_total")),
                _esc((row.get("deployment_tier") or "")[:12]),
                _esc(row.get("commercial_deployments")),
                _esc(news),
                _esc("Yes" if row.get("capability_ahead_of_deployment") else ""),
            ])
        story.append(_table(irows, [0.35 * inch, 1.5 * inch, 0.55 * inch, 0.5 * inch, 0.85 * inch, 0.5 * inch, 0.55 * inch, 0.4 * inch]))

    matrix = comparisons.get("peer_heif_matrix") or {}
    matrix_robots = matrix.get("robots") or []
    dim_labels = matrix.get("dimension_labels") or []
    if matrix_robots and dim_labels:
        story.append(Paragraph("Peer HEIF comparison (top slice, 0–4 per dimension)", h2))
        header = ["Robot", "Total"] + [lbl[:8] for lbl in dim_labels]
        mrows = [header]
        for r in matrix_robots:
            dims = r.get("dimensions") or {}
            mrows.append(
                [_esc((r.get("name") or "")[:18]), _esc(r.get("heif_total"))]
                + [_esc(dims.get(dim, "")) for dim in HEIF_DIMS]
            )
        col_w = [1.4 * inch] + [0.55 * inch] + [0.55 * inch] * 6
        story.append(_table(mrows, col_w))

    gaps = comparisons.get("capability_vs_deployment_gaps") or {}
    high_gap = gaps.get("high_heif_low_use") or []
    if high_gap:
        story.append(Paragraph("Capability ahead of deployment (HEIF ≥2.5, tier ≤ PoC)", h2))
        grows = [["Robot", "HEIF", "Tier", "Deployments"]]
        for g in high_gap[:8]:
            grows.append([
                _esc(g.get("name")),
                _esc(g.get("heif_total")),
                _esc(g.get("deployment_tier")),
                _esc(g.get("commercial_deployments")),
            ])
        story.append(_table(grows, [2.2 * inch, 0.7 * inch, 1.2 * inch, 1.0 * inch]))

    customers = report.get("customer_landscape") or []
    if customers:
        story.append(Paragraph("Customers in press coverage", h2))
        crows = [["Customer", "Robots", "Deploy / trial headlines"]]
        for c in customers[:15]:
            crows.append([
                _esc(c.get("customer")),
                _esc(", ".join((c.get("robots") or [])[:3])),
                _esc(f"{c.get('deployment_headlines', 0)} / {c.get('trial_headlines', 0)}"),
            ])
        story.append(_table(crows, [1.5 * inch, 2.5 * inch, 1.3 * inch]))

    story.append(PageBreak())
    story.append(Paragraph("Top-ranked robots — score drivers & evidence", h2))
    for robot in report.get("top_ranked") or []:
        story.append(Paragraph(
            f"<b>#{robot.get('rank')} {_esc(robot.get('name'))}</b> · {_esc(robot.get('vendor'))} · "
            f"Index {_esc(robot.get('score_total'))} · HEIF {_esc(robot.get('heif_total'))} · "
            f"{_esc(robot.get('deployment_tier_label'))}",
            body,
        ))
        story.append(Paragraph(_esc(robot.get("why_top_rank")), body))
        cust = (robot.get("customer_integrations") or {}).get("named_customers") or []
        if cust:
            story.append(Paragraph(f"Customers: {_esc(', '.join(cust[:6]))}", body))
        for headline in (robot.get("top_headlines") or [])[:2]:
            if headline.get("title"):
                story.append(Paragraph(f"• {_esc(headline.get('title'))}", bullet))
        rationale = robot.get("score_rationale") or {}
        top_dims = sorted(
            rationale.items(),
            key=lambda x: float((x[1] or {}).get("heif") or 0),
            reverse=True,
        )[:3]
        for _key, dim in top_dims:
            drivers = "; ".join((dim.get("drivers") or [])[:2])
            story.append(Paragraph(
                f"{_esc(dim.get('label'))}: HEIF {_esc(dim.get('heif'))} — {_esc(drivers)}",
                bullet,
            ))
        story.append(Spacer(1, 8))

    story.append(Paragraph("Methodology & disclaimer", h2))
    story.append(Paragraph(_esc(report.get("methodology")), body))
    story.append(Paragraph(
        "Scores and deployment counts are derived from public vendor pages, HEIR 2026 research, "
        "and automated news scanning. Verify all customer names and deployment claims before external citation.",
        body,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue(), _pdf_filename(report)
