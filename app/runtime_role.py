"""Fly process role — web serves HTTP; worker runs cache rebuilds and schedulers."""
from __future__ import annotations

import os


def process_role() -> str:
    """``web`` (API only) or ``worker`` (background jobs)."""
    explicit = (os.getenv("RFR_PROCESS_ROLE") or "").strip().lower()
    if explicit in ("web", "worker"):
        return explicit
    fly_group = (os.getenv("FLY_PROCESS_GROUP") or "").strip().lower()
    if fly_group in ("web", "worker"):
        return fly_group
    return "web"


def is_web_process() -> bool:
    return process_role() == "web"


def is_worker_process() -> bool:
    return process_role() == "worker"
