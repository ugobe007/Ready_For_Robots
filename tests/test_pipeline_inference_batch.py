"""Pipeline inference batch selection."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.pipeline_inference_batch import select_top_pipeline_company_ids


def test_select_top_pipeline_company_ids_delegates_to_pipeline_surface():
    db = MagicMock()
    with patch(
        "app.services.pipeline_inference_batch.select_pipeline_surface_company_ids",
        return_value=[2, 1],
    ) as mock_surface:
        ids = select_top_pipeline_company_ids(db, limit=5)
    mock_surface.assert_called_once_with(db, limit=5, slots_multiplier=2)
    assert ids == [2, 1]
