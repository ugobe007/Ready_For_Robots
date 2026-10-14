import pytest

from scripts.test_understanding_v2_benchmark import (
    names_match,
    normalize_benchmark,
    score_gap_probe,
    score_negative_control,
    select_target_record,
    summarize,
)

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


def test_gap_probe_without_form_key_skips_form():
    probe = {k: v for k, v in PROBE.items() if k != "form_ok"}
    gap = score_gap_probe(_extracted("Surgical robot."), probe)
    assert "form" not in gap["fields"] and gap["gap_pass"] is True


def test_forbid_must_not_probe_fails_when_forbidden_industry_tagged():
    probe = {"id": "gp2-01", "offering_type_ok": ["autonomy_software"], "industries_required": [],
             "industries_must_not": ["grocery", "restaurant"]}
    notes = "Automotive and mobility customers have no industry value."
    clean = score_gap_probe(_extracted(notes, industries=[]), probe)
    tagged = score_gap_probe(_extracted(notes, industries=[{"value": "grocery"}]), probe)
    assert clean["gap_pass"] is True
    assert tagged["gap_named"] is True and tagged["gap_pass"] is False
    assert tagged["forbidden_industries_found"] == ["grocery"]


def test_negative_control_with_page_type_requires_match_and_zero_records():
    expected = {"page_type": "directory_or_multi_company", "offering_type": "non_robot"}
    page_only = {"page": {"page_type": "directory_or_multi_company"}, "product_names": []}
    assert score_negative_control({"offering_type": "non_robot"}, expected, page_only)["pass"] is True
    wrong_type = {"page": {"page_type": "manufacturer_product_page"}, "product_names": ["X"]}
    neg = score_negative_control({"offering_type": "robot_product"}, expected, wrong_type)
    assert neg["pass"] is False and len(neg["checks"]) == 3
    only_page_type = score_negative_control({}, {"page_type": "news_press"},
                                            {"page": {"page_type": "news_press"}, "product_names": []})
    assert only_page_type["pass"] is True


def test_summary_reports_page_type_per_entry():
    results = [
        {"id": "v2-01", "group": "robot", "bucket": "PASSED", "expected_page_type": "manufacturer_product_page",
         "metadata": {"page": {"page_type": "news_press"}}},
        {"id": "v2-02", "group": "robot", "bucket": "FETCH_FAILED", "expected_page_type": "manufacturer_product_page"},
        {"id": "gp2-01", "group": "gap_probe", "bucket": "GAP_NAMED", "expected_page_type": None,
         "gap_probe_score": {"fields": {}}, "metadata": {"page": {"page_type": "manufacturer_product_page"}}},
    ]
    s = summarize(results)
    assert s["robots"]["page_types"]["v2-01"] == {"expected": "manufacturer_product_page",
                                                  "assigned": "news_press", "match": False}
    assert s["robots"]["page_types"]["v2-02"]["assigned"] == "NOT READ"
    assert s["taxonomy_gap_probes"]["page_types"]["gp2-01"]["match"] is None


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


@pytest.mark.parametrize("target,name,expected", [
    ("Spot", "Spot", True),
    ("Vision 60", "Vision 60 (Q-UGV)", True),
    ("Skydio X10 / Dock", "X10", True),
    ("LIFTBOT scaffolding robot", "LIFTBOT™", True),
    ("UVD Robot", "UVD Robots", True),
    ("Geek+ warehouse robots", "Geek+ P800", False),
    ("TUG", "T3 Robot", False),
    ("Cartken delivery robots", "Cartken Hauler", False),
    ("UVD Robot", "Robot", False),
    ("Badger retail robot", "Badger Technologies Digital Teammate (Autonomous Retail Robot)", False),
])
def test_names_match(target, name, expected):
    assert names_match(target, name) is expected


def test_select_takes_first_match_in_extraction_order():
    products = [{"product_name": "X10 Dock"}, {"product_name": "Spot"}, {"product_name": "Spot Arm"}]
    assert select_target_record(products, "Spot") == 1
    assert select_target_record(products, "Skydio X10 / Dock") == 0
    assert select_target_record(products, "TUG") is None


def test_alias_match_takes_first_record_matching_target_or_any_alias():
    products = [{"product_name": "Geek+ P800"}, {"product_name": "OTTO 600"}, {"product_name": "OTTO 1500"}]
    assert select_target_record(products, "OTTO autonomous mobile robots") is None
    assert select_target_record(products, "OTTO autonomous mobile robots", ["OTTO 1500", "OTTO 600"]) == 1
    assert runner_module().matched_record_indexes(products, "OTTO AMRs", ["OTTO 600", "OTTO 1500"]) == [1, 2]


def runner_module():
    import scripts.test_understanding_v2_benchmark as runner
    return runner


def test_alias_matched_records_all_returned_and_first_is_scored(monkeypatch):
    runner = _fake_extract(monkeypatch, ["T3 Robot", "TUG", "Carrello"])
    extracted, meta = runner.extract_robot_taxonomy_values("u", "t", target_product="Aethon robots",
                                                           target_aliases=["TUG", "T3 Robot"])
    assert meta["matched_record_indexes"] == [0, 1]
    assert extracted["form"] == "form-T3 Robot"
    assert [r["form"] for r in meta["matched_records"]] == ["form-T3 Robot", "form-TUG"]
    assert meta["target_aliases"] == ["TUG", "T3 Robot"]


def _fake_snapshot(monkeypatch, runner, final_url="https://final.example/p", words=200):
    monkeypatch.setattr(runner, "load_snapshot", lambda _id: {
        "metadata": {"status_code": 200, "final_url": final_url, "fetch_date": "2026-10-14"},
        "text": "word " * words, "html": ""})


def test_target_not_on_page_is_separate_from_extraction_failure(monkeypatch):
    runner = runner_module()
    _fake_snapshot(monkeypatch, runner)
    called = []
    monkeypatch.setattr(runner, "extract_robot_taxonomy_values", lambda **kw: called.append(kw))
    r = runner.test_robot({"id": "v2-07", "company": "SwarmFarm Robotics", "url": "https://www.swarmfarm.com",
                           "target_product": "SwarmBot",
                           "target_not_on_page": "The saved page does not name SwarmBot."})
    assert r["bucket"] == "TARGET_NOT_ON_PAGE"
    assert called == []
    r["group"] = "robot"
    summary = summarize([r])["robots"]
    assert summary["target_not_on_page"] == {"v2-07": "The saved page does not name SwarmBot."}
    assert summary["failed"] == [] and summary["target_not_extracted"] == [] and summary["readable"] == 0


def test_unreadable_reason_in_key_is_fetch_failed_with_reason(monkeypatch):
    runner = runner_module()
    _fake_snapshot(monkeypatch, runner)
    called = []
    monkeypatch.setattr(runner, "extract_robot_taxonomy_values", lambda **kw: called.append(kw))
    r = runner.test_robot({"id": "v2-12", "company": "SafeAI", "url": "https://safeai.ai",
                           "target_product": "SafeAI autonomy", "unreadable_reason": "Acquired by Pronto"})
    assert r["bucket"] == "FETCH_FAILED" and r["unreadable_reason"] == "Acquired by Pronto"
    assert called == []
    r["group"] = "robot"
    assert summarize([r])["robots"]["unreadable_reasons"] == {"v2-12": "Acquired by Pronto"}


def test_runner_uses_snapshot_final_url_aliases_and_scores_all_matched(monkeypatch):
    runner = runner_module()
    _fake_snapshot(monkeypatch, runner)
    seen = {}
    rec = {"offering_type": "robot_product", "form": "amr", "primary_class": "logistics",
           "primary_function": {"value": "transport"}, "secondary_functions": [], "industries": []}
    other = {**rec, "form": "arm"}

    def fake(**kw):
        seen.update(kw)
        return rec, {"product_names": ["A", "B"], "matched_record_indexes": [0, 1],
                     "matched_records": [rec, other], "target_record_index": 0, "target_not_extracted": False}

    monkeypatch.setattr(runner, "extract_robot_taxonomy_values", fake)
    robot = {"id": "v2-11", "company": "ExRobotics", "url": "https://old.example", "target_product": "ExR",
             "target_aliases": ["ExR-2.5"], "offering_type_ok": ["robot_product"], "form_ok": ["amr"],
             "primary_class_ok": ["logistics"], "functions_required": [], "functions_any": [],
             "industries_required": [], "industries_any": []}
    r = runner.test_robot(robot)
    assert seen["url"] == "https://final.example/p" and r["url"] == "https://final.example/p"
    assert seen["target_aliases"] == ["ExR-2.5"]
    assert [s["form"]["pass"] for s in r["all_matched_scores"]] == [True, False]
    r["group"] = "robot"
    acc = summarize([r])["robots"]["per_field_accuracy_all_matched_records"]
    assert acc["form"] == {"pass": 1, "total": 2} and acc["offering_type"] == {"pass": 2, "total": 2}


def _fake_extract(monkeypatch, names, page_type="manufacturer_product_page"):
    import scripts.test_understanding_v2_benchmark as runner

    products = [{"product_name": n, "offering_type": {"value": "robot_product"}, "form": {"value": f"form-{n}"},
                 "primary_class": {"value": "x"}, "industries": []} for n in names]
    page = {"page_type": page_type, "produces_records": page_type == "manufacturer_product_page",
            "offering_type": "robot_product" if page_type == "manufacturer_product_page" else "non_robot"}
    monkeypatch.setattr(runner, "extract_robot_taxonomy",
                        lambda **_: {"page": page, "products": products, "extraction_metadata": {}})
    return runner


def test_scoring_uses_target_record_not_first(monkeypatch):
    runner = _fake_extract(monkeypatch, ["T3 Robot", "TUG", "Carrello"])
    extracted, meta = runner.extract_robot_taxonomy_values("u", "t", target_product="TUG")
    assert extracted["form"] == "form-TUG"
    assert meta["target_record_index"] == 1 and meta["target_not_extracted"] is False


def test_target_not_extracted_is_flagged_and_empty(monkeypatch):
    runner = _fake_extract(monkeypatch, ["T3 Robot", "Carrello"])
    extracted, meta = runner.extract_robot_taxonomy_values("u", "t", target_product="TUG")
    assert meta["target_not_extracted"] is True and meta["target_record_index"] is None
    assert extracted["form"] == "" and extracted["unclassified_notes"] == "target_not_extracted"
    assert meta["product_names"] == ["T3 Robot", "Carrello"]


def test_non_manufacturer_page_robot_is_target_not_extracted(monkeypatch):
    runner = _fake_extract(monkeypatch, [], page_type="news_press")
    extracted, meta = runner.extract_robot_taxonomy_values("u", "t", target_product="TUG")
    assert meta["target_not_extracted"] is True and extracted["offering_type"] == "non_robot"


def test_summary_lists_target_not_extracted_as_failure_type():
    results = [
        {"id": "v2-01", "group": "robot", "bucket": "TARGET_NOT_EXTRACTED", "score": None,
         "metadata": {"target_product": "Geek+ warehouse robots", "product_names": ["P800"], "target_record_index": None}},
        {"id": "v2-02", "group": "robot", "bucket": "PASSED", "score": None, "metadata": {}},
        {"id": "gp2-01", "group": "gap_probe", "bucket": "TARGET_NOT_EXTRACTED"},
    ]
    s = summarize(results)
    assert s["robots"]["target_not_extracted"] == ["v2-01"]
    assert "v2-01" in s["robots"]["failed"] and s["robots"]["passed"] == ["v2-02"]
    assert s["robots"]["target_records"]["v2-01"]["records"] == ["P800"]
    assert s["taxonomy_gap_probes"]["verdicts"] == {"gp2-01": "TARGET_NOT_EXTRACTED"}


def test_page_type_only_result_flattens_to_non_robot(monkeypatch):
    import scripts.test_understanding_v2_benchmark as runner

    page = {"page_type": "news_press", "produces_records": False, "offering_type": "non_robot"}
    monkeypatch.setattr(runner, "extract_robot_taxonomy",
                        lambda **_: {"page": page, "products": [], "extraction_metadata": {"tokens_used": 3}})
    extracted, metadata = runner.extract_robot_taxonomy_values("https://news.example", "text")
    assert extracted["offering_type"] == "non_robot" and extracted["primary_class"] == ""
    assert metadata["page"] == page and metadata["product_names"] == []


def test_runner_reads_products_and_still_accepts_robots():
    assert normalize_benchmark({"products": [{"id": "p1"}]})["robots"] == [{"id": "p1"}]
    assert normalize_benchmark({"robots": [{"id": "r1"}]})["robots"] == [{"id": "r1"}]
    both = normalize_benchmark({"products": [{"id": "p1"}], "robots": [{"id": "r1"}]})
    assert [e["id"] for e in both["robots"]] == ["p1", "r1"]
