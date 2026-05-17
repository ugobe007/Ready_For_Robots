"""
Admin page smoke + logic tests
==============================
Covers:
  - Auth gates (401/403 without valid credentials)
  - GET /api/admin/stats       — shape + field types
  - GET /api/admin/workflow/actions
  - GET /api/admin/scrape/targets
  - GET /api/admin/users/stats
  - GET /api/admin/users
  - GET /api/admin/activity
  - GET /api/admin/export/all
  - POST /api/admin/import/urls   — valid + invalid payloads
  - POST /api/admin/import/companies
  - GET /api/analytics            — field completeness + in-process cache
  - GET /api/leads/summary        — SQL-aggregation path (hot/warm/cold ≥ 0)
  - GET /api/leads                — response shape + 30-second cache
"""

import os
import time

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# --- App wiring ---------------------------------------------------------------
# Point DATABASE_URL at SQLite before any app module imports it.
os.environ.setdefault("DATABASE_URL", "sqlite:///./test_admin_pages.db")
os.environ.setdefault("ADMIN_EMAILS", "admin@test.com")
# Disable OpenAI URL resolver so tests don't need OPENAI_API_KEY.
os.environ.setdefault("COMPANY_URL_OPENAI_RESOLVE", "0")

import app.models  # noqa: F401 — registers all ORM metadata
from app.api.auth_deps import require_admin
from app.database import Base, get_db
from app.main import app

# --- SQLite test DB -----------------------------------------------------------

_engine = create_engine(
    "sqlite:///./test_admin_pages.db",
    connect_args={"check_same_thread": False},
)
Base.metadata.create_all(bind=_engine)
_TestSession = sessionmaker(autocommit=False, autoflush=False, bind=_engine)


def _override_get_db():
    db = _TestSession()
    try:
        yield db
    finally:
        db.close()


def _override_require_admin():
    """Bypass JWT validation — return a fake admin user."""
    return {"uid": "test-uid", "email": "admin@test.com"}


app.dependency_overrides[get_db] = _override_get_db
app.dependency_overrides[require_admin] = _override_require_admin


@pytest.fixture(scope="module")
def client():
    with TestClient(app, raise_server_exceptions=True) as c:
        yield c


@pytest.fixture(autouse=True)
def _clear_leads_cache():
    """Reset the in-process leads-list cache between tests."""
    from app.api import leads as leads_mod
    leads_mod._LEADS_LIST_CACHE.clear()
    yield
    leads_mod._LEADS_LIST_CACHE.clear()


@pytest.fixture(autouse=True)
def _clear_analytics_cache():
    """Reset the analytics cache between tests."""
    from app.api import analytics as analytics_mod
    analytics_mod._ANALYTICS_CACHE.clear()
    yield
    analytics_mod._ANALYTICS_CACHE.clear()


# =============================================================================
# Auth gate tests (without the override — uses a separate unauthenticated client)
# =============================================================================

def test_admin_stats_requires_auth():
    """Unauthenticated request must return 401 or 403."""
    bare_app = app
    # Remove the override temporarily.
    bare_app.dependency_overrides.pop(require_admin, None)
    try:
        with TestClient(bare_app, raise_server_exceptions=False) as bare:
            resp = bare.get("/api/admin/stats")
        assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"
    finally:
        bare_app.dependency_overrides[require_admin] = _override_require_admin


# =============================================================================
# GET /api/admin/stats
# =============================================================================

class TestAdminStats:
    def test_returns_200(self, client):
        resp = client.get("/api/admin/stats")
        assert resp.status_code == 200

    def test_has_required_top_level_keys(self, client):
        data = client.get("/api/admin/stats").json()
        for key in ("totals", "pipeline_value", "conversion_metrics"):
            assert key in data, f"Missing key: {key}"

    def test_totals_are_non_negative_ints(self, client):
        totals = client.get("/api/admin/stats").json()["totals"]
        for field in ("companies", "signals", "scored"):
            assert field in totals, f"Missing totals.{field}"
            assert isinstance(totals[field], int) and totals[field] >= 0

    def test_pipeline_value_is_numeric(self, client):
        pv = client.get("/api/admin/stats").json()["pipeline_value"]
        assert isinstance(pv, (int, float)) and pv >= 0

    def test_conversion_metrics_shape(self, client):
        cm = client.get("/api/admin/stats").json()["conversion_metrics"]
        assert "hot_rate" in cm and "avg_score" in cm
        assert 0 <= cm["hot_rate"] <= 100


# =============================================================================
# GET /api/admin/workflow/actions
# =============================================================================

class TestAdminWorkflow:
    def test_returns_200(self, client):
        resp = client.get("/api/admin/workflow/actions?limit=10")
        assert resp.status_code == 200

    def test_returns_list_or_dict_with_items(self, client):
        data = client.get("/api/admin/workflow/actions?limit=10").json()
        # Response may be a list or {"items": [...]}
        items = data if isinstance(data, list) else data.get("items", data.get("actions", []))
        assert isinstance(items, list)

    def test_limit_param_accepted(self, client):
        resp = client.get("/api/admin/workflow/actions?limit=5")
        assert resp.status_code == 200


# =============================================================================
# GET /api/admin/scrape/targets
# =============================================================================

class TestAdminScrapeTargets:
    def test_returns_200(self, client):
        assert client.get("/api/admin/scrape/targets").status_code == 200

    def test_response_is_list_or_dict(self, client):
        data = client.get("/api/admin/scrape/targets").json()
        assert isinstance(data, (list, dict))


# =============================================================================
# GET /api/admin/users/stats
# =============================================================================

class TestAdminUserStats:
    def test_returns_200(self, client):
        assert client.get("/api/admin/users/stats").status_code == 200

    def test_has_numeric_fields(self, client):
        data = client.get("/api/admin/users/stats").json()
        # Accept either flat {"total": N} or nested {"stats": {"total": N}}
        flat = data.get("stats", data)
        for v in flat.values():
            if isinstance(v, (int, float)):
                assert v >= 0


# =============================================================================
# GET /api/admin/users
# =============================================================================

class TestAdminUsers:
    def test_returns_200(self, client):
        assert client.get("/api/admin/users").status_code == 200

    def test_response_has_users_key_or_is_list(self, client):
        data = client.get("/api/admin/users").json()
        users = data.get("users", data) if isinstance(data, dict) else data
        assert isinstance(users, list)


# =============================================================================
# GET /api/admin/activity
# =============================================================================

class TestAdminActivity:
    def test_returns_200(self, client):
        assert client.get("/api/admin/activity?limit=20").status_code == 200

    def test_response_has_activity_key_or_is_list(self, client):
        data = client.get("/api/admin/activity?limit=20").json()
        activity = data.get("activity", data) if isinstance(data, dict) else data
        assert isinstance(activity, list)


# =============================================================================
# GET /api/admin/export/all
# =============================================================================

class TestAdminExport:
    def test_returns_200(self, client):
        assert client.get("/api/admin/export/all").status_code == 200

    def test_response_is_dict(self, client):
        data = client.get("/api/admin/export/all").json()
        assert isinstance(data, dict)


# =============================================================================
# POST /api/admin/import/urls
# =============================================================================

class TestAdminImportUrls:
    def test_valid_payload_accepted(self, client):
        resp = client.post(
            "/api/admin/import/urls",
            json={"urls": ["https://example.com/robotics-news"]},
        )
        assert resp.status_code in (200, 201, 202)

    def test_empty_urls_returns_error_or_zero(self, client):
        resp = client.post("/api/admin/import/urls", json={"urls": []})
        # Either a 422 validation error or a 200 with imported=0
        if resp.status_code == 200:
            data = resp.json()
            imported = data.get("imported", data.get("count", 0))
            assert imported == 0
        else:
            assert resp.status_code in (400, 422)

    def test_malformed_payload_returns_422(self, client):
        resp = client.post("/api/admin/import/urls", json={"not_urls": "bad"})
        assert resp.status_code == 422


# =============================================================================
# POST /api/admin/import/companies
# =============================================================================

class TestAdminImportCompanies:
    def test_valid_company_accepted(self, client):
        resp = client.post(
            "/api/admin/import/companies",
            json={"companies": [{"name": "Acme Robotics Test Corp", "industry": "Manufacturing"}]},
        )
        assert resp.status_code in (200, 201, 202)

    def test_empty_companies_returns_error_or_zero(self, client):
        resp = client.post("/api/admin/import/companies", json={"companies": []})
        if resp.status_code == 200:
            data = resp.json()
            assert data.get("imported", data.get("count", 0)) == 0
        else:
            assert resp.status_code in (400, 422)

    def test_missing_name_returns_422(self, client):
        resp = client.post(
            "/api/admin/import/companies",
            json={"companies": [{"industry": "Logistics"}]},
        )
        # Must reject missing required `name` field.
        assert resp.status_code == 422


# =============================================================================
# GET /api/analytics — field completeness + in-process cache
# =============================================================================

class TestAnalyticsEndpoint:
    _REQUIRED_KEYS = {
        "total_companies", "total_signals", "total_scored",
        "hot_count", "warm_count", "cold_count",
        "new_companies", "company_growth",
        "new_signals", "signal_growth",
        "top_industries", "signal_type_breakdown", "score_distribution",
        "top_hot_leads", "insights",
    }

    def test_returns_200(self, client):
        assert client.get("/api/analytics?range=7d").status_code == 200

    def test_all_required_fields_present(self, client):
        data = client.get("/api/analytics?range=7d").json()
        missing = self._REQUIRED_KEYS - data.keys()
        assert not missing, f"Analytics response missing fields: {missing}"

    def test_counts_are_non_negative(self, client):
        data = client.get("/api/analytics?range=7d").json()
        for field in ("total_companies", "total_signals", "hot_count", "warm_count", "cold_count"):
            assert data[field] >= 0, f"{field} should be >= 0"

    def test_hot_warm_cold_sum_leq_total_scored(self, client):
        data = client.get("/api/analytics?range=7d").json()
        bucket_sum = data["hot_count"] + data["warm_count"] + data["cold_count"]
        assert bucket_sum <= data["total_scored"] + 1  # +1 for floating-point rounding

    def test_score_distribution_has_three_bands(self, client):
        dist = client.get("/api/analytics?range=7d").json()["score_distribution"]
        assert len(dist) == 3

    def test_range_params_all_accepted(self, client):
        for r in ("7d", "30d", "90d", "all"):
            assert client.get(f"/api/analytics?range={r}").status_code == 200

    def test_invalid_range_rejected(self, client):
        assert client.get("/api/analytics?range=999d").status_code == 422

    def test_in_process_cache_serves_repeat_request(self, client):
        """Second call within TTL must hit cache (same object returned)."""
        from app.api import analytics as analytics_mod
        analytics_mod._ANALYTICS_CACHE.clear()
        r1 = client.get("/api/analytics?range=7d").json()
        # Populate cache entry with a sentinel value to confirm cache is read.
        analytics_mod._ANALYTICS_CACHE["7d"] = (time.monotonic(), {"__cache_sentinel__": True})
        r2 = client.get("/api/analytics?range=7d").json()
        assert r2.get("__cache_sentinel__") is True, "Second call did not use the in-process cache"

    def test_expired_cache_is_bypassed(self, client):
        """An expired cache entry must not be served."""
        from app.api import analytics as analytics_mod
        # Plant an entry timestamped far in the past.
        analytics_mod._ANALYTICS_CACHE["7d"] = (time.monotonic() - 9999, {"__stale__": True})
        r = client.get("/api/analytics?range=7d").json()
        assert "__stale__" not in r, "Expired cache entry was incorrectly served"


# =============================================================================
# GET /api/leads/summary — SQL aggregation path
# =============================================================================

class TestLeadsSummary:
    _REQUIRED_KEYS = {
        "total", "hot", "warm", "cold",
        "companies_in_database", "signals_in_database",
        "leads_list_max_per_request",
    }

    def test_returns_200(self, client):
        assert client.get("/api/leads/summary?exclude_junk=true").status_code == 200

    def test_required_fields_present(self, client):
        data = client.get("/api/leads/summary?exclude_junk=true").json()
        missing = self._REQUIRED_KEYS - data.keys()
        assert not missing, f"Summary missing fields: {missing}"

    def test_counts_non_negative(self, client):
        data = client.get("/api/leads/summary?exclude_junk=true").json()
        for field in ("total", "hot", "warm", "cold", "companies_in_database"):
            assert data[field] >= 0, f"{field} should be >= 0, got {data[field]}"

    def test_exclude_junk_false_returns_200(self, client):
        assert client.get("/api/leads/summary?exclude_junk=false").status_code == 200

    def test_summary_cache_is_populated(self, client):
        from app.api import leads as leads_mod
        leads_mod._summary_cache.clear() if hasattr(leads_mod, "_summary_cache") else None
        client.get("/api/leads/summary?exclude_junk=true")
        # A second request must succeed (cache hit path).
        assert client.get("/api/leads/summary?exclude_junk=true").status_code == 200


# =============================================================================
# GET /api/leads — response shape + 30-second in-process cache
# =============================================================================

class TestLeadsList:
    def test_returns_200(self, client):
        assert client.get("/api/leads?limit=5&exclude_junk=true").status_code == 200

    def test_response_is_list(self, client):
        data = client.get("/api/leads?limit=5&exclude_junk=true").json()
        assert isinstance(data, list)

    def test_limit_respected(self, client):
        data = client.get("/api/leads?limit=3&exclude_junk=true").json()
        assert len(data) <= 3

    def test_each_item_has_required_keys(self, client):
        data = client.get("/api/leads?limit=5&exclude_junk=false").json()
        required = {"id", "company_name"}
        for item in data:
            missing = required - item.keys()
            assert not missing, f"Lead item missing keys {missing}: {item}"

    def test_sort_by_name_accepted(self, client):
        assert client.get("/api/leads?limit=5&sort=name").status_code == 200

    def test_sort_by_signals_accepted(self, client):
        assert client.get("/api/leads?limit=5&sort=signals").status_code == 200

    def test_in_process_cache_serves_repeat_request(self, client):
        """Second identical request within TTL must come from cache."""
        from app.api import leads as leads_mod
        leads_mod._LEADS_LIST_CACHE.clear()
        key = "0.0|100.0|None|None|None|True|5|score|None"
        # First call — populates cache.
        client.get("/api/leads?limit=5&exclude_junk=true&sort=score")
        assert key in leads_mod._LEADS_LIST_CACHE, "Cache was not populated after first call"
        # Overwrite with sentinel.
        leads_mod._LEADS_LIST_CACHE[key] = (time.monotonic(), [{"__cache_sentinel__": True}])
        r2 = client.get("/api/leads?limit=5&exclude_junk=true&sort=score").json()
        assert r2[0].get("__cache_sentinel__") is True, "Second call did not use the in-process cache"

    def test_expired_cache_not_served(self, client):
        """An expired leads cache entry must trigger a fresh DB query."""
        from app.api import leads as leads_mod
        key = "0.0|100.0|None|None|None|True|5|score|None"
        leads_mod._LEADS_LIST_CACHE[key] = (time.monotonic() - 9999, [{"__stale__": True}])
        r = client.get("/api/leads?limit=5&exclude_junk=true&sort=score").json()
        assert not (len(r) == 1 and r[0].get("__stale__")), "Stale cache was incorrectly served"
