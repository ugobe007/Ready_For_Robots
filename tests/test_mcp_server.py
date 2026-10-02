"""Tests for Ready For Robots MCP server."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.mcp.client import R4RClient, format_json
from app.mcp.config import PUBLIC_READ_TOOLS
from app.mcp.server import create_mcp_app


@pytest.fixture
def mcp_app():
    return create_mcp_app()


def test_public_tool_names_registered(mcp_app):
    tools = asyncio.run(mcp_app.list_tools())
    names = {t.name for t in tools}
    assert PUBLIC_READ_TOOLS.issubset(names)
    for tool in tools:
        ann = tool.annotations
        assert ann is not None, tool.name
        assert isinstance(ann.readOnlyHint, bool), tool.name
        assert isinstance(ann.openWorldHint, bool), tool.name
        assert isinstance(ann.destructiveHint, bool), tool.name
        if ann.readOnlyHint:
            assert ann.destructiveHint is False


def test_format_json_truncates_large_payloads():
    big = {"items": list(range(5000))}
    out = format_json(big, max_chars=200)
    assert "truncated" in out
    assert len(out) <= 220


def test_humanoid_list_robots_tool(mcp_app):
    sample = [{"name": "Unitree G1", "model_slug": "unitree-g1", "score_total": 72.5}]
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=sample)

    with patch("app.mcp.server.get_client", return_value=mock_client):
        tool = next(t for t in asyncio.run(mcp_app.list_tools()) if t.name == "humanoid_list_robots")
        result = asyncio.run(tool.fn(limit=10))

    mock_client.get.assert_awaited_once_with("/api/humanoid/robots")
    parsed = json.loads(result)
    assert parsed[0]["model_slug"] == "unitree-g1"


def test_robot_ready_match_tool(mcp_app):
    sample = {"matched_companies": [{"company": "Acme", "match_score": 88}]}
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=sample)

    with patch("app.mcp.server.get_client", return_value=mock_client):
        tool = next(t for t in asyncio.run(mcp_app.list_tools()) if t.name == "robot_ready_match")
        result = asyncio.run(tool.fn(robot_name="TUG", url="https://example.com/tug"))

    mock_client.post.assert_awaited_once()
    call = mock_client.post.await_args
    assert call.args[0] == "/api/robot-ready/submit"
    assert call.kwargs["json_body"]["robot_name"] == "TUG"
    assert "Acme" in result


def test_match_robot_jobs_mcp_tool(mcp_app):
    sample = {"status": "success", "matched_job_count": 1, "jobs": [{"title": "Material Handler"}]}
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=sample)

    with patch("app.mcp.server.get_client", return_value=mock_client):
        tool = next(t for t in asyncio.run(mcp_app.list_tools()) if t.name == "match_robot_jobs")
        result = asyncio.run(tool.fn(url="https://alpharoboticsai.com", robot_name="UR10e"))

    mock_client.post.assert_awaited_once()
    call = mock_client.post.await_args
    assert call.args[0] == "/api/v1/gpt-actions/match-jobs"
    assert call.kwargs["json_body"]["robot_name"] == "UR10e"
    assert "Material Handler" in result


def test_calculate_robot_payback_mcp_tool(mcp_app):
    sample = {"payback_period_months": 4.6, "annual_roi_percent": 253.3}
    mock_client = AsyncMock()
    mock_client.post = AsyncMock(return_value=sample)

    with patch("app.mcp.server.get_client", return_value=mock_client):
        tool = next(t for t in asyncio.run(mcp_app.list_tools()) if t.name == "calculate_robot_payback")
        result = asyncio.run(
            tool.fn(robot_cost=45000.0, hourly_labor_rate=28.5, shift_hours_per_day=8.0)
        )

    mock_client.post.assert_awaited_once()
    call = mock_client.post.await_args
    assert call.args[0] == "/api/v1/gpt-actions/calculate-payback"
    assert "4.6" in result


def test_r4r_client_adds_partner_key_header():
    client = R4RClient(base_url="https://api.test", api_key="partner-key-123")
    headers = client._headers()
    assert headers["X-R4R-API-Key"] == "partner-key-123"
