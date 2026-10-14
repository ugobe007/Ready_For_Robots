from scripts.test_understanding_v2_benchmark import score_gap_probe, summarize

PROBE = {
    "id": "gp-02",
    "offering_type_ok": ["robot_product"],
    "form_ok": ["robotic_arm_cobot"],
    "primary_class_ok": ["healthcare"],
    "industries_required": ["hospital"],
    "industries_any": [],
    "industries_must_not": ["restaurant"],
}


def _extracted(notes: str, **overrides):
    base = {
        "offering_type": "robot_product",
        "form": "robotic_arm_cobot",
        "primary_class": "healthcare",
        "primary_function": {"value": "general_purpose"},
        "industries": [{"value": "hospital"}],
        "unclassified_notes": notes,
    }
    base.update(overrides)
    return base


def test_gap_probe_named_and_fields_scored_without_functions():
    gap = score_gap_probe(_extracted("Robotic surgery has no function value in the taxonomy."), PROBE)
    assert gap["gap_named"] is True
    assert set(gap["fields"]) == {"offering_type", "form", "primary_class", "industries"}
    assert all(f["pass"] for f in gap["fields"].values())


def test_gap_probe_not_named_and_blanked_field_scores_wrong():
    gap = score_gap_probe(_extracted("Hospital robot.", primary_class=""), PROBE)
    assert gap["gap_named"] is False
    assert gap["fields"]["primary_class"]["pass"] is False


def test_summary_keeps_three_groups_separate_and_counts_unsupported_by_field():
    results = [
        {"id": "h-01", "group": "robot", "bucket": "PASSED", "score": None,
         "extracted": {"unsupported_facts": [{"field": "industries"}, {"field": "form"}]}},
        {"id": "h-02", "group": "robot", "bucket": "FETCH_FAILED"},
        {"id": "h-03", "group": "robot", "bucket": "EXTRACTION_FAILED", "error": "boom"},
        {"id": "gp-02", "group": "gap_probe", "bucket": "GAP_NAMED",
         "gap_probe_score": {"fields": {"form": {"pass": True}}},
         "extracted": {"unsupported_facts": [{"field": "primary_function"}]}},
        {"id": "neg-h1", "group": "negative_control", "bucket": "NEG_FAIL",
         "extracted": {"unsupported_facts": [{"field": "offering_type"}]}},
    ]
    s = summarize(results)
    assert s["robots"]["passed"] == ["h-01"]
    assert s["robots"]["unreadable"] == ["h-02"]
    assert s["robots"]["crashed"] == ["h-03"]
    assert s["robots"]["unsupported_by_field"]["industries"] == 1
    assert s["robots"]["unsupported_by_field"]["form"] == 1
    assert s["taxonomy_gap_probes"]["verdicts"] == {"gp-02": "PASS"}
    assert s["taxonomy_gap_probes"]["unsupported_by_field"]["primary_function"] == 1
    assert s["negative_controls"]["verdicts"] == {"neg-h1": "FAIL"}
    assert s["negative_controls"]["unsupported_by_field"]["offering_type"] == 1


def test_page_type_only_result_flattens_to_non_robot(monkeypatch):
    import scripts.test_understanding_v2_benchmark as runner

    page = {"page_type": "news_press", "produces_records": False, "offering_type": "non_robot"}
    monkeypatch.setattr(runner, "extract_robot_taxonomy",
                        lambda **_: {"page": page, "products": [], "extraction_metadata": {"tokens_used": 3}})
    extracted, metadata = runner.extract_robot_taxonomy_values("https://news.example", "text")
    assert extracted["offering_type"] == "non_robot" and extracted["primary_class"] == ""
    assert metadata["page"] == page and metadata["product_names"] == []
