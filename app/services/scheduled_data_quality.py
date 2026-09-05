"""
Scheduled data-quality maintenance (weekly on Fly when SKIP_CELERY=1).

  1. Purge invalid leads (is_valid_lead gate)
  2. Normalize company names
  3. Export quality decision log for rule mining
"""
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

logger = logging.getLogger(__name__)

_STATE: Dict[str, Any] = {"last_run": None, "last_result": None}


def get_data_quality_job_status() -> Dict[str, Any]:
    return dict(_STATE)


def run_weekly_data_quality_job(*, apply: bool = True) -> Dict[str, Any]:
    """
    Weekly hygiene: purge junk via logic engine, normalize names, export JSONL log.
    """
    import sys
    from pathlib import Path

    from app.database import SessionLocal
    from app.models.company import Company
    from app.services.quality_decision_log import build_decision_record, export_timestamp_iso

    root = Path(__file__).resolve().parents[2]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from scripts.cleanup_leads import Stats, phase_normalize_names, phase_purge_junk

    started = datetime.now(timezone.utc).isoformat()
    result: Dict[str, Any] = {"started_at": started, "apply": apply}

    db = SessionLocal()
    db.expire_on_commit = False
    try:

        stats = Stats()
        phase_purge_junk(db, apply, stats, junk_only=False)
        db.expire_all()
        phase_normalize_names(db, apply, stats)
        db.commit()
        result["purge_deleted"] = stats.junk_deleted
        result["names_normalized"] = stats.normalized_names

        export_limit = int(os.getenv("QUALITY_LOG_EXPORT_LIMIT", "2500"))
        since_id = int(os.getenv("QUALITY_LOG_SINCE_ID", "0") or "0")
        q = db.query(Company).order_by(Company.id.desc())
        if since_id > 0:
            q = q.filter(Company.id >= since_id)
        rows = q.limit(export_limit).all()

        export_ts = export_timestamp_iso()
        records = [
            build_decision_record(
                company_id=c.id,
                name=c.name or "",
                source=c.source,
                created_at=c.created_at,
                export_ts=export_ts,
            )
            for c in rows
        ]
        reports_dir = Path(__file__).resolve().parents[2] / "reports"
        reports_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        out_path = reports_dir / f"quality_decision_log_{stamp}.jsonl"
        with out_path.open("w", encoding="utf-8") as fh:
            for rec in records:
                fh.write(json.dumps(rec, default=str) + "\n")

        result["quality_log_path"] = str(out_path)
        result["quality_log_rows"] = len(records)
        result["exported_at"] = export_timestamp_iso()
        result["status"] = "completed"
        result["finished_at"] = datetime.now(timezone.utc).isoformat()

        try:
            from app.services.public_surface_cache import hydrate_public_surface_caches

            hydrate_public_surface_caches()
            result["cache_refresh"] = "ok"
        except Exception as exc:
            result["cache_refresh"] = f"failed: {exc}"

        _STATE["last_run"] = result["finished_at"]
        _STATE["last_result"] = {k: v for k, v in result.items() if k != "quality_log_path"}
        print(
            f"[data-quality] weekly job done purged={stats.junk_deleted} "
            f"log_rows={len(records)} path={out_path}",
            flush=True,
        )
        logger.info("Weekly data quality job complete: %s", result)
        return result
    except Exception as exc:
        logger.exception("Weekly data quality job failed: %s", exc)
        result["status"] = "failed"
        result["error"] = str(exc)[:500]
        _STATE["last_run"] = datetime.now(timezone.utc).isoformat()
        _STATE["last_result"] = result
        return result
    finally:
        db.close()
