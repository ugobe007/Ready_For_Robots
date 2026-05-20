"""
Shared LLM client factory.

Priority order for configuration:
  1. INFERENCE_ENGINE_URL  — base URL of any OpenAI-compatible endpoint
                              (Ollama, vLLM, Together AI, LM Studio, Fireworks, etc.)
     INFERENCE_ENGINE_API_KEY — auth token for that endpoint (use "ollama" for local)
     INFERENCE_ENGINE_MODEL   — model name override (e.g. "llama3.2", "mistral")

  2. OPENAI_API_KEY / OPEN_API_KEY — falls back to the official OpenAI API

All callers should use `get_llm_client()` and `get_llm_model()` rather than
constructing their own OpenAI clients directly.
"""
from __future__ import annotations

import os
from typing import Optional


def get_llm_client(timeout: float = 20.0):
    """
    Return a configured OpenAI client pointing at either:
    - INFERENCE_ENGINE_URL  (any OpenAI-compatible endpoint), or
    - OpenAI API (default).

    Raises RuntimeError if no key / URL is configured.
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package not installed") from exc

    engine_url = (os.getenv("INFERENCE_ENGINE_URL") or "").strip()
    engine_key = (os.getenv("INFERENCE_ENGINE_API_KEY") or "").strip()

    if engine_url:
        # Self-hosted / alternative inference endpoint
        api_key = engine_key or "inference-engine"  # vLLM/Ollama ignore the key
        return OpenAI(api_key=api_key, base_url=engine_url, timeout=timeout)

    # Fall back to OpenAI
    openai_key = (os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY") or "").strip()
    if not openai_key:
        raise RuntimeError(
            "No LLM configured: set INFERENCE_ENGINE_URL + INFERENCE_ENGINE_API_KEY "
            "for a self-hosted model, or OPENAI_API_KEY for OpenAI."
        )
    return OpenAI(api_key=openai_key, timeout=timeout)


def get_llm_model(default: str = "gpt-4o-mini") -> str:
    """
    Return the model name to use.

    Checks (in order):
      1. INFERENCE_ENGINE_MODEL — explicit model override
      2. The caller-supplied default (e.g. "gpt-4o-mini", "gpt-4o")
    """
    return (os.getenv("INFERENCE_ENGINE_MODEL") or default).strip()


def is_inference_engine_configured() -> bool:
    """True when a self-hosted inference engine is active (not OpenAI)."""
    return bool((os.getenv("INFERENCE_ENGINE_URL") or "").strip())
