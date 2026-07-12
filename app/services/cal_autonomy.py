"""Cal autonomous outreach — draft, refresh, send, and format review notifications."""
from __future__ import annotations

import hashlib
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from typing import Any, Optional

from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

_REDIS_FP_KEY = "cal:outreach:template_fingerprint"
_REDIS_AUTONOMY_KEY = "cal:autonomy:runtime_enabled"


def get_cal_review_email() -> Optional[str]:
    """Operator inbox for Cal format reviews (ADMIN_EMAIL on Fly)."""
    for key in ("ADMIN_EMAIL", "CAL_REVIEW_EMAIL", "HARNESS_NOTIFY_EMAIL"):
        raw = (os.getenv(key) or "").strip()
        if raw and "@" in raw:
            return raw.split(",")[0].strip()
    admins = (os.getenv("ADMIN_EMAILS") or "").strip()
    if admins:
        first = admins.split(",")[0].strip()
        return first if "@" in first else None
    return None


def get_cal_autonomy_runtime_override() -> Optional[bool]:
    """Operator toggle stored in Redis; None = use env default."""
    client = _redis_client()
    if not client:
        return None
    try:
        raw = client.get(_REDIS_AUTONOMY_KEY)
        if raw is None:
            return None
        return str(raw).strip().lower() in ("1", "true", "yes")
    except Exception:
        return None


def set_cal_autonomy_runtime_override(enabled: bool) -> bool:
    client = _redis_client()
    if not client:
        return False
    try:
        client.set(_REDIS_AUTONOMY_KEY, "1" if enabled else "0")
        return True
    except Exception:
        return False


def _cal_autonomy_env_default() -> bool:
    if os.getenv("CAL_AUTONOMY_ENABLED", "").strip().lower() in ("0", "false", "no"):
        return False
    if os.getenv("CAL_AUTONOMY_ENABLED", "").strip().lower() in ("1", "true", "yes"):
        return True
    return os.getenv("ENABLE_SCHEDULED_CAL_AUTONOMY", "").strip().lower() in ("1", "true", "yes")


def cal_autonomy_enabled() -> bool:
    if os.getenv("CAL_AUTONOMY_ENABLED", "").strip().lower() in ("0", "false", "no"):
        return False
    override = get_cal_autonomy_runtime_override()
    if override is not None:
        return override
    return _cal_autonomy_env_default()


def _redis_client():
    url = (os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL") or "").strip()
    if not url:
        return None
    try:
        import redis

        return redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def _stored_template_fingerprint() -> Optional[str]:
    client = _redis_client()
    if not client:
        return None
    try:
        return client.get(_REDIS_FP_KEY)
    except Exception:
        return None


def _persist_template_fingerprint(fp: str) -> None:
    client = _redis_client()
    if not client:
        return
    try:
        client.set(_REDIS_FP_KEY, fp, ex=60 * 60 * 24 * 120)
    except Exception:
        pass


# ── Safe auto-send guards: daily cap + angle rotation/retirement ──────────────

def cal_daily_send_cap() -> int:
    """Hard ceiling on buyer intros per calendar day across all cycles.

    Deliberately conservative — we resume auto-send throttled low so the new
    trust-first angles can prove out on small batches before any volume push.
    """
    try:
        return max(0, int(os.getenv("CAL_AUTONOMY_DAILY_CAP", "10") or "10"))
    except (TypeError, ValueError):
        return 10


def _daily_send_key() -> str:
    return f"cal:auto:daily_sent:{datetime.now(timezone.utc).date().isoformat()}"


def cal_daily_sent_count() -> int:
    client = _redis_client()
    if not client:
        return 0
    try:
        return int(client.get(_daily_send_key()) or 0)
    except Exception:
        return 0


def _incr_daily_sent(n: int = 1) -> None:
    if n <= 0:
        return
    client = _redis_client()
    if not client:
        return
    try:
        key = _daily_send_key()
        client.incrby(key, n)
        client.expire(key, 60 * 60 * 36)
    except Exception:
        pass


# Retire an angle only after enough sends to mean anything, and only if its
# negative-reply rate is clearly bad. Never retire the last surviving angle.
_VARIANT_MIN_SENDS_TO_JUDGE = int(os.getenv("CAL_VARIANT_MIN_SENDS", "12") or "12")
_VARIANT_MAX_NEGATIVE_RATE = float(os.getenv("CAL_VARIANT_MAX_NEG_RATE", "0.40") or "0.40")


def active_buyer_variants(db) -> list[str]:
    """Angles Cal is allowed to draft right now.

    Priority:
      1. Operator override in Redis (`cal:buyer_variants:active`, comma list).
      2. Auto-retirement: drop any angle whose negative-reply rate over the last
         30 days exceeds the threshold once it has enough sends to judge.
    Always returns at least one angle (never retires the last one).
    """
    from app.services.agent_messaging import BUYER_VARIANTS

    client = _redis_client()
    if client is not None:
        try:
            raw = (client.get("cal:buyer_variants:active") or "").strip()
        except Exception:
            raw = ""
        if raw:
            chosen = [v.strip() for v in raw.split(",") if v.strip() in BUYER_VARIANTS]
            if chosen:
                return chosen

    try:
        from app.models.outreach import OutreachMessage, OutreachReply

        since = datetime.now(timezone.utc) - timedelta(days=30)
        variant_expr = OutreachMessage.payload.op("->>")("variant_id")
        sent_by_variant: dict[str, int] = {}
        for vid, cnt in (
            db.query(variant_expr, func.count(OutreachMessage.id))
            .filter(
                OutreachMessage.sent_at.isnot(None),
                OutreachMessage.sent_at >= since,
                variant_expr.isnot(None),
            )
            .group_by(variant_expr)
            .all()
        ):
            if vid:
                sent_by_variant[vid] = int(cnt or 0)

        neg_by_variant: dict[str, int] = {}
        rows = (
            db.query(variant_expr, OutreachReply.sentiment, OutreachReply.detected_intent)
            .join(OutreachReply, OutreachReply.outreach_message_id == OutreachMessage.id)
            .filter(OutreachReply.received_at >= since, variant_expr.isnot(None))
            .all()
        )
        for vid, sentiment, intent in rows:
            if vid and (sentiment == "negative" or intent in ("not_a_fit", "unsubscribe")):
                neg_by_variant[vid] = neg_by_variant.get(vid, 0) + 1

        keep: list[str] = []
        retired: list[str] = []
        for vid in BUYER_VARIANTS:
            sent = sent_by_variant.get(vid, 0)
            neg = neg_by_variant.get(vid, 0)
            if sent >= _VARIANT_MIN_SENDS_TO_JUDGE and (neg / sent) >= _VARIANT_MAX_NEGATIVE_RATE:
                retired.append(vid)
            else:
                keep.append(vid)
        # Never retire everything — if all look bad, keep the least-bad by neg rate.
        if not keep:
            keep = sorted(
                BUYER_VARIANTS,
                key=lambda v: (neg_by_variant.get(v, 0) / max(1, sent_by_variant.get(v, 0))),
            )[:1]
        if retired:
            logger.info("Cal auto-retired losing buyer angles: %s", retired)
        return keep
    except Exception as exc:  # noqa: BLE001 — rotation must never break the cycle
        logger.info("active_buyer_variants fell back to all angles: %s", exc)
        return list(BUYER_VARIANTS)


def cal_buyer_outreach_body(company: Any, *, fresh: bool = False, variant_id: str | None = None) -> str:
    """Cal-voice outreach to buyer-side prospects (admin Cal queue + autonomy).

    Trust-first: picks one of the humble, non-presumptuous angles. Selection is
    deterministic by company id so the stored draft and the send agree on the
    angle; callers may override with an explicit variant_id.
    """
    from app.services.agent_messaging import (
        build_buyer_variant_body,
        build_context_reason,
        pick_buyer_variant,
    )

    name = (getattr(company, "name", None) or "your team").strip()
    industry = (getattr(company, "industry", None) or "your industry").strip()
    vid = variant_id or pick_buyer_variant(getattr(company, "id", None))
    reason = build_context_reason(name, _company_signal_blob(company))
    return build_buyer_variant_body(name, industry, vid, reason=reason)


def _company_signal_blob(company: Any) -> str:
    """Best-effort plain-text of a company's own signal evidence for grounding.

    Returns "" (no reason cited) if signals aren't loaded/attached, so a detached
    instance or a company with no signals simply falls back to the clean industry
    opener — Cal never fabricates a reason.
    """
    try:
        from app.services.lead_signal_display import strip_extraction_artifacts

        sigs = list(getattr(company, "signals", None) or [])[:12]
        parts = [
            strip_extraction_artifacts(getattr(s, "signal_text", None)) for s in sigs
        ]
        return " ".join(p for p in parts if p).strip()
    except Exception:  # noqa: BLE001 — grounding is optional; never break drafting
        return ""


def cal_vendor_outreach_body(company: Any, *, fresh: bool = False) -> str:
    """Cal-voice outreach to robot companies — sherpa tone, PoC-aware."""
    from app.services.agent_messaging import (
        CAL_VENDOR_BUYER_MATCH_CTA,
        CAL_VENDOR_SHERPA_LINE,
        cal_vendor_match_paragraph,
        cal_signature,
    )
    from app.services.cal_insights import pick_cal_insight

    name = (getattr(company, "name", None) or "your team").strip()
    industry = (getattr(company, "industry", None) or "your space").strip()
    week = datetime.now(timezone.utc).isocalendar().week
    allow_humor = fresh or (week % 2 == 0)

    lines = [
        "Hi,",
        "",
        cal_vendor_match_paragraph(name, industry=industry),
        "",
        pick_cal_insight(company_name=name, allow_humor=allow_humor, audience="vendor"),
        "",
        CAL_VENDOR_SHERPA_LINE,
        "",
        CAL_VENDOR_BUYER_MATCH_CTA,
        "",
        cal_signature(),
    ]
    return "\n".join(lines)


def format_cal_draft_storage(subject: str, body: str) -> str:
    sub = (subject or "").strip()
    text = (body or "").strip()
    if sub.lower().startswith("subject:"):
        return text if text else sub
    return f"Subject: {sub}\n\n{text}" if sub else text


def outreach_template_fingerprint() -> str:
    version = (os.getenv("CAL_TEMPLATE_VERSION") or "2").strip()
    sample_company = SimpleNamespace(name="Sample Robotics Co", industry="Logistics", website=None, id=1)
    sample_body = cal_vendor_outreach_body(sample_company, fresh=False)
    # Fold every buyer angle in so a change to any trust-first variant also trips
    # the format-review notification, not just vendor copy.
    from app.services.agent_messaging import BUYER_VARIANTS, build_buyer_variant_body

    buyer_samples = "|".join(
        build_buyer_variant_body("Sample Ops Co", "Logistics", vid)[:400] for vid in BUYER_VARIANTS
    )
    payload = f"{version}|{sample_body[:800]}|{buyer_samples}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:20]


def notify_admin_of_format_change(
    *,
    sample_company: str,
    sample_subject: str,
    sample_draft: str,
    previous_fingerprint: Optional[str],
    new_fingerprint: str,
) -> bool:
    """Email ADMIN_EMAIL when Cal's outreach template/format changes."""
    to_email = get_cal_review_email()
    if not to_email:
        logger.warning("Cal format changed but ADMIN_EMAIL / ADMIN_EMAILS is not configured")
        return False

    from app.services.resend_email import ResendEmailError, send_email_via_resend

    subject = "Cal updated outreach format — review sample"
    body = f"""Cal refreshed the outreach template Cal uses for prospective buyers.

Previous fingerprint: {previous_fingerprint or "(none)"}
New fingerprint: {new_fingerprint}
Template version: {os.getenv("CAL_TEMPLATE_VERSION") or "2"}

Sample company: {sample_company}
Sample subject: {sample_subject}

--- Sample draft Cal will send (autonomous sends continue) ---

{sample_draft}

---
Review in the command center: /admin#cal-outreach
Reply to this email if you want Cal paused or the tone adjusted.
"""
    try:
        send_email_via_resend(
            to_email=to_email,
            subject=subject,
            body_text=body,
            from_display_name="Ready For Robots · Cal ops",
            idempotency_key=f"cal-format-review-{new_fingerprint}",
        )
        return True
    except ResendEmailError as exc:
        logger.warning("Cal format review email failed: %s", exc)
        return False


def resolve_cal_admin_context(db: Session) -> Optional[tuple[uuid.UUID, Any]]:
    from app.models.crm import Team, TeamMember

    team = db.query(Team).filter(Team.slug == "admin-cal-outreach").first()
    if team:
        member = (
            db.query(TeamMember)
            .filter(TeamMember.team_id == team.id)
            .order_by(TeamMember.created_at.asc())
            .first()
        )
        if member:
            return member.user_id, team

    uid_raw = (os.getenv("CAL_ADMIN_USER_ID") or "").strip()
    if not uid_raw:
        return None
    try:
        uid = uuid.UUID(uid_raw)
    except ValueError:
        logger.warning("Invalid CAL_ADMIN_USER_ID")
        return None
    from app.api.admin_extended import _admin_team

    email = get_cal_review_email() or "admin@readyforrobots.com"
    team = _admin_team(db, uid, email)
    return uid, team


def _draft_and_store(
    db: Session,
    *,
    company: Any,
    acct: Any,
    team: Any,
    existing: dict[int, Any],
    regenerate: bool,
    stale_before: Optional[datetime],
    allowed_variants: Optional[list[str]] = None,
) -> tuple[bool, bool]:
    """Return (drafted, refreshed)."""
    from app.api.admin_extended import _cal_draft_for_company

    company_id = company.id
    acct = existing.get(company_id) if acct is None else acct
    has_draft = bool(acct and acct.outreach_draft)
    is_stale = False
    if acct and stale_before:
        ts = acct.updated_at or acct.created_at
        if ts:
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            is_stale = ts <= stale_before

    if has_draft and not regenerate and not is_stale:
        from app.services.cal_draft_guard import draft_needs_regeneration

        account_type = getattr(acct, "account_type", None) or "buyer"
        needs_refresh, _ = draft_needs_regeneration(acct.outreach_draft, account_type=account_type)
        if not needs_refresh:
            return False, False

    # Resolve the trust-first angle once and persist it so the send loop tags the
    # exact same variant that was drafted (survives future angle-rotation logic).
    from app.services.agent_messaging import pick_buyer_variant

    is_buyer = (company.crm_metadata or {}).get("outreach_pipeline") != "stagegate"
    variant_id = (
        pick_buyer_variant(company.id, allowed=allowed_variants) if is_buyer else None
    )
    subject, draft_body = _cal_draft_for_company(
        company, fresh=regenerate or is_stale, variant_id=variant_id
    )
    if variant_id:
        meta = dict(company.crm_metadata or {})
        meta["cal_variant_id"] = variant_id
        company.crm_metadata = meta

    if acct is None:
        from app.models.crm import CrmAccount

        acct = CrmAccount(
            team_id=team.id,
            company_id=company.id,
            name=company.name or "Unknown",
            website=company.website,
            industry=company.industry,
            account_type="vendor"
            if (company.crm_metadata or {}).get("outreach_pipeline") == "stagegate"
            else "buyer",
        )
        db.add(acct)
        db.flush()
        existing[company_id] = acct
    elif (company.crm_metadata or {}).get("outreach_pipeline") == "stagegate":
        acct.account_type = "vendor"

    # Do NOT stamp a guessed role inbox onto contact_email here. A stored
    # contact_email short-circuits resolve_outreach_email (returns "crm_contact",
    # untrusted) BEFORE it ever reaches Hunter — so a guess written at draft time
    # permanently blocks the verified-contact upgrade and the account can never
    # send. Leave contact_email empty; the send loop resolves through the full
    # waterfall (Apollo → Hunter → …) and only a verified address clears the gate.

    acct.outreach_draft = format_cal_draft_storage(subject, draft_body)
    from app.api.admin_extended import cal_manual_approval_required

    acct.outreach_stage = (
        "draft_approved" if not cal_manual_approval_required() else "draft_ready"
    )
    return True, bool(has_draft and (regenerate or is_stale))


# Off-ICP industries — genuine non-buyers only. Hospitality, aviation, gaming,
# and food service are DELIBERATE service/cleaning/delivery-robot buyer segments
# (see seed_v2/v3 + the manual "las_vegas_cleaning_robot_prospects" source), so
# they are NOT excluded — bounce safety is handled by the recipient-trust +
# deliverability gates at send time, not by blanket industry exclusion. Scoped to
# Cal's outreach path only; broader pipeline/UI classification is unchanged.
_CAL_OFF_ICP_INDUSTRY_TOKENS = (
    "publishing", "newspaper", "market research", "trade publication",
)

# Strong automation-buyer signals that override a noisy off-ICP industry label
# (e.g. "Amazon Fulfillment" mislabeled as hospitality is still a core buyer).
_CAL_IN_ICP_OVERRIDE_TOKENS = (
    "fulfillment", "warehouse", "logistics", "distribution", "supply chain",
    "manufactur", "factory", "industrial", "3pl", "e-commerce", "ecommerce",
    "grocery", "cold storage", "material handling", "automation",
)


def _cal_buyer_eligible(company: Any, acct: Any = None) -> tuple[bool, str]:
    """
    Buyer-outreach eligibility gate, contained to Cal so the queue cannot
    re-contaminate: real buyer name (not vendor/OEM/fragment), a reachable
    website domain, and an in-ICP industry.
    """
    from app.services.lead_filter import is_junk
    from app.services.lead_enrichment import company_website_domain
    from app.services.brand import BRAND_STAGEGATE, company_brand

    # Brand isolation: the Ready For Robots buyer loop must never read, draft, or
    # send to StageGate (onstage.bot logistics) accounts. Those are worked in the
    # StageGate pipeline, from a StageGate identity — never as an RFR buyer.
    if company_brand(company, acct) == BRAND_STAGEGATE:
        return False, "stagegate account — isolated from Ready For Robots buyer loop"

    # Reply-driven suppression: a prospect who opted out or told us "not a fit"
    # must never be re-drafted or re-sent — even if a later bounce-recovery pass
    # clears outreach_sent_at.
    meta = getattr(company, "crm_metadata", None) or {}
    if meta.get("do_not_contact"):
        return False, f"do-not-contact ({meta.get('do_not_contact_reason') or 'opt_out'})"
    stage = (getattr(acct, "outreach_stage", None) or "").lower()
    if stage in ("opted_out", "unsubscribed", "not_a_fit"):
        return False, f"suppressed ({stage})"

    name = (getattr(company, "name", None) or "").strip()
    junk, reason = is_junk(name, "buyer")
    if junk:
        return False, f"junk/vendor: {reason}"
    if not company_website_domain(company, acct):
        return False, "no verifiable website domain"
    blob = (
        f"{name.lower()} "
        f"{(getattr(company, 'industry', None) or '').lower()} "
        f"{(getattr(company, 'sub_industry', None) or '').lower()}"
    )
    if any(tok in blob for tok in _CAL_IN_ICP_OVERRIDE_TOKENS):
        return True, "ok"
    for tok in _CAL_OFF_ICP_INDUSTRY_TOKENS:
        if tok in blob:
            return False, f"off-ICP industry ({tok})"
    return True, "ok"


def prioritize_unsent(companies: list, accounts_by_company_id: dict) -> list:
    """Move never-contacted buyers to the front of the HOT/WARM window.

    ``companies`` is a list of ``(company, score, tier)`` tuples in score order.
    ``accounts_by_company_id`` maps company id -> CrmAccount. Accounts that have
    already been sent (``outreach_sent_at`` set) fall to the back so the draft
    batch and send loop reach actionable/reset runway first. Sort is stable, so
    score order is preserved within the unsent and already-sent groups.
    """
    def _already_contacted(entry) -> int:
        acct = accounts_by_company_id.get(entry[0].id)
        return 1 if (acct is not None and getattr(acct, "outreach_sent_at", None)) else 0

    return sorted(companies, key=_already_contacted)


def run_cal_autonomy_cycle(
    db: Session,
    *,
    dry_run: bool = False,
    admin_uid: Optional[uuid.UUID] = None,
    admin_email: str = "",
) -> dict[str, Any]:
    """Draft pending HOT+WARM leads, refresh stale copy, send up to limit, notify on format change."""
    if not cal_autonomy_enabled():
        return {"status": "disabled", "reason": "CAL_AUTONOMY_ENABLED / ENABLE_SCHEDULED_CAL_AUTONOMY off"}

    if admin_uid is not None:
        from app.api.admin_extended import _admin_team

        team = _admin_team(db, admin_uid, admin_email or get_cal_review_email() or "admin@readyforrobots.com")
        uid = admin_uid
    else:
        ctx = resolve_cal_admin_context(db)
        if not ctx:
            return {"status": "skipped", "reason": "No admin-cal-outreach team — sign in to /admin once or set CAL_ADMIN_USER_ID"}
        uid, team = ctx
    from app.api.admin_extended import (
        _hot_warm_companies,
        _invalidate_admin_caches,
        _cal_draft_for_company,
    )
    from app.services.lead_enrichment import (
        outreach_recipient_trusted,
        resolve_outreach_email,
        verify_email_deliverable,
    )
    from app.services.company_domain import normalize_website_domain
    from app.services.outreach_email_inference import infer_cc_outreach_emails
    from app.services.resend_email import ResendEmailError, send_email_via_resend
    from app.models.crm import CrmAccount

    draft_limit = int(os.getenv("CAL_AUTONOMY_DRAFT_BATCH", "100") or "100")
    send_limit = int(os.getenv("CAL_AUTONOMY_SEND_LIMIT", "25") or "25")
    # Angle rotation: only draft with angles that haven't been auto-retired.
    allowed_variants = active_buyer_variants(db)
    # Daily cap across all cycles — resume auto-send throttled low.
    daily_cap = cal_daily_send_cap()
    already_sent_today = cal_daily_sent_count()
    daily_remaining = max(0, daily_cap - already_sent_today) if daily_cap else send_limit
    if daily_cap:
        send_limit = min(send_limit, daily_remaining)
    followup_limit = int(os.getenv("CAL_AUTONOMY_FOLLOWUP_LIMIT", "25") or "25")
    # Pool window is decoupled from the draft batch so Cal can look past the
    # bounce-era top ranks and reach freshly-unsent (or reset) buyers deeper in
    # the HOT/WARM list. Sends stay throttled by send_limit and the verified gate.
    pool_limit = int(os.getenv("CAL_AUTONOMY_POOL", "400") or "400")
    stale_days = int(os.getenv("CAL_REFRESH_STALE_DAYS", "7") or "7")
    stale_before = datetime.now(timezone.utc) - timedelta(days=max(stale_days, 1))

    companies = _hot_warm_companies(db, limit=max(pool_limit, draft_limit, 100))
    company_ids = [c.id for c, _, _ in companies]
    existing: dict[int, CrmAccount] = {}
    if company_ids:
        for acct in db.query(CrmAccount).filter(
            CrmAccount.company_id.in_(company_ids),
            CrmAccount.team_id == team.id,
        ).all():
            if acct.company_id:
                existing[acct.company_id] = acct

    # Prioritise never-sent buyers so the draft batch and send loop reach
    # actionable runway first (incl. accounts reset after a bounce-era send).
    companies = prioritize_unsent(companies, existing)

    drafted = 0
    refreshed = 0
    skipped_ineligible = 0
    format_sample: Optional[tuple[str, str, str]] = None

    for company, _score, _tier in companies[:draft_limit]:
        acct = existing.get(company.id)
        eligible, _elig_reason = _cal_buyer_eligible(company, acct)
        if not eligible:
            skipped_ineligible += 1
            continue
        did_draft, did_refresh = _draft_and_store(
            db,
            company=company,
            acct=acct,
            team=team,
            existing=existing,
            regenerate=False,
            stale_before=stale_before,
            allowed_variants=allowed_variants,
        )
        if did_draft:
            drafted += 1
        if did_refresh:
            refreshed += 1
        if format_sample is None and did_draft:
            sub, body = _cal_draft_for_company(company, fresh=True)
            format_sample = (company.name or "Sample", sub, format_cal_draft_storage(sub, body))

    new_fp = outreach_template_fingerprint()
    old_fp = _stored_template_fingerprint()
    format_notified = False
    if format_sample and (old_fp is None or old_fp != new_fp) and not dry_run:
        format_notified = notify_admin_of_format_change(
            sample_company=format_sample[0],
            sample_subject=format_sample[1],
            sample_draft=format_sample[2],
            previous_fingerprint=old_fp,
            new_fingerprint=new_fp,
        )
    if not dry_run and (old_fp != new_fp or old_fp is None):
        _persist_template_fingerprint(new_fp)

    sent = 0
    skipped_no_draft = 0
    skipped_already_sent = 0
    skipped_unverified = 0
    errors: list[dict[str, Any]] = []
    now = datetime.now(timezone.utc)

    for company, _score, tier in companies:
        if sent >= send_limit:
            break
        if tier not in ("HOT", "WARM"):
            continue
        acct = existing.get(company.id)
        if not acct or not acct.outreach_draft:
            skipped_no_draft += 1
            continue
        if acct.outreach_sent_at:
            skipped_already_sent += 1
            continue

        eligible, elig_reason = _cal_buyer_eligible(company, acct)
        if not eligible:
            skipped_ineligible += 1
            errors.append({
                "company_id": company.id,
                "name": company.name,
                "error": f"Ineligible buyer skipped ({elig_reason})",
            })
            continue

        # Always resolve so we know the email SOURCE — a pre-stored acct.contact_email
        # may be a laundered name-guess from a prior cycle.
        to_email, email_source, _title = resolve_outreach_email(company, acct, use_apollo=True)
        if not to_email:
            errors.append({"company_id": company.id, "name": company.name, "error": "No recipient email"})
            continue

        # Hard-gate: never send to guessed domains. Verified provider OR the
        # email must sit on the company's real website domain.
        trusted, trust_reason = outreach_recipient_trusted(company, acct, to_email, email_source)
        if not trusted:
            skipped_unverified += 1
            errors.append({
                "company_id": company.id,
                "name": company.name,
                "error": f"Unverified recipient skipped ({trust_reason})",
            })
            continue

        from app.api.admin_extended import cal_manual_approval_required

        if cal_manual_approval_required() and (acct.outreach_stage or "") not in (
            "draft_approved",
            "approved",
        ):
            skipped_no_draft += 1
            continue

        ok, verify_reason = verify_email_deliverable(to_email)
        if not ok:
            skipped_unverified += 1
            continue

        from app.services.cal_outreach_send import parse_cal_draft
        from app.services.cal_draft_guard import is_complete_cal_draft

        draft_ok, draft_reason = is_complete_cal_draft(acct.outreach_draft)
        if not draft_ok:
            skipped_no_draft += 1
            errors.append({
                "company_id": company.id,
                "name": company.name,
                "error": f"Incomplete draft skipped: {draft_reason}",
            })
            continue

        subject, body_text = parse_cal_draft(acct.outreach_draft, company.name or "your team")

        if dry_run:
            sent += 1
            continue

        from app.services.cal_assembly_agent import assemble_buyer_outreach, cal_assembly_required

        if cal_assembly_required():
            assembly = assemble_buyer_outreach(
                company_name=company.name or "",
                subject=subject,
                body=body_text,
            )
            if not assembly.approved:
                from app.services.cal_ops_monitor import record_cal_assembly_rejection

                record_cal_assembly_rejection(
                    db,
                    channel="buyer",
                    company_id=company.id,
                    vendor_name=company.name or "",
                    subject=subject,
                    issues=assembly.issues,
                )
                errors.append({
                    "company_id": company.id,
                    "name": company.name,
                    "error": f"Cal assembly rejected: {'; '.join(assembly.issues[:3])}",
                })
                continue

        domain = normalize_website_domain(company.website or acct.website)
        cc_list = infer_cc_outreach_emails(domain, company.industry, primary=to_email)
        cc_email = cc_list[0] if cc_list else None

        try:
            from app.services.cal_outreach_send import enroll_cal_followup, send_cal_intro_email

            from app.services.agent_messaging import resolve_buyer_variant

            variant_id = resolve_buyer_variant(company, acct)
            send_cal_intro_email(
                db,
                acct=acct,
                company=company,
                team_id=team.id,
                to_email=to_email,
                subject=subject,
                body_text=body_text,
                cc=[cc_email] if cc_email else None,
                sender_user_id=uid,
                idempotency_key=f"cal-auto-{acct.id}-{now.date().isoformat()}",
                send_identity="cal",
                variant_id=variant_id,
            )
            sent += 1
            _incr_daily_sent(1)
            enroll_cal_followup(db, team_id=team.id, crm_account_id=acct.id, variant_id=variant_id)
        except ResendEmailError as exc:
            errors.append({"company_id": company.id, "name": company.name, "error": str(exc)})

    followups: dict[str, Any] = {"processed": 0, "sent": 0, "skipped": 0, "failed": 0}
    if not dry_run:
        try:
            from app.services.sequence_runner import process_due_enrollments

            followups = process_due_enrollments(db, limit=followup_limit)
        except Exception as exc:
            logger.warning("Cal follow-up cycle failed: %s", exc)

    if not dry_run:
        db.commit()
        _invalidate_admin_caches()

    return {
        "status": "ok",
        "dry_run": dry_run,
        "drafted": drafted,
        "refreshed": refreshed,
        "sent": sent,
        "followups": followups,
        "skipped_no_draft": skipped_no_draft,
        "skipped_already_sent": skipped_already_sent,
        "skipped_unverified": skipped_unverified,
        "skipped_ineligible": skipped_ineligible,
        "errors": errors[:20],
        "template_fingerprint": new_fp,
        "format_review_notified": format_notified,
        "review_email": get_cal_review_email(),
        "admin_user_id": str(uid),
        "active_variants": allowed_variants,
        "daily_cap": daily_cap,
        "daily_sent": cal_daily_sent_count(),
    }


def get_cal_autonomy_status() -> dict[str, Any]:
    from app.services.cal_assembly_agent import get_cal_assembly_status

    try:
        from app.services.cal_watchdog import watchdog_status

        heartbeat = watchdog_status()
    except Exception:
        heartbeat = None

    return {
        "heartbeat": heartbeat,
        "enabled": cal_autonomy_enabled(),
        "env_enabled": _cal_autonomy_env_default(),
        "runtime_override": get_cal_autonomy_runtime_override(),
        "runtime_toggle_available": _redis_client() is not None,
        "scheduled_on_worker": os.getenv("ENABLE_SCHEDULED_CAL_AUTONOMY", "1").strip().lower()
        not in ("0", "false", "no"),
        "review_email": get_cal_review_email(),
        "template_fingerprint": outreach_template_fingerprint(),
        "stored_fingerprint": _stored_template_fingerprint(),
        "template_version": os.getenv("CAL_TEMPLATE_VERSION") or "2",
        "send_limit": int(os.getenv("CAL_AUTONOMY_SEND_LIMIT", "25") or "25"),
        "followup_limit": int(os.getenv("CAL_AUTONOMY_FOLLOWUP_LIMIT", "25") or "25"),
        "draft_batch": int(os.getenv("CAL_AUTONOMY_DRAFT_BATCH", "100") or "100"),
        "pool_window": int(os.getenv("CAL_AUTONOMY_POOL", "400") or "400"),
        "refresh_stale_days": int(os.getenv("CAL_REFRESH_STALE_DAYS", "7") or "7"),
        "every_hours": float(os.getenv("CAL_AUTONOMY_EVERY_HOURS", "3") or "3"),
        "manual_approval": (os.getenv("CAL_MANUAL_APPROVAL") or "0").strip().lower() in ("1", "true", "yes"),
        "assembly": get_cal_assembly_status(),
    }
