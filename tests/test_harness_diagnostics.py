"""Harness diagnostics — site health, code conventions, conversion parsing."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.harness_diagnostics import (
    _check_pricing_checkout_auth_gate,
    _parse_open_conversion_challenges,
    _probe_checkout_requires_auth,
    _scan_file_for_api_violations,
    check_code_conventions,
    render_daily_report_markdown,
)


def test_parse_open_conversion_challenges_finds_open_row():
    # Parser mechanics: Open rows are returned, ✅ Done rows are excluded.
    markdown = (
        "| Rank | Challenge | Agent | Acceptance test |\n"
        "|------|-----------|-------|-----------------|\n"
        "| 7 | **Done thing** — already shipped | ProductSurface | ✅ Done 2026-07-08 |\n"
        "| 8 | **Open thing** — needs building | ProductSurface | Open |\n"
    )
    rows = _parse_open_conversion_challenges(markdown)
    ranks = [r["rank"] for r in rows]
    assert ranks == [8]
    assert "open thing" in rows[0]["title"].lower()


def test_parse_open_conversion_challenges_live_board_parses():
    # The live board must parse without error; may legitimately be fully cleared.
    rows = _parse_open_conversion_challenges()
    assert isinstance(rows, list)
    assert all(isinstance(r.get("rank"), int) for r in rows)


def test_scan_flags_getapibase_without_public_read(tmp_path: Path):
    bad = tmp_path / "BadPage.tsx"
    bad.write_text(
        'import { getApiBase } from "@/lib/apiBase";\n'
        'fetch(`${getApiBase()}/api/leads/pipeline`);\n',
        encoding="utf-8",
    )
    violations = _scan_file_for_api_violations(bad)
    assert any(v["endpoint"] == "/api/leads/pipeline" for v in violations)


def test_scan_skips_when_public_read_helper_present(tmp_path: Path):
    ok = tmp_path / "GoodPage.tsx"
    ok.write_text(
        'import { getPublicReadApiBase } from "@/lib/apiBase";\n'
        'fetch(`${getPublicReadApiBase()}/api/humanoid/robots`);\n',
        encoding="utf-8",
    )
    assert _scan_file_for_api_violations(ok) == []


def test_check_code_conventions_login_import():
    code = check_code_conventions()
    assert code.get("login_import_ok") is True
    assert code.get("auth_helpers_ok") is True
    assert code.get("checkout_auth_gate_ok") is True
    assert code.get("supply_match_gate_ok") is True


def test_pricing_checkout_auth_gate_passes():
    gate = _check_pricing_checkout_auth_gate()
    assert gate["ok"] is True, gate.get("issues")


def test_checkout_api_requires_auth():
    probe = _probe_checkout_requires_auth()
    assert probe.get("ok") is True, probe


def test_render_daily_report_includes_sections():
    md = render_daily_report_markdown(
        snapshot={"api": {"pipeline": {"leads_count": 12, "built_at": "2026-01-01"}}},
        diagnostics={
            "conversion": {"available": True, "signups_7d": 2, "signups_total": 10, "active_subscriptions": 0},
            "site_health": {"fly_robots": {"ok": True, "robots_count": 50, "latency_ms": 800}, "alerts": []},
            "code_review": {"violation_count": 0, "open_conversion_challenges": []},
            "priority_actions": ["Test action"],
        },
        mission_name="2026-07-01-daily-cycle",
        outcome_md="Shipped signup fix.",
    )
    assert "## Executive summary" in md
    assert "## Site health" in md
    assert "## Code review" in md
    assert "Shipped signup fix" in md
