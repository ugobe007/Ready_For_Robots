#!/usr/bin/env python3
"""RETIRED. Hermes is not a Jobs agent.

There was never a single bridge runner in this repo. Mac cron plus
scripts/hermes_auth_smoke.py were the execution paths. Both are retired.
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
