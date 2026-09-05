#!/usr/bin/env python3
"""RETIRED. Hermes ingest is not a Jobs feed.

Fly ingest returns 410 unless HERMES_INGEST_ENABLED=1.
Jobs uses POST /api/robot-job-match.
Leftover --provider ai-gateway (HTTP 402) must not be revived.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from hermes_retired import RETIRED_MSG, refuse_unless_overridden  # noqa: E402

if __name__ == "__main__":
    refuse_unless_overridden()
    print(RETIRED_MSG, file=sys.stderr)
    raise SystemExit(2)
