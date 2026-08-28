"""International robot URLs: IDNA, compound ccTLDs, DNS-over-HTTPS fallback."""
from __future__ import annotations

import json

import pytest

from app.services.robot_url_safety import (
    UrlSafetyError,
    assert_public_http_url,
    canonical_robot_url,
    idna_hostname,
    normalize_product_url,
    registrable_domain,
)
from app.services.robot_understanding_v1.resolve import _root_domain


def test_registrable_domain_keeps_compound_cn_suffix():
    assert registrable_domain("en.engineai.com.cn") == "engineai.com.cn"
    assert registrable_domain("www.engineai.com.cn") == "engineai.com.cn"
    assert registrable_domain("engineai.com.cn") == "engineai.com.cn"


def test_registrable_domain_uk_and_jp():
    assert registrable_domain("shop.example.co.uk") == "example.co.uk"
    assert registrable_domain("docs.maker.co.jp") == "maker.co.jp"


def test_registrable_domain_plain_gtld():
    assert registrable_domain("www.agilityrobotics.com") == "agilityrobotics.com"


def test_root_domain_from_engineai_en_host():
    assert _root_domain("https://en.engineai.com.cn/") == "engineai.com.cn"


def test_idna_hostname_punycode():
    assert idna_hostname("münchen.example") == "xn--mnchen-3ya.example"
    assert idna_hostname("en.engineai.com.cn") == "en.engineai.com.cn"


def test_normalize_rewrites_unicode_host_to_punycode():
    out = normalize_product_url("https://münchen.example/robots")
    assert out is not None
    assert "xn--mnchen-3ya.example" in out
    assert "münchen" not in out


def test_example_unicode_host_skips_dns():
    url = assert_public_http_url("https://münchen.example/product")
    assert url.startswith("https://xn--mnchen-3ya.example")


def test_ssrf_still_rejects_loopback():
    with pytest.raises(UrlSafetyError):
        assert_public_http_url("http://127.0.0.1/robot")
    with pytest.raises(UrlSafetyError):
        assert_public_http_url("http://localhost/product")


def test_canonical_robot_url_strips_www_and_keeps_path():
    assert canonical_robot_url("https://www.Agtonomy.com/") == "https://agtonomy.com"
    assert canonical_robot_url("https://agtonomy.com/") == "https://agtonomy.com"
    assert canonical_robot_url("https://unitree.com/products/b2") != canonical_robot_url(
        "https://unitree.com/products/g1"
    )


def test_doh_fallback_when_system_dns_fails(monkeypatch):
    monkeypatch.setattr(
        "app.services.robot_url_safety._system_resolve_ips",
        lambda host: [],
    )
    monkeypatch.setattr(
        "app.services.robot_url_safety._doh_resolve_ips",
        lambda host: ["43.152.43.121"],
    )
    url = assert_public_http_url("https://en.engineai.com.cn/")
    assert url.startswith("https://en.engineai.com.cn")


def test_doh_parses_cloudflare_a_records(monkeypatch):
    body = json.dumps(
        {
            "Answer": [
                {"type": 5, "data": "en.engineai.com.cn.cdn.dnsv1.com."},
                {"type": 1, "data": "43.152.43.121"},
                {"type": 1, "data": "43.152.22.80"},
            ]
        }
    )

    class _Resp:
        def read(self):
            return body.encode()

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(
        "app.services.robot_url_safety.urllib.request.urlopen",
        lambda *a, **k: _Resp(),
    )
    from app.services.robot_url_safety import _doh_resolve_ips

    assert _doh_resolve_ips("en.engineai.com.cn") == ["43.152.43.121", "43.152.22.80"]


def test_doh_does_not_override_ssrf(monkeypatch):
    monkeypatch.setattr(
        "app.services.robot_url_safety._system_resolve_ips",
        lambda host: [],
    )
    monkeypatch.setattr(
        "app.services.robot_url_safety._doh_resolve_ips",
        lambda host: ["127.0.0.1"],
    )
    with pytest.raises(UrlSafetyError, match="Private|Non-public"):
        assert_public_http_url("https://evil.engineai.com.cn/")


def test_unresolvable_host_still_errors(monkeypatch):
    monkeypatch.setattr(
        "app.services.robot_url_safety._system_resolve_ips",
        lambda host: [],
    )
    monkeypatch.setattr(
        "app.services.robot_url_safety._doh_resolve_ips",
        lambda host: [],
    )
    with pytest.raises(UrlSafetyError, match="Could not resolve"):
        assert_public_http_url("https://no-such-host.engineai.com.cn/")
