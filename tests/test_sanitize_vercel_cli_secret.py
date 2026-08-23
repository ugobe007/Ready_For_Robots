from scripts.sanitize_vercel_cli_secret import (
    assert_cli_safe,
    sanitize_vercel_cli_secret,
)


def test_trailing_space_is_the_gha_failure_mode():
    # GitHub Actions env dump showed `VERCEL_TOKEN: *** ` (space after mask).
    out = sanitize_vercel_cli_secret("abc123 ")
    assert out.value == "abc123"
    assert out.stripped_whitespace
    assert_cli_safe("VERCEL_TOKEN", out)


def test_trailing_newline_from_secret_paste():
    out = sanitize_vercel_cli_secret("abc123\n")
    assert out.value == "abc123"
    assert_cli_safe("VERCEL_TOKEN", out)


def test_bearer_prefix():
    out = sanitize_vercel_cli_secret("Bearer abc123")
    assert out.value == "abc123"
    assert out.stripped_bearer
    assert_cli_safe("VERCEL_TOKEN", out)


def test_wrapped_quotes():
    out = sanitize_vercel_cli_secret('"abc123"')
    assert out.value == "abc123"
    assert out.stripped_quotes
    assert_cli_safe("VERCEL_TOKEN", out)


def test_empty_is_unsafe():
    out = sanitize_vercel_cli_secret("   \n")
    try:
        assert_cli_safe("VERCEL_TOKEN", out)
    except ValueError as exc:
        assert "empty" in str(exc)
    else:
        raise AssertionError("expected empty secret to fail")


def test_internal_space_is_unsafe():
    out = sanitize_vercel_cli_secret("abc 123")
    try:
        assert_cli_safe("VERCEL_TOKEN", out)
    except ValueError as exc:
        assert "whitespace" in str(exc)
    else:
        raise AssertionError("expected internal space to fail")


def test_main_rewrites_github_env(tmp_path, monkeypatch):
    env_file = tmp_path / "env"
    out_file = tmp_path / "out"
    env_file.write_text("")
    out_file.write_text("")
    monkeypatch.setenv("VERCEL_TOKEN", "tok123 ")
    monkeypatch.setenv("VERCEL_ORG_ID", "team_abc")
    monkeypatch.setenv("VERCEL_PROJECT_ID", "prj_abc")
    monkeypatch.setenv("GITHUB_ENV", str(env_file))
    monkeypatch.setenv("GITHUB_OUTPUT", str(out_file))

    from scripts.sanitize_vercel_cli_secret import main

    assert main() == 0
    written = env_file.read_text()
    assert "VERCEL_TOKEN=tok123\n" in written
    assert "configured=true\n" in out_file.read_text()
