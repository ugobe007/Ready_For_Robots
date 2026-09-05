"""hermes_auth_smoke.py — reject wrong secret kinds without hitting Fly."""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "hermes_auth_smoke.py"


def _load_smoke():
    spec = importlib.util.spec_from_file_location("hermes_auth_smoke", SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(mod)
    return mod


def _run(extra: dict[str, str]) -> subprocess.CompletedProcess[str]:
    env = {k: v for k, v in os.environ.items() if k not in ("RFR_ADMIN_KEY", "ADMIN_KEY")}
    env["HERMES_RETIRED_OVERRIDE"] = "1"
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


def test_request_maps_timeout_to_598(monkeypatch):
    smoke = _load_smoke()

    def _boom(*_a, **_k):
        raise TimeoutError("The read operation timed out")

    monkeypatch.setattr(smoke.urllib.request, "urlopen", _boom)
    monkeypatch.setattr(smoke.time, "sleep", lambda _s: None)
    code, body = smoke._request("https://example.com/timeout", "k", {"dry_run": True})
    assert code == 598
    assert body["error"] == "timeout"


def test_tracks_8_10_dry_payloads_are_dry_run():
    smoke = _load_smoke()
    payloads = smoke.tracks_8_10_dry_payloads(941)
    assert payloads["buying_window"]["dry_run"] is True
    assert payloads["video"]["dry_run"] is True
    assert payloads["vendor_video"]["dry_run"] is True
    assert payloads["buying_window"]["overlays"][0]["company_id"] == 941
    assert payloads["video"]["videos"][0]["source_url"].startswith("https://example.com/")
    assert payloads["vendor_video"]["videos"][0]["vendor_name"] == "Agility Robotics"
