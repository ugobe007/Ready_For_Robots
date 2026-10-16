import json
from types import SimpleNamespace

import pytest

from app.services.robot_understanding_v1 import taxonomy_extraction as te

PAGE = "Acme builds autonomous floor scrubbers for airports and grocery stores."


def fact(value, evidence, confidence=0.9):
    return {"value": value, "evidence": evidence, "confidence": confidence}


def product(**overrides):
    base = {
        "company": "Acme",
        "product_name": "Scrubber",
        "offering_type": fact("robot_product", "Acme builds autonomous floor scrubbers"),
        "form": fact("amr_mobile_robot", "autonomous floor scrubbers"),
        "primary_class": fact("cleaning", "floor scrubbers"),
        "primary_function": fact("cleaning", "floor scrubbers"),
        "secondary_functions": [],
        "industries": [
            fact("airport", "for airports"),
            fact("hospital", "trusted by hospitals nationwide"),
        ],
        "unclassified_notes": "",
    }
    base.update(overrides)
    return base


CONFIG = {"evidence_check": "normalized_substring", "exclude_unsupported_facts": True, "unsupported_confidence_cap": 0.3}


def test_unsupported_industry_is_removed_and_logged():
    out = te.apply_evidence_policy(product(), PAGE, CONFIG)
    assert [i["value"] for i in out["industries"]] == ["airport"]
    assert out["unsupported_facts"] == [
        {"value": "hospital", "evidence": "trusted by hospitals nationwide", "confidence": 0.3, "field": "industries"}
    ]


def test_unsupported_single_value_field_becomes_none():
    out = te.apply_evidence_policy(product(form=fact("humanoid", "a bipedal humanoid")), PAGE, CONFIG)
    assert out["form"] is None
    assert out["unsupported_facts"][0]["field"] == "form"


def test_exclusion_can_be_disabled_in_config():
    out = te.apply_evidence_policy(product(), PAGE, {**CONFIG, "exclude_unsupported_facts": False})
    hospital = [i for i in out["industries"] if i["value"] == "hospital"][0]
    assert hospital["confidence"] == 0.3 and hospital["evidence_validated"] is False
    assert len(out["unsupported_facts"]) == 1


def test_shipped_config_excludes_unsupported_facts():
    cfg = te.load_extraction_config()
    assert cfg["exclude_unsupported_facts"] is True
    assert cfg["evidence_check"] == "normalized_pieces_in_order"
    assert cfg["max_output_tokens"] == 8192 and cfg["max_records_per_page"] == 5
    assert cfg["temperature"] == 0


def test_definition_key_is_not_an_enum_value():
    taxonomy = te.load_taxonomy()
    assert "_definition" in taxonomy["industries"]
    schema = te.build_extraction_schema(taxonomy)
    enum = schema["properties"]["products"]["items"]["properties"]["industries"]["items"]["properties"]["value"]["enum"]
    assert "_definition" not in enum and "hospital" in enum


@pytest.mark.parametrize("raw", [
    json.dumps([product()]),
    [json.dumps(product())],
    product(),
])
def test_string_encoded_products_are_parsed(raw):
    assert te._coerce_products(raw)[0]["company"] == "Acme"


def _response(products, page_type="manufacturer_product_page"):
    tool_input = {"page_type": {"value": page_type, "confidence": 0.9, "evidence": "Acme builds"}, "products": products}
    block = SimpleNamespace(type="tool_use", name="classify_robot", input=tool_input)
    return SimpleNamespace(content=[block], usage=SimpleNamespace(input_tokens=10, output_tokens=5),
                           model="fake", stop_reason="tool_use")


def test_malformed_output_is_retried_and_tokens_counted():
    replies = iter([_response('[{"evidence": "an "unescaped" quote"}]'), _response([product()])])
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: next(replies)))
    result, call = te._call_with_retry(client, {}, retries=1)
    assert result["products"][0]["company"] == "Acme"
    assert call["attempts"] == 2 and call["input_tokens"] == 20 and len(call["errors"]) == 1


def test_retry_gives_up_after_limit():
    client = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: _response("not json")))
    with pytest.raises(ValueError, match="after 2 attempts"):
        te._call_with_retry(client, {}, retries=1)


def _fake_client(monkeypatch, response):
    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            return response

    monkeypatch.setattr(te, "Anthropic", lambda api_key=None: SimpleNamespace(messages=FakeMessages()))
    return captured


def test_prompt_carries_definition_version_and_limits(monkeypatch):
    captured = _fake_client(monkeypatch, _response(json.dumps([product()])))
    result = te.extract_robot_taxonomy("https://acme.example", PAGE)

    prompt = captured["messages"][0]["content"]
    assert "PRIMARY CLASS DEFINITION:" in prompt
    assert te.load_taxonomy()["primary_class"]["_definition"] in prompt
    assert "INDUSTRY DEFINITION:" in prompt
    assert "organization that buys and operates the robot" in prompt
    assert "STEP 1 - PAGE TYPE" in prompt and "ONE contiguous passage copied exactly" in prompt
    assert captured["max_tokens"] == 8192
    assert captured["extra_body"]["temperature"] == 0
    assert captured["tools"][0]["input_schema"]["properties"]["products"]["maxItems"] == 5
    assert result["extraction_metadata"]["prompt_version"] == "v6"
    assert "- restaurant: Full-service and casual restaurants, cafes, ghost/delivery kitchens, including the bars inside them" in prompt
    assert "- bar_nightclub: Standalone bars, lounges and nightclubs" in prompt
    assert "- _definition:" not in prompt
    assert result["page"]["page_type"] == "manufacturer_product_page"
    assert [i["value"] for i in result["products"][0]["industries"]] == ["airport"]


@pytest.mark.parametrize("page_type", ["news_press", "buyer_corporate_site", "directory_or_multi_company"])
def test_non_manufacturer_page_produces_only_a_page_record(monkeypatch, page_type):
    _fake_client(monkeypatch, _response([product()], page_type=page_type))
    result = te.extract_robot_taxonomy("https://news.example", PAGE)
    assert result["products"] == []
    assert result["page"] == {**result["page"], "page_type": page_type, "produces_records": False, "offering_type": "non_robot"}
    assert result["extraction_metadata"]["records_dropped_by_page_type"] == 1


def test_records_capped_and_hinted_product_kept():
    products = [product(product_name=f"Bot {i}") for i in range(7)] + [product(product_name="Target X")]
    kept = te.cap_records(products, "Target X", 5)
    assert len(kept) == 5 and kept[0]["product_name"] == "Target X"
    assert [p["product_name"] for p in te.cap_records(products, None, 5)] == [f"Bot {i}" for i in range(5)]


@pytest.mark.parametrize("evidence", [
    "Acme\u2019s scrubbers \u2014 for airports",
    "acme's SCRUBBERS - for   airports",
    "Acme's scrubbers... for airports",
    "Acme's scrubbers \u2026 grocery stores",
])
def test_evidence_v2_normalizes_and_accepts_ordered_pieces(evidence):
    page = "Acme\u2019s scrubbers \u2013 for airports and \u201cgrocery stores\u201d."
    assert te.validate_evidence(evidence, page)


@pytest.mark.parametrize("evidence", [
    "grocery stores... Acme's scrubbers",
    "Acme's scrubbers... for hospitals",
    "...",
    "Acme's scrubbers for airports",
])
def test_evidence_v2_rejects_out_of_order_missing_or_joined(evidence):
    page = "Acme\u2019s scrubbers \u2013 for airports and grocery stores."
    assert not te.validate_evidence(evidence, page)
