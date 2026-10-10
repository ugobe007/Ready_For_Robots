from fastapi.testclient import TestClient

from app.main import app


def test_openai_apps_challenge_is_plain_token(monkeypatch):
    monkeypatch.setenv("OPENAI_APPS_CHALLENGE_TOKEN", "challenge-token-value")
    response = TestClient(app).get("/.well-known/openai-apps-challenge")
    assert response.status_code == 200
    assert response.text == "challenge-token-value"
    assert response.headers["content-type"].startswith("text/plain")


def test_openai_apps_challenge_missing_token_is_empty(monkeypatch):
    monkeypatch.delenv("OPENAI_APPS_CHALLENGE_TOKEN", raising=False)
    response = TestClient(app).get("/.well-known/openai-apps-challenge")
    assert response.status_code == 404
    assert response.text == ""
