"""
Robot Understanding v1 — Phases 1–3 only.

URL → identity → typed sources → atomic facts → auditable Robot Profile → STOP.

No jobs. No capability→workflow inference. No matcher.
Governing standard: docs/robot_understanding_v1.md
"""
from __future__ import annotations

from app.services.robot_understanding_v1.pipeline import build_robot_profile
from app.services.robot_understanding_v1.models import RobotProfile

__all__ = ["build_robot_profile", "RobotProfile"]
