from scripts.vercel_cli_preflight import (
    CANONICAL_PROJECT_ID,
    CANONICAL_PROJECT_NAME,
    classify_token_scope,
    resolve_canonical_project,
    write_project_json,
)


def test_project_scoped_is_the_gha_pull_failure():
    # Reproduced with a vcp_ token: user 404, team 403, project 200.
    assert (
        classify_token_scope(user_status=404, team_status=403, project_status=200)
        == "project_scoped"
    )


def test_team_token_is_ok_for_pull():
    assert (
        classify_token_scope(user_status=200, team_status=200, project_status=200)
        == "team_or_account"
    )


def test_wrong_project():
    assert (
        classify_token_scope(user_status=200, team_status=200, project_status=404)
        == "wrong_project"
    )


def test_resolve_canonical_by_name_or_id():
    projects = [
        {"id": "prj_other", "name": "other"},
        {"id": CANONICAL_PROJECT_ID, "name": CANONICAL_PROJECT_NAME, "accountId": "team_x"},
    ]
    found = resolve_canonical_project(projects)
    assert found is not None
    assert found["id"] == CANONICAL_PROJECT_ID


def test_write_project_json(tmp_path):
    dest = tmp_path / ".vercel" / "project.json"
    write_project_json("team_abc", "prj_abc", dest)
    assert '"orgId": "team_abc"' in dest.read_text()
    assert '"projectId": "prj_abc"' in dest.read_text()
