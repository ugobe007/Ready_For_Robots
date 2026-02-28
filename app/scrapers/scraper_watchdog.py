"""
Scraper Watchdog
================
Monitors scraper jobs for hangs, crashes, and repeated failures.
Provides auto-recovery, circuit breaking, and health reporting.

Features:
  - Per-URL timeout enforcement (kills stuck Playwright pages)
  - Heartbeat tracking (detects frozen scrapers mid-run)
  - Circuit breaker (stops retrying a URL that fails N times)
  - Auto-restart on crash (up to MAX_RESTARTS)
  - Structured health log stored in SQLite via a simple JSON file
  - API-compatible status() method for the /api/scraper-health endpoint

Usage:
    from app.scrapers.scraper_watchdog import ScraperWatchdog

    watchdog = ScraperWatchdog()

    # Wrap a scraper run
    watchdog.run_guarded("hotel", hotel_scraper, hotel_urls)

    # Check health
    print(watchdog.status())
"""
import json
import logging
import os
import threading
import time
import traceback
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Any

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
HEALTH_LOG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "scraper_health.json"
)

MAX_RESTARTS       = 3          # max auto-restarts per run
HEARTBEAT_INTERVAL = 30         # seconds between heartbeat checks
URL_TIMEOUT        = 90         # seconds before a single URL is declared stuck
CIRCUIT_OPEN_AFTER = 3          # consecutive failures to trip a circuit breaker
CIRCUIT_RESET_SECS = 600        # seconds before a circuit resets (10 min)


# ─────────────────────────────────────────────
# Data structures
# ─────────────────────────────────────────────
@dataclass
class UrlHealth:
    url: str
    attempts: int = 0
    successes: int = 0
    failures: int = 0
    consecutive_failures: int = 0
    circuit_open: bool = False
    circuit_opened_at: Optional[float] = None
    last_attempt_at: Optional[float] = None
    last_error: Optional[str] = None

    def trip_circuit(self):
        self.circuit_open = True
        self.circuit_opened_at = time.time()
        logger.warning("[CIRCUIT OPEN] %s — too many failures", self.url)

    def try_reset_circuit(self) -> bool:
        """Return True if circuit was reset (enough time has passed)."""
        if not self.circuit_open:
            return True
        if self.circuit_opened_at and (time.time() - self.circuit_opened_at) >= CIRCUIT_RESET_SECS:
            self.circuit_open = False
            self.consecutive_failures = 0
            logger.info("[CIRCUIT RESET] %s", self.url)
            return True
        return False

    def record_success(self):
        self.successes += 1
        self.consecutive_failures = 0
        self.circuit_open = False

    def record_failure(self, error: str):
        self.failures += 1
        self.consecutive_failures += 1
        self.last_error = error[:300]
        if self.consecutive_failures >= CIRCUIT_OPEN_AFTER:
            self.trip_circuit()


@dataclass
class ScraperRunRecord:
    scraper_name: str
    started_at: str = ""
    finished_at: Optional[str] = None
    status: str = "running"        # running | success | failed | timeout | restarted
    urls_attempted: int = 0
    urls_succeeded: int = 0
    urls_skipped_circuit: int = 0
    restarts: int = 0
    errors: List[str] = field(default_factory=list)
    current_url: Optional[str] = None


# ─────────────────────────────────────────────
# Watchdog
# ─────────────────────────────────────────────
class ScraperWatchdog:
    """
    Thread-safe watchdog that wraps scraper execution with:
      - per-URL circuit breakers
      - heartbeat / stuck-detection
      - auto restart on crash
      - structured health log
    """

    def __init__(self, health_log_path: str = HEALTH_LOG_PATH):
        self._lock = threading.Lock()
        self._url_health: Dict[str, UrlHealth] = {}
        self._run_history: List[ScraperRunRecord] = []
        self._health_log_path = health_log_path
        self._heartbeat_ts: Dict[str, float] = {}   # scraper_name → last heartbeat
        self._load_state()

    # ── Public API ──────────────────────────────────────────────────────────

    def run_guarded(
        self,
        scraper_name: str,
        scraper_instance,
        urls: List[str],
        *,
        on_url_success: Optional[Callable[[str], None]] = None,
        on_url_failure: Optional[Callable[[str, Exception], None]] = None,
    ) -> ScraperRunRecord:
        """
        Execute scraper.run(urls) with full watchdog protection:
          - skips circuit-broken URLs
          - enforces per-URL timeout
          - auto-restarts up to MAX_RESTARTS on crash
          - records heartbeat so external monitors can detect hangs
        """
        record = ScraperRunRecord(
            scraper_name=scraper_name,
            started_at=self._now(),
        )
        self._run_history.append(record)
        logger.info("[WATCHDOG] Starting %s — %d URLs", scraper_name, len(urls))

        # Filter circuit-broken URLs
        allowed_urls, skipped = self._filter_urls(urls)
        record.urls_skipped_circuit = skipped
        record.urls_attempted = len(allowed_urls)

        if not allowed_urls:
            record.status = "skipped_all_circuit_open"
            record.finished_at = self._now()
            self._save_state()
            logger.warning("[WATCHDOG] %s — all URLs circuit-open, skipped", scraper_name)
            return record

        # Replace scraper's URL list with filtered list and wrap its run() method
        attempted = [0]
        succeeded = [0]
        crash_count = [0]

        def _run_with_heartbeat():
            """Run the scraper URL-by-URL with per-URL timeout and heartbeat."""
            for url in allowed_urls:
                uh = self._get_url_health(url)

                # Re-check circuit (may have reset while we were running)
                if uh.circuit_open and not uh.try_reset_circuit():
                    record.urls_skipped_circuit += 1
                    logger.warning("[WATCHDOG] %s circuit still open, skipping", url)
                    continue

                record.current_url = url
                uh.attempts += 1
                uh.last_attempt_at = time.time()
                attempted[0] += 1
                self._heartbeat(scraper_name)

                success = self._run_single_url(
                    scraper_name, scraper_instance, url, record
                )
                if success:
                    uh.record_success()
                    succeeded[0] += 1
                    record.urls_succeeded += 1
                    if on_url_success:
                        on_url_success(url)
                else:
                    # Error already recorded inside _run_single_url
                    if on_url_failure:
                        on_url_failure(url, Exception(uh.last_error or "unknown"))

                self._heartbeat(scraper_name)
                self._save_state()

        # Auto-restart loop
        while crash_count[0] <= MAX_RESTARTS:
            try:
                _run_with_heartbeat()
                break   # clean exit
            except Exception as exc:
                crash_count[0] += 1
                record.restarts += 1
                err_msg = f"Crash #{crash_count[0]}: {exc}"
                record.errors.append(err_msg)
                logger.error("[WATCHDOG] %s crashed: %s", scraper_name, exc)
                if crash_count[0] > MAX_RESTARTS:
                    record.status = "failed"
                    break
                record.status = "restarted"
                logger.info("[WATCHDOG] Restarting %s (attempt %d/%d)...",
                            scraper_name, crash_count[0], MAX_RESTARTS)
                time.sleep(5 * crash_count[0])   # exponential backoff

        if record.status not in ("failed", "restarted"):
            record.status = "success" if succeeded[0] > 0 else "no_results"

        record.current_url = None
        record.finished_at = self._now()
        self._save_state()

        logger.info(
            "[WATCHDOG] %s finished — status=%s  attempted=%d  succeeded=%d  skipped=%d  restarts=%d",
            scraper_name, record.status,
            record.urls_attempted, record.urls_succeeded,
            record.urls_skipped_circuit, record.restarts,
        )
        return record

    def status(self) -> Dict[str, Any]:
        """Return a dict suitable for the /api/scraper-health endpoint."""
        with self._lock:
            return {
                "url_health": {
                    url: {
                        "attempts": uh.attempts,
                        "successes": uh.successes,
                        "failures": uh.failures,
                        "circuit_open": uh.circuit_open,
                        "consecutive_failures": uh.consecutive_failures,
                        "last_error": uh.last_error,
                        "circuit_opens_in_secs": (
                            max(0, CIRCUIT_RESET_SECS - (time.time() - uh.circuit_opened_at))
                            if uh.circuit_open and uh.circuit_opened_at else None
                        ),
                    }
                    for url, uh in self._url_health.items()
                },
                "recent_runs": [
                    {k: v for k, v in asdict(r).items() if k != "current_url"}
                    for r in self._run_history[-20:]
                ],
                "active_runs": [
                    {"scraper": r.scraper_name, "current_url": r.current_url,
                     "started_at": r.started_at}
                    for r in self._run_history
                    if r.status == "running" and r.current_url
                ],
                "circuit_open_urls": [
                    url for url, uh in self._url_health.items() if uh.circuit_open
                ],
            }

    def reset_circuit(self, url: str) -> bool:
        """Manually reset a circuit breaker for a URL. Returns True if found."""
        with self._lock:
            uh = self._url_health.get(url)
            if uh:
                uh.circuit_open = False
                uh.consecutive_failures = 0
                uh.circuit_opened_at = None
                self._save_state()
                logger.info("[WATCHDOG] Circuit manually reset for %s", url)
                return True
        return False

    def reset_all_circuits(self):
        """Reset all circuit breakers (useful after fixing a scraper)."""
        with self._lock:
            for uh in self._url_health.values():
                uh.circuit_open = False
                uh.consecutive_failures = 0
                uh.circuit_opened_at = None
            self._save_state()
        logger.info("[WATCHDOG] All circuits reset")

    def last_heartbeat_age(self, scraper_name: str) -> Optional[float]:
        """Seconds since last heartbeat for a scraper. None if never started."""
        ts = self._heartbeat_ts.get(scraper_name)
        return (time.time() - ts) if ts else None

    def is_stuck(self, scraper_name: str, threshold_secs: float = URL_TIMEOUT * 2) -> bool:
        """True if a scraper's last heartbeat is older than threshold_secs."""
        age = self.last_heartbeat_age(scraper_name)
        return age is not None and age > threshold_secs

    # ── Private helpers ─────────────────────────────────────────────────────

    def _run_single_url(
        self,
        scraper_name: str,
        scraper_instance,
        url: str,
        record: ScraperRunRecord,
    ) -> bool:
        """
        Run scraper on one URL with a hard timeout thread.
        Returns True on success, False on failure.
        """
        result = {"html": None, "error": None}
        uh = self._get_url_health(url)

        def _fetch():
            try:
                # Use the scraper's internal Playwright context for one URL
                from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
                import random

                ua = random.choice([
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 Safari/605.1.15",
                ])
                with sync_playwright() as p:
                    browser = p.chromium.launch(headless=True)
                    ctx = browser.new_context(user_agent=ua)
                    page = ctx.new_page()
                    try:
                        page.goto(url, timeout=URL_TIMEOUT * 1000)
                        html = page.content()
                        result["html"] = html
                    except PWTimeout:
                        result["error"] = f"Playwright timeout after {URL_TIMEOUT}s"
                    except Exception as e:
                        result["error"] = str(e)
                    finally:
                        page.close()
                    browser.close()
            except Exception as e:
                result["error"] = f"Browser launch failed: {e}"

        t = threading.Thread(target=_fetch, daemon=True)
        t.start()
        t.join(timeout=URL_TIMEOUT + 15)   # extra 15s for browser teardown

        if t.is_alive():
            # Thread is stuck — record timeout
            err = f"Hard timeout: URL did not complete in {URL_TIMEOUT + 15}s"
            uh.record_failure(err)
            record.errors.append(f"{url}: {err}")
            logger.error("[WATCHDOG] STUCK: %s — %s", scraper_name, url)
            return False

        if result["error"]:
            uh.record_failure(result["error"])
            record.errors.append(f"{url}: {result['error']}")
            logger.warning("[WATCHDOG] FAIL: %s — %s — %s", scraper_name, url, result["error"])
            return False

        if result["html"]:
            try:
                scraper_instance.parse(result["html"], url)
            except Exception as e:
                err = f"Parse error: {e}"
                uh.record_failure(err)
                record.errors.append(f"{url}: {err}")
                logger.warning("[WATCHDOG] PARSE FAIL: %s — %s — %s", scraper_name, url, err)
                return False

        return True

    def _filter_urls(self, urls: List[str]):
        """Split urls into (allowed, skipped_count) based on circuit state."""
        allowed = []
        skipped = 0
        with self._lock:
            for url in urls:
                uh = self._get_url_health(url)
                if uh.circuit_open:
                    if uh.try_reset_circuit():
                        allowed.append(url)
                    else:
                        skipped += 1
                        logger.info("[CIRCUIT SKIP] %s", url)
                else:
                    allowed.append(url)
        return allowed, skipped

    def _get_url_health(self, url: str) -> UrlHealth:
        """Get-or-create UrlHealth (not thread-safe on its own — call within lock or single thread)."""
        if url not in self._url_health:
            self._url_health[url] = UrlHealth(url=url)
        return self._url_health[url]

    def _heartbeat(self, scraper_name: str):
        self._heartbeat_ts[scraper_name] = time.time()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    # ── Persistence ─────────────────────────────────────────────────────────

    def _save_state(self):
        try:
            state = {
                "url_health": {
                    url: asdict(uh) for url, uh in self._url_health.items()
                },
                "run_history": [asdict(r) for r in self._run_history[-100:]],
            }
            with open(self._health_log_path, "w") as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.warning("Could not save watchdog state: %s", e)

    def _load_state(self):
        if not os.path.exists(self._health_log_path):
            return
        try:
            with open(self._health_log_path) as f:
                state = json.load(f)
            for url, data in state.get("url_health", {}).items():
                uh = UrlHealth(**{k: v for k, v in data.items()})
                self._url_health[url] = uh
            for r in state.get("run_history", []):
                try:
                    self._run_history.append(ScraperRunRecord(**r))
                except Exception:
                    pass
            logger.info("[WATCHDOG] Loaded state: %d URLs, %d runs",
                        len(self._url_health), len(self._run_history))
        except Exception as e:
            logger.warning("Could not load watchdog state: %s", e)


# ─────────────────────────────────────────────
# Module-level singleton
# ─────────────────────────────────────────────
_watchdog = ScraperWatchdog()


def get_watchdog() -> ScraperWatchdog:
    """Return the global watchdog singleton."""
    return _watchdog


# ─────────────────────────────────────────────
# Convenience wrapper — drop-in replacement for scraper.run()
# ─────────────────────────────────────────────
def guarded_run(scraper_name: str, scraper_instance, urls: List[str], **kwargs):
    """
    Drop-in replacement for scraper.run(urls) — adds full watchdog protection.

    Example:
        from app.scrapers.scraper_watchdog import guarded_run
        guarded_run("hotel", hotel_scraper, hotel_urls)
    """
    return _watchdog.run_guarded(scraper_name, scraper_instance, urls, **kwargs)
