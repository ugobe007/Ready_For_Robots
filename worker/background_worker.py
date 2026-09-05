"""
Dedicated Fly worker entrypoint — no HTTP server.

Runs cache refresh loops, social post generation, and scheduled maintenance
that previously shared the web machine's CPU.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)


def main() -> None:
    # Import registers ORM + DB events (same as uvicorn worker would).
    import app.models  # noqa: F401
    from app.db_events import register_db_events
    from app.main import _configure_logging, _run_worker_startup

    register_db_events()
    _configure_logging()
    logger.info("Background worker starting (RFR_PROCESS_ROLE=worker)")
    _run_worker_startup()
    while True:
        time.sleep(3600)


if __name__ == "__main__":
    main()
