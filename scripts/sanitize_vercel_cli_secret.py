"""Normalize GitHub Actions secrets before passing them to `vercel --token`.

Vercel CLI 59+ rejects `--token` if the value contains a space
(https://err.sh/vercel/invalid-token-value). GitHub secret paste often
includes a trailing newline/space or a `Bearer ` prefix from the dashboard.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_BEARER = re.compile(r"bearer\s+", re.IGNORECASE)
_WRAP_QUOTES = re.compile(r"^(['\"])(.*)\1$")


@dataclass(frozen=True)
class SanitizedSecret:
    value: str
    stripped_whitespace: bool
    stripped_bearer: bool
    stripped_quotes: bool


def sanitize_vercel_cli_secret(raw: str | None) -> SanitizedSecret:
    original = raw or ""
    v = original.replace("\r", " ").replace("\n", " ").replace("\t", " ").strip()

    bearer = bool(_BEARER.match(v))
    if bearer:
        v = _BEARER.sub("", v).strip()

    quotes = False
    quoted = _WRAP_QUOTES.match(v)
    if quoted:
        quotes = True
        v = quoted.group(2).strip()

    return SanitizedSecret(
        value=v,
        stripped_whitespace=v != original,
        stripped_bearer=bearer,
        stripped_quotes=quotes,
    )


def assert_cli_safe(name: str, secret: SanitizedSecret) -> None:
    if not secret.value:
        raise ValueError(f"{name} is empty after sanitizing")
    if re.search(r"\s", secret.value):
        raise ValueError(
            f"{name} still contains whitespace after trim — re-paste a single "
            "token with no spaces, no quotes, and no Bearer prefix"
        )


def main() -> int:
    """Sanitize GHA secrets in-place via GITHUB_ENV. Used by deploy-frontend.yml."""
    import os

    names = ("VERCEL_TOKEN", "VERCEL_ORG_ID", "VERCEL_PROJECT_ID")
    sanitized: dict[str, SanitizedSecret] = {}
    for name in names:
        secret = sanitize_vercel_cli_secret(os.environ.get(name))
        try:
            assert_cli_safe(name, secret)
        except ValueError as exc:
            print(f"::error::{exc}")
            if name == "VERCEL_TOKEN" and not secret.value:
                print(
                    "Vercel CLI secrets not set (VERCEL_TOKEN / VERCEL_ORG_ID / "
                    "VERCEL_PROJECT_ID)."
                )
                print(
                    "This job used to skip-green in ~7s while readyforrobots.com "
                    "did not move."
                )
                print("See docs/vercel_production_secrets.md")
            return 1
        sanitized[name] = secret
        # GitHub only masks the exact stored secret. A trimmed copy would leak.
        print(f"::add-mask::{secret.value}")

    env_path = os.environ.get("GITHUB_ENV")
    out_path = os.environ.get("GITHUB_OUTPUT")
    if env_path:
        with open(env_path, "a", encoding="utf-8") as handle:
            for name, secret in sanitized.items():
                handle.write(f"{name}={secret.value}\n")
    if out_path:
        with open(out_path, "a", encoding="utf-8") as handle:
            handle.write("configured=true\n")

    notes = []
    for name, secret in sanitized.items():
        bits = []
        if secret.stripped_whitespace:
            bits.append("whitespace")
        if secret.stripped_bearer:
            bits.append("Bearer prefix")
        if secret.stripped_quotes:
            bits.append("quotes")
        if bits:
            notes.append(f"Sanitized {name} (removed {', '.join(bits)}).")
    if notes:
        for line in notes:
            print(line)
        print(
            "Vercel CLI 59+ rejects --token values that contain a space. "
            "The GitHub secret likely has a trailing space (Actions env dump "
            "shows `VERCEL_TOKEN: *** `). Trim is applied for this run; "
            "re-paste the secret without a trailing space when you can."
        )
    else:
        print("Vercel CLI secrets are present and CLI-safe.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
