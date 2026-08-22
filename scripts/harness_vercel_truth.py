#!/usr/bin/env python3
"""Classify whether a GitHub 'Deploy frontend to Vercel' run actually shipped."""
from __future__ import annotations

SKIP_SUCCESS_MAX_SECONDS = 30


def classify_frontend_deploy_run(
    *,
    conclusion: str | None,
    duration_seconds: float | None,
) -> str:
    """Return a deploy-truth label for one GHA run.

    A success under 30s is the missing-secrets skip (checkout + echo + done).
    A real `vercel build && vercel deploy --prebuilt --prod` is minutes.
    """
    status = (conclusion or "").strip().lower() or "unknown"
    if status != "success":
        return status
    if duration_seconds is not None and duration_seconds < SKIP_SUCCESS_MAX_SECONDS:
        return "skipped_missing_secrets"
    return "shipped_or_long_enough"


def vercel_production_is_a_lie(label: str) -> bool:
    return label == "skipped_missing_secrets"
