"""Generate downloadable PDF for the humanoid intelligence report."""
from __future__ import annotations

import html
import io
import re
from datetime import datetime, timezone
from typing import Any, List

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from app.services.humanoid_deployment_report import TIER_LABELS
from app.services.humanoid_scraper import HEIF_DIMS

TEAL = colors.HexColor("#0d9488")
PURPLE = colors.HexColor("#6d28d9")
MUTED = colors.HexColor("#64748b")
INK = colors.HexColor("#1e293b")


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
                ("FONTSIZE", (0, 0), (-1, 0), 9),
                ("FONTSIZE", (0, 1), (-1, -1), 8),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#e2e8f0")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return t


def _pdf_filename(report: dict) -> str:
    title = report.get("title") or "Humanoid_Intelligence_Report"
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
    return f"{slug}.pdf"


def _section(story: list, title: str, h2: ParagraphStyle) -> None:
    story.append(Paragraph(title, h2))


def _paragraphs(story: list, lines: List[str], style: ParagraphStyle) -> None:
    for line in lines:
        if line and str(line).strip():
            story.append(Paragraph(_esc(line), style))


def build_humanoid_intelligence_report_pdf(payload: dict) -> tuple[bytes, str]:
    """Build PDF bytes from build_humanoid_intelligence_report_payload() result."""
    report = payload.get("report")
    if not report:
        raise ValueError("Report payload is empty")

    narrative = report.get("narrative") or {}
    glance = narrative.get("at_a_glance") or {}

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.7 * inch,
        leftMargin=0.7 * inch,
        topMargin=0.65 * inch,
        bottomMargin=0.75 * inch,
    )
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "RptTitle",
        parent=styles["Heading1"],
        fontSize=22,
        textColor=PURPLE,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    )
    subtitle_style = ParagraphStyle(
        "RptSub",
        parent=styles["Normal"],
        fontSize=11,
        textColor=MUTED,
        alignment=TA_CENTER,
        spaceAfter=10,
    )
    h2 = ParagraphStyle(
        "RptH2",
        parent=styles["Heading2"],
        fontSize=14,
        textColor=TEAL,
        spaceBefore=16,
        spaceAfter=8,
        fontName="Helvetica-Bold",
    )
    h3 = ParagraphStyle(
        "RptH3",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=INK,
        spaceBefore=10,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    )
    body = ParagraphStyle(
        "RptBody",
        parent=styles["Normal"],
        fontSize=10,
        leading=14,
        spaceAfter=8,
        alignment=TA_JUSTIFY,
        textColor=INK,
    )
    bullet = ParagraphStyle(
        "RptBullet",
        parent=body,
        leftIndent=14,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )
    finding_style = ParagraphStyle(
        "RptFinding",
        parent=body,
        leftIndent=0,
        spaceAfter=10,
    )

    story: list[Any] = []
    generated = payload.get("generated_at") or datetime.now(timezone.utc).isoformat()

    story.append(Spacer(1, 0.35 * inch))
    story.append(Paragraph(_esc(report.get("title")), title_style))
    story.append(Paragraph(_esc(narrative.get("subtitle") or report.get("subtitle")), subtitle_style))
    story.append(Paragraph(
        f"Ready For Robots · HEIR 2026 / HEIF · Generated {generated[:10]} · readyforrobots.com/robots",
        subtitle_style,
    ))

    if glance:
        story.append(Spacer(1, 10))
        glance_rows = [
            ["At a glance", ""],
            ["Robots indexed", _esc(glance.get("robots_indexed"))],
            ["Index leader", _esc(f"{glance.get('index_leader')} ({glance.get('index_leader_score')})")],
            ["PoC-or-better (fleet)", _esc(f"{glance.get('poc_or_better_pct')}%")],
            ["Commercial / fleet signals", _esc(f"{glance.get('commercial_signal_pct')}%")],
            ["Distinct dimension leaders", _esc(glance.get("dimension_leader_count"))],
        ]
        gt = Table(glance_rows, colWidths=[2.2 * inch, 3.8 * inch])
        gt.setStyle(
            TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("SPAN", (0, 0), (1, 0)),
                ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f5f3ff")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#c4b5fd")),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ])
        )
        story.append(gt)

    _section(story, "Market overview", h2)
    _paragraphs(story, narrative.get("market_overview") or [], body)
    if not narrative.get("market_overview"):
        for line in report.get("executive_summary") or []:
            story.append(Paragraph(f"• {_esc(line)}", bullet))

    mom = report.get("month_over_month") or {}
    if mom.get("has_prior"):
        _section(story, f"Month over month (vs {mom.get('previous_period')})", h2)
        for line in mom.get("narrative_bullets") or []:
            story.append(Paragraph(f"• {_esc(line)}", bullet))
        leader = mom.get("leader") or {}
        if leader.get("changed"):
            story.append(Paragraph(
                f"<b>Leader change:</b> {_esc(leader.get('previous', {}).get('name'))} → "
                f"{_esc(leader.get('current', {}).get('name'))}",
                body,
            ))
        fm = mom.get("fleet_metrics") or {}
        if fm:
            mom_rows = [["Metric", "Prior", "Current", "Δ"]]
            for label, key in (
                ("Robots indexed", "total_robots"),
                ("PoC-or-better", "poc_or_better_count"),
                ("Commercial signals", "deployment_signal_count"),
                ("Avg HEIF", "fleet_avg_heif"),
            ):
                block = fm.get(key)
                if block:
                    mom_rows.append([
                        label,
                        _esc(block.get("previous")),
                        _esc(block.get("current")),
                        _esc(block.get("delta")),
                    ])
            if len(mom_rows) > 1:
                story.append(_table(mom_rows, [1.5 * inch, 0.9 * inch, 0.9 * inch, 0.8 * inch]))
        movers = [m for m in (mom.get("movers") or []) if m.get("type") == "mover"][:6]
        if movers:
            mrows = [["Robot", "Rank was", "Rank now", "Score Δ"]]
            for m in movers:
                mrows.append([
                    _esc(m.get("name")),
                    _esc(m.get("rank_previous")),
                    _esc(m.get("rank_current")),
                    _esc(m.get("score_delta")),
                ])
            story.append(_table(mrows, [1.8 * inch, 0.8 * inch, 0.8 * inch, 0.8 * inch]))
    elif mom.get("baseline_note"):
        _section(story, "Month over month", h2)
        story.append(Paragraph(_esc(mom.get("baseline_note")), body))

    findings = narrative.get("key_findings") or []
    if findings:
        _section(story, "Key findings", h2)
        for item in findings:
            story.append(Paragraph(f"<b>{_esc(item.get('title'))}</b>", h3))
            story.append(Paragraph(_esc(item.get("body")), finding_style))

    for section_title, key in (
        ("Competitive dynamics", "competitive_dynamics"),
        ("Deployment reality", "deployment_reality"),
        ("How to read the rankings", "ranking_commentary"),
    ):
        lines = narrative.get(key) or []
        if lines:
            _section(story, section_title, h2)
            _paragraphs(story, lines, body)

    metrics = report.get("adoption_metrics") or {}
    _section(story, "Evidence base (full fleet)", h2)
    metric_rows = [
        ["Metric", "Value"],
        ["Robots in index", _esc(metrics.get("fleet_total_robots") or report.get("total_robots"))],
        ["PoC-or-better evidence", _esc(f"{metrics.get('fleet_poc_or_better_count')} ({metrics.get('fleet_poc_or_better_pct')}%)")],
        ["Commercial / fleet signals", _esc(metrics.get("fleet_deployment_signal_count"))],
        ["Capability-only scoring", _esc(metrics.get("fleet_capability_only_count"))],
        ["With news in catalog", _esc(metrics.get("fleet_with_news_sources"))],
    ]
    story.append(_table(metric_rows, [2.6 * inch, 3.6 * inch]))

    comparisons = report.get("comparisons") or {}
    divergence = comparisons.get("ranking_divergence") or []
    if divergence:
        _section(story, "Index vs deployment-weighted rank", h2)
        drows = [["Robot", "Index #", "Deployment #", "Comment"]]
        for d in divergence[:6]:
            drows.append([
                _esc(d.get("name")),
                _esc(d.get("index_rank")),
                _esc(d.get("deployment_weighted_rank")),
                _esc(d.get("commentary")),
            ])
        story.append(_table(drows, [1.4 * inch, 0.65 * inch, 0.85 * inch, 2.4 * inch]))

    leaders = comparisons.get("dimension_leaders") or []
    if leaders:
        _section(story, "Who leads each HEIF dimension", h2)
        lrows = [["Dimension", "Robot", "Vendor", "HEIF", "Index"]]
        for entry in leaders:
            lrows.append([
                _esc(entry.get("dimension")),
                _esc(entry.get("name")),
                _esc(entry.get("vendor")),
                _esc(entry.get("heif")),
                _esc(entry.get("index_score")),
            ])
        story.append(_table(lrows, [1.15 * inch, 1.45 * inch, 1.25 * inch, 0.55 * inch, 0.55 * inch]))

    idx_dep = comparisons.get("index_vs_deployment") or []
    if idx_dep:
        story.append(PageBreak())
        _section(story, "Top robots — capability vs field evidence", h2)
        story.append(Paragraph(
            "Index score reflects engineering maturity from specs and HEIR research. "
            "Deployment tier reflects catalog status, deployment counts, and news. "
            "Gap = high HEIF (≥2.5) but tier still PoC or weaker.",
            body,
        ))
        irows = [["#", "Robot", "Index", "HEIF", "Tier", "Depl.", "Gap"]]
        for row in idx_dep:
            irows.append([
                _esc(row.get("rank")),
                _esc(row.get("name")),
                _esc(row.get("score_total")),
                _esc(row.get("heif_total")),
                _esc((row.get("deployment_tier_label") or "")[:22]),
                _esc(row.get("commercial_deployments")),
                _esc("Yes" if row.get("capability_ahead_of_deployment") else ""),
            ])
        story.append(_table(irows, [0.35 * inch, 1.55 * inch, 0.5 * inch, 0.45 * inch, 1.35 * inch, 0.45 * inch, 0.4 * inch]))

    matrix = comparisons.get("peer_heif_matrix") or {}
    matrix_robots = matrix.get("robots") or []
    if matrix_robots:
        _section(story, "Peer comparison — HEIF by dimension (0–4)", h2)
        dim_labels = matrix.get("dimension_labels") or []
        header = ["Robot", "Total"] + [lbl[:7] for lbl in dim_labels]
        mrows = [header]
        for r in matrix_robots:
            dims = r.get("dimensions") or {}
            mrows.append(
                [_esc((r.get("name") or "")[:20]), _esc(r.get("heif_total"))]
                + [_esc(dims.get(dim, "")) for dim in HEIF_DIMS]
            )
        story.append(_table(mrows, [1.35 * inch, 0.5 * inch] + [0.52 * inch] * 6))

    vendors = comparisons.get("vendor_leaderboard") or []
    if vendors:
        _section(story, "Vendor comparison", h2)
        vrows = [["Vendor", "Models", "PoC+", "Commercial", "Deployments"]]
        for v in vendors[:10]:
            vrows.append([
                _esc(v.get("vendor")),
                _esc(v.get("robot_count")),
                _esc(f"{v.get('poc_or_deployment')} ({v.get('poc_or_deployment_pct')}%)"),
                _esc(v.get("deployment_signal")),
                _esc(v.get("total_deployments")),
            ])
        story.append(_table(vrows, [1.5 * inch, 0.65 * inch, 1.0 * inch, 0.9 * inch, 1.0 * inch]))

    guidance = narrative.get("buyer_guidance") or []
    if guidance:
        _section(story, "Buyer guidance", h2)
        for g in guidance:
            story.append(Paragraph(f"• {_esc(g)}", bullet))

    story.append(PageBreak())
    _section(story, "Robot profiles (top ranked)", h2)
    for robot in report.get("top_ranked") or []:
        story.append(Paragraph(
            f"<b>#{robot.get('rank')} {_esc(robot.get('name'))}</b> — {_esc(robot.get('vendor'))}",
            h3,
        ))
        story.append(Paragraph(
            f"Index {_esc(robot.get('score_total'))} · HEIF {_esc(robot.get('heif_total'))}/4 · "
            f"{_esc(robot.get('deployment_tier_label'))}",
            body,
        ))
        story.append(Paragraph(_esc(robot.get("why_top_rank")), finding_style))

    _section(story, "Methodology", h2)
    story.append(Paragraph(_esc(report.get("methodology")), body))
    story.append(Paragraph(
        "Verify customer names and deployment claims before external citation. "
        "© Ready For Robots — monthly index update.",
        bullet,
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue(), _pdf_filename(report)
