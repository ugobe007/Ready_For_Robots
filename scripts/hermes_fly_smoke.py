#!/usr/bin/env python3
"""RETIRED. Do not --apply Hermes infer-qualify onto Fly.

The old path was scripts/hermes_auth_smoke.py --apply via
.github/workflows/hermes-fly-smoke.yml. That workflow is skip-by-default.
Jobs uses POST /api/robot-job-match.
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
