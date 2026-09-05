"""Generate matplotlib charts for the humanoid intelligence report (Manus layout)."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Manus / report.html palette
NAVY = "#0F172A"
EMERALD = "#10B981"
LIGHT_BLUE = "#38BDF8"
VIOLET = "#818CF8"
SLATE = "#64748B"
WHITE = "#FFFFFF"
OFF_WHITE = "#F8FAFC"
AMBER = "#F59E0B"
TEAL = "#14B8A6"
ORANGE = "#F97316"

TIER_COLORS = {
    "commercial": EMERALD,
    "fleet": EMERALD,
    "pilot": LIGHT_BLUE,
    "active pilot": LIGHT_BLUE,
    "poc": VIOLET,
    "trial": VIOLET,
    "demo": AMBER,
    "research": AMBER,
    "none": SLATE,
}


def _tier_color(label: str) -> str:
    low = (label or "").lower()
    for key, color in TIER_COLORS.items():
        if key in low:
            return color
    return SLATE


def _tier_key(label: str) -> str:
    low = (label or "").lower()
    if "commercial" in low or "fleet" in low:
        return "Commercial"
    if "pilot" in low:
        return "Active Pilot"
    if "poc" in low or "trial" in low:
        return "PoC/Trial"
    if "demo" in low:
        return "Demo Only"
    return "Research"


def generate_report_charts(payload: dict, out_dir: Path) -> Dict[str, str]:
    """
    Write chart PNGs to ``out_dir`` and return basenames for the HTML template.
    Returns empty dict if matplotlib is unavailable.
    """
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        import numpy as np
        from matplotlib.patches import FancyBboxPatch
    except ImportError as exc:
        logger.warning("matplotlib not installed — charts omitted: %s", exc)
        return {}

    report = payload.get("report") or {}
    comparisons = report.get("comparisons") or {}
    metrics = report.get("adoption_metrics") or {}
    narrative = report.get("narrative") or {}
    paths: Dict[str, str] = {}

    out_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams["font.family"] = "DejaVu Sans"
    plt.rcParams["axes.facecolor"] = OFF_WHITE
    plt.rcParams["figure.facecolor"] = WHITE

    # Chart 1 — top robots index scores
    idx_rows = comparisons.get("index_vs_deployment") or []
    if idx_rows:
        robots = [r.get("name", "") for r in idx_rows]
        scores = [float(r.get("score_total") or 0) for r in idx_rows]
        tiers = [_tier_key(r.get("deployment_tier_label") or "") for r in idx_rows]
        tier_legend = {
            "Commercial": EMERALD,
            "Active Pilot": LIGHT_BLUE,
            "PoC/Trial": VIOLET,
            "Demo Only": AMBER,
        }
        bar_colors = [tier_legend.get(t, SLATE) for t in tiers]

        fig, ax = plt.subplots(figsize=(12, max(5, len(robots) * 0.45)))
        fig.patch.set_facecolor(WHITE)
        ax.set_facecolor("#F1F5F9")
        y_pos = np.arange(len(robots))
        bars = ax.barh(y_pos, scores, color=bar_colors, height=0.65, zorder=3, alpha=0.92)
        for i, (bar, score) in enumerate(zip(bars, scores)):
            ax.text(
                score + 0.3, i, f"{score:.0f}", va="center", ha="left",
                fontsize=10, fontweight="bold", color=NAVY,
            )
        ax.set_yticks(y_pos)
        ax.set_yticklabels([f"#{i+1}  {r}" for i, r in enumerate(robots)], fontsize=10, color=NAVY)
        ax.set_xlabel("HEIR Index Score (0–100)", fontsize=11, color=SLATE)
        ax.set_title("Top Humanoids — HEIR Index Score", fontsize=14, fontweight="bold", color=NAVY, pad=15)
        ax.set_xlim(0, 92)
        ax.invert_yaxis()
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.grid(axis="x", alpha=0.3, color="#CBD5E1", zorder=1)
        legend_patches = [mpatches.Patch(color=c, label=t) for t, c in tier_legend.items()]
        ax.legend(handles=legend_patches, loc="lower right", fontsize=9, framealpha=0.9)
        plt.tight_layout()
        p = out_dir / "chart_index_scores.png"
        plt.savefig(p, dpi=150, bbox_inches="tight", facecolor=WHITE)
        plt.close()
        paths["chart_index_scores"] = p.name

    # Chart 2 — deployment funnel
    total = int(metrics.get("fleet_total_robots") or report.get("total_robots") or 0)
    poc = int(metrics.get("fleet_poc_or_better_count") or 0)
    commercial = int(metrics.get("fleet_deployment_signal_count") or 0)
    dep_break = comparisons.get("fleet_commercial_deployments_breakdown") or {}
    with_dep = sum(
        int(v) for k, v in dep_break.items() if str(k) not in ("0", "0.0", "") and int(v) > 0
    )
    if not with_dep and total:
        with_dep = max(0, total - int(dep_break.get("0", 0)))

    if total > 0:
        poc_pct = f"{100 * poc / total:.1f}%"
        comm_pct = f"{100 * commercial / total:.1f}%"
        dep_pct = f"{100 * with_dep / total:.1f}%"
        funnel_data = [
            (total, "Total Indexed", "100%", LIGHT_BLUE),
            (poc, "PoC-or-Better Evidence", poc_pct, VIOLET),
            (with_dep, "Catalog Deployments > 0", dep_pct, EMERALD),
            (commercial, "Fleet-Scale Signals", comm_pct, AMBER),
        ]
        fig, ax = plt.subplots(figsize=(10, 6))
        fig.patch.set_facecolor(WHITE)
        ax.axis("off")
        full_width, x_left = 0.82, 0.09
        row_h, gap, top_y = 0.14, 0.06, 0.90
        alphas = [0.95, 0.80, 0.70, 0.60]
        for i, (val, label, pct, color) in enumerate(funnel_data):
            y_top = top_y - i * (row_h + gap)
            y_bot = y_top - row_h
            y_mid = (y_top + y_bot) / 2
            rect = FancyBboxPatch(
                (x_left, y_bot), full_width, row_h,
                boxstyle="round,pad=0.008",
                facecolor=color, alpha=alphas[i],
                edgecolor="white", linewidth=1.5,
                transform=ax.transAxes, zorder=3, clip_on=False,
            )
            ax.add_patch(rect)
            ax.text(
                0.5, y_mid, f"{val}   ·   {label}   ·   {pct}",
                transform=ax.transAxes, ha="center", va="center",
                fontsize=11, fontweight="bold", color=NAVY, zorder=5,
            )
        ax.set_title(f"Deployment Funnel — {total} Robots Indexed", fontsize=14, fontweight="bold", color=NAVY, pad=14)
        plt.tight_layout()
        p = out_dir / "chart_funnel.png"
        plt.savefig(p, dpi=150, bbox_inches="tight", facecolor=WHITE)
        plt.close()
        paths["chart_funnel"] = p.name

    # Chart 3 — radar (top 5 by score)
    matrix = comparisons.get("peer_heif_matrix") or {}
    matrix_robots = (matrix.get("robots") or [])[:5]
    if matrix_robots:
        import numpy as np

        categories = matrix.get("dimension_labels") or [
            "Mobility", "Manipulation", "Cognition", "Safety", "Data Pipeline", "Production",
        ]
        N = len(categories)
        angles = [n / float(N) * 2 * np.pi for n in range(N)]
        angles += angles[:1]
        radar_colors = [EMERALD, LIGHT_BLUE, VIOLET, AMBER, TEAL]
        fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
        fig.patch.set_facecolor(WHITE)
        for i, row in enumerate(matrix_robots):
            dims = row.get("dimensions") or {}
            from app.services.humanoid_scraper import HEIF_DIMS

            values = [float(dims.get(d, 0) or 0) for d in HEIF_DIMS]
            vals = values + values[:1]
            c = radar_colors[i % len(radar_colors)]
            ax.plot(angles, vals, "o-", linewidth=2, color=c, label=row.get("name", ""), alpha=0.9)
            ax.fill(angles, vals, alpha=0.08, color=c)
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(categories, size=10, color=NAVY, fontweight="bold")
        ax.set_ylim(0, 4)
        ax.set_title("HEIF Dimension Comparison — Top 5 Robots", size=14, fontweight="bold", color=NAVY, pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.35, 1.12), fontsize=8)
        plt.tight_layout()
        p = out_dir / "chart_radar.png"
        plt.savefig(p, dpi=150, bbox_inches="tight", facecolor=WHITE)
        plt.close()
        paths["chart_radar"] = p.name

    # Chart 4 — vendors
    vendors = (comparisons.get("vendor_leaderboard") or [])[:10]
    if vendors:
        import numpy as np

        names = [v.get("vendor", "")[:18] for v in vendors]
        deployments = [int(v.get("total_deployments") or 0) for v in vendors]
        poc_rates = [float(v.get("poc_or_deployment_pct") or 0) for v in vendors]
        fig, ax1 = plt.subplots(figsize=(12, 6))
        fig.patch.set_facecolor(WHITE)
        ax1.set_facecolor("#F1F5F9")
        x = np.arange(len(names))
        bars = ax1.bar(x, deployments, color=EMERALD, alpha=0.85, width=0.55, zorder=3)
        ax2 = ax1.twinx()
        ax2.plot(x, poc_rates, "o--", color=VIOLET, linewidth=2, markersize=8, zorder=4)
        ax1.set_xticks(x)
        ax1.set_xticklabels(names, fontsize=9, color=NAVY)
        ax1.set_ylabel("Catalog Deployments", fontsize=11, color=EMERALD)
        ax2.set_ylabel("PoC-or-Better Rate (%)", fontsize=11, color=VIOLET)
        ax1.set_title("Vendor Comparison — Deployments & PoC Rate", fontsize=14, fontweight="bold", color=NAVY, pad=15)
        for bar, val in zip(bars, deployments):
            if val > 0:
                ax1.text(
                    bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                    str(val), ha="center", va="bottom", fontsize=9, fontweight="bold", color=NAVY,
                )
        plt.tight_layout()
        p = out_dir / "chart_vendors.png"
        plt.savefig(p, dpi=150, bbox_inches="tight", facecolor=WHITE)
        plt.close()
        paths["chart_vendors"] = p.name

    # Chart 5 — dimension leaders
    leaders = comparisons.get("dimension_leaders") or []
    if leaders:
        from matplotlib.patches import FancyBboxPatch

        dimensions = [e.get("dimension", "") for e in leaders]
        names = [e.get("name", "") for e in leaders]
        heif_vals = [float(e.get("heif") or 0) for e in leaders]
        index_vals = [float(e.get("index_score") or 0) for e in leaders]
        dim_colors = [LIGHT_BLUE, EMERALD, VIOLET, AMBER, TEAL, ORANGE]

        fig, ax = plt.subplots(figsize=(11, max(4, len(leaders) * 0.7)))
        fig.patch.set_facecolor(WHITE)
        ax.set_facecolor("#F1F5F9")
        ax.axis("off")
        col_x = [0.01, 0.16, 0.50, 0.64]
        headers = ["Dimension", "Leader Robot", "HEIF Score", "Index Score"]
        for j, (hdr, x) in enumerate(zip(headers, col_x)):
            ax.text(
                x, 0.93, hdr, transform=ax.transAxes, fontsize=10,
                fontweight="bold", color=WHITE,
                bbox=dict(boxstyle="round,pad=0.3", facecolor=NAVY, edgecolor="none"),
            )
        for i, (dim, leader, heif, idx, color) in enumerate(
            zip(dimensions, names, heif_vals, index_vals, dim_colors)
        ):
            y = 0.80 - i * 0.135
            bg = "#F8FAFC" if i % 2 == 0 else "#EFF6FF"
            rect = FancyBboxPatch(
                (0.0, y - 0.055), 0.78, 0.115,
                boxstyle="round,pad=0.005",
                facecolor=bg, edgecolor="#E2E8F0", linewidth=0.5,
                transform=ax.transAxes, zorder=2,
            )
            ax.add_patch(rect)
            ax.text(
                col_x[0] + 0.065, y, dim, transform=ax.transAxes, fontsize=9.5,
                fontweight="bold", color=WHITE, ha="center", va="center",
                bbox=dict(boxstyle="round,pad=0.3", facecolor=color, edgecolor="none"),
            )
            ax.text(col_x[1], y, leader, transform=ax.transAxes, fontsize=9.5, color=NAVY, va="center")
            ax.text(
                col_x[2] + 0.06, y, f"{heif}/4.0", transform=ax.transAxes, fontsize=10,
                color=EMERALD, va="center", ha="center", fontweight="bold",
            )
            ax.text(
                col_x[3] + 0.06, y, f"{idx:.0f}", transform=ax.transAxes, fontsize=10,
                color=NAVY, va="center", ha="center", fontweight="bold",
            )
        ax.set_title("HEIF Dimension Leaders", fontsize=14, fontweight="bold", color=NAVY, pad=10, y=1.02)
        plt.tight_layout()
        p = out_dir / "chart_dimension_leaders.png"
        plt.savefig(p, dpi=150, bbox_inches="tight", facecolor=WHITE)
        plt.close()
        paths["chart_dimension_leaders"] = p.name

    return paths
