"""company_validator.is_valid_lead — logic engine gates."""
import pytest

from app.services.company_validator import is_valid_lead

# Long enough to trigger ``needs_wikidata_verification`` (7+ words) but not
# the 10+ word junk regex; distinctive token (Acme) passes generic-word gate.
_LONG_HEADLINE_LIKE = "Acme Very Long Synthetic Phrase About Robotics"


@pytest.mark.parametrize(
    "name",
    [
        "EVERSANA Strengthens Position",
        "Acme Strengthens Presence in EMEA",
        "GlobalCo Strengthens Leadership Team",
    ],
)
def test_pr_strengthens_headlines_rejected(name):
    ok, reason = is_valid_lead(name)
    assert ok is False
    assert "structural" in reason.lower() or "junk" in reason.lower()


@pytest.mark.parametrize(
    "name",
    [
        "Eversana",
        "EVERSANA",
        "EquipmentShare Inc",
    ],
)
def test_strengthens_pattern_does_not_reject_legitimate_names(name):
    ok, _ = is_valid_lead(name)
    assert ok is True


def test_equipment_alone_rejected_via_junk_filter():
    ok, reason = is_valid_lead("Equipment")
    assert ok is False
    assert "junk" in reason.lower()


def test_placeholder_name_rejected():
    ok, reason = is_valid_lead("NAME")
    assert ok is False
    assert "placeholder" in reason.lower()


def test_wikidata_gate_rejects_when_likely_not_org(monkeypatch):
    monkeypatch.setenv("COMPANY_NAME_WIKIDATA_VERIFY", "1")

    def _fake_lk(name: str, *, timeout: float = 2.5):
        assert name == _LONG_HEADLINE_LIKE
        return "likely_not_org"

    monkeypatch.setattr(
        "app.services.company_validator.wikidata_entity_likelihood",
        _fake_lk,
    )
    ok, reason = is_valid_lead(_LONG_HEADLINE_LIKE)
    assert ok is False
    assert "wikidata" in reason.lower() or "external check" in reason.lower()


def test_wikidata_gate_skipped_when_disabled(monkeypatch):
    monkeypatch.delenv("COMPANY_NAME_WIKIDATA_VERIFY", raising=False)

    def _should_not_run(*args, **kwargs):
        raise AssertionError("Wikidata should not be called when verify is off")

    monkeypatch.setattr(
        "app.services.company_validator.wikidata_entity_likelihood",
        _should_not_run,
    )
    ok, _ = is_valid_lead(_LONG_HEADLINE_LIKE)
    assert ok is True


def test_wikidata_gate_allows_unknown(monkeypatch):
    monkeypatch.setenv("COMPANY_NAME_WIKIDATA_VERIFY", "1")

    monkeypatch.setattr(
        "app.services.company_validator.wikidata_entity_likelihood",
        lambda n, timeout=2.5: "unknown",
    )
    ok, _ = is_valid_lead(_LONG_HEADLINE_LIKE)
    assert ok is True


def test_dns_https_strict_rejects_when_unreachable(monkeypatch):
    monkeypatch.setenv("COMPANY_NAME_DNS_HTTPS_VERIFY", "1")
    monkeypatch.setenv("COMPANY_NAME_DNS_HTTPS_STRICT", "1")
    monkeypatch.setattr(
        "app.services.company_validator.dns_https_probe",
        lambda n, **kw: "unreachable",
    )
    ok, reason = is_valid_lead(_LONG_HEADLINE_LIKE)
    assert ok is False
    assert "footprint" in reason.lower() or "dns" in reason.lower()


def test_dns_https_probe_not_run_when_disabled(monkeypatch):
    monkeypatch.delenv("COMPANY_NAME_DNS_HTTPS_VERIFY", raising=False)

    def _no(*a, **k):
        raise AssertionError("dns_https_probe should not run when verify is off")

    monkeypatch.setattr("app.services.company_validator.dns_https_probe", _no)
    ok, _ = is_valid_lead(_LONG_HEADLINE_LIKE)
    assert ok is True


def test_dns_https_strict_allows_when_reachable(monkeypatch):
    monkeypatch.setenv("COMPANY_NAME_DNS_HTTPS_VERIFY", "1")
    monkeypatch.setenv("COMPANY_NAME_DNS_HTTPS_STRICT", "1")
    monkeypatch.setattr(
        "app.services.company_validator.dns_https_probe",
        lambda n, **kw: "reachable",
    )
    ok, _ = is_valid_lead(_LONG_HEADLINE_LIKE)
    assert ok is True
