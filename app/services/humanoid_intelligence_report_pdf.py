"""Generate downloadable PDF for the humanoid intelligence report (Manus / RFR layout)."""
from __future__ import annotations

import html
import io
import logging
import re
from datetime import datetime, timezone
from typing import Any, List

logger = logging.getLogger(__name__)

from reportlab.lib import colors
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from app.services.humanoid_scraper import HEIF_DIMS

# Ready For Robots brand (matches readyforrobots.com/robots)
BG_DARK = colors.HexColor("#0d0520")
TEAL = colors.HexColor("#03DAC5")
PURPLE = colors.HexColor("#7c3aed")
PURPLE_LIGHT = colors.HexColor("#a78bfa")
MUTED = colors.HexColor("#64748b")
INK = colors.HexColor("#1e1b2e")
WHITE = colors.white
TEAL_TINT = colors.HexColor("#ecfeff")
PURPLE_TINT = colors.HexColor("#f5f3ff")
BORDER = colors.HexColor("#e2e8f0")

PAGE_W, PAGE_H = letter
MARGIN_L = 0.65 * inch
MARGIN_R = 0.65 * inch
MARGIN_T = 0.72 * inch
MARGIN_B = 0.85 * inch
CONTENT_W = PAGE_W - MARGIN_L - MARGIN_R


def _esc(text: Any) -> str:
    if text is None:
        return "—"
    return html.escape(str(text))


def _tier_upper(tier_label: str) -> str:
    if not tier_label:
        return "—"
    return str(tier_label).upper().replace("_", " ")


def _pdf_filename(report: dict) -> str:
    title = report.get("title") or "Humanoid_Intelligence_Report"
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
    if not slug.lower().endswith(".pdf"):
        return f"{slug}.pdf"
    return slug


def _footer(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(MUTED)
    page_num = canvas.getPageNumber()
    if page_num > 1:
        canvas.drawString(MARGIN_L, 0.48 * inch, "Ready For Robots · HEIR 2026")
        canvas.drawRightString(PAGE_W - MARGIN_R, 0.48 * inch, str(page_num))
    canvas.restoreState()


def _cover_page(canvas, doc) -> None:
    canvas.saveState()
    canvas.setFillColor(BG_DARK)
    canvas.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    canvas.setFillColor(TEAL)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(MARGIN_L, PAGE_H - 1.0 * inch, "READY FOR ROBOTS")
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 32)
    canvas.drawString(MARGIN_L, PAGE_H - 1.65 * inch, "Humanoid Intelligence")
    canvas.setFont("Helvetica-Bold", 28)
    canvas.drawString(MARGIN_L, PAGE_H - 2.05 * inch, "Report")
    canvas.setFillColor(PURPLE_LIGHT)
    canvas.setFont("Helvetica", 12)
    y = PAGE_H - 2.65 * inch
    for line in (
        "Monthly market intelligence on humanoid capability,",
        "deployments, and buyer readiness",
    ):
        canvas.drawString(MARGIN_L, y, line)
        y -= 16
    canvas.setFillColor(TEAL)
    canvas.setFont("Helvetica", 10)
    y -= 0.25 * inch
    meta = getattr(doc, "_cover_meta", {})
    for label, key in (
        ("Edition:", "edition"),
        ("Published:", "published"),
        ("Framework:", "framework"),
    ):
        canvas.drawString(MARGIN_L, y, f"{label} {_esc(meta.get(key, ''))}")
        y -= 14
    canvas.setFillColor(PURPLE_LIGHT)
    canvas.drawString(MARGIN_L, 1.1 * inch, "readyforrobots.com/robots")
    canvas.restoreState()


def _styles():
    base = getSampleStyleSheet()
    return {
        "section": ParagraphStyle(
            "RptSection",
            parent=base["Heading2"],
            fontSize=11,
            textColor=PURPLE,
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=8,
            leading=13,
        ),
        "subsection": ParagraphStyle(
            "RptSub",
            parent=base["Heading3"],
            fontSize=10,
            textColor=INK,
            fontName="Helvetica-Bold",
            spaceBefore=10,
            spaceAfter=5,
        ),
        "body": ParagraphStyle(
            "RptBody",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            spaceAfter=7,
            alignment=TA_JUSTIFY,
            textColor=INK,
        ),
        "finding": ParagraphStyle(
            "RptFinding",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            spaceAfter=9,
            textColor=INK,
        ),
        "bullet": ParagraphStyle(
            "RptBullet",
            parent=base["Normal"],
            fontSize=9.5,
            leading=13,
            leftIndent=14,
            bulletIndent=0,
            spaceAfter=5,
            textColor=INK,
        ),
        "callout": ParagraphStyle(
            "RptCallout",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            textColor=INK,
        ),
        "profile_title": ParagraphStyle(
            "RptProfTitle",
            parent=base["Normal"],
            fontSize=10,
            fontName="Helvetica-Bold",
            textColor=INK,
            spaceAfter=3,
        ),
        "profile_meta": ParagraphStyle(
            "RptProfMeta",
            parent=base["Normal"],
            fontSize=9,
            textColor=MUTED,
            spaceAfter=4,
        ),
        "profile_body": ParagraphStyle(
            "RptProfBody",
            parent=base["Normal"],
            fontSize=9,
            leading=12,
            spaceAfter=12,
            textColor=INK,
        ),
    }


def _data_table(
    data: List[List[Any]],
    col_widths: List[float],
    *,
    header_rows: int = 1,
) -> Table:
    t = Table(data, colWidths=col_widths, repeatRows=header_rows)
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, header_rows - 1), PURPLE),
                ("TEXTCOLOR", (0, 0), (-1, header_rows - 1), WHITE),
                ("FONTNAME", (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, header_rows - 1), 8),
                ("FONTSIZE", (0, header_rows), (-1, -1), 8),
                ("FONTNAME", (0, header_rows), (-1, -1), "Helvetica"),
                ("TEXTCOLOR", (0, header_rows), (-1, -1), INK),
                ("ALIGN", (0, 0), (-1, -1), "LEFT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.25, BORDER),
                ("ROWBACKGROUNDS", (0, header_rows), (-1, -1), [WHITE, PURPLE_TINT]),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    return t


def _metric_cards(glance: dict) -> Table:
    """Three KPI tiles on executive summary page."""
    cells = [
        [
            Paragraph(f'<para align="center"><font size="18" color="#7c3aed"><b>{_esc(glance.get("robots_indexed"))}</b></font></para>', _styles()["body"]),
            Paragraph(f'<para align="center"><font size="18" color="#7c3aed"><b>{_esc(glance.get("poc_or_better_pct"))}%</b></font></para>', _styles()["body"]),
            Paragraph(f'<para align="center"><font size="18" color="#7c3aed"><b>{_esc(glance.get("commercial_signal_pct"))}%</b></font></para>', _styles()["body"]),
        ],
        [
            Paragraph('<para align="center"><font size="7" color="#64748b"><b>ROBOTS INDEXED</b></font></para>', _styles()["body"]),
            Paragraph('<para align="center"><font size="7" color="#64748b"><b>POC-OR-BETTER (FLEET)</b></font></para>', _styles()["body"]),
            Paragraph('<para align="center"><font size="7" color="#64748b"><b>COMMERCIAL / FLEET SIGNALS</b></font></para>', _styles()["body"]),
        ],
    ]
    col = CONTENT_W / 3
    t = Table(cells, colWidths=[col, col, col])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PURPLE_TINT),
                ("BOX", (0, 0), (-1, -1), 0.75, PURPLE_LIGHT),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    return t


def _callout_box(title: str, body: str, st: dict) -> List[Any]:
    inner = [
        [Paragraph(f"<b>{_esc(title)}</b>", st["subsection"])],
        [Paragraph(_esc(body), st["callout"])],
    ]
    t = Table(inner, colWidths=[CONTENT_W - 16])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), TEAL_TINT),
                ("BOX", (0, 0), (-1, -1), 0.75, TEAL),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    return [t, Spacer(1, 8)]


def _section(story: list, title: str, st: dict) -> None:
    story.append(Paragraph(title.upper(), st["section"]))


def _profile_block(robot: dict, st: dict) -> List[Any]:
    rank = robot.get("rank")
    name = robot.get("name")
    vendor = robot.get("vendor")
    tier = _tier_upper(robot.get("deployment_tier_label") or "")
    customers = robot.get("customer_integrations") or {}
    dep_count = customers.get("catalog_deployment_count", 0)
    score = robot.get("score_total")
    heif = robot.get("heif_total")
    header = Paragraph(
        f"<b>#{rank} {_esc(name)}</b> — {_esc(vendor)} &nbsp;&nbsp; "
        f'<font color="#7c3aed">{_esc(tier)}</font>',
        st["profile_title"],
    )
    meta = Paragraph(
        f"Index {_esc(score)} · HEIF {_esc(heif)}/4 · {_esc(dep_count)} catalog deployments",
        st["profile_meta"],
    )
    body = Paragraph(_esc(robot.get("why_top_rank") or ""), st["profile_body"])
    return [header, meta, body]


def build_humanoid_intelligence_report_pdf(
    payload: dict,
    *,
    renderer: str = "fast",
) -> tuple[bytes, str]:
    """Build PDF bytes from build_humanoid_intelligence_report_payload() result.

    ``renderer=fast`` (default): ReportLab — ~10–30s, suitable for API + Vercel proxy.
    ``renderer=manus`` / ``weasyprint``: HTML + charts via WeasyPrint — slow on small VMs.
    """
    report = payload.get("report")
    if not report:
        raise ValueError("Report payload is empty")

    mode = (renderer or "fast").strip().lower()
    if mode in ("manus", "weasyprint", "html"):
        try:
            from app.services.humanoid_intelligence_report_render import (
                build_humanoid_intelligence_report_pdf_weasyprint,
            )

            return build_humanoid_intelligence_report_pdf_weasyprint(payload)
        except Exception as exc:
            logger.warning("WeasyPrint PDF failed (%s); using ReportLab", exc)

    return _build_humanoid_intelligence_report_pdf_reportlab(payload)


def _build_humanoid_intelligence_report_pdf_reportlab(payload: dict) -> tuple[bytes, str]:
    """ReportLab fallback when WeasyPrint or matplotlib is unavailable."""
    report = payload.get("report")
    if not report:
        raise ValueError("Report payload is empty")

    narrative = report.get("narrative") or {}
    glance = narrative.get("at_a_glance") or {}
    st = _styles()
    generated = payload.get("generated_at") or datetime.now(timezone.utc).isoformat()
    pub_date = generated[:10]
    edition_match = re.search(r"(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4}", report.get("title") or "")
    edition = edition_match.group(0) if edition_match else pub_date[:7]

    buffer = io.BytesIO()
    doc = BaseDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=MARGIN_L,
        rightMargin=MARGIN_R,
        topMargin=MARGIN_T,
        bottomMargin=MARGIN_B,
    )
    doc._cover_meta = {
        "edition": edition,
        "published": pub_date,
        "framework": "HEIF (HEIR 2026)",
    }

    frame = Frame(MARGIN_L, MARGIN_B, CONTENT_W, PAGE_H - MARGIN_T - MARGIN_B, id="normal")
    doc.addPageTemplates([
        PageTemplate(id="cover", frames=[frame], onPage=_cover_page),
        PageTemplate(id="body", frames=[frame], onPage=_footer),
    ])

    story: list[Any] = []

    # ── Cover (page 1) — drawn in _cover_page; switch to body template after ──
    story.append(Spacer(1, 0.01))
    story.append(NextPageTemplate("body"))
    story.append(PageBreak())

    # ── Executive summary (page 2) ───────────────────────────────────────────
    _section(story, "Executive Summary", st)
    if glance:
        story.append(_metric_cards(glance))
        story.append(Spacer(1, 12))

    story.append(Paragraph("Market Overview", st["subsection"]))
    for para in narrative.get("market_overview") or []:
        if para and str(para).strip():
            story.append(Paragraph(_esc(para), st["body"]))

    callout = narrative.get("deployment_news_callout")
    if callout:
        story.extend(_callout_box("Deployment News Status", callout, st))

    mom_lines = narrative.get("month_over_month") or []
    mom = report.get("month_over_month") or {}
    if mom_lines or mom.get("baseline_note") or mom.get("has_prior"):
        story.append(Paragraph("Month over Month", st["subsection"]))
        if mom.get("has_prior"):
            for line in mom.get("narrative_bullets") or []:
                story.append(Paragraph(f"• {_esc(line)}", st["bullet"]))
        elif mom.get("baseline_note"):
            story.append(Paragraph(_esc(mom.get("baseline_note")), st["body"]))
        else:
            for line in mom_lines:
                story.append(Paragraph(_esc(line), st["body"]))

    # ── Key findings (page 3) ────────────────────────────────────────────────
    findings = narrative.get("key_findings") or []
    if findings:
        story.append(PageBreak())
        _section(story, "Key Findings", st)
        for item in findings:
            title = (item.get("title") or "Finding").strip()
            body = (item.get("body") or "").strip()
            if title.lower() == "month over month" and mom.get("baseline_note"):
                continue
            story.append(
                Paragraph(
                    f"<b>{_esc(title)}:</b> {_esc(body)}",
                    st["finding"],
                )
            )

    # ── Competitive dynamics & deployment funnel (page 4) ─────────────────
    comp = narrative.get("competitive_dynamics") or []
    dep_real = narrative.get("deployment_reality") or []
    if comp or dep_real:
        story.append(PageBreak())
        _section(story, "Competitive Dynamics & Deployment Funnel", st)
        for para in comp:
            story.append(Paragraph(_esc(para), st["body"]))
        if dep_real:
            story.append(Paragraph("Deployment Funnel", st["subsection"]))
            for para in dep_real:
                story.append(Paragraph(_esc(para), st["body"]))

    # ── Evidence & dimension leaders (page 5) ───────────────────────────────
    metrics = report.get("adoption_metrics") or {}
    comparisons = report.get("comparisons") or {}
    story.append(PageBreak())
    _section(story, "Evidence & Dimension Leaders", st)

    story.append(Paragraph("Evidence Base (Full Fleet)", st["subsection"]))
    metric_rows = [
        ["Metric", "Value"],
        ["Robots in index", _esc(metrics.get("fleet_total_robots") or report.get("total_robots"))],
        ["PoC-or-better evidence", _esc(f"{metrics.get('fleet_poc_or_better_count')} ({metrics.get('fleet_poc_or_better_pct')}%)")],
        ["Commercial / fleet signals", _esc(metrics.get("fleet_deployment_signal_count"))],
        ["Capability-only scoring", _esc(metrics.get("fleet_capability_only_count"))],
        ["With news in catalog", _esc(metrics.get("fleet_with_news_sources"))],
    ]
    story.append(_data_table(metric_rows, [2.4 * inch, CONTENT_W - 2.4 * inch]))
    story.append(Spacer(1, 10))

    divergence = comparisons.get("ranking_divergence") or []
    if divergence:
        story.append(Paragraph("Index vs Deployment-Weighted Rank", st["subsection"]))
        drows = [["Robot", "Index #", "Depl. #", "Comment"]]
        for d in divergence[:6]:
            drows.append([
                _esc(d.get("name")),
                _esc(d.get("index_rank")),
                _esc(d.get("deployment_weighted_rank")),
                _esc(d.get("commentary")),
            ])
        story.append(_data_table(drows, [1.35 * inch, 0.55 * inch, 0.55 * inch, CONTENT_W - 2.45 * inch]))

    leaders = comparisons.get("dimension_leaders") or []
    if leaders:
        story.append(Spacer(1, 8))
        story.append(Paragraph("HEIF Dimension Leaders", st["subsection"]))
        lrows = [["Dimension", "Robot", "Vendor", "HEIF", "Index"]]
        for entry in leaders:
            lrows.append([
                _esc(entry.get("dimension")),
                _esc(entry.get("name")),
                _esc(entry.get("vendor")),
                _esc(entry.get("heif")),
                _esc(entry.get("index_score")),
            ])
        story.append(_data_table(lrows, [1.0 * inch, 1.2 * inch, 1.1 * inch, 0.45 * inch, 0.45 * inch]))

    # ── Top robots & peer comparison (pages 6–7) ──────────────────────────────
    idx_dep = comparisons.get("index_vs_deployment") or []
    matrix = comparisons.get("peer_heif_matrix") or {}
    matrix_robots = matrix.get("robots") or []
    if idx_dep or matrix_robots:
        story.append(PageBreak())
        _section(story, "Top Robots & Peer Comparison", st)

    if idx_dep:
        story.append(Paragraph("Top Robots — Capability vs Field Evidence", st["subsection"]))
        story.append(Paragraph(
            "Index score reflects engineering maturity from specs and HEIR research. "
            "Deployment tier reflects catalog status, deployment counts, and news. "
            "Gap = high HEIF (≥2.5) but tier still PoC or weaker.",
            st["body"],
        ))
        irows = [["#", "Robot", "Index", "HEIF", "Tier", "Depl.", "Gap"]]
        for row in idx_dep:
            irows.append([
                _esc(row.get("rank")),
                _esc(row.get("name")),
                _esc(row.get("score_total")),
                _esc(row.get("heif_total")),
                _esc((row.get("deployment_tier_label") or "")[:24]),
                _esc(row.get("commercial_deployments")),
                _esc("Yes" if row.get("capability_ahead_of_deployment") else ""),
            ])
        cw = CONTENT_W
        story.append(_data_table(
            irows,
            [0.32 * inch, 1.45 * inch, 0.48 * inch, 0.42 * inch, 1.35 * inch, 0.42 * inch, cw - 3.44 * inch],
        ))

    if matrix_robots:
        story.append(Spacer(1, 10))
        _section(story, "HEIF Dimension Comparison", st)
        dim_labels = matrix.get("dimension_labels") or []
        short = ["Mob.", "Manip.", "Cog.", "Safe.", "Data", "Prod."]
        header = ["Robot", "Total"] + short[: len(dim_labels)]
        mrows = [header]
        for r in matrix_robots:
            dims = r.get("dimensions") or {}
            mrows.append(
                [_esc((r.get("name") or "")[:22]), _esc(r.get("heif_total"))]
                + [_esc(dims.get(dim, "")) for dim in HEIF_DIMS]
            )
        ncol = len(header)
        first = 1.25 * inch
        rest = (CONTENT_W - first - 0.42 * inch) / max(1, ncol - 2)
        story.append(_data_table(mrows, [first, 0.42 * inch] + [rest] * (ncol - 2)))

    # ── Vendor analysis & buyer guidance (page 8) ───────────────────────────
    vendors = comparisons.get("vendor_leaderboard") or []
    guidance = narrative.get("buyer_guidance") or []
    if vendors or guidance:
        story.append(PageBreak())
        _section(story, "Vendor Analysis & Buyer Guidance", st)

    if vendors:
        story.append(Paragraph("Vendor Comparison", st["subsection"]))
        vrows = [["Vendor", "Models", "PoC+ Rate", "Commercial Models", "Deployments"]]
        for v in vendors[:10]:
            vrows.append([
                _esc(v.get("vendor")),
                _esc(v.get("robot_count")),
                _esc(f"{v.get('poc_or_deployment')} ({v.get('poc_or_deployment_pct')}%)"),
                _esc(v.get("deployment_signal")),
                _esc(v.get("total_deployments")),
            ])
        story.append(_data_table(vrows, [1.35 * inch, 0.5 * inch, 0.95 * inch, 0.95 * inch, CONTENT_W - 3.75 * inch]))

    if guidance:
        story.append(Paragraph("Buyer Guidance & Recommendations", st["subsection"]))
        for g in guidance:
            story.append(Paragraph(f"• {_esc(g)}", st["bullet"]))

    # ── Robot profiles (pages 9–10) ───────────────────────────────────────────
    top_ranked = report.get("top_ranked") or []
    if top_ranked:
        story.append(PageBreak())
        _section(story, "Robot Profiles (Top Ranked)", st)
        for robot in top_ranked:
            story.extend(_profile_block(robot, st))

    # ── Methodology (page 11) ─────────────────────────────────────────────────
    story.append(PageBreak())
    _section(story, "Robot Profiles & Methodology", st)
    story.append(Paragraph("Methodology", st["subsection"]))
    story.append(Paragraph(_esc(report.get("methodology")), st["body"]))
    story.append(Paragraph(
        "Verify customer names and deployment claims before external citation. "
        "© Ready For Robots — monthly index update.",
        st["body"],
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue(), _pdf_filename(report)
