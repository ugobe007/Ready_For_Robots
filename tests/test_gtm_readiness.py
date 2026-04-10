"""Tests for GTM readiness (stage + why now)."""

from datetime import datetime, timezone, timedelta

from app.services.gtm_readiness import compute_gtm_readiness


class _Sig:
    def __init__(self, signal_type: str, strength: float = 1.0, created_at=None):
        self.signal_type = signal_type
        self.signal_strength = strength
        self.created_at = created_at or datetime.now(timezone.utc)


def test_deploying_when_deployment_signal():
    sigs = [_Sig("rfp_posted")]
    g = compute_gtm_readiness(sigs, "WARM", ["mid-market boost"])
    assert g["readiness_stage"] == "deploying"
    assert g["readiness_label"] == "Deploy / scale"
    assert any("RFP" in w or "procurement" in w for w in g["why_now"])


def test_evaluating_hot_without_deployment():
    sigs = [_Sig("capex"), _Sig("labor_shortage")]
    g = compute_gtm_readiness(sigs, "HOT", ["2 hot-type signals (capex, labor_shortage)"])
    assert g["readiness_stage"] == "evaluating"
    assert g["readiness_label"] == "Active evaluation"


def test_exploring_cold():
    sigs = [_Sig("news")]
    g = compute_gtm_readiness(sigs, "COLD", [])
    assert g["readiness_stage"] == "exploring"
    assert g["readiness_label"] == "Early / nurture"


def test_fresh_activity_appended():
    old = datetime.now(timezone.utc) - timedelta(days=3)
    sigs = [_Sig("news", created_at=old)]
    g = compute_gtm_readiness(sigs, "COLD", [])
    assert any("Recent signal" in w for w in g["why_now"])
