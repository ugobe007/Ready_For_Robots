"""
Shared LLM client factory.

Supports two providers — picked automatically from environment variables:

  ANTHROPIC_API_KEY   → uses Anthropic (Claude) via the anthropic package.
                         Set LLM_MODEL to override model (default: claude-3-5-haiku-20241022).

  OPENAI_API_KEY      → uses OpenAI.
  OPEN_API_KEY          Set LLM_MODEL to override model (default: gpt-4o-mini).

Anthropic is preferred when both keys are present (it's cheaper per token for
analytical tasks). Set LLM_PREFER_OPENAI=1 to reverse that preference.

Paid lookups are **off by default**. Set ``RFR_ALLOW_PAID_LLM=1`` to enable
OpenAI/Anthropic. Otherwise callers use the local inference / heuristic engine
(see industry_brief_service._heuristic_brief, lead_inference_engine).
"""
from __future__ import annotations

import os


# ── Provider selection ─────────────────────────────────────────────────────────

def _anthropic_key() -> str:
    return (os.getenv("ANTHROPIC_API_KEY") or "").strip()

def _openai_key() -> str:
    return (os.getenv("OPENAI_API_KEY") or os.getenv("OPEN_API_KEY") or "").strip()

def _prefer_openai() -> bool:
    return os.getenv("LLM_PREFER_OPENAI", "").strip().lower() in ("1", "true", "yes")


def paid_llm_allowed() -> bool:
    """Paid OpenAI/Anthropic lookups are off unless explicitly re-enabled.

    Hermes, industry briefs, and digest jobs must use the local inference engine.
    Set ``RFR_ALLOW_PAID_LLM=1`` only for a deliberate paid-LLM exception.
    """
    return os.getenv("RFR_ALLOW_PAID_LLM", "").strip().lower() in ("1", "true", "yes")


def active_provider() -> str | None:
    """Returns 'anthropic', 'openai', or None (use local heuristics)."""
    if not paid_llm_allowed():
        return None
    if _anthropic_key() and not _prefer_openai():
        return "anthropic"
    if _openai_key():
        return "openai"
    if _anthropic_key():
        return "anthropic"
    return None


# ── OpenAI-style client (for services that use the openai SDK directly) ───────

def _llm_max_retries(default: int = 1) -> int:
    """SDK auto-retries multiply wall-clock time (timeout × (1+retries) + backoff).
    Keep it low so bulk enrichment can't stall. Override with LLM_MAX_RETRIES."""
    try:
        return max(0, int(os.getenv("LLM_MAX_RETRIES", str(default))))
    except (TypeError, ValueError):
        return default


def get_llm_client(timeout: float = 20.0, max_retries: int | None = None):
    """
    Returns an OpenAI-SDK client.
    Raises RuntimeError if neither OpenAI nor Anthropic key is set.

    Note: Anthropic has an OpenAI-compatible proxy endpoint, so we can use
    the openai package for both providers when response_format=json is not needed.
    For structured JSON output (industry brief) we use get_anthropic_client() instead.
    """
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError("openai package not installed") from exc

    key = _openai_key()
    if not key:
        raise RuntimeError(
            "No LLM API key found. Set OPENAI_API_KEY (or OPEN_API_KEY) "
            "or ANTHROPIC_API_KEY."
        )
    retries = _llm_max_retries() if max_retries is None else max_retries
    return OpenAI(api_key=key, timeout=timeout, max_retries=retries)


def get_llm_model(default: str = "gpt-4o-mini") -> str:
    """Return the model name, respecting an optional LLM_MODEL override."""
    return (os.getenv("LLM_MODEL") or default).strip()


# ── Anthropic client ──────────────────────────────────────────────────────────

def get_anthropic_client(timeout: float = 20.0):
    """
    Returns an Anthropic client.
    Raises RuntimeError if ANTHROPIC_API_KEY is not set.
    """
    try:
        import anthropic
    except ImportError as exc:
        raise RuntimeError(
            "anthropic package not installed. Run: pip install anthropic"
        ) from exc

    key = _anthropic_key()
    if not key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set.")
    return anthropic.Anthropic(api_key=key, timeout=timeout, max_retries=_llm_max_retries())


def get_anthropic_model(default: str = "claude-3-5-haiku-20241022") -> str:
    return (os.getenv("LLM_MODEL") or default).strip()


# ── Convenience: call any provider with a prompt, return text ─────────────────

def llm_json_completion(
    system_prompt: str,
    user_prompt: str,
    *,
    max_tokens: int = 2400,
    temperature: float = 0.35,
    timeout: float = 20.0,
) -> str | None:
    """
    Send a prompt to whichever provider is configured and return the raw text.
    Returns None if no provider is configured (caller should use heuristics).

    Tries Anthropic first (when key present), falls back to OpenAI.
    Returns None when paid LLM is disabled (default) so callers use local inference.
    """
    if not paid_llm_allowed():
        return None
    provider = active_provider()

    if provider == "anthropic":
        try:
            client = get_anthropic_client(timeout=timeout)  # bounded retries
            model = get_anthropic_model()
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return (resp.content[0].text or "").strip()
        except Exception:
            # Fall through to OpenAI
            pass

    if provider == "openai" or _openai_key():
        try:
            from openai import OpenAI
            client = OpenAI(api_key=_openai_key(), timeout=timeout, max_retries=_llm_max_retries())
            model = get_llm_model()
            resp = client.chat.completions.create(
                model=model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return (resp.choices[0].message.content or "").strip()
        except Exception:
            pass

    return None  # No provider available — use local heuristics
