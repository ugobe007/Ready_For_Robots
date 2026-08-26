"""Vercel Git ignoreCommand: skip Preview and cursor/*; keep production main."""
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from scripts.vercel_git_build_policy import should_skip_vercel_git_build

ROOT = Path(__file__).resolve().parents[1]


def _ignore_command() -> str:
    data = json.loads((ROOT / "vercel.json").read_text(encoding="utf-8"))
    cmd = data.get("ignoreCommand")
    assert isinstance(cmd, str) and cmd.strip()
    return cmd


def test_policy_skips_preview_and_agent_branches():
    assert should_skip_vercel_git_build(
        vercel_env="preview", git_ref="cursor/vercel-agent-spend-009b"
    )
    assert should_skip_vercel_git_build(vercel_env="preview", git_ref="main")
    assert should_skip_vercel_git_build(
        vercel_env="production", git_ref="cursor/job-card-title-only-009b"
    )
    assert not should_skip_vercel_git_build(vercel_env="production", git_ref="main")


def test_root_vercel_json_ignore_command_matches_policy():
    cmd = _ignore_command()
    assert "VERCEL_ENV" in cmd
    assert "cursor/*" in cmd
    assert len(cmd) <= 256

    cases = [
        ({"VERCEL_ENV": "preview", "VERCEL_GIT_COMMIT_REF": "cursor/foo"}, True),
        ({"VERCEL_ENV": "preview", "VERCEL_GIT_COMMIT_REF": "feat/human"}, True),
        ({"VERCEL_ENV": "production", "VERCEL_GIT_COMMIT_REF": "cursor/foo"}, True),
        ({"VERCEL_ENV": "production", "VERCEL_GIT_COMMIT_REF": "main"}, False),
    ]
    for overrides, skip in cases:
        env = {**os.environ, **overrides}
        proc = subprocess.run(
            ["bash", "-c", cmd],
            env=env,
            cwd=ROOT,
            check=False,
        )
        assert (proc.returncode == 0) is skip, (overrides, proc.returncode)
        assert should_skip_vercel_git_build(
            vercel_env=overrides["VERCEL_ENV"],
            git_ref=overrides["VERCEL_GIT_COMMIT_REF"],
        ) is skip
