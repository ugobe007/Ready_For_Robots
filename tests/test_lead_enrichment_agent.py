"""Lead enrichment agent (heuristic path, no LLM)."""
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.lead_enrichment_agent import enrich_lead_with_agent


def test_enrich_lead_with_agent_heuristic_only():
    company = SimpleNamespace(
        id=99,
        name="Acme Logistics",
        industry="Logistics",
        employee_estimate=1200,
        automation_profile={},
        crm_metadata={},
    )
    signals = [
        SimpleNamespace(
            signal_type="capex",
            signal_text="Acme announced $8M capex for warehouse AMR deployment. RFP due Q3.",
            created_at=None,
        )
    ]
    db = MagicMock()
    db.add = MagicMock()
    db.commit = MagicMock()

    dossier = SimpleNamespace(
        is_lead=True,
        to_dict=lambda: {
            "specific_problem": "Throughput constraint",
            "why_lead": ["High intent"],
            "procurement": {"stage": "rfp"},
            "timetable": {"window": "Q3"},
            "robot_categories": ["amr"],
            "intent_score": 88,
            "tier": "HOT",
        },
    )

    with patch("app.services.lead_enrichment_agent.refresh_company_inference", return_value=dossier):
        with patch("app.services.lead_enrichment_agent.load_learned_store", return_value={"buckets": {}, "word_shapes": [], "stats": {}}):
            with patch("app.services.lead_enrichment_agent.save_learned_store"):
                with patch("app.services.lead_enrichment_agent._llm_extract_candidates", return_value=None):
                    with patch(
                        "app.services.lead_enrichment_agent.enrich_company_contact_intelligence",
                        return_value={
                            "status": "ready",
                            "phone": {"best": {"phone": "+14155551212"}},
                            "linkedin": {"best_profile": {"url": "https://www.linkedin.com/in/jane-doe"}},
                        },
                    ):
                        result = enrich_lead_with_agent(
                            company, signals, db, use_llm=False, update_global_ontology=True
                        )

    assert result.inference_refreshed is True
    assert result.company_id == 99
    assert company.crm_metadata.get("agent_enrichment")
    assert company.crm_metadata.get("contact_intelligence", {}).get("status") == "ready"
    assert db.commit.called
