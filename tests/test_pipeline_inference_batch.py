"""Pipeline inference batch selection."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.pipeline_inference_batch import select_top_pipeline_company_ids


def test_select_top_pipeline_company_ids_orders_by_priority():
    rows = [
        SimpleNamespace(id=1, name="Low Intent Corp", signal_count=2, hot_hits=0, warm_hits=1, overall_score=40.0, employee_estimate=None, industry="Logistics"),
        SimpleNamespace(id=2, name="High Intent Corp", signal_count=3, hot_hits=1, warm_hits=0, overall_score=92.0, employee_estimate=500, industry="Logistics"),
    ]
    db = MagicMock()
    with patch("app.api.leads._lead_rows_query_limited") as q:
        q.return_value.all.return_value = rows
        ids = select_top_pipeline_company_ids(db, limit=5)
    assert ids[0] == 2
    assert 1 in ids
