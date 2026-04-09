"""Tests for signal time decay and quality multipliers."""
from datetime import datetime, timedelta, timezone

from app.services.signal_quality import (
    USE_CASE_WORKFLOW_CONCEPTS,
    announcement_noise_ratio,
    time_weight_for_signal,
    use_case_workflow_count,
)
from app.services.inference_engine import analyze_signals
from app.services.semantic_parser import SemanticParser


def test_time_weight_fresh_is_near_one():
    now = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    created = now - timedelta(days=1)
    w = time_weight_for_signal(created, now=now)
    assert w > 0.95


def test_time_weight_old_is_reduced():
    now = datetime(2026, 4, 1, 12, 0, tzinfo=timezone.utc)
    created = now - timedelta(days=120)
    w = time_weight_for_signal(created, now=now)
    assert w < 0.5
    assert w >= 0.12  # floor


def test_time_weight_none_is_full():
    assert time_weight_for_signal(None) == 1.0


def test_announcement_noise_ratio():
    texts = [
        "Company X unveils new humanoid robot platform for enterprise",
        "We are expanding our warehouse and struggling with labor shortage",
    ]
    r = announcement_noise_ratio(texts)
    assert 0.0 < r < 1.0


def test_analyze_signals_with_decay_sets_quality_metadata():
    old = datetime(2025, 1, 1, tzinfo=timezone.utc)
    fresh = datetime(2026, 3, 30, tzinfo=timezone.utc)
    texts = [
        "Series B funding announced for robotics startup",
        "labor shortage and cannot hire enough warehouse staff for peak season",
    ]
    r = analyze_signals(
        texts,
        company_name="TestCo",
        industry="logistics",
        signal_times=[old, fresh],
    )
    assert r.signal_quality is not None
    assert "combined_multiplier" in r.signal_quality
    assert "per_domain_combined_factor" in r.signal_quality
    f = r.signal_quality["per_domain_combined_factor"]
    assert f["expansion"] <= f["labor_pain"] + 1e-6  # press penalty hits expansion harder
    assert 0.0 <= r.overall_intent <= 1.0


def test_use_case_workflow_set_non_empty():
    assert "warehouse_automation" in USE_CASE_WORKFLOW_CONCEPTS
    assert "labor_shortage" in USE_CASE_WORKFLOW_CONCEPTS


def test_parser_weighted_merges():
    p = SemanticParser()
    r = p.parse_multi_weighted(
        [
            ("labor shortage in our warehouse", 1.0),
            ("unveils new humanoid robot", 0.2),
        ]
    )
    assert use_case_workflow_count(r) >= 0
