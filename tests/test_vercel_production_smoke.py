from unittest.mock import patch

from scripts.vercel_production_smoke import (
    STALE_JS,
    check_origin,
    extract_deploy_url,
    js_path_from_html,
    main,
    smoke_custom_domain,
)

FRESH_JS = "/assets/index-CoF0C_UB.js"
HTML = f'<script type="module" src="{FRESH_JS}"></script>'
STALE_HTML = f'<script type="module" src="{STALE_JS}"></script>'
JS_BODY = ("x" * 120_000 + "Find Jobs for your robot").encode()


def test_extract_deploy_url_from_cli_log():
    log = (
        "Inspect         https://vercel.com/team/ready-for-robots/abc\n"
        "Production      https://ready-for-robots-87igrkw5w-ugobe07-gmailcoms-projects.vercel.app\n"
        "Aliased         https://readyforrobots.com\n"
        "Deployed https://ready-for-robots-87igrkw5w-ugobe07-gmailcoms-projects.vercel.app\n"
    )
    assert (
        extract_deploy_url(log)
        == "https://ready-for-robots-87igrkw5w-ugobe07-gmailcoms-projects.vercel.app"
    )


def test_js_path_from_html():
    assert js_path_from_html(HTML) == FRESH_JS
    assert js_path_from_html("<html></html>") is None


def _pages(mapping: dict[str, tuple[int, bytes]]):
    def get(url: str) -> tuple[int, bytes]:
        for prefix, payload in mapping.items():
            if url.startswith(prefix):
                return payload
        return 404, b"not found"

    return get


def test_check_origin_accepts_fresh_jobs_bundle():
    origin = "https://readyforrobots.com"
    get = _pages(
        {
            f"{origin}/?n=": (200, HTML.encode()),
            f"{origin}{FRESH_JS}": (200, JS_BODY),
        }
    )
    result = check_origin(origin, get=get, nonce="1")
    assert result.ok
    assert result.js_path == FRESH_JS
    assert result.js_bytes > 100_000


def test_check_origin_rejects_stale_hash():
    origin = "https://readyforrobots.com"
    get = _pages({f"{origin}/?n=": (200, STALE_HTML.encode())})
    result = check_origin(origin, get=get, nonce="1")
    assert not result.ok
    assert "stale" in result.reason


def test_check_origin_404_is_not_ok():
    origin = "https://example.vercel.app"
    get = _pages({f"{origin}/?n=": (404, b"NOT_FOUND")})
    result = check_origin(origin, get=get, nonce="1")
    assert not result.ok
    assert result.status == 404


def test_check_origin_rejects_tiny_or_html_fallback():
    origin = "https://readyforrobots.com"
    get = _pages(
        {
            f"{origin}/?n=": (200, HTML.encode()),
            f"{origin}{FRESH_JS}": (200, b"<html>spa fallback</html>"),
        }
    )
    result = check_origin(origin, get=get, nonce="1")
    assert not result.ok
    assert "small" in result.reason


def test_smoke_ignores_deploy_url_404_when_domain_is_fresh():
    """Reproduce #105: curl -f of *.vercel.app 404 must not abort the domain poll."""
    deploy = "https://ready-for-robots-87igrkw5w-ugobe07-gmailcoms-projects.vercel.app"
    domain = "https://readyforrobots.com"
    sleeps: list[float] = []

    def get(url: str) -> tuple[int, bytes]:
        if url.startswith(deploy):
            return 404, b"NOT_FOUND"
        if url.startswith(f"{domain}/?n="):
            return 200, HTML.encode()
        if url.startswith(f"{domain}{FRESH_JS}"):
            return 200, JS_BODY
        return 500, b"unexpected"

    result = smoke_custom_domain(
        domain,
        attempts=3,
        sleep_s=5,
        get=get,
        sleeper=sleeps.append,
        nonce_factory=lambda: "n",
    )
    assert result.ok
    assert sleeps == []

    with patch("scripts.vercel_production_smoke.http_get", get):
        rc = main(["--domain", domain, "--deploy-url", deploy, "--attempts", "1", "--sleep", "0"])
    assert rc == 0


def test_smoke_retries_then_fails_if_domain_stays_stale():
    origin = "https://readyforrobots.com"
    sleeps: list[float] = []
    get = _pages({f"{origin}/?n=": (200, STALE_HTML.encode())})
    result = smoke_custom_domain(
        origin,
        attempts=3,
        sleep_s=5,
        get=get,
        sleeper=sleeps.append,
    )
    assert not result.ok
    assert sleeps == [5, 5]
    with patch("scripts.vercel_production_smoke.http_get", get):
        assert main(["--domain", origin, "--attempts", "1", "--sleep", "0"]) == 1
