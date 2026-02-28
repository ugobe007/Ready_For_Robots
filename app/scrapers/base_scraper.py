import time
import random
import logging
from abc import ABC, abstractmethod
from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models.company import Company
from app.models.signal import Signal

logger = logging.getLogger(__name__)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 Safari/605.1.15",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/121.0.0.0 Safari/537.36",
]

class BaseScraper(ABC):
    def __init__(self, proxies=None, db: Session = None, headless=True):
        self.proxies = proxies or []
        self.db = db or SessionLocal()
        self.headless = headless
        self._watchdog = None   # injected by ScraperWatchdog when using guarded_run

    def _random_user_agent(self):
        return random.choice(USER_AGENTS)

    def _select_proxy(self):
        return random.choice(self.proxies) if self.proxies else None

    def _retry(self, fn, retries=3, backoff=2):
        for attempt in range(1, retries + 1):
            try:
                return fn()
            except Exception as e:
                logger.warning("Attempt %s failed: %s", attempt, e)
                if attempt == retries:
                    raise
                time.sleep(backoff ** attempt)

    @abstractmethod
    def parse(self, html: str, url: str):
        raise NotImplementedError

    def run(self, start_urls: list):
        """
        Standard run — uses the module-level watchdog automatically.
        For manual watchdog-free runs, call _run_bare() directly.
        """
        from app.scrapers.scraper_watchdog import get_watchdog
        scraper_name = self.__class__.__name__
        watchdog = get_watchdog()
        watchdog.run_guarded(scraper_name, self, start_urls)

    def _run_bare(self, start_urls: list):
        """Original Playwright run without watchdog (used internally by watchdog itself)."""
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            context = browser.new_context(user_agent=self._random_user_agent())
            for url in start_urls:
                try:
                    def visit():
                        page = context.new_page()
                        page.goto(url, timeout=45000)
                        content = page.content()
                        page.close()
                        return content
                    html = self._retry(visit)
                    self.parse(html, url)
                except PWTimeout:
                    logger.error("Timeout visiting %s", url)
                except Exception as e:
                    logger.exception("Error scraping %s: %s", url, e)
            browser.close()

    def save_company(self, data: dict) -> Company:
        existing = self.db.query(Company).filter(Company.name == data.get("name")).first()
        if existing:
            return existing
        company = Company(**data)
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        return company

    def save_signal(self, company_id: int, signal_data: dict) -> Signal:
        signal = Signal(company_id=company_id, **signal_data)
        self.db.add(signal)
        self.db.commit()
        return signal