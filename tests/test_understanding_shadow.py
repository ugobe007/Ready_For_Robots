"""Understanding v1.0 observe-only shadow — fail-open write + review labels."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.services.understanding_shadow import (
    REVIEW_LABELS,
    observation_payload_from_profile,
    record_shadow_observation,
    validate_failure_themes,
    validate_review_label,
)


def test_review_label_enum_accepts_canonical():
    for label in ("GOOD", "INCOMPLETE", "WRONG", "UNVERIFIABLE"):
        assert validate_review_label(label) == label
        assert validate_review_label(label.lower()) == label


def test_review_label_enum_rejects_unknown():
    with pytest.raises(ValueError):
        validate_review_label("OK")
    with pytest.raises(ValueError):
        validate_review_label("")


def test_review_labels_constant_matches_docs():
    assert REVIEW_LABELS == ("GOOD", "INCOMPLETE", "WRONG", "UNVERIFIABLE")


def test_failure_themes_validate():
    assert validate_failure_themes(["pdf", "CN_OEM", "pdf"]) == ["pdf", "cn_oem"]
    with pytest.raises(ValueError):
        validate_failure_themes(["not_a_theme"])


@dataclass
class _FakeCompany:
    name: str = "Acme Robotics"
    primary_domain: str = "acme.example"
    aliases: list[str] = field(default_factory=list)
    id: str = "co_test"


@dataclass
class _FakeProduct:
    id: str = "prod_test"
    company_id: str = "co_test"
    name: str = "Widget"
    generation: Optional[str] = None
    display_class: Optional[str] = "amr"


@dataclass
class _FakeProfile:
    submitted_url: str = "https://acme.example/"
    company: Any = field(default_factory=_FakeCompany)
    products: list = field(default_factory=lambda: [_FakeProduct()])
    selected_product: Any = field(default_factory=_FakeProduct)
    sources: list = field(default_factory=list)
    facts: list = field(default_factory=list)
    profile_confidence: str = "B"
    source_grounding_rate: float = 1.0
    ungrounded_fact_ids: list = field(default_factory=list)
    notes: list = field(default_factory=lambda: ["degraded fetch note"])
    needs_product_choice: bool = False
    research_stages: list = field(default_factory=list)
    coverage_rate: float = 0.5
    coverage_level: str = "medium"
    source_quality_rate: float = 0.4
    source_quality_level: str = "low"
    research_morphology: Optional[str] = "default"
    built_at: str = "2026-08-17T00:00:00+00:00"

    def to_dict(self) -> dict[str, Any]:
        from dataclasses import asdict

        return {
            "submitted_url": self.submitted_url,
            "built_at": self.built_at,
            "profile_confidence": self.profile_confidence,
            "source_grounding_rate": self.source_grounding_rate,
            "coverage_rate": self.coverage_rate,
            "coverage_level": self.coverage_level,
            "source_quality_rate": self.source_quality_rate,
            "source_quality_level": self.source_quality_level,
            "research_morphology": self.research_morphology,
            "ungrounded_fact_ids": list(self.ungrounded_fact_ids),
            "notes": list(self.notes),
            "needs_product_choice": self.needs_product_choice,
            "research_stages": list(self.research_stages),
            "company": asdict(self.company),
            "products": [asdict(p) for p in self.products],
            "selected_product": asdict(self.selected_product) if self.selected_product else None,
            "sources": [],
            "facts": [],
        }


def test_observation_payload_from_profile_projects_fields():
    payload = observation_payload_from_profile(
        _FakeProfile(),  # type: ignore[arg-type]
        research_duration_ms=1234,
        correlation_id="corr-1",
    )
    assert payload["submitted_url"] == "https://acme.example/"
    assert payload["company_name"] == "Acme Robotics"
    assert payload["selected_product"] == "Widget"
    assert payload["profile_tier"] == "B"
    assert payload["research_duration_ms"] == 1234
    assert payload["correlation_id"] == "corr-1"
    assert "degraded fetch note" in payload["notes"]


def test_record_shadow_fail_open_on_commit_error():
    db = MagicMock()
    db.bind = MagicMock()
    monkey_inspect = MagicMock()
    monkey_inspect.has_table.return_value = True

    profile = _FakeProfile()
    db.commit.side_effect = RuntimeError("db down")

    import app.services.understanding_shadow as mod

    original = mod.inspect

    def _fake_inspect(_bind):
        return monkey_inspect

    mod.inspect = _fake_inspect  # type: ignore[assignment]
    try:
        result = record_shadow_observation(db, profile, research_duration_ms=10)  # type: ignore[arg-type]
        assert result is None
        db.rollback.assert_called()
    finally:
        mod.inspect = original  # type: ignore[assignment]


def test_robot_profile_api_succeeds_when_shadow_write_fails(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")

    from app.services.robot_understanding_v1.models import (
        RobotCompany,
        RobotProduct,
        RobotProfile,
    )

    fake = RobotProfile(
        submitted_url="https://example.com/",
        company=RobotCompany.create("Example", "example.com"),
        products=[RobotProduct.create("co", "Bot")],
        selected_product=RobotProduct.create("co", "Bot"),
        sources=[],
        facts=[],
        profile_confidence="C",
        source_grounding_rate=1.0,
        notes=["ok"],
    )

    def _build(*_a, **_k):
        return fake

    def _boom(*_a, **_k):
        raise RuntimeError("shadow unavailable")

    monkeypatch.setattr("app.api.robot_profile.build_robot_profile", _build)
    monkeypatch.setattr("app.api.robot_profile.record_shadow_observation", _boom)

    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/robot-profile",
        json={"url": "https://example.com/", "product": "Bot"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["submitted_url"] == "https://example.com/"
    assert body["profile_confidence"] == "C"
    assert body["company"]["name"] == "Example"


def test_admin_review_rejects_bad_label(monkeypatch):
    monkeypatch.setenv("ADMIN_KEY", "test-admin-secret")
    from app.main import app

    client = TestClient(app)

    # Force set_shadow_review path via monkeypatch to avoid DB
    def _raise_value(*_a, **_k):
        raise ValueError("Invalid review_label")

    monkeypatch.setattr(
        "app.api.admin_understanding_shadow.set_shadow_review",
        _raise_value,
    )
    r = client.post(
        "/api/admin/understanding-shadow/fake-id/review",
        headers={"X-Admin-Key": "test-admin-secret"},
        json={"review_label": "OK"},
    )
    assert r.status_code == 400
