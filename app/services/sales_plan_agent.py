"""Sales plan agent — generates structured CRM plans per docs/agent-spec.md."""
from __future__ import annotations

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session, joinedload

from app.models.company import Company
from app.models.crm import AgentRun, CrmAccount, CrmEngagement, CrmNote, CrmTask
from app.models.signal import Signal
from app.services.crm_engagement_sync import ensure_engagement_for_opportunity, serialize_engagement, sync_account_stage_to_engagement
from app.services.pstack_protocol import crm_copilot_intent, refuse_gateway, wrap_site_agent
from app.services.sales_learning_agent import crm_workflow_intelligence

logger = logging.getLogger(__name__)

PROMPT_VERSION = "plan_v1"
PLAN_SCHEMA_VERSION = 1


def _fallback_plan(account: CrmAccount, company: Company | None, signals: list[Signal], intel: dict[str, Any]) -> dict[str, Any]:
    signal_types = sorted({(s.signal_type or "signal") for s in signals[:8]})
    citations = [
        {"signal_id": s.id, "claim": (s.title or s.signal_type or "signal")[:160]}
        for s in signals[:5]
    ]
    tasks = [
        {
            "title": "Confirm decision-maker and outreach email",
            "rationale": "Outreach quality depends on the right contact.",
            "priority": "high",
            "due_offset_days": 1,
            "linked_signal_types": signal_types[:2],
        },
        {
            "title": "Send Cal intro referencing top buying signal",
            "rationale": intel.get("recommended_action") or "Lead shows automation intent.",
            "priority": "high",
            "due_offset_days": 2,
            "linked_signal_types": signal_types[:3],
        },
    ]
    if intel.get("reply_count"):
        tasks.insert(
            0,
            {
                "title": "Draft context-aware reply and propose meeting",
                "rationale": "A reply exists — maintain momentum.",
                "priority": "high",
                "due_offset_days": 0,
                "linked_signal_types": signal_types[:1],
            },
        )
    return {
        "plan_schema_version": PLAN_SCHEMA_VERSION,
        "executive_summary": f"{account.name} shows automation buying intent with {len(signals)} tracked signal(s).",
        "hypothesis": f"Timing and signal mix suggest {account.name} is worth a focused automation conversation now.",
        "recommended_next_stage": "outreach" if not account.outreach_sent_at else "discovery",
        "stakeholders": [
            {
                "role": "Operations leader",
                "why_relevant": "Owns deployment and ROI for automation initiatives.",
                "suggested_outreach_angle": "Reference labor pain or facility expansion signals.",
            }
        ],
        "tasks": tasks,
        "risks": [
            {
                "risk": "Contact email may be inferred rather than verified.",
                "mitigation": "Validate via Apollo or a warm intro before high-stakes outreach.",
            }
        ],
        "talk_tracks": [
            f"We noticed signals around {signal_types[0]} at {account.name}." if signal_types else f"We are tracking automation intent at {account.name}.",
            "Happy to share how peer operators are deploying robotics for similar workflows.",
        ],
        "citations": citations,
    }


def _openai_plan(account: CrmAccount, company: Company | None, signals: list[Signal], intel: dict[str, Any]) -> dict[str, Any] | None:
    # Frozen on OpenAI (server-side). pstack roles wrap the call.
    # Do not set SCOUT_PLAN_PROVIDER=ai-gateway. Do not call Hermes.
    blocked = refuse_gateway(os.getenv("SCOUT_PLAN_PROVIDER"))
    if blocked:
        logger.warning("pstack refused CRM plan provider: %s", blocked["detail"])
        return None
    api_key = (os.getenv("OPENAI_API_KEY") or "").strip()
    if not api_key:
        return None
    try:
        import openai

        client = openai.OpenAI(api_key=api_key)
        signal_lines = [
            f"- [{s.signal_type}] {(s.title or s.raw_text or '')[:200]}"
            for s in signals[:12]
        ]
        prompt = (
            "You are a B2B sales copilot for robotics/automation. "
            "Return JSON only matching this schema: plan_schema_version, executive_summary, hypothesis, "
            "recommended_next_stage, stakeholders[], tasks[], risks[], talk_tracks[], citations[]. "
            "Do not invent private contact data. Ground claims in provided signals.\n\n"
            f"Account: {account.name}\nIndustry: {account.industry}\nStage: {account.outreach_stage}\n"
            f"Workflow intelligence: {json.dumps(intel)[:1200]}\nSignals:\n" + "\n".join(signal_lines)
        )
        model = (os.getenv("SCOUT_PLAN_MODEL") or os.getenv("SCOUT_CHAT_MODEL") or "gpt-4o-mini").strip()
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Return valid JSON only."},
                {"role": "user", "content": prompt},
            ],
            response_format={"type": "json_object"},
            temperature=0.3,
        )
        content = (resp.choices[0].message.content or "").strip()
        plan = json.loads(content)
        plan.setdefault("plan_schema_version", PLAN_SCHEMA_VERSION)
        return plan
    except Exception as exc:
        logger.warning("OpenAI plan generation failed: %s", exc)
        return None


def generate_sales_plan(
    db: Session,
    *,
    account: CrmAccount,
    user_id: uuid.UUID,
    commit_tasks: bool = False,
) -> dict[str, Any]:
    company = None
    signals: list[Signal] = []
    if account.company_id:
        company = (
            db.query(Company)
            .options(joinedload(Company.signals))
            .filter(Company.id == account.company_id)
            .first()
        )
        if company and company.signals:
            signals = sorted(company.signals, key=lambda s: s.detected_at or datetime.min.replace(tzinfo=timezone.utc), reverse=True)

    intel = crm_workflow_intelligence(db, account)
    how = crm_copilot_intent()
    plan = _openai_plan(account, company, signals, intel) or _fallback_plan(account, company, signals, intel)
    engagement = sync_account_stage_to_engagement(db, account)
    pstack = wrap_site_agent(
        role="act",
        surface="crm_generate_plan",
        payload={"how": how, "signal_count": len(signals)},
    )

    run = AgentRun(
        team_id=account.team_id,
        user_id=user_id,
        crm_account_id=account.id,
        engagement_id=engagement.id if engagement else None,
        model=(os.getenv("SCOUT_PLAN_MODEL") or os.getenv("SCOUT_CHAT_MODEL") or "rules+fallback"),
        prompt_version=PROMPT_VERSION,
        input_json={
            "account_id": str(account.id),
            "company_id": account.company_id,
            "signal_count": len(signals),
            "workflow_intelligence": intel,
            "pstack": pstack,
        },
        output_json=plan,
    )
    db.add(run)
    db.flush()

    created_tasks: list[dict[str, Any]] = []
    if commit_tasks:
        now = datetime.now(timezone.utc)
        for item in plan.get("tasks") or []:
            if not isinstance(item, dict):
                continue
            due_days = int(item.get("due_offset_days") or 3)
            task = CrmTask(
                team_id=account.team_id,
                crm_account_id=account.id,
                engagement_id=engagement.id if engagement else None,
                title=(item.get("title") or "Follow up")[:240],
                body=(item.get("rationale") or "")[:2000] or None,
                status="todo",
                priority=(item.get("priority") or "normal")[:32],
                due_at=now + timedelta(days=due_days),
                assignee_user_id=user_id,
                source="agent",
            )
            db.add(task)
            db.flush()
            created_tasks.append(
                {
                    "id": str(task.id),
                    "title": task.title,
                    "priority": task.priority,
                    "due_at": task.due_at.isoformat() if task.due_at else None,
                }
            )
        summary = plan.get("executive_summary") or "Agent plan generated."
        db.add(
            CrmNote(
                team_id=account.team_id,
                crm_account_id=account.id,
                engagement_id=engagement.id if engagement else None,
                author_user_id=user_id,
                body=summary[:4000],
                source="agent",
            )
        )

    return {
        "plan": plan,
        "agent_run_id": str(run.id),
        "engagement": serialize_engagement(engagement) if engagement else None,
        "tasks": created_tasks,
        "pstack": pstack,
    }
