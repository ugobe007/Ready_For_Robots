"""Paid LLM lookups stay off unless RFR_ALLOW_PAID_LLM=1."""
import os

from app.services.company_url_openai import openai_url_resolve_enabled
from app.services.llm_client import active_provider, llm_json_completion, paid_llm_allowed


def test_paid_llm_disallowed_by_default(monkeypatch):
    monkeypatch.delenv("RFR_ALLOW_PAID_LLM", raising=False)
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test")
    assert paid_llm_allowed() is False
    assert active_provider() is None
    assert llm_json_completion("sys", "user") is None


def test_paid_llm_opt_in(monkeypatch):
    monkeypatch.setenv("RFR_ALLOW_PAID_LLM", "1")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("LLM_PREFER_OPENAI", raising=False)
    assert paid_llm_allowed() is True
    assert active_provider() == "openai"


def test_openai_url_resolve_off_without_paid_flag(monkeypatch):
    monkeypatch.delenv("RFR_ALLOW_PAID_LLM", raising=False)
    monkeypatch.setenv("COMPANY_URL_OPENAI_RESOLVE", "1")
    assert openai_url_resolve_enabled() is False
    os.environ.pop("COMPANY_URL_OPENAI_RESOLVE", None)
