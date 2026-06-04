"""Learned signal ontology store and validation."""
from app.services.learned_signal_ontology import (
    extract_heuristic_candidates,
    merge_candidates_into_store,
    validate_ontology_term,
    validate_word_shape,
)


def test_validate_ontology_term_rejects_noise():
    assert not validate_ontology_term("the")
    assert validate_ontology_term("staffing shortage", bucket="buying_phrases")


def test_validate_word_shape_requires_compilable_regex():
    assert validate_word_shape(r"(?i)\bdeployed\s+\d+\s+robots?\b")
    assert not validate_word_shape("[")


def test_heuristic_extracts_procurement_phrase():
    text = (
        "Acme Logistics issued an RFP for warehouse AMR vendors. "
        "Capital expenditure of $4M is approved for automation within 6 months."
    )
    out = extract_heuristic_candidates(text, industry="Logistics")
    assert out["buying_phrases"] or out["capex_financial_signals"] or out["trigger_expressions"]
    assert out["word_shapes"]


def test_merge_candidates_dedupes():
    store = {"buckets": {"pain_words": ["shortage"], "buying_phrases": [], "trigger_expressions": [],
                         "job_title_signals": [], "capex_financial_signals": [],
                         "expansion_facility_signals": [], "regulatory_compliance_signals": []},
             "word_shapes": [], "stats": {}}
    added = merge_candidates_into_store(
        store,
        {"pain_words": ["shortage", "turnover"], "buying_phrases": ["warehouse automation"]},
        source_company_id=1,
    )
    assert added == 2
    assert "turnover" in store["buckets"]["pain_words"]
