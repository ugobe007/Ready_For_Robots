"""
Reliable secondary-pass execution on Fly (SKIP_CELERY=1).

Problems this fixes:
- Admin BackgroundTasks bypassed locks and could run leads + humanoids concurrently.
- App loggers were invisible in Fly logs (no basicConfig).
- No status surface to confirm success vs silent failure.

One global lock serializes all secondary work. Scheduled runs execute leads then humanoids
sequentially in a single daemon thread.
"""
from __future__ import annotations

import logging
import os
import threading
import traceback
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Literal, Optional

logger = logging.getLogger(__name__)

JobKind = Literal["leads", "humanoids", "full"]

_GLOBAL_LOCK = threading.Lock()
_STATE_LOCK = threading.Lock()

_STATE: Dict[str, Any] = {
    "running": None,
    "running_since": None,
    "last_leads": None,
    "last_humanoids": None,
    "last_full": None,
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _emit(event: str, **fields: Any) -> None:
    """Print to stdout (Fly captures) and log at INFO."""
    parts = " ".join(f"{k}={v}" for k, v in fields.items())
    line = f"[secondary-pass] {event}" + (f" {parts}" if parts else "")
    print(line, flush=True)
    logger.info(line)


def get_secondary_pass_status() -> Dict[str, Any]:
    with _STATE_LOCK:
        return {
            "running": _STATE["running"],
            "running_since": _STATE["running_since"],
            "last_leads": _STATE["last_leads"],
            "last_humanoids": _STATE["last_humanoids"],
            "last_full": _STATE["last_full"],
        }


def _set_running(kind: Optional[JobKind]) -> None:
    with _STATE_LOCK:
        _STATE["running"] = kind
        _STATE["running_since"] = _utc_now() if kind else None


def _record_finish(kind: JobKind, result: Dict[str, Any]) -> None:
    entry = {
        "finished_at": _utc_now(),
        "status": result.get("status", "completed"),
        "stats": {k: v for k, v in result.items() if k != "sample"},
        "sample": (result.get("sample") or [])[:5],
    }
    with _STATE_LOCK:
        if kind == "leads":
            _STATE["last_leads"] = entry
        elif kind == "humanoids":
            _STATE["last_humanoids"] = entry
        else:
            _STATE["last_full"] = entry


def _record_error(kind: JobKind, exc: BaseException) -> Dict[str, Any]:
    result = {
        "status": "failed",
        "error": str(exc)[:500],
        "traceback": traceback.format_exc()[-1500:],
    }
    entry = {"finished_at": _utc_now(), **result}
    with _STATE_LOCK:
        if kind == "leads":
            _STATE["last_leads"] = entry
        elif kind == "humanoids":
            _STATE["last_humanoids"] = entry
        else:
            _STATE["last_full"] = entry
    return result


def _llm_available() -> bool:
    return bool(os.getenv("ANTHROPIC_API_KEY") or os.getenv("OPENAI_API_KEY"))


def run_leads_secondary_pass_sync(
    *,
    limit: int = 120,
    min_score: float = 15.0,
    use_llm: bool = True,
    rescore: bool = True,
) -> Dict[str, Any]:
    if not _GLOBAL_LOCK.acquire(blocking=False):
        _emit("leads_skipped", reason="already_running", running=get_secondary_pass_status().get("running"))
        return {"status": "skipped", "reason": "already_running"}

    _set_running("leads")
    _emit("leads_start", limit=limit, min_score=min_score, use_llm=use_llm)
    try:
        from app.services.lead_secondary_pass import run_secondary_pass_batch_and_refresh_caches

        if use_llm and not _llm_available():
            _emit("leads_llm_disabled", reason="no_api_key")
            use_llm = False

        stats = run_secondary_pass_batch_and_refresh_caches(
            limit=limit,
            min_score=min_score,
            use_llm=use_llm,
            rescore=rescore,
        )
        result = {"status": "completed", **stats}
        _record_finish("leads", result)
        _emit(
            "leads_done",
            processed=stats.get("processed"),
            fields_filled=stats.get("fields_filled_total"),
            errors=stats.get("errors"),
        )
        return result
    except Exception as exc:
        result = _record_error("leads", exc)
        _emit("leads_failed", error=str(exc)[:200])
        return result
    finally:
        _set_running(None)
        _GLOBAL_LOCK.release()


def run_humanoids_secondary_pass_sync(
    *,
    limit: int = 40,
    sparse_threshold_pct: float = 85.0,
    use_llm_scrape: bool = True,
    persist_deployment_news: bool = True,
    deployment_query_cap: int = 24,
) -> Dict[str, Any]:
    if not _GLOBAL_LOCK.acquire(blocking=False):
        _emit("humanoids_skipped", reason="already_running", running=get_secondary_pass_status().get("running"))
        return {"status": "skipped", "reason": "already_running"}

    _set_running("humanoids")
    _emit("humanoids_start", limit=limit, use_llm=use_llm_scrape, news_queries=deployment_query_cap)
    try:
        from app.services.humanoid_secondary_pass import (
            run_humanoid_secondary_pass_batch_and_refresh_caches,
        )

        if use_llm_scrape and not os.getenv("ANTHROPIC_API_KEY"):
            _emit("humanoids_llm_disabled", reason="no_anthropic_key")
            use_llm_scrape = False

        stats = run_humanoid_secondary_pass_batch_and_refresh_caches(
            limit=limit,
            sparse_threshold_pct=sparse_threshold_pct,
            use_llm_scrape=use_llm_scrape,
            persist_deployment_news=persist_deployment_news,
            deployment_query_cap=deployment_query_cap,
        )
        result = {"status": "completed", **stats}
        _record_finish("humanoids", result)
        news_updated = (stats.get("deployment_news") or {}).get("robots_updated")
        _emit(
            "humanoids_done",
            processed=stats.get("processed"),
            errors=stats.get("errors"),
            news_updated=news_updated,
            avg_spec_fill=stats.get("avg_spec_fill_pct"),
        )
        return result
    except Exception as exc:
        result = _record_error("humanoids", exc)
        _emit("humanoids_failed", error=str(exc)[:200])
        return result
    finally:
        _set_running(None)
        _GLOBAL_LOCK.release()


def run_full_secondary_pipeline_sync(
    *,
    lead_limit: Optional[int] = None,
    lead_min_score: Optional[float] = None,
    lead_use_llm: Optional[bool] = None,
    lead_rescore: Optional[bool] = None,
    humanoid_limit: Optional[int] = None,
    humanoid_sparse_pct: Optional[float] = None,
    humanoid_use_llm: Optional[bool] = None,
    humanoid_persist_news: Optional[bool] = None,
    humanoid_news_queries: Optional[int] = None,
) -> Dict[str, Any]:
    """Run leads then humanoids under one lock (scheduled nightly job)."""
    if not _GLOBAL_LOCK.acquire(blocking=False):
        _emit("pipeline_skipped", reason="already_running")
        return {"status": "skipped", "reason": "already_running"}

    _set_running("full")
    _emit("pipeline_start")
    leads_result: Dict[str, Any] = {}
    humanoids_result: Dict[str, Any] = {}

    try:
        from app.services.lead_secondary_pass import run_secondary_pass_batch_and_refresh_caches
        from app.services.humanoid_secondary_pass import (
            run_humanoid_secondary_pass_batch_and_refresh_caches,
        )

        lim = lead_limit if lead_limit is not None else int(os.getenv("SECONDARY_PASS_LIMIT", "120"))
        min_score = lead_min_score if lead_min_score is not None else float(
            os.getenv("SECONDARY_PASS_MIN_SCORE", "15")
        )
        use_llm = (
            lead_use_llm
            if lead_use_llm is not None
            else os.getenv("SECONDARY_PASS_USE_LLM", "1").strip().lower() not in ("0", "false", "no")
        )
        rescore = (
            lead_rescore
            if lead_rescore is not None
            else os.getenv("SECONDARY_PASS_RESCORE", "1").strip().lower() not in ("0", "false", "no")
        )
        if use_llm and not _llm_available():
            use_llm = False

        _emit("pipeline_leads_start", limit=lim)
        leads_result = run_secondary_pass_batch_and_refresh_caches(
            limit=lim,
            min_score=min_score,
            use_llm=use_llm,
            rescore=rescore,
        )
        leads_result = {"status": "completed", **leads_result}
        _emit(
            "pipeline_leads_done",
            processed=leads_result.get("processed"),
            fields_filled=leads_result.get("fields_filled_total"),
            errors=leads_result.get("errors"),
        )

        if os.getenv("SECONDARY_PIPELINE_RUN_HUMANOIDS", "1").strip().lower() not in (
            "0", "false", "no"
        ):
            h_lim = humanoid_limit if humanoid_limit is not None else int(
                os.getenv("HUMANOID_SECONDARY_PASS_LIMIT", "40")
            )
            sparse = humanoid_sparse_pct if humanoid_sparse_pct is not None else float(
                os.getenv("HUMANOID_SECONDARY_PASS_SPARSE_PCT", "85")
            )
            h_llm = (
                humanoid_use_llm
                if humanoid_use_llm is not None
                else os.getenv("HUMANOID_SECONDARY_PASS_USE_LLM", "1").strip().lower()
                not in ("0", "false", "no")
            )
            persist = (
                humanoid_persist_news
                if humanoid_persist_news is not None
                else os.getenv("HUMANOID_SECONDARY_PASS_PERSIST_NEWS", "1").strip().lower()
                not in ("0", "false", "no")
            )
            news_q = humanoid_news_queries if humanoid_news_queries is not None else int(
                os.getenv("HUMANOID_SECONDARY_PASS_NEWS_QUERIES", "24")
            )
            if h_llm and not os.getenv("ANTHROPIC_API_KEY"):
                h_llm = False

            _emit("pipeline_humanoids_start", limit=h_lim)
            humanoids_result = run_humanoid_secondary_pass_batch_and_refresh_caches(
                limit=h_lim,
                sparse_threshold_pct=sparse,
                use_llm_scrape=h_llm,
                persist_deployment_news=persist,
                deployment_query_cap=news_q,
            )
            humanoids_result = {"status": "completed", **humanoids_result}
            _emit(
                "pipeline_humanoids_done",
                processed=humanoids_result.get("processed"),
                news_updated=(humanoids_result.get("deployment_news") or {}).get("robots_updated"),
            )
        else:
            humanoids_result = {"status": "skipped", "reason": "SECONDARY_PIPELINE_RUN_HUMANOIDS=0"}

        combined = {
            "status": "completed",
            "leads": leads_result,
            "humanoids": humanoids_result,
        }
        _record_finish("full", combined)
        _emit("pipeline_done")
        return combined
    except Exception as exc:
        result = _record_error("full", exc)
        _emit("pipeline_failed", error=str(exc)[:200])
        return {**result, "leads": leads_result, "humanoids": humanoids_result}
    finally:
        _set_running(None)
        _GLOBAL_LOCK.release()


def start_secondary_job_in_thread(
    fn: Callable[..., Dict[str, Any]],
    *,
    job_kind: JobKind,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Non-blocking trigger for admin/cron — runs in a dedicated daemon thread."""
    status = get_secondary_pass_status()
    if status.get("running"):
        return {
            "status": "skipped",
            "reason": "already_running",
            "running": status["running"],
            "running_since": status.get("running_since"),
        }

    def _target() -> None:
        try:
            fn(**kwargs)
        except Exception as exc:
            _emit("thread_job_failed", kind=job_kind, error=str(exc)[:200])
            logger.exception("Secondary job thread failed (%s): %s", job_kind, exc)

    t = threading.Thread(target=_target, name=f"secondary-{job_kind}", daemon=True)
    t.start()
    _emit("thread_job_started", kind=job_kind)
    return {"status": "started", "job": job_kind, "kwargs": kwargs}
