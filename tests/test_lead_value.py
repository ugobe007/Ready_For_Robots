from app.services.lead_value import LEAD_VALUE_WEIGHTS, compute_lead_value


def test_lead_value_prefers_large_account_with_specs():
    small = compute_lead_value(
        72.0,
        400,
        {
            "deployment_contexts": ["logistics_warehouse"],
            "robot_categories": ["amr_amr_forklift"],
            "application_areas": ["goods_to_person"],
            "confidence": "medium",
        },
        [],
    )
    large = compute_lead_value(
        70.0,
        12_000,
        {
            "deployment_contexts": ["logistics_warehouse", "distribution_center"],
            "robot_categories": ["amr_amr_forklift", "agv"],
            "application_areas": ["palletizing", "sortation", "goods_to_person"],
            "confidence": "high",
        },
        [],
    )
    assert large["lead_value_score"] > small["lead_value_score"]


def test_weights_sum_to_one():
    assert abs(sum(LEAD_VALUE_WEIGHTS.values()) - 1.0) < 1e-6


def test_components_rounded():
    r = compute_lead_value(50.0, None, {"confidence": "low"}, [])
    assert "intent_strength" in r["components"]
    assert "procurement_timeline" in r["components"]
    assert r["lead_value_score"] >= 0 and r["lead_value_score"] <= 100


class _Sig:
    def __init__(self, text: str):
        self.signal_text = text
        self.created_at = None


def test_procurement_timeline_boosts_value():
    base = compute_lead_value(60.0, 1000, {"confidence": "medium"}, [_Sig("Considering automation options.")])
    with_rfp = compute_lead_value(
        60.0,
        1000,
        {"confidence": "medium"},
        [_Sig("RFP for warehouse automation due March 2026; go-live targeted Q3 2026.")],
    )
    assert with_rfp["components"]["procurement_timeline"] > base["components"]["procurement_timeline"]
    assert with_rfp["lead_value_score"] > base["lead_value_score"]
    assert "rfp_procurement" in with_rfp.get("procurement_hints", [])


def test_extra_timeline_text_from_crm_notes():
    r = compute_lead_value(
        55.0,
        500,
        {"confidence": "low"},
        [],
        extra_timeline_text="Customer says pilot ends Q2 FY2027 then fleet rollout.",
    )
    assert r["components"]["procurement_timeline"] >= 0.5
    assert len(r.get("procurement_hints", [])) >= 1
