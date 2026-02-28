#!/usr/bin/env python
"""
watch_leads.py — Live Lead Intelligence Monitor
================================================
Reads directly from the local SQLite DB and refreshes every 5 s.
Applies junk filter + priority tier in real time.

Usage:
  python scripts/watch_leads.py                   # default — all leads
  python scripts/watch_leads.py --tier HOT        # hot leads only
  python scripts/watch_leads.py --industry hotel  # filter by industry
  python scripts/watch_leads.py --min-score 50    # min raw score (0-100)
  python scripts/watch_leads.py --show-junk       # include junk (for debugging)
  python scripts/watch_leads.py --interval 3      # refresh every 3 s (default 5)
  python scripts/watch_leads.py --once            # single snapshot, no live loop
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# ── ensure project root on path ──────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rich import box
from rich.align import Align
from rich.columns import Columns
from rich.console import Console
from rich.layout import Layout
from rich.live import Live
from rich.panel import Panel
from rich.progress_bar import ProgressBar
from rich.table import Table
from rich.text import Text

from sqlalchemy.orm import joinedload
from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal
from app.services.lead_filter import classify_lead, is_junk

console = Console()

HEALTH_FILE = ROOT / "scraper_health.json"

# ─── colour maps ─────────────────────────────────────────────────────────────
TIER_STYLE = {"HOT": "bold red", "WARM": "bold yellow", "COLD": "dim cyan"}
TIER_ICON  = {"HOT": "🔥", "WARM": "🌡 ", "COLD": "❄ "}

SIG_STYLE = {
    "funding_round":   ("violet",  "Funding"),
    "strategic_hire":  ("blue",    "Exec Hire"),
    "capex":           ("cyan",    "CapEx"),
    "ma_activity":     ("magenta", "M&A"),
    "expansion":       ("green",   "Expand"),
    "job_posting":     ("yellow",  "Hiring"),
    "labor_shortage":  ("red",     "Labor Gap"),
    "news":            ("white",   "News"),
}


def score_bar(value: float, width: int = 12) -> Text:
    """Return a compact coloured block progress bar."""
    pct = min(100.0, max(0.0, value))
    filled = round(pct / 100 * width)
    if pct >= 75:
        colour = "green"
    elif pct >= 50:
        colour = "yellow"
    elif pct >= 30:
        colour = "dark_orange"
    else:
        colour = "red"
    bar = "█" * filled + "░" * (width - filled)
    t = Text()
    t.append(bar, style=colour)
    t.append(f" {pct:4.0f}", style="dim")
    return t


def sig_badges(signals) -> Text:
    seen = set()
    t = Text()
    for s in sorted(signals, key=lambda x: x.signal_strength, reverse=True):
        st = s.signal_type
        if st in seen:
            continue
        seen.add(st)
        colour, label = SIG_STYLE.get(st, ("white", st))
        if t._length > 0:
            t.append(" ")
        t.append(f"[{label}]", style=colour)
    return t


# ─── load data ───────────────────────────────────────────────────────────────
def load_leads(args):
    db = SessionLocal()
    try:
        companies = (
            db.query(Company)
            .options(joinedload(Company.scores), joinedload(Company.signals))
            .all()
        )

        rows = []
        junk_count = 0

        for c in companies:
            junk, junk_reason, pri = classify_lead(c, c.scores, c.signals)
            if junk:
                junk_count += 1
                if not args.show_junk:
                    continue

            raw = (c.scores.overall_intent_score if c.scores else 0) * 100
            if raw < args.min_score:
                continue
            if args.tier and pri.tier != args.tier.upper():
                continue
            if args.industry and (not c.industry or args.industry.lower() not in c.industry.lower()):
                continue

            rows.append((c, pri, junk, junk_reason))

        rows.sort(key=lambda x: x[1].score, reverse=True)
        return rows, junk_count
    finally:
        db.close()


def load_recent_signals(limit=12):
    db = SessionLocal()
    try:
        return (
            db.query(Signal)
            .order_by(Signal.id.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()


def load_health():
    if not HEALTH_FILE.exists():
        return None
    try:
        return json.loads(HEALTH_FILE.read_text())
    except Exception:
        return None


# ─── renderable builders ─────────────────────────────────────────────────────
def build_lead_table(rows, max_rows=40) -> Table:
    t = Table(
        box=box.SIMPLE_HEAVY,
        show_header=True,
        header_style="bold white on grey23",
        expand=True,
        padding=(0, 1),
    )
    t.add_column("#",       style="dim",       width=3,  no_wrap=True)
    t.add_column("Tier",                       width=6,  no_wrap=True)
    t.add_column("Company",                    min_width=22, no_wrap=True)
    t.add_column("Industry",  style="dim",     width=14, no_wrap=True)
    t.add_column("Overall",                    width=18, no_wrap=True)
    t.add_column("Auto",                       width=18, no_wrap=True)
    t.add_column("Labor",                      width=18, no_wrap=True)
    t.add_column("Signals",                    min_width=24)

    for i, (c, pri, junk, _) in enumerate(rows[:max_rows], 1):
        s  = c.scores
        ov = (s.overall_intent_score if s else 0) * 100
        au = (s.automation_score     if s else 0) * 100
        lb = (s.labor_pain_score     if s else 0) * 100

        tier_txt = Text()
        tier_txt.append(TIER_ICON[pri.tier], style=TIER_STYLE[pri.tier])
        tier_txt.append(pri.tier, style=TIER_STYLE[pri.tier])

        name_style = "bold" if pri.tier == "HOT" else ("white" if pri.tier == "WARM" else "dim")
        name_txt = Text(c.name or "—", style=name_style, no_wrap=True, overflow="ellipsis")
        if junk:
            name_txt.stylize("dim strike")

        t.add_row(
            str(i),
            tier_txt,
            name_txt,
            Text(c.industry or "—", style="dim", no_wrap=True, overflow="ellipsis"),
            score_bar(ov),
            score_bar(au),
            score_bar(lb),
            sig_badges(c.signals or []),
        )

    return t


def build_signal_feed(signals) -> Table:
    t = Table(box=box.MINIMAL, show_header=True, header_style="dim", padding=(0, 1), expand=True)
    t.add_column("Company",     width=20, no_wrap=True)
    t.add_column("Type",        width=12, no_wrap=True)
    t.add_column("Strength",    width=8,  no_wrap=True)
    t.add_column("Text",        min_width=30)

    for sig in signals:
        colour, label = SIG_STYLE.get(sig.signal_type, ("white", sig.signal_type))
        strength_pct = sig.signal_strength * 100
        if strength_pct >= 70:
            str_style = "green"
        elif strength_pct >= 40:
            str_style = "yellow"
        else:
            str_style = "dim"

        comp_name = "—"
        db = SessionLocal()
        try:
            c = db.query(Company).filter(Company.id == sig.company_id).first()
            comp_name = (c.name or "—")[:20] if c else "—"
        finally:
            db.close()

        raw_text = (sig.signal_text or "")[:80]
        t.add_row(
            Text(comp_name, no_wrap=True, overflow="ellipsis"),
            Text(f"[{label}]", style=colour),
            Text(f"{strength_pct:.0f}%", style=str_style),
            Text(raw_text, style="dim", no_wrap=True, overflow="ellipsis"),
        )
    return t


def build_health_panel(health) -> Panel:
    if not health:
        return Panel(
            Text("No scraper_health.json found — run a scraper first.", style="dim"),
            title="[bold]Scraper Health[/bold]",
            border_style="grey50",
        )

    url_health = health.get("url_health", {})
    open_circuits = health.get("circuit_open_urls", [])
    recent = health.get("recent_runs", [])

    t = Table(box=box.MINIMAL, show_header=False, padding=(0, 1), expand=True)
    t.add_column("●",      width=2, no_wrap=True)
    t.add_column("URL",    min_width=30)
    t.add_column("Fails",  width=6,  no_wrap=True)
    t.add_column("Status", width=10, no_wrap=True)

    for url, info in list(url_health.items())[:8]:
        dot    = Text("●", style="red" if info.get("circuit_open") else "green")
        status = Text("OPEN ⚡", style="bold red") if info.get("circuit_open") else Text("OK", style="green")
        fails  = str(info.get("consecutive_failures", 0))
        short  = url.replace("https://", "").replace("http://", "")[:35]
        t.add_row(dot, Text(short, style="dim"), Text(fails, style="dim"), status)

    summary_parts = []
    total  = len(url_health)
    open_n = len(open_circuits)
    last   = recent[-1] if recent else None

    summary_parts.append(Text(f"URLs: {total}  ", style="dim"))
    summary_parts.append(Text(f"Healthy: {total - open_n}  ", style="green"))
    if open_n:
        summary_parts.append(Text(f"Open circuits: {open_n}  ", style="bold red"))
    if last:
        last_style = "green" if last.get("status") == "success" else "red"
        summary_parts.append(Text(f"Last: {last.get('scraper_name','?')} ({last.get('status','?')})  ",
                                  style=last_style))

    summary = Text()
    for p in summary_parts:
        summary.append_text(p)

    content = Columns([summary, t])
    return Panel(content, title="[bold]Scraper Health[/bold]", border_style="grey50")


def build_stats_bar(rows, junk_count) -> Text:
    hot  = sum(1 for _, pri, junk, _ in rows if not junk and pri.tier == "HOT")
    warm = sum(1 for _, pri, junk, _ in rows if not junk and pri.tier == "WARM")
    cold = sum(1 for _, pri, junk, _ in rows if not junk and pri.tier == "COLD")
    clean = hot + warm + cold
    t = Text()
    t.append("  Leads: ", style="dim")
    t.append(f"{clean} clean", style="bold white")
    t.append("  │  🔥 ", style="dim")
    t.append(f"{hot} HOT", style="bold red")
    t.append("  🌡  ", style="dim")
    t.append(f"{warm} WARM", style="bold yellow")
    t.append("  ❄  ", style="dim")
    t.append(f"{cold} COLD", style="bold cyan")
    t.append("  │  🗑 ", style="dim")
    t.append(f"{junk_count} junk filtered", style="dim red")
    t.append(f"  │  {datetime.now().strftime('%H:%M:%S')}", style="dim")
    return t


# ─── main ─────────────────────────────────────────────────────────────────────
def render(args):
    rows, junk_count = load_leads(args)
    signals          = load_recent_signals()
    health           = load_health()

    # header
    title = Text()
    title.append("  🤖 READY FOR ROBOTS", style="bold white")
    title.append("  ·  Lead Intelligence Monitor", style="dim")
    stats = build_stats_bar(rows, junk_count)

    header = Panel(
        Align(stats, align="left"),
        title="[bold cyan]Ready for Robots[/bold cyan]",
        subtitle="[dim]press Ctrl+C to exit[/dim]",
        border_style="cyan",
    )

    # lead table
    lead_panel = Panel(
        build_lead_table(rows),
        title=f"[bold]Ranked Leads[/bold] [dim]({len(rows)} shown)[/dim]",
        border_style="blue",
    )

    # signal feed
    sig_panel = Panel(
        build_signal_feed(signals),
        title="[bold]Recent Signals[/bold]",
        border_style="magenta",
    )

    # health
    health_widget = build_health_panel(health)

    from rich.console import Group
    return Group(header, lead_panel, sig_panel, health_widget)


def parse_args():
    p = argparse.ArgumentParser(description="Live lead intelligence monitor")
    p.add_argument("--tier",        default=None,  help="HOT | WARM | COLD")
    p.add_argument("--industry",    default=None,  help="Partial industry match")
    p.add_argument("--min-score",   type=float, default=0.0,
                   dest="min_score", help="Min overall score 0-100")
    p.add_argument("--show-junk",   action="store_true", dest="show_junk",
                   help="Include junk leads (dim/strikethrough)")
    p.add_argument("--interval",    type=float, default=5.0,
                   help="Refresh interval in seconds (default 5)")
    p.add_argument("--once",        action="store_true",
                   help="Render once and exit (no live loop)")
    return p.parse_args()


def main():
    args = parse_args()

    if args.once:
        console.print(render(args))
        return

    with Live(render(args), console=console, refresh_per_second=1, screen=True) as live:
        try:
            while True:
                time.sleep(args.interval)
                live.update(render(args))
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
