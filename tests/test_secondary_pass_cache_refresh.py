"""Secondary pass cache refresh behavior."""
from unittest.mock import MagicMock, patch

from app.services.lead_secondary_pass import run_secondary_pass_batch_and_refresh_caches


def test_secondary_pass_rebuilds_pipeline_cache():
    with patch("app.services.lead_secondary_pass.run_secondary_pass_batch", return_value={"processed": 3}) as mock_batch, patch(
        "app.services.public_surface_cache.refresh_pipeline_surface_caches",
        return_value={"pipeline_feed_leads": 35},
    ) as mock_refresh, patch(
        "app.services.public_surface_cache.hydrate_public_surface_caches",
    ) as mock_hydrate, patch("app.database.SessionLocal") as mock_session:
        db = MagicMock()
        mock_session.return_value = db
        stats = run_secondary_pass_batch_and_refresh_caches(limit=10)

    mock_batch.assert_called_once()
    mock_refresh.assert_called_once()
    mock_hydrate.assert_called_once()
    db.commit.assert_called_once()
    assert stats["cache_refresh"] == "ok"
