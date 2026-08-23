"""hermes_auth_smoke.py — reject wrong secret kinds without hitting Fly."""
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hermes_auth_smoke.py"


def _run(extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = {
        k: v
        for k, v in os.environ.items()
        if k not in ("RFR_ADMIN_KEY", "ADMIN_KEY", "RFR_ADMIN_KEY")
    }
    env.update(extra)
    return subprocess.run(
        [sys.executable, str(SCRIPT)],
        env=env,
        capture_output=True,
        text=True,
        timeout=15,
    )


def test_smoke_rejects_service_role_jwt():
    proc = _run({"RFR_ADMIN_KEY": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.e30.sig"})
    assert proc.returncode == 1, proc.stdout + proc.stderr
    body = json.loads(proc.stdout)
    assert body["ok"] is False
    assert body["key_kind"] == "jwt"
    assert body["reason"] == "wrong_kind_of_secret"
