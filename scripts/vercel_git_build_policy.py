"""When Vercel Git should skip a build (ignoreCommand contract).

Vercel: ignoreCommand exit 0 → skip; exit 1 → build.

Agents push `cursor/*` many times per PR. Vercel Git was running a full
pnpm + Vite Preview on every push. Production for `readyforrobots.com` is
GitHub Actions `vercel deploy --prebuilt --prod` (see deploy-frontend.yml),
not Preview.

This module is the testable form of root `vercel.json` `ignoreCommand`.
The JSON command is POSIX shell so Vercel's ignore step does not need Python.
"""
from __future__ import annotations

import os


def should_skip_vercel_git_build(
    *,
    vercel_env: str | None,
    git_ref: str | None,
) -> bool:
    """True when a Git-triggered Vercel build must not run.

    Skip all Preview (and any `cursor/*` ref, even if Vercel labels it
    production). Build only Git production on non-cursor branches (main).
    CLI `vercel deploy --prod` from Actions is not an ignoreCommand path.
    """
    ref = (git_ref or "").strip()
    env = (vercel_env or "").strip().lower()
    if ref.startswith("cursor/"):
        return True
    return env != "production"


def main(argv: list[str] | None = None) -> int:
    del argv  # ignoreCommand has no args; env vars only
    skip = should_skip_vercel_git_build(
        vercel_env=os.environ.get("VERCEL_ENV"),
        git_ref=os.environ.get("VERCEL_GIT_COMMIT_REF"),
    )
    return 0 if skip else 1


if __name__ == "__main__":
    raise SystemExit(main())
