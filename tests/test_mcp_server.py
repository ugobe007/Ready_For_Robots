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
    tools = {t.name for t in asyncio.run(mcp_app.list_tools())}
    assert PUBLIC_READ_TOOLS.issubset(tools)


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


def test_r4r_client_adds_partner_key_header():
    client = R4RClient(base_url="https://api.test", api_key="partner-key-123")
    headers = client._headers()
    assert headers["X-R4R-API-Key"] == "partner-key-123"
