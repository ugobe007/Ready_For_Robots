import pytest

from app.services.apollo_client import (
    ApolloConfigError,
    ApolloProspectClient,
    recommended_prospect_titles,
)


class _Response:
    status_code = 200
    content = b"{}"

    def __init__(self, data):
        self._data = data
        self.text = str(data)

    def json(self):
        return self._data


def test_apollo_client_requires_api_key(monkeypatch):
    monkeypatch.delenv("APOLLO_API_KEY", raising=False)
    monkeypatch.delenv("Apollo_API_Key", raising=False)

    with pytest.raises(ApolloConfigError):
        ApolloProspectClient()


def test_apollo_client_accepts_existing_fly_secret_casing(monkeypatch):
    monkeypatch.delenv("APOLLO_API_KEY", raising=False)
    monkeypatch.setenv("Apollo_API_Key", "mixed-case-key")

    client = ApolloProspectClient()

    assert client.api_key == "mixed-case-key"


def test_recommended_titles_reflect_industry_and_stage():
    titles = recommended_prospect_titles("Logistics", "technical_specs_request")

    assert "Director of Engineering" in titles
    assert "VP Supply Chain" in titles


def test_search_people_sends_apollo_header_and_filters(monkeypatch):
    captured = {}

    def fake_post(url, headers, params, timeout):
        captured.update({"url": url, "headers": headers, "params": params, "timeout": timeout})
        return _Response(
            {
                "people": [
                    {
                        "id": "p1",
                        "first_name": "Jane",
                        "last_name": "Smith",
                        "title": "VP Operations",
                        "linkedin_url": "https://linkedin.com/in/jane-smith",
                        "organization": {"name": "Acme", "primary_domain": "acme.com"},
                    }
                ],
                "pagination": {"page": 1},
            }
        )

    monkeypatch.setattr("app.services.apollo_client.requests.post", fake_post)

    result = ApolloProspectClient(api_key="test-key").search_people(
        organization_name="Acme",
        organization_domain="https://www.acme.com/about",
        titles=["VP Operations"],
        per_page=3,
    )

    assert captured["headers"]["X-Api-Key"] == "test-key"
    assert ("q_organization_domains_list[]", "acme.com") in captured["params"]
    assert ("person_titles[]", "VP Operations") in captured["params"]
    assert ("per_page", 3) in captured["params"]
    assert result["prospects"][0]["name"] == "Jane Smith"
    assert result["prospects"][0]["organization_domain"] == "acme.com"


def test_search_people_uses_keywords_when_domain_missing(monkeypatch):
    captured = {}

    def fake_post(url, headers, params, timeout):
        captured.update({"url": url, "headers": headers, "params": params, "timeout": timeout})
        return _Response({"people": [], "pagination": {"page": 1}})

    monkeypatch.setattr("app.services.apollo_client.requests.post", fake_post)

    ApolloProspectClient(api_key="test-key").search_people(
        organization_name="IHG Hotels & Resorts",
        titles=["General Manager"],
    )

    assert ("q_keywords", "IHG Hotels & Resorts") in captured["params"]
    assert not any(key == "q_organization_domains_list[]" for key, _ in captured["params"])
