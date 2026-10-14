"""
Taxonomy-based benchmark scoring (v2).

Replaces free-text capability scoring with exact-match validation against
closed taxonomy lists. Every field is scored independently, so per-field
accuracy shows WHERE an extractor is weak.

Scorer is FROZEN after calibration. No tuning against regex/semantic results.
"""
import json
from pathlib import Path
from typing import Any


TAXONOMY_PATH = Path("tests/fixtures/taxonomy.v1.json")


def load_taxonomy() -> dict[str, Any]:
    """Load the taxonomy (single source of truth)."""
    with open(TAXONOMY_PATH) as f:
        return json.load(f)


def score_offering_type(extracted: str, expected: list[str]) -> tuple[bool, str]:
    """
    Score offering_type field.
    
    Returns:
        (passed, reason)
    """
    if not extracted:
        return False, "offering_type is empty"
    
    if extracted in expected:
        return True, f"offering_type '{extracted}' matches expected"
    
    return False, f"offering_type '{extracted}' not in {expected}"


def score_form(extracted: str, expected: list[str]) -> tuple[bool, str]:
    """
    Score form field.
    
    Returns:
        (passed, reason)
    """
    if not extracted:
        return False, "form is empty"
    
    if extracted in expected:
        return True, f"form '{extracted}' matches expected"
    
    return False, f"form '{extracted}' not in {expected}"


def score_primary_class(extracted: str, expected: list[str]) -> tuple[bool, str]:
    """
    Score primary_class field.
    
    First value in expected is preferred; others are acceptable alternates.
    
    Returns:
        (passed, reason)
    """
    if not extracted:
        return False, "primary_class is empty"
    
    if extracted in expected:
        is_preferred = extracted == expected[0]
        reason = f"primary_class '{extracted}' matches expected"
        if not is_preferred:
            reason += f" (alternate; preferred is '{expected[0]}')"
        return True, reason
    
    return False, f"primary_class '{extracted}' not in {expected}"


def score_functions(
    extracted: list[str],
    required: list[str],
    ok_extra: list[str]
) -> tuple[bool, str, dict]:
    """
    Score functions field.
    
    PASS if:
    - Every required function is extracted
    - Every extracted function is in (required + ok_extra)
    
    Returns:
        (passed, reason, details)
    """
    if not extracted:
        return False, "functions is empty", {}
    
    extracted_set = set(extracted)
    required_set = set(required)
    allowed_set = required_set | set(ok_extra)
    
    missing = required_set - extracted_set
    invalid = extracted_set - allowed_set
    
    details = {
        "extracted": list(extracted_set),
        "required": required,
        "ok_extra": ok_extra,
        "missing": list(missing),
        "invalid": list(invalid),
    }
    
    if missing:
        return False, f"missing required functions: {list(missing)}", details
    
    if invalid:
        return False, f"invalid functions: {list(invalid)}", details
    
    return True, f"all required functions extracted, no invalid", details


def score_industries(
    extracted: list[str],
    required: list[str],
    any_of: list[str],
    must_not: list[str],
    ok_extra: list[str]
) -> tuple[bool, str, dict]:
    """
    Score industries field.
    
    PASS if:
    - Every required industry is extracted
    - (any_of is empty OR at least one of any_of is extracted)
    - None of must_not is extracted
    - Extra industries not in ok_extra are logged but not penalized
    
    Returns:
        (passed, reason, details)
    """
    extracted_set = set(extracted)
    required_set = set(required)
    any_of_set = set(any_of)
    must_not_set = set(must_not)
    ok_extra_set = set(ok_extra)
    
    missing_required = required_set - extracted_set
    forbidden_found = extracted_set & must_not_set
    unexpected = extracted_set - (required_set | any_of_set | ok_extra_set)
    
    details = {
        "extracted": list(extracted_set),
        "required": required,
        "any_of": any_of,
        "must_not": must_not,
        "ok_extra": ok_extra,
        "missing_required": list(missing_required),
        "forbidden_found": list(forbidden_found),
        "unexpected": list(unexpected),
    }
    
    if missing_required:
        return False, f"missing required industries: {list(missing_required)}", details
    
    if any_of and not (extracted_set & any_of_set):
        return False, f"none of any_of found: {any_of}", details
    
    if forbidden_found:
        return False, f"forbidden industries found: {list(forbidden_found)}", details
    
    # Unexpected industries are logged but not penalized
    reason = "all required industries met"
    if any_of:
        found_any = list(extracted_set & any_of_set)
        reason += f", at least one of any_of found: {found_any}"
    if unexpected:
        reason += f" (unexpected extras: {list(unexpected)})"
    
    return True, reason, details


def score_robot(
    extracted: dict[str, Any],
    expected: dict[str, Any]
) -> dict[str, Any]:
    """
    Score one robot against expected taxonomy values.
    
    Returns:
        {
            "offering_type": {"pass": bool, "reason": str},
            "form": {"pass": bool, "reason": str},
            "primary_class": {"pass": bool, "reason": str},
            "functions": {"pass": bool, "reason": str, "details": dict},
            "industries": {"pass": bool, "reason": str, "details": dict},
            "robot_pass": bool,
        }
    """
    # Score offering_type
    offering_pass, offering_reason = score_offering_type(
        extracted.get("offering_type", ""),
        expected["offering_type_ok"]
    )
    
    # Score form
    form_pass, form_reason = score_form(
        extracted.get("form", ""),
        expected["form_ok"]
    )
    
    # Score primary_class
    primary_pass, primary_reason = score_primary_class(
        extracted.get("primary_class", ""),
        expected["primary_class_ok"]
    )
    
    # Score functions
    extracted_functions = [f["value"] if isinstance(f, dict) else f
                           for f in extracted.get("functions", [])]
    functions_pass, functions_reason, functions_details = score_functions(
        extracted_functions,
        expected["functions_required"],
        expected.get("functions_ok", [])
    )
    
    # Score industries
    extracted_industries = [i["value"] if isinstance(i, dict) else i
                            for i in extracted.get("industries", [])]
    industries_pass, industries_reason, industries_details = score_industries(
        extracted_industries,
        expected["industries_required"],
        expected.get("industries_any", []),
        expected.get("industries_must_not", []),
        expected.get("industries_ok_extra", [])
    )
    
    # Overall robot pass: all five fields must pass
    robot_pass = all([
        offering_pass,
        form_pass,
        primary_pass,
        functions_pass,
        industries_pass,
    ])
    
    return {
        "offering_type": {"pass": offering_pass, "reason": offering_reason},
        "form": {"pass": form_pass, "reason": form_reason},
        "primary_class": {"pass": primary_pass, "reason": primary_reason},
        "functions": {"pass": functions_pass, "reason": functions_reason, "details": functions_details},
        "industries": {"pass": industries_pass, "reason": industries_reason, "details": industries_details},
        "robot_pass": robot_pass,
    }


def compute_per_field_accuracy(results: list[dict]) -> dict[str, float]:
    """
    Compute per-field accuracy across all robots.
    
    Shows WHERE an extractor is weak.
    
    Returns:
        {
            "offering_type": float (0-1),
            "form": float,
            "primary_class": float,
            "functions": float,
            "industries": float,
            "overall": float,
        }
    """
    if not results:
        return {}
    
    # Filter out fetch failures and rows with no valid score
    extraction_results = [r for r in results if r.get("bucket") != "FETCH_FAILED" and r.get("score") is not None]
    
    if not extraction_results:
        return {}
    
    field_totals = {
        "offering_type": 0,
        "form": 0,
        "primary_class": 0,
        "functions": 0,
        "industries": 0,
    }
    
    for result in extraction_results:
        score = result.get("score", {})
        for field in field_totals:
            if score.get(field, {}).get("pass"):
                field_totals[field] += 1
    
    n = len(extraction_results)
    accuracy = {field: count / n for field, count in field_totals.items()}
    
    # Overall = all fields pass
    overall_pass = sum(1 for r in extraction_results if r.get("score", {}).get("robot_pass"))
    accuracy["overall"] = overall_pass / n
    
    return accuracy
