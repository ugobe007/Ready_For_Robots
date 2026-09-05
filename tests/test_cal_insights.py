import pytest

from app.services.cal_insights import pick_cal_insight


def test_pick_cal_insight_is_deterministic():
    a = pick_cal_insight(company_name="Acme Robotics", trade_show="CES 2026")
    b = pick_cal_insight(company_name="Acme Robotics", trade_show="CES 2026")
    assert a == b
    assert len(a) > 40


def test_pick_cal_insight_prefers_show_specific():
    insight = pick_cal_insight(company_name="TestCo", trade_show="Automate 2026")
    assert "Automate" in insight or "ProMat" in insight or "throughput" in insight.lower()


def test_pick_cal_insight_no_stagegate_branding():
    insight = pick_cal_insight(company_name="AnyCo", trade_show="CES")
    assert "StageGate" not in insight
    assert "onstage.bot" not in insight
