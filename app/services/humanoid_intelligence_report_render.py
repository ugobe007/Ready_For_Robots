"""Render humanoid intelligence report HTML (Manus layout) and export PDF via WeasyPrint."""
from __future__ import annotations

import logging
import re
import shutil
import tempfile
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from jinja2 import Environment, FileSystemLoader, select_autoescape

from app.services.humanoid_report_charts import generate_report_charts
from app.services.humanoid_scraper import HEIF_DIMS

logger = logging.getLogger(__name__)

_TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "templates" / "humanoid_intelligence_report"
_ASSETS_DIR = Path(__file__).resolve().parent.parent / "report_assets" / "humanoid"
_DIM_SHORT = {
    "mobility": "Mob.",
    "manipulation": "Manip.",
    "cognition": "Cogn.",
    "safety": "Safe.",
    "data_pipeline": "Data",
    "production": "Prod.",
}


def tier_badge_class(tier_label: str) -> str:
    low = (tier_label or "").lower()
    if "commercial" in low or "fleet" in low:
        return "badge-commercial"
    if "pilot" in low:
        return "badge-pilot"
    if "poc" in low or "trial" in low:
        return "badge-poc"
    if "demo" in low:
        return "badge-demo"
    return "badge-demo"


def _pdf_filename(report: dict) -> str:
    title = report.get("title") or "Humanoid_Intelligence_Report"
    slug = re.sub(r"[^A-Za-z0-9]+", "_", title).strip("_")
    return slug if slug.lower().endswith(".pdf") else f"{slug}.pdf"


def _materialize_cover_image(work_dir: Path, payload: dict) -> Optional[str]:
    """Copy or download cover art into ``work_dir``; return basename for HTML ``src``."""
    report = payload.get("report") or {}
    for robot in report.get("top_ranked") or []:
        url = robot.get("image_url")
        if not url or not str(url).startswith(("http://", "https://")):
            continue
        try:
            dest = work_dir / "cover_robot.jpg"
            req = urllib.request.Request(str(url), headers={"User-Agent": "ReadyForRobots/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = resp.read()
            if len(data) > 5000:
                dest.write_bytes(data)
                return dest.name
        except Exception as exc:
            logger.warning("cover image download failed for %s: %s", url, exc)

    for name in ("robot_industrial.jpg", "cover.jpg"):
        bundled = _ASSETS_DIR / name
        if bundled.is_file():
            dest = work_dir / name
            shutil.copy2(bundled, dest)
            return dest.name
    return None


def _edition_strings(report: dict) -> Tuple[str, str]:
    now = datetime.now(timezone.utc)
    title = report.get("title") or ""
    m = re.search(r"—\s*(\w+\s+\d{4})", title)
    edition = m.group(1) if m else now.strftime("%B %Y")
    published = now.strftime("%B %d, %Y").replace(" 0", " ")
    return edition, published


def build_report_render_context(payload: dict, *, assets_dir: Optional[Path] = None) -> Dict[str, Any]:
    """Build Jinja context from API payload."""
    report = payload.get("report") or {}
    narrative = report.get("narrative") or {}
    glance = narrative.get("at_a_glance") or {}
    metrics = report.get("adoption_metrics") or {}
    comparisons = report.get("comparisons") or {}
    dep_summary = report.get("deployment_summary") or {}
    edition, published = _edition_strings(report)

    total = int(report.get("total_robots") or metrics.get("fleet_total_robots") or 0)
    poc_count = int(metrics.get("fleet_poc_or_better_count") or dep_summary.get("poc_or_better_count") or 0)
    poc_pct = float(metrics.get("fleet_poc_or_better_pct") or (100 * poc_count / total if total else 0))
    commercial = int(metrics.get("fleet_deployment_signal_count") or dep_summary.get("deployment_signal_count") or 0)
    comm_pct = round(100 * commercial / total, 1) if total else 0

    work_dir = assets_dir or Path(tempfile.mkdtemp(prefix="heir_report_"))
    work_dir.mkdir(parents=True, exist_ok=True)
    chart_files = generate_report_charts(payload, work_dir)
    chart_paths = dict(chart_files)
    cover_image_src = _materialize_cover_image(work_dir, payload)

    peer = comparisons.get("peer_heif_matrix") or {}
    dim_labels = peer.get("dimension_labels") or [
        "Mobility", "Manipulation", "Cognition", "Safety", "Data Pipeline", "Production",
    ]

    ranking_divergence = narrative.get("ranking_divergence") or comparisons.get("ranking_divergence") or []
    index_dep_table = []
    for row in ranking_divergence[:6]:
        index_dep_table.append({
            "name": row.get("name"),
            "index_rank": row.get("index_rank"),
            "deployment_rank": row.get("deployment_weighted_rank") or row.get("deployment_rank"),
            "comment": row.get("commentary") or row.get("note") or row.get("comment") or "",
        })
    if not index_dep_table:
        for p in (report.get("top_ranked") or [])[:3]:
            index_dep_table.append({
                "name": p.get("name"),
                "index_rank": p.get("rank"),
                "deployment_rank": "—",
                "comment": "See live index for deployment-weighted rank",
            })

    return {
        "edition": edition,
        "published": published,
        "report": report,
        "narrative": narrative,
        "glance": glance,
        "metrics": metrics,
        "comparisons": comparisons,
        "dep_summary": dep_summary,
        "total_robots": total,
        "poc_count": poc_count,
        "poc_pct": poc_pct,
        "commercial_count": commercial,
        "commercial_pct": comm_pct,
        "capability_only": int(metrics.get("fleet_capability_only_count") or dep_summary.get("capability_only_count") or 0),
        "with_news": int(metrics.get("fleet_with_news_sources") or dep_summary.get("robots_with_news_sources") or 0),
        "findings": narrative.get("key_findings") or [],
        "guidance": narrative.get("buyer_guidance") or [],
        "deployment_news_callout": narrative.get("deployment_news_callout"),
        "month_over_month": report.get("month_over_month"),
        "top_ranked": report.get("top_ranked") or [],
        "index_vs_deployment": comparisons.get("index_vs_deployment") or [],
        "dimension_leaders": comparisons.get("dimension_leaders") or [],
        "vendor_leaderboard": (comparisons.get("vendor_leaderboard") or [])[:10],
        "peer_heif_matrix": peer,
        "dim_labels": dim_labels,
        "dim_short": _DIM_SHORT,
        "heif_dims": HEIF_DIMS,
        "index_dep_table": index_dep_table,
        "charts": chart_paths,
        "cover_image_src": cover_image_src,
        "tier_badge_class": tier_badge_class,
        "work_dir": str(work_dir),
    }


def render_report_html(payload: dict, *, assets_dir: Optional[Path] = None) -> str:
    ctx = build_report_render_context(payload, assets_dir=assets_dir)
    env = Environment(
        loader=FileSystemLoader(str(_TEMPLATE_DIR)),
        autoescape=select_autoescape(["html", "xml"]),
    )
    env.filters["tier_badge"] = tier_badge_class
    template = env.get_template("report.html")
    return template.render(**ctx)


def build_humanoid_intelligence_report_pdf_weasyprint(payload: dict) -> Tuple[bytes, str]:
    """Render Manus-style HTML + charts to PDF bytes."""
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise RuntimeError("weasyprint is not installed") from exc

    report = payload.get("report") or {}
    if not report:
        raise ValueError("empty report payload")

    with tempfile.TemporaryDirectory(prefix="heir_pdf_") as tmp:
        work = Path(tmp)
        html_str = render_report_html(payload, assets_dir=work)
        html_path = work / "report.html"
        html_path.write_text(html_str, encoding="utf-8")
        pdf_bytes = HTML(filename=str(html_path), base_url=str(work)).write_pdf()
        return pdf_bytes, _pdf_filename(report)
