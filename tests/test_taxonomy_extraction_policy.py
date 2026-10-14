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
    assert cfg["evidence_check"] == "normalized_substring"


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


def test_prompt_carries_definition_and_version(monkeypatch):
    captured = {}

    class FakeMessages:
        def create(self, **kwargs):
            captured.update(kwargs)
            block = SimpleNamespace(type="tool_use", name="classify_robot", input={"products": json.dumps([product()])})
            return SimpleNamespace(content=[block], usage=SimpleNamespace(input_tokens=1, output_tokens=1),
                                   model="fake", stop_reason="tool_use")

    monkeypatch.setattr(te, "Anthropic", lambda api_key=None: SimpleNamespace(messages=FakeMessages()))
    result = te.extract_robot_taxonomy("https://acme.example", PAGE)

    prompt = captured["messages"][0]["content"]
    assert "INDUSTRY DEFINITION:" in prompt
    assert "organization that buys and operates the robot" in prompt
    assert result["extraction_metadata"]["prompt_version"] == "v3"
    assert [i["value"] for i in result["products"][0]["industries"]] == ["airport"]
