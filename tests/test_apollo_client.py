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

    with pytest.raises(ApolloConfigError):
        ApolloProspectClient()


def test_recommended_titles_reflect_industry_and_stage():
    titles = recommended_prospect_titles("Logistics", "technical_specs_request")

    assert "Director of Engineering" in titles
    assert "VP Supply Chain" in titles


def test_search_people_sends_apollo_header_and_filters(monkeypatch):
    captured = {}

    def fake_post(url, headers, json, timeout):
        captured.update({"url": url, "headers": headers, "json": json, "timeout": timeout})
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
    assert captured["json"]["q_organization_domains"] == "acme.com"
    assert captured["json"]["organization_names"] == ["Acme"]
    assert captured["json"]["person_titles"] == ["VP Operations"]
    assert result["prospects"][0]["name"] == "Jane Smith"
    assert result["prospects"][0]["organization_domain"] == "acme.com"
