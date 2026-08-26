"""Hermes is retired. Jobs uses POST /api/robot-job-match.

Scripts that used to ingest into Fly or smoke Hermes must call
refuse_unless_overridden() first. Set HERMES_RETIRED_OVERRIDE=1 only for
forensics. Do not pin leftover --provider ai-gateway (HTTP 402).
"""
from __future__ import annotations

import os
import sys

RETIRED_MSG = "Hermes is retired — Jobs uses POST /api/robot-job-match"


def refuse_unless_overridden() -> None:
    if os.environ.get("HERMES_RETIRED_OVERRIDE", "").strip() != "1":
        print(RETIRED_MSG, file=sys.stderr)
        raise SystemExit(2)
