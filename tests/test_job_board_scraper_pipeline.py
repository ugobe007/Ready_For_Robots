"""Job-board Robot Job pipeline — Fly worker loop + industry URL resolution."""
from unittest.mock import MagicMock, patch

from app.runtime_role import celery_disabled
from app.scrapers.job_board_scraper_enhanced import (
    EnhancedJobBoardScraper,
    calculate_job_relevancy_score,
)
from app.scrapers.scrape_targets import get_urls
from app.services.job_board_scraper_runner import (
    DEFAULT_INDUSTRY_ROTATION,
    job_board_urls,
    run_job_board_scraper_sync,
    scheduled_industries,
)


def test_job_board_urls_match_lowercase_beat_kwargs():
    assert len(get_urls("job_board", industry="hospitality")) >= 8
    assert len(get_urls("job_board", industry="Hospitality")) == len(
        get_urls("job_board", industry="hospitality")
    )
    assert len(get_urls("job_board", industry="logistics")) >= 8
    assert len(get_urls("job_board", industry="healthcare")) >= 8
    hospitality = set(get_urls("job_board", industry="hospitality"))
    assert set(job_board_urls(industry="hospitality")) <= hospitality


def test_job_board_urls_prefer_robot_job_targets():
    urls = job_board_urls(industry="Hospitality")
    assert "housekeeper" in urls[0]
    simplyhired = [u for u in urls if "simplyhired.com" in u and "housekeeper" in u]
    vp = [u for u in urls if "VP+Director+rooms" in u or "VP+Director+operations" in u]
    if simplyhired and vp:
        assert urls.index(simplyhired[0]) < urls.index(vp[0])


def test_food_service_urls_include_qsr_make_line_not_only_vp():
    urls = job_board_urls(industry="Food Service")
    blob = " ".join(urls).lower()
    assert "make+line" in blob or "make%20line" in blob or "qsr" in blob
    assert "bowl" in blob or "kitchen+automation" in blob or "prep+cook" in blob
    vp = [u for u in urls if "VP+Director" in u or "Chief+Operating+Officer" in u]
    operational = [
        u
        for u in urls
        if any(
            bit in u.lower()
            for bit in ("make+line", "qsr", "prep+cook", "kitchen+automation", "bowl")
        )
    ]
    assert operational, urls
    if vp:
        assert urls.index(operational[0]) < urls.index(vp[0])


def test_food_prep_serving_cleaning_urls_cover_venues_not_housekeeping():
    food = job_board_urls(industry="Food Service")
    hospitality = job_board_urls(industry="Hospitality")
    healthcare = job_board_urls(industry="Healthcare")
    food_blob = " ".join(food).lower()
    hosp_blob = " ".join(hospitality).lower()
    health_blob = " ".join(healthcare).lower()
    venue_kitchen = [
        u
        for u in food + hospitality
        if "kitchen" in u.lower()
        and any(v in u.lower() for v in ("hotel", "casino", "airport"))
    ]
    assert venue_kitchen, food_blob
    assert any("busser" in u.lower() for u in food + hospitality)
    assert any("janitor" in u.lower() for u in food + hospitality)
    assert any("data+center" in u.lower() or "data%20center" in u.lower() for u in hospitality)
    assert "housekeeper" in hosp_blob
    assert "housekeep" not in food_blob
    janitor_urls = [u for u in food + hospitality if "janitor" in u.lower()]
    assert janitor_urls
    assert all("housekeep" not in u.lower() for u in janitor_urls)
    assert "evs" in health_blob or "environmental" in health_blob or "patient" in health_blob


def test_scheduled_rotation_covers_core_verticals(monkeypatch):
    monkeypatch.delenv("JOB_BOARD_INDUSTRIES", raising=False)
    industries = scheduled_industries()
    assert industries == list(DEFAULT_INDUSTRY_ROTATION)
    for name in (
        "Hospitality",
        "Logistics",
        "Healthcare",
        "Food Service",
        "Agriculture",
        "Construction",
        "Mining",
        "Factory",
    ):
        assert name in industries
        assert job_board_urls(industry=name), name


def test_scheduled_cycle_continues_after_one_industry_fails(monkeypatch):
    monkeypatch.setenv("JOB_BOARD_INDUSTRIES", "Hospitality,Logistics")
    calls = []

    def fake_sync(*, industry=None, urls=None):
        calls.append(industry)
        if industry == "Hospitality":
            raise RuntimeError("indeed blocked")
        return {"status": "ok", "industry": industry, "urls": 3}

    monkeypatch.setattr(
        "app.services.job_board_scraper_runner.run_job_board_scraper_sync",
        fake_sync,
    )
    from app.services.job_board_scraper_runner import run_scheduled_job_board_cycle

    result = run_scheduled_job_board_cycle()
    assert calls == ["Hospitality", "Logistics"]
    assert result["failed"] == 1
    assert result["ok"] == 1
    assert result["status"] == "completed"


def test_empty_url_list_does_not_launch_playwright():
    with patch(
        "app.scrapers.job_board_scraper_enhanced.EnhancedJobBoardScraper.run"
    ) as run:
        result = run_job_board_scraper_sync(urls=[])
    run.assert_not_called()
    assert result["status"] == "skipped"
    assert result["reason"] == "no_urls"


def test_operational_titles_pass_relevancy_and_builders_fail():
    assert calculate_job_relevancy_score("Line Cook", "Immediate hire. Multiple openings.") >= 0.15
    assert calculate_job_relevancy_score(
        "Hotel Housekeeper / Room Attendant", "Hiring now."
    ) >= 0.15
    assert calculate_job_relevancy_score(
        "Warehouse Associate - Order Picker", "Night shift."
    ) >= 0.15
    assert calculate_job_relevancy_score(
        "Patient Transporter", "Hospital environmental services."
    ) >= 0.15
    assert calculate_job_relevancy_score("Cook", "Immediate hire.") >= 0.15
    assert calculate_job_relevancy_score("Server", "Multiple openings.") >= 0.15
    assert calculate_job_relevancy_score("Warehouse Worker", "Night shift.") >= 0.15
    assert calculate_job_relevancy_score("EVS Technician", "Hospital floors.") >= 0.15
    assert calculate_job_relevancy_score("Palletizer Operator", "Packaging line.") >= 0.15
    assert calculate_job_relevancy_score(
        "Robotics Engineer", "Build AMR firmware for our robot."
    ) == 0.0
    assert calculate_job_relevancy_score(
        "VP of Operations", "Distribution network."
    ) >= 0.15


def test_line_cook_parse_persists_robot_job_without_relevancy_patch():
    html = """
    <div class="job_seen_beacon">
      <h2>Line Cook</h2>
      <div class="companyName">Chipotle</div>
      <div class="companyLocation">Austin, TX</div>
      <div class="job-snippet">Prep cook. Immediate hire. Multiple openings. $18 an hour.</div>
    </div>
    """
    scraper = EnhancedJobBoardScraper()
    scraper.db = MagicMock()
    company = MagicMock()
    company.id = 7
    scraper.save_company = MagicMock(return_value=company)
    scraper.save_signal = MagicMock()
    with patch(
        "app.scrapers.job_board_scraper_enhanced.upsert_robot_job_from_extract",
        return_value=MagicMock(),
    ) as upsert:
        scraper.parse(html, "https://www.indeed.com/jobs?q=line+cook")
    scraper.save_signal.assert_called_once()
    assert scraper.save_signal.call_args[0][1]["signal_type"] == "robot_job"
    upsert.assert_called_once()


def test_simplyhired_card_is_parsed():
    html = """
    <div class="SerpJob-jobCard">
      <h3 class="jobposting-title">Hotel Housekeeper</h3>
      <span class="jobposting-company">Hilton</span>
      <p class="jobposting-snippet">Room attendant. Immediate hire. Multiple openings.</p>
    </div>
    """
    scraper = EnhancedJobBoardScraper()
    scraper.db = MagicMock()
    company = MagicMock()
    company.id = 9
    scraper.save_company = MagicMock(return_value=company)
    scraper.save_signal = MagicMock()
    with patch(
        "app.scrapers.job_board_scraper_enhanced.upsert_robot_job_from_extract",
        return_value=MagicMock(),
    ) as upsert:
        scraper.parse(
            html,
            "https://www.simplyhired.com/search?q=housekeeper+room+attendant+hotel",
        )
    scraper.save_signal.assert_called_once()
    assert scraper.save_signal.call_args[0][1]["signal_type"] == "robot_job"
    upsert.assert_called_once()


def test_rejected_company_does_not_abort_remaining_postings():
    html = """
    <div class="job_seen_beacon">
      <h2>Warehouse Associate - Order Picker</h2>
      <div class="companyName">Junk Headline</div>
      <div class="companyLocation">Memphis, TN</div>
      <div class="job-snippet">Night shift order picker. Immediate hire. Multiple openings.</div>
    </div>
    <div class="job_seen_beacon">
      <h2>Warehouse Associate - Order Picker</h2>
      <div class="companyName">Acme Fulfillment LLC</div>
      <div class="companyLocation">Memphis, TN</div>
      <div class="job-snippet">Night shift order picker. Immediate hire. Multiple openings. $18 an hour.</div>
    </div>
    """
    scraper = EnhancedJobBoardScraper()
    scraper.db = MagicMock()
    saved = []

    def save_company(data):
        if "Junk" in data["name"]:
            return None
        company = MagicMock()
        company.id = 42
        saved.append(data["name"])
        return company

    scraper.save_company = save_company
    scraper.save_signal = MagicMock()
    with patch(
        "app.scrapers.job_board_scraper_enhanced.upsert_robot_job_from_extract",
        return_value=MagicMock(),
    ) as upsert:
        scraper.parse(html, "https://www.indeed.com/jobs?q=warehouse+associate")
    assert saved == ["Acme Fulfillment LLC"]
    scraper.save_signal.assert_called_once()
    assert scraper.save_signal.call_args[0][0] == 42
    assert scraper.save_signal.call_args[0][1]["signal_type"] == "robot_job"
    # Rejected name still upserts a Robot Job with no company_id; valid name follows.
    assert upsert.call_count == 2


def test_job_board_scheduler_starts_beside_intelligence(monkeypatch):
    started = []

    class FakeThread:
        def __init__(self, target=None, daemon=None, name=None):
            self.target = target
            self.name = name

        def start(self):
            started.append(self.name)

    monkeypatch.setenv("SKIP_CELERY", "1")
    monkeypatch.setenv("FLY_APP_NAME", "ready-2-robot")
    monkeypatch.setenv("ENABLE_SCHEDULED_SCRAPER", "1")
    monkeypatch.setenv("ENABLE_SCHEDULED_JOB_BOARD", "1")
    monkeypatch.setattr("app.runtime_role.is_worker_process", lambda: True)
    monkeypatch.setattr("app.main.threading.Thread", FakeThread)
    from app.main import _start_scheduled_job_board, _start_scheduled_scraper

    _start_scheduled_scraper()
    _start_scheduled_job_board()
    assert "intelligence-scraper" in started
    assert "job-board-scraper" in started


def test_job_board_scheduler_skipped_on_web(monkeypatch):
    started = []

    class FakeThread:
        def __init__(self, target=None, daemon=None, name=None):
            self.name = name

        def start(self):
            started.append(self.name)

    monkeypatch.setenv("SKIP_CELERY", "1")
    monkeypatch.setenv("FLY_APP_NAME", "ready-2-robot")
    monkeypatch.setattr("app.runtime_role.is_worker_process", lambda: False)
    monkeypatch.setattr("app.main.threading.Thread", FakeThread)
    from app.main import _start_scheduled_job_board

    _start_scheduled_job_board()
    assert started == []


def test_job_board_kill_switch_leaves_intelligence(monkeypatch):
    started = []

    class FakeThread:
        def __init__(self, target=None, daemon=None, name=None):
            self.name = name

        def start(self):
            started.append(self.name)

    monkeypatch.setenv("SKIP_CELERY", "1")
    monkeypatch.setenv("FLY_APP_NAME", "ready-2-robot")
    monkeypatch.setenv("ENABLE_SCHEDULED_SCRAPER", "1")
    monkeypatch.setenv("ENABLE_SCHEDULED_JOB_BOARD", "0")
    monkeypatch.setattr("app.runtime_role.is_worker_process", lambda: True)
    monkeypatch.setattr("app.main.threading.Thread", FakeThread)
    from app.main import _start_scheduled_job_board, _start_scheduled_scraper

    _start_scheduled_scraper()
    _start_scheduled_job_board()
    assert "intelligence-scraper" in started
    assert "job-board-scraper" not in started


def test_run_job_boards_uses_in_process_when_celery_skipped(monkeypatch):
    monkeypatch.setenv("SKIP_CELERY", "1")
    assert celery_disabled() is True
    called = {}

    def fake_sync(*args, **kwargs):
        called["ran"] = True

    monkeypatch.setattr(
        "app.api.scraper_control._run_job_board_scraper_sync", fake_sync
    )
    from fastapi.testclient import TestClient

    from app.main import app

    with TestClient(app) as client:
        res = client.post("/api/scraper/run/job_boards")
    assert res.status_code == 200, res.text
    body = res.json()
    assert body["mode"] == "in_process"
    assert body["scraper_type"] == "job_boards"
    assert called.get("ran") is True


def _parse_with_upsert(html: str, url: str):
    scraper = EnhancedJobBoardScraper()
    scraper.db = MagicMock()
    company = MagicMock()
    company.id = 7
    scraper.save_company = MagicMock(return_value=company)
    scraper.save_signal = MagicMock()
    upsert = MagicMock(return_value=MagicMock())
    with patch(
        "app.scrapers.job_board_scraper_enhanced.upsert_robot_job_from_extract",
        upsert,
    ):
        scraper.parse(html, url)
    return scraper, upsert


def test_short_operational_titles_persist_as_robot_jobs():
    html = """
    <div class="job_seen_beacon">
      <h2>Cook</h2>
      <div class="companyName">Local Diner</div>
      <div class="companyLocation">Austin, TX</div>
      <div class="job-snippet">Immediate hire. Multiple openings.</div>
    </div>
    """
    scraper, upsert = _parse_with_upsert(html, "https://www.indeed.com/jobs?q=line+cook")
    scraper.save_signal.assert_called_once()
    assert scraper.save_signal.call_args[0][1]["signal_type"] == "robot_job"
    upsert.assert_called_once()


def test_palletizer_does_not_die_on_second_pain_gate():
    html = """
    <div class="job_seen_beacon">
      <h2>Palletizer Operator</h2>
      <div class="companyName">Acme Foods</div>
      <div class="companyLocation">Memphis, TN</div>
      <div class="job-snippet">Packaging line. Immediate hire.</div>
    </div>
    """
    scraper, upsert = _parse_with_upsert(
        html, "https://www.indeed.com/jobs?q=palletizer+operator"
    )
    scraper.save_signal.assert_called_once()
    assert scraper.save_signal.call_args[0][1]["signal_type"] == "robot_job"
    upsert.assert_called_once()


def test_jsonld_jobposting_persists_without_css_cards():
    html = """
    <script type="application/ld+json">
    {
      "@type": "JobPosting",
      "title": "Warehouse Worker",
      "description": "Night shift picker. Immediate hire.",
      "hiringOrganization": {"@type": "Organization", "name": "GXO Logistics"},
      "jobLocation": {
        "@type": "Place",
        "address": {"addressLocality": "Allentown", "addressRegion": "PA"}
      }
    }
    </script>
    """
    scraper, upsert = _parse_with_upsert(
        html, "https://www.indeed.com/jobs?q=warehouse+associate"
    )
    scraper.save_signal.assert_called_once()
    assert scraper.save_signal.call_args[0][1]["signal_type"] == "robot_job"
    upsert.assert_called_once()
    extract = upsert.call_args.kwargs["extract"]
    assert extract["employer"] == "GXO Logistics"
    assert extract["employer_email"] is None


def test_jsonld_email_is_passed_to_persist():
    html = """
    <script type="application/ld+json">
    {
      "@type": "JobPosting",
      "title": "Patient Transporter",
      "description": "Hospital unit delivery. Immediate hire.",
      "hiringOrganization": {
        "@type": "Organization",
        "name": "Named Hospital",
        "email": "ops@named-hospital.org",
        "url": "https://named-hospital.org"
      },
      "jobLocation": {
        "@type": "Place",
        "address": {"addressLocality": "Portland", "addressRegion": "OR"}
      }
    }
    </script>
    """
    scraper, upsert = _parse_with_upsert(
        html, "https://www.indeed.com/jobs?q=patient+transporter"
    )
    scraper.save_signal.assert_called_once()
    upsert.assert_called_once()
    extract = upsert.call_args.kwargs["extract"]
    assert extract["employer"] == "Named Hospital"
    assert extract["employer_email"] == "ops@named-hospital.org"
    assert extract["contact_url"] == "https://named-hospital.org"


def test_jsonld_indeed_mailbox_is_not_passed_to_persist():
    html = """
    <script type="application/ld+json">
    {
      "@type": "JobPosting",
      "title": "Warehouse Worker",
      "description": "Night shift picker. Immediate hire.",
      "hiringOrganization": {
        "@type": "Organization",
        "name": "GXO Logistics",
        "email": "jobs@indeed.com"
      },
      "email": "noreply@indeed.com",
      "jobLocation": {
        "@type": "Place",
        "address": {"addressLocality": "Allentown", "addressRegion": "PA"}
      }
    }
    </script>
    """
    scraper, upsert = _parse_with_upsert(
        html, "https://www.indeed.com/jobs?q=warehouse+associate"
    )
    upsert.assert_called_once()
    extract = upsert.call_args.kwargs["extract"]
    assert extract["employer"] == "GXO Logistics"
    assert extract["employer_email"] is None


def test_indeed_testid_company_is_parsed():
    html = """
    <div class="job_seen_beacon">
      <h2 class="jobTitle"><a class="jcs-JobTitle"><span title="Server">Server</span></a></h2>
      <span data-testid="company-name">Hilton</span>
      <div data-testid="text-location">Dallas, TX</div>
      <div data-testid="job-snippet">Food runner. Multiple openings.</div>
    </div>
    """
    scraper, upsert = _parse_with_upsert(
        html, "https://www.indeed.com/jobs?q=food+runner+busser+server"
    )
    scraper.save_signal.assert_called_once()
    assert scraper.save_signal.call_args[0][1]["signal_type"] == "robot_job"
    upsert.assert_called_once()


def test_job_board_name_is_not_persisted_as_employer():
    html = """
    <div class="job_seen_beacon">
      <h2>Warehouse Associate - Order Picker</h2>
      <div class="companyName">Indeed</div>
      <div class="companyLocation">Memphis, TN</div>
      <div class="job-snippet">Night shift order picker. Immediate hire.</div>
    </div>
    """
    scraper, upsert = _parse_with_upsert(
        html, "https://www.indeed.com/jobs?q=warehouse+associate"
    )
    upsert.assert_not_called()
    scraper.save_signal.assert_not_called()


def test_farm_harvest_title_persists_robot_job():
    html = """
    <div class="job_seen_beacon">
      <h2>Harvest Worker</h2>
      <div class="companyName">Sunrise Orchards</div>
      <div class="companyLocation">Yakima, WA</div>
      <div class="job-snippet">Farm laborer harvest worker. Immediate hire. Multiple openings.</div>
    </div>
    """
    scraper, upsert = _parse_with_upsert(
        html, "https://www.indeed.com/jobs?q=farm+worker+harvest+orchard"
    )
    scraper.save_signal.assert_called_once()
    assert scraper.save_signal.call_args[0][1]["signal_type"] == "robot_job"
    upsert.assert_called_once()
    extract = upsert.call_args.kwargs["extract"]
    assert extract["employer"] == "Sunrise Orchards"
    assert extract["job_function"] == "harvest"


def test_generic_gm_is_not_a_robot_job():
    html = """
    <div class="job_seen_beacon">
      <h2>General Manager</h2>
      <div class="companyName">Acme Holdings LLC</div>
      <div class="companyLocation">Austin, TX</div>
      <div class="job-snippet">Lead the business unit.</div>
    </div>
    """
    scraper, upsert = _parse_with_upsert(
        html, "https://www.indeed.com/jobs?q=General+Manager"
    )
    upsert.assert_not_called()
    scraper.save_signal.assert_not_called()
