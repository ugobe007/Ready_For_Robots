"""pstack site protocol: roles, matcher ownership, refusals."""
from pathlib import Path

from app.services.pstack_protocol import (
    CRM_WALL_REQUIRED,
    CRITIC_HELDOUT_FIND_URLS,
    JOBS_MATCHER_SOURCE,
    ROLES,
    critic_gate_ids,
    critic_heldout_find_urls,
    crm_copilot_intent,
    jobs_matcher_path,
    refuse_gateway,
    refuse_site_agent,
    wrap_site_agent,
)

ROOT = Path(__file__).resolve().parents[1]


def test_roles_and_matcher_source():
    assert set(ROLES) == {"how", "act", "critic"}
    assert JOBS_MATCHER_SOURCE["kind"] == "matcher"
    assert JOBS_MATCHER_SOURCE["path"] == "/api/robot-job-match"
    assert jobs_matcher_path() == "POST /api/robot-job-match"
    assert critic_gate_ids() == [
        "find",
        "find_abort",
        "find_identity",
        "crm_leftover",
        "job_cards",
        "wall",
        "matcher",
        "oem_extract",
    ]
    assert CRM_WALL_REQUIRED is True


def test_critic_heldout_find_urls_cover_unknown_oems():
    urls = critic_heldout_find_urls()
    assert urls == list(CRITIC_HELDOUT_FIND_URLS)
    for host in (
        "advanced.farm",
        "bedrockrobotics.com",
        "xpeng.com",
        "aandkrobotics.com",
        "avatarrobotics.com",
        "agtonomy.com",
        "greenfieldincorporated.com",
        "organifarms.de",
    ):
        assert any(host in u for u in urls)


def test_refusals_block_gateway_hermes_and_chat():
    assert refuse_site_agent("vercel_ai_gateway")["ok"] is False
    assert refuse_gateway("ai-gateway")["reason"] == "vercel_ai_gateway"
    assert refuse_gateway("openai") is None
    assert refuse_site_agent("hermes_ingest")["detail"].startswith("Hermes")
    assert wrap_site_agent(role="act", surface="scout_chat")["ok"] is False


def test_crm_copilot_is_not_the_matcher():
    how = crm_copilot_intent()
    assert how["not_the_matcher"] is True
    assert how["job_source"]["owner"] == "app/services/robot_job_capability_match.py"
    tagged = wrap_site_agent(role="act", surface="crm_generate_plan", payload={"how": how})
    assert tagged["ok"] is True
    assert tagged["protocol"] == "pstack"
    assert tagged["role"] == "act"
    assert tagged["job_source"]["kind"] == "matcher"


def test_matcher_module_stays_code():
    matcher = (ROOT / "app" / "services" / "robot_job_capability_match.py").read_text()
    protocol = (ROOT / "app" / "services" / "pstack_protocol.py").read_text()
    assert "def match_jobs_for_profile" in matcher
    assert "Do not call Vercel AI Gateway" in protocol
    assert "robot_job_capability_match.py" in protocol


def test_sales_plan_agent_uses_pstack_not_gateway():
    src = (ROOT / "app" / "services" / "sales_plan_agent.py").read_text()
    assert "from app.services.pstack_protocol import" in src
    assert "wrap_site_agent" in src
    assert "crm_copilot_intent" in src
    assert "refuse_gateway" in src
    assert "ai-gateway" in src
    assert "Do not set SCOUT_PLAN_PROVIDER=ai-gateway" in src
