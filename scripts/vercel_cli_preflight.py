"""Preflight for GitHub Actions Vercel production deploy.

`vercel pull` in CLI 59 fails on project-scoped tokens with a misleading
`.vercel` error (GET /v2/user → 404, GET /teams/{id} → 403, GET project → 200).
See https://github.com/vercel/vercel/issues/17506

This script checks the token against the Vercel API, resolves the ready-for-robots
project ids, and writes `.vercel/project.json`. The workflow then runs
`vercel deploy --prod` (which works with project-scoped tokens) instead of pull.
"""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_root))

from scripts.sanitize_vercel_cli_secret import sanitize_vercel_cli_secret  # noqa: E402

CANONICAL_ORG_ID = "team_i9wBQr2ur295OmAB8COX5Q0r"
CANONICAL_PROJECT_ID = "prj_VHdUEY8x5jC9O2dnUdYxbDHWeTqn"
CANONICAL_PROJECT_NAME = "ready-for-robots"
CANONICAL_TEAM_SLUG = "ugobe07-gmailcoms-projects"
API = "https://api.vercel.com"


def classify_token_scope(*, user_status: int, team_status: int, project_status: int) -> str:
    if project_status == 401:
        return "token_invalid"
    if user_status == 404 and team_status in (401, 403) and project_status == 200:
        return "project_scoped"
    if user_status == 200 and team_status == 200 and project_status == 200:
        return "team_or_account"
    if project_status == 200:
        return "project_accessible"
    if project_status in (403, 404):
        return "wrong_project"
    return "unknown"


def api_get(token: str, path: str) -> tuple[int, Any]:
    req = urllib.request.Request(
        API + path,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as err:
        raw = err.read().decode(errors="replace")
        try:
            body: Any = json.loads(raw)
        except json.JSONDecodeError:
            body = {"raw": raw[:500]}
        return err.code, body
    except urllib.error.URLError as err:
        return 0, {"error": {"code": "network", "message": str(err.reason)}}


def _project_matches(project: dict[str, Any]) -> bool:
    return project.get("id") == CANONICAL_PROJECT_ID or project.get("name") == CANONICAL_PROJECT_NAME


def resolve_canonical_project(projects: list[dict[str, Any]]) -> dict[str, Any] | None:
    for project in projects:
        if _project_matches(project):
            return project
    return None


def write_project_json(org_id: str, project_id: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(
        json.dumps({"orgId": org_id, "projectId": project_id}, indent=2) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    token = sanitize_vercel_cli_secret(os.environ.get("VERCEL_TOKEN")).value
    org_secret = sanitize_vercel_cli_secret(os.environ.get("VERCEL_ORG_ID")).value
    project_secret = sanitize_vercel_cli_secret(os.environ.get("VERCEL_PROJECT_ID")).value
    if not token:
        print("::error::VERCEL_TOKEN is empty.")
        return 1

    user_status, _user = api_get(token, "/v2/user")
    team_status, _team = api_get(token, f"/v2/teams/{org_secret or CANONICAL_ORG_ID}")
    listed_status, listed_body = api_get(token, "/v9/projects?limit=20")
    projects = []
    if listed_status == 200 and isinstance(listed_body, dict):
        projects = list(listed_body.get("projects") or [])

    probe_id = project_secret or CANONICAL_PROJECT_ID
    project_status, project_body = api_get(token, f"/v9/projects/{probe_id}")
    if project_status != 200:
        project_status, project_body = api_get(token, f"/v9/projects/{CANONICAL_PROJECT_ID}")

    scope = classify_token_scope(
        user_status=user_status,
        team_status=team_status,
        project_status=project_status,
    )
    print(
        f"Vercel token scope: {scope} "
        f"(user HTTP {user_status}, team HTTP {team_status}, project HTTP {project_status})"
    )

    if scope == "token_invalid":
        print("::error::VERCEL_TOKEN was rejected (401). Create a new token and update the GitHub secret.")
        return 1

    canonical = None
    if isinstance(project_body, dict) and project_status == 200 and _project_matches(project_body):
        canonical = project_body
    if canonical is None:
        canonical = resolve_canonical_project(projects)

    if canonical is None:
        names = [
            f"{p.get('name')} ({p.get('id')})"
            for p in projects
            if isinstance(p, dict)
        ]
        print(
            "::error::This token cannot see Vercel project "
            f"{CANONICAL_PROJECT_NAME} ({CANONICAL_PROJECT_ID})."
        )
        print("Projects this token can see:", ", ".join(names) or "(none)")
        print(
            "Create the token on the ready-for-robots project, or set "
            f"VERCEL_PROJECT_ID={CANONICAL_PROJECT_ID} and "
            f"VERCEL_ORG_ID={CANONICAL_ORG_ID}."
        )
        return 1

    org_id = str(canonical.get("accountId") or CANONICAL_ORG_ID)
    project_id = str(canonical.get("id") or CANONICAL_PROJECT_ID)
    print(
        f"Linked {canonical.get('name')} project_id={project_id} org_id={org_id} "
        f"team={CANONICAL_TEAM_SLUG}"
    )
    if project_secret and project_secret not in {project_id, CANONICAL_PROJECT_NAME}:
        print(
            f"GitHub VERCEL_PROJECT_ID did not match; using {project_id} from the token."
        )
    if org_secret and org_secret not in {org_id, CANONICAL_TEAM_SLUG}:
        print(f"GitHub VERCEL_ORG_ID did not match; using {org_id} from the token.")

    if scope == "project_scoped":
        print(
            "Token is project-scoped. Vercel CLI 59 `vercel pull` fails with "
            "'Could not retrieve Project Settings' (user 404 + team 403) even when "
            "the project GET is 200. This workflow uses `vercel deploy --prod` instead."
        )

    write_project_json(org_id, project_id, _root / ".vercel" / "project.json")

    env_path = os.environ.get("GITHUB_ENV")
    if env_path:
        with open(env_path, "a", encoding="utf-8") as handle:
            handle.write(f"VERCEL_ORG_ID={org_id}\n")
            handle.write(f"VERCEL_PROJECT_ID={project_id}\n")
    print("::add-mask::" + org_id)
    print("::add-mask::" + project_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
