"""Cal worker watchdog — heartbeat + email alert so Cal can't die silently.

The worker process (which runs Cal's autonomy scheduler) writes a heartbeat to
Redis on every loop tick. The always-on web process runs a watchdog that alerts
the admin by email if the heartbeat goes stale (worker stopped, crash-looped, or
the scheduler thread died). It also sends a one-shot "recovered" notice.

All functions fail safe: with no Redis or no email configured they no-op rather
than raise, so the watchdog can never take down a process it's meant to protect.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Optional

logger = logging.getLogger(__name__)

_HEARTBEAT_KEY = "cal:heartbeat:autonomy"
_ALERT_STATE_KEY = "cal:watchdog:alerted"  # set while an outage alert is outstanding
_ALERT_COOLDOWN_KEY = "cal:watchdog:alert_cooldown"  # TTL guard against repeat alerts

_HEARTBEAT_TTL_SEC = 2 * 24 * 3600


def _redis_client():
    url = (os.getenv("REDIS_URL") or os.getenv("CELERY_BROKER_URL") or "").strip()
    if not url:
        return None
    try:
        import redis

        return redis.from_url(url, decode_responses=True)
    except Exception:
        return None


def _now() -> datetime:
    return datetime.now(timezone.utc)


def stale_threshold_seconds() -> int:
    minutes = float(os.getenv("CAL_WATCHDOG_STALE_MINUTES", "30") or "30")
    return int(max(300, minutes * 60))


def watchdog_enabled() -> bool:
    return (os.getenv("CAL_WATCHDOG_ENABLED", "1") or "1").strip().lower() not in ("0", "false", "no")


# ── Fly Machines API (self-heal) ─────────────────────────────────────────────────
def _fly_api_token() -> str:
    return (os.getenv("FLY_API_TOKEN") or os.getenv("FLY_MACHINES_TOKEN") or "").strip()


def _fly_app_name() -> str:
    return (os.getenv("FLY_APP_NAME") or os.getenv("FLY_APP") or "").strip()


def _fly_machines_base() -> str:
    return (os.getenv("FLY_MACHINES_API") or "https://api.machines.dev").rstrip("/")


def _fly_machines_api(method: str, path: str, timeout: float = 10.0):
    """Minimal Fly Machines API call. Returns (status_code, parsed_json | None).

    Raises on transport error so callers can log and fail open. Kept as a thin,
    monkeypatchable seam so the self-heal logic can be unit-tested without network.
    """
    import urllib.request

    req = urllib.request.Request(
        f"{_fly_machines_base()}{path}",
        method=method,
        headers={
            "Authorization": f"Bearer {_fly_api_token()}",
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read().decode() or ""
        data = json.loads(raw) if raw.strip() else None
        return resp.status, data


def autostart_stopped_workers() -> dict[str, Any]:
    """Best-effort: start any 'worker' process-group machine that is stopped.

    Fly's ``[[restart]] policy = "always"`` only restarts a crashed *process* on a
    *running* machine — it does not start a machine left in the ``stopped`` state
    (by a deploy or crash-backoff). This closes that gap so the always-on web
    watchdog can bring Cal's worker back without a human.

    Fails open: missing token/app or any API error → no-op (never raises).
    """
    if not _fly_api_token():
        return {"attempted": False, "reason": "no_token"}
    app = _fly_app_name()
    if not app:
        return {"attempted": False, "reason": "no_app"}
    try:
        status, machines = _fly_machines_api("GET", f"/v1/apps/{app}/machines")
    except Exception as exc:
        logger.warning("[cal-watchdog] fly list machines failed: %s", exc)
        return {"attempted": True, "reason": "list_failed", "error": str(exc)[:200]}
    if status >= 300 or not isinstance(machines, list):
        return {"attempted": True, "reason": f"list_status_{status}"}

    started: list[str] = []
    failed: list[str] = []
    for m in machines:
        if not isinstance(m, dict):
            continue
        pg = ((m.get("config") or {}).get("metadata") or {}).get("fly_process_group")
        if pg != "worker" or m.get("state") == "started":
            continue
        mid = m.get("id")
        if not mid:
            continue
        try:
            _fly_machines_api("POST", f"/v1/apps/{app}/machines/{mid}/start")
            started.append(mid)
            logger.warning("[cal-watchdog] auto-started stopped worker machine %s", mid)
        except Exception as exc:
            failed.append(mid)
            logger.warning("[cal-watchdog] fly start %s failed: %s", mid, exc)
    return {"attempted": True, "started": started, "failed": failed}


# ── Heartbeat (worker side) ─────────────────────────────────────────────────────
def record_cal_heartbeat(status: str = "alive", extra: Optional[dict[str, Any]] = None) -> bool:
    client = _redis_client()
    if not client:
        return False
    payload = {"ts": _now().isoformat(), "status": status}
    if extra:
        payload.update(extra)
    try:
        client.set(_HEARTBEAT_KEY, json.dumps(payload), ex=_HEARTBEAT_TTL_SEC)
        return True
    except Exception:
        return False


def get_cal_heartbeat() -> Optional[dict[str, Any]]:
    client = _redis_client()
    if not client:
        return None
    try:
        raw = client.get(_HEARTBEAT_KEY)
        if not raw:
            return None
        data = json.loads(raw)
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def cal_heartbeat_age_seconds() -> Optional[float]:
    hb = get_cal_heartbeat()
    if not hb or not hb.get("ts"):
        return None
    try:
        ts = datetime.fromisoformat(str(hb["ts"]))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        return max(0.0, (_now() - ts).total_seconds())
    except Exception:
        return None


def watchdog_status() -> dict[str, Any]:
    """Compact heartbeat health for the admin Command Center."""
    hb = get_cal_heartbeat()
    age = cal_heartbeat_age_seconds()
    threshold = stale_threshold_seconds()
    stale = age is None or age > threshold
    return {
        "enabled": watchdog_enabled(),
        "redis_available": _redis_client() is not None,
        "last_heartbeat": hb.get("ts") if hb else None,
        "last_status": hb.get("status") if hb else None,
        "age_seconds": int(age) if age is not None else None,
        "stale_threshold_seconds": threshold,
        "stale": stale,
    }


# ── Alerting (web side) ─────────────────────────────────────────────────────────
def _send_alert_email(subject: str, body: str) -> bool:
    try:
        from app.services.cal_autonomy import get_cal_review_email
        from app.services.resend_email import send_email_via_resend

        to_email = get_cal_review_email()
        if not to_email:
            logger.warning("[cal-watchdog] no admin email configured; cannot alert")
            return False
        send_email_via_resend(
            to_email=to_email,
            subject=subject,
            body_text=body,
            from_display_name="Ready For Robots Watchdog",
        )
        return True
    except Exception as exc:
        logger.warning("[cal-watchdog] alert email failed: %s", exc)
        return False


def _cooldown_active(client) -> bool:
    try:
        return bool(client.get(_ALERT_COOLDOWN_KEY))
    except Exception:
        return False


def _arm_cooldown(client) -> None:
    hours = float(os.getenv("CAL_WATCHDOG_ALERT_COOLDOWN_HOURS", "6") or "6")
    try:
        client.set(_ALERT_COOLDOWN_KEY, _now().isoformat(), ex=int(max(600, hours * 3600)))
    except Exception:
        pass


def check_and_alert() -> dict[str, Any]:
    """One watchdog pass. Alerts once when Cal goes stale; notifies once on recovery.

    Returns a small dict describing the action taken (for logs/tests).
    """
    if not watchdog_enabled():
        return {"checked": False, "reason": "disabled"}

    # Only alert when Cal is supposed to be running.
    try:
        from app.services.cal_autonomy import cal_autonomy_enabled

        cal_on = cal_autonomy_enabled()
    except Exception:
        cal_on = True
    scheduled = (os.getenv("ENABLE_SCHEDULED_CAL_AUTONOMY", "1") or "1").strip().lower() not in (
        "0", "false", "no",
    )
    if not (cal_on and scheduled):
        return {"checked": False, "reason": "cal_disabled"}

    client = _redis_client()
    if not client:
        return {"checked": False, "reason": "no_redis"}

    age = cal_heartbeat_age_seconds()
    threshold = stale_threshold_seconds()
    stale = age is None or age > threshold

    try:
        alerted_outstanding = bool(client.get(_ALERT_STATE_KEY))
    except Exception:
        alerted_outstanding = False

    if stale:
        if _cooldown_active(client):
            return {"checked": True, "stale": True, "action": "cooldown"}

        # Self-heal first: try to start a stopped worker machine, then notify.
        autostart = autostart_stopped_workers()
        recovered_ids = autostart.get("started") or []
        age_desc = "never (no heartbeat)" if age is None else f"{int(age // 60)} min ago"

        if recovered_ids:
            subject = "🔧 Cal worker was down — auto-restarted"
            body = (
                "Ready For Robots watchdog detected Cal's autonomy worker had not "
                f"reported a heartbeat within the last {threshold // 60} minutes and "
                "automatically restarted it.\n\n"
                f"Last heartbeat: {age_desc}\n"
                f"Restarted machine(s): {', '.join(recovered_ids)}\n\n"
                "Cal should resume drafting/sending within a few minutes; you'll get a "
                "follow-up email once the heartbeat is confirmed healthy.\n\n"
                "If this keeps recurring, check for OOM/crash-loops:\n"
                "  fly logs -a ready-2-robot\n"
            )
        else:
            reason = autostart.get("reason")
            if reason == "no_token":
                note = (
                    "Auto-restart is not configured (no FLY_API_TOKEN secret), so this "
                    "needs manual recovery.\n\n"
                )
            elif autostart.get("attempted"):
                note = "Auto-restart was attempted but did not start a worker (see logs).\n\n"
            else:
                note = ""
            subject = "⚠️ Cal worker may be down — heartbeat stale"
            body = (
                "Ready For Robots watchdog detected that Cal's autonomy worker has not "
                f"reported a heartbeat within the last {threshold // 60} minutes.\n\n"
                f"Last heartbeat: {age_desc}\n\n"
                f"{note}"
                "Likely cause: the Fly 'worker' machine is stopped or crash-looping, so "
                "Cal is not drafting/sending outreach.\n\n"
                "How to recover:\n"
                "  1. fly status -a ready-2-robot   (check the worker machine STATE)\n"
                "  2. fly machine start <worker-id> -a ready-2-robot\n"
                "  3. fly logs -a ready-2-robot   (look for tracebacks on boot)\n\n"
                "You will get a follow-up email when Cal's heartbeat recovers."
            )
        sent = _send_alert_email(subject, body)
        if sent:
            try:
                client.set(_ALERT_STATE_KEY, _now().isoformat(), ex=_HEARTBEAT_TTL_SEC)
            except Exception:
                pass
            _arm_cooldown(client)
        logger.warning(
            "[cal-watchdog] Cal heartbeat stale (age=%s); autostart=%s alert sent=%s",
            age, autostart, sent,
        )
        return {
            "checked": True,
            "stale": True,
            "action": "alert" if sent else "alert_failed",
            "autostart": autostart,
        }

    # Healthy — clear any outstanding alert and notify recovery once.
    if alerted_outstanding:
        _send_alert_email(
            "✅ Cal worker recovered — heartbeat healthy",
            "Cal's autonomy worker is reporting heartbeats again. Outreach cycles have resumed.",
        )
        try:
            client.delete(_ALERT_STATE_KEY)
            client.delete(_ALERT_COOLDOWN_KEY)
        except Exception:
            pass
        return {"checked": True, "stale": False, "action": "recovered"}

    return {"checked": True, "stale": False, "action": "ok"}
