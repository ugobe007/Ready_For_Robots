"""Weekly communication learning report — per-variant outreach performance.

Closes the learning loop: every intro send is tagged with a trust-first angle
(``OutreachMessage.payload.variant_id``) and every reply is classified
(``OutreachReply.detected_intent`` / ``sentiment``). This report rolls those up
by angle so we can see which narrative actually earns positive replies, sliced
by industry, plus a light lexicon read of the subjects that correlate with
positive intent.

Honest constraint: at our send volume this is a *directional* qualitative read,
not statistically significant A/B testing. The report says so and ranks by
signal, never by fake p-values.
"""
from __future__ import annotations

import logging
import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import desc, func
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_REDIS_KEY = "cal:comm_learning:last_sent_date"
_SITE = (os.getenv("PUBLIC_SITE_URL") or "https://readyforrobots.com").rstrip("/")

_POSITIVE_INTENTS = ("interested", "meeting", "pricing", "referral")
_NEGATIVE_INTENTS = ("not_a_fit", "unsubscribe")


def _redis_client():
    from app.services.cal_autonomy import _redis_client as client_fn

    return client_fn()


def _pct(part: int, whole: int) -> float:
    return round(100.0 * part / whole, 1) if whole else 0.0


def build_communication_learning_report(db: Session, *, period_hours: int = 168) -> dict[str, Any]:
    """Aggregate intro sends and their classified replies by trust-first angle."""
    from app.models.crm import CrmAccount
    from app.models.outreach import OutreachMessage, OutreachReply
    from app.services.agent_messaging import BUYER_VARIANTS

    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=max(1, period_hours))

    variant_expr = OutreachMessage.payload.op("->>")("variant_id")

    # Intro sends in-window that carry a variant tag (the trust-first buyer path).
    msgs = (
        db.query(
            OutreachMessage.id,
            OutreachMessage.crm_account_id,
            OutreachMessage.subject,
            OutreachMessage.status,
            variant_expr.label("variant_id"),
        )
        .filter(
            OutreachMessage.sent_at.isnot(None),
            OutreachMessage.sent_at >= since,
            OutreachMessage.sent_at <= now,
            variant_expr.isnot(None),
        )
        .all()
    )

    # Reply intent keyed by the message it answered.
    reply_rows = (
        db.query(
            OutreachReply.outreach_message_id,
            OutreachReply.detected_intent,
            OutreachReply.sentiment,
        )
        .filter(OutreachReply.received_at >= since, OutreachReply.received_at <= now)
        .all()
    )
    reply_by_msg: dict[str, dict[str, str | None]] = {}
    for mid, intent, sentiment in reply_rows:
        # Keep the first (usually only) classified reply per message.
        reply_by_msg.setdefault(str(mid), {"intent": intent, "sentiment": sentiment})

    industry_by_acct = {
        str(a): (ind or "unknown").strip() or "unknown"
        for a, ind in db.query(CrmAccount.id, CrmAccount.industry).all()
    }

    def _blank() -> dict[str, Any]:
        return {
            "sent": 0,
            "delivered": 0,
            "opened": 0,
            "replied": 0,
            "positive": 0,
            "negative": 0,
            "subjects": [],
        }

    per_variant: dict[str, dict[str, Any]] = {v: _blank() for v in BUYER_VARIANTS}
    per_industry: dict[str, dict[str, int]] = defaultdict(lambda: {"sent": 0, "replied": 0, "positive": 0})
    totals = _blank()

    for row in msgs:
        vid = row.variant_id or "unknown"
        agg = per_variant.setdefault(vid, _blank())
        status = (row.status or "").lower()
        rep = reply_by_msg.get(str(row.id))
        industry = industry_by_acct.get(str(row.crm_account_id), "unknown")

        for bucket in (agg, totals):
            bucket["sent"] += 1
            if status in ("delivered", "opened", "clicked", "replied"):
                bucket["delivered"] += 1
            # A click or reply implies the email was opened — count them so the
            # "seen" funnel isn't understated once later states land on a message.
            if status in ("opened", "clicked", "replied"):
                bucket["opened"] += 1
        per_industry[industry]["sent"] += 1
        if row.subject:
            agg["subjects"].append(row.subject)

        if rep:
            for bucket in (agg, totals):
                bucket["replied"] += 1
            per_industry[industry]["replied"] += 1
            if (rep.get("intent") in _POSITIVE_INTENTS) or (rep.get("sentiment") == "positive"):
                for bucket in (agg, totals):
                    bucket["positive"] += 1
                per_industry[industry]["positive"] += 1
            elif (rep.get("intent") in _NEGATIVE_INTENTS) or (rep.get("sentiment") == "negative"):
                for bucket in (agg, totals):
                    bucket["negative"] += 1

    # Rank variants by positive-reply rate, then reply rate (directional only).
    variant_rows: list[dict[str, Any]] = []
    for vid, agg in per_variant.items():
        variant_rows.append(
            {
                "variant_id": vid,
                "sent": agg["sent"],
                "delivered": agg["delivered"],
                "opened": agg["opened"],
                "replied": agg["replied"],
                "positive": agg["positive"],
                "negative": agg["negative"],
                "reply_rate": _pct(agg["replied"], agg["sent"]),
                "positive_rate": _pct(agg["positive"], agg["sent"]),
                "subject_sample": (agg["subjects"][0] if agg["subjects"] else None),
            }
        )
    variant_rows.sort(key=lambda r: (r["positive_rate"], r["reply_rate"], r["sent"]), reverse=True)

    industry_rows = sorted(
        (
            {
                "industry": ind,
                "sent": v["sent"],
                "replied": v["replied"],
                "positive": v["positive"],
                "positive_rate": _pct(v["positive"], v["sent"]),
            }
            for ind, v in per_industry.items()
        ),
        key=lambda r: r["sent"],
        reverse=True,
    )[:8]

    return {
        "period_hours": period_hours,
        "generated_at": now.isoformat(),
        "totals": {
            "sent": totals["sent"],
            "delivered": totals["delivered"],
            "opened": totals["opened"],
            "replied": totals["replied"],
            "positive": totals["positive"],
            "negative": totals["negative"],
            "reply_rate": _pct(totals["replied"], totals["sent"]),
            "positive_rate": _pct(totals["positive"], totals["sent"]),
        },
        "variants": variant_rows,
        "industries": industry_rows,
    }


def render_communication_learning_text(report: dict[str, Any]) -> str:
    days = round((report.get("period_hours") or 168) / 24)
    t = report.get("totals") or {}
    sent_n = t.get("sent", 0)
    lines = [
        f"Cal communication learning report — last {days}d",
        "",
        "How to read this: directional signal, not statistical proof. At our send "
        "volume, treat these as hints about which angle earns trust — not a verdict. "
        "With few replies, delivered/open rates are the leading indicators — read "
        "those first.",
        "",
        "Totals",
        f"  • Intro sends (tagged): {sent_n}",
        f"  • Delivered: {t.get('delivered', 0)}  ({_pct(t.get('delivered', 0), sent_n)}% of sends)",
        f"  • Opened: {t.get('opened', 0)}  ({_pct(t.get('opened', 0), sent_n)}% of sends)",
        f"  • Replied: {t.get('replied', 0)}  ({t.get('reply_rate', 0)}% of sends)",
        f"  • Positive replies: {t.get('positive', 0)}  ({t.get('positive_rate', 0)}% of sends)",
        f"  • Negative / opt-out: {t.get('negative', 0)}",
        "",
        "By angle (ranked by positive-reply rate)",
    ]
    variants = report.get("variants") or []
    if not any(v["sent"] for v in variants):
        lines.append("  • No tagged sends yet in this window — nothing to compare.")
    else:
        for v in variants:
            if not v["sent"]:
                continue
            lines.append(
                f"  • {v['variant_id']}: sent {v['sent']}, opened {v['opened']} "
                f"({_pct(v['opened'], v['sent'])}%), replied {v['replied']} "
                f"({v['reply_rate']}%), positive {v['positive']} ({v['positive_rate']}%)"
            )
            if v.get("subject_sample"):
                lines.append(f"      subject: \"{v['subject_sample']}\"")

    # Lexicon read — which subject line correlates with the best positive rate.
    scored = [v for v in variants if v["sent"] >= 3]
    if not scored:
        lines.extend([
            "",
            "Lexicon read",
            "  • Not enough sends per angle yet (need ~3+ each) to call a winner. "
            "Keep rotating.",
        ])
    elif any(v["positive"] for v in scored):
        # Real positive signal exists → the positive-rate ranking is meaningful.
        best = scored[0]
        lines.extend([
            "",
            "Lexicon read",
            f"  • Best-performing opener so far: {best['variant_id']} "
            f"({best['positive_rate']}% positive on {best['sent']} sends).",
        ])
        weakest = scored[-1]
        if weakest["variant_id"] != best["variant_id"] and weakest["positive_rate"] < best["positive_rate"]:
            lines.append(
                f"  • Weakest opener: {weakest['variant_id']} "
                f"({weakest['positive_rate']}% positive on {weakest['sent']} sends) "
                f"— candidate to retire if the gap holds."
            )
    else:
        # No positive replies on ANY angle yet — the positive-rate ranking above is
        # all zeros, so it cannot name a winner or loser. Say so plainly (never
        # suggest retiring an angle on a 0-vs-0 "gap") and fall back to open rate as
        # the only directional proxy we have.
        by_open = sorted(
            scored,
            key=lambda r: (_pct(r["opened"], r["sent"]), r["sent"]),
            reverse=True,
        )
        top = by_open[0]
        lines.extend([
            "",
            "Lexicon read",
            "  • No replies on any angle yet, so none has earned trust — the "
            "positive-rate ranking above is not meaningful. Do NOT retire an angle "
            "on this.",
        ])
        if top["opened"]:
            lines.append(
                f"  • Only proxy so far is open rate: {top['variant_id']} leads at "
                f"{_pct(top['opened'], top['sent'])}% opened on {top['sent']} sends."
            )
        else:
            lines.append(
                "  • No opens recorded on any angle either — that points to a "
                "deliverability or open-tracking gap, not a copy problem. Verify the "
                "Resend delivery/open webhook and SPF/DKIM/DMARC before touching copy."
            )

    industries = report.get("industries") or []
    if industries:
        lines.extend(["", "By industry (top by volume)"])
        for ind in industries:
            lines.append(
                f"  • {ind['industry']}: sent {ind['sent']}, positive {ind['positive']} "
                f"({ind['positive_rate']}%)"
            )

    lines.extend([
        "",
        "Links",
        f"  • Admin (Cal control): {_SITE}/admin",
        f"  • Replies inbox: {_SITE}/inbox",
        "",
        "Weekly. Reply to adjust which angles Cal keeps rotating.",
    ])
    return "\n".join(lines)


def get_learning_report_recipients() -> list[str]:
    from app.services.cal_daily_digest import get_cal_digest_recipients

    return get_cal_digest_recipients()


def send_communication_learning_report(
    db: Session, *, period_hours: int = 168, force: bool = False
) -> dict[str, Any]:
    """Email the weekly learning report. Skips if already sent today unless force."""
    recipients = get_learning_report_recipients()
    if not recipients:
        return {"sent": False, "reason": "No CAL_DAILY_DIGEST_EMAIL / ADMIN_EMAIL configured"}

    today = datetime.now(timezone.utc).date().isoformat()
    client = _redis_client()
    if not force and client is not None:
        try:
            if str(client.get(_REDIS_KEY) or "") == today:
                return {"sent": False, "reason": "Already sent today", "date": today}
        except Exception:
            pass

    report = build_communication_learning_report(db, period_hours=period_hours)
    body = render_communication_learning_text(report)
    days = round(period_hours / 24)

    from app.services.resend_email import ResendEmailError, send_email_via_resend

    try:
        result = send_email_via_resend(
            to_email=recipients,
            subject=f"Cal learning report — last {days}d ({report['totals']['positive']} positive replies)",
            body_text=body,
            from_display_name="Ready For Robots · Cal",
            idempotency_key=f"cal-comm-learning-{today}",
        )
    except ResendEmailError as exc:
        logger.warning("Cal communication learning report email failed: %s", exc)
        return {"sent": False, "reason": str(exc), "recipients": recipients}

    if client is not None:
        try:
            client.set(_REDIS_KEY, today, ex=60 * 60 * 24 * 8)
        except Exception:
            pass

    return {
        "sent": True,
        "date": today,
        "recipients": recipients,
        "resend_id": result.get("resend_id"),
        "totals": report.get("totals"),
    }


def communication_learning_enabled() -> bool:
    if os.getenv("CAL_COMM_LEARNING_ENABLED", "").strip().lower() in ("0", "false", "no"):
        return False
    return os.getenv("ENABLE_SCHEDULED_CAL_COMM_LEARNING", "1").strip().lower() in ("1", "true", "yes")
