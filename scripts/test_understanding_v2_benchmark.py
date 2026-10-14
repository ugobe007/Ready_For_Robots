"""
Taxonomy-based benchmark runner (v2).

Tests extraction against robot_benchmark_set.v2.json using exact-match
taxonomy validation. Scorer is FROZEN - no tuning against results.

Usage:
    python3 scripts/test_understanding_v2_benchmark.py
    python3 scripts/test_understanding_v2_benchmark.py --robot hc-01
"""
import json
import re
import sys
import time
from pathlib import Path
from typing import Any

from app.services.robot_understanding_v1.industries import with_parents
from app.services.robot_understanding_v1.taxonomy_extraction import extract_robot_taxonomy
from scripts.benchmark_scoring_v2 import (
    score_robot,
    score_offering_type,
    score_form,
    score_primary_class,
    score_industries,
    compute_per_field_accuracy,
    load_taxonomy,
)


BENCHMARK_PATH = Path("tests/fixtures/robot_benchmark_set.v2.json")
FIXTURES_DIR = Path("tests/fixtures/robot_pages")
THIN_CONTENT_WORD_THRESHOLD = 150
GROUPS = (("robots", "robot"), ("taxonomy_gap_probes", "gap_probe"), ("negative_controls", "negative_control"))
SCORED_FIELDS = ("offering_type", "form", "primary_class", "functions", "industries")
UNSUPPORTED_FIELDS = ("offering_type", "form", "primary_class", "primary_function", "secondary_functions", "industries")

# Fixed before each hold-out run. Automated first pass only; the verbatim
# unclassified_notes are saved for a human to confirm the gap is named.
# forbid_must_not: the key's PASS rule also requires no industries_must_not value.
GAP_RULES = {
    "gp-01": {"terms": ("lab automation", "laboratory automation", "liquid handling", "liquid-handling", "pipett")},
    "gp-02": {"terms": ("surgery", "surgical")},
    "gp2-01": {"terms": ("automotive", "automaker", "auto maker", "car maker", "carmaker", "mobility"),
               "forbid_must_not": True},
    "gp2-02": {"terms": ("exoskeleton", "wearable")},
    "gp2-03": {"terms": ("research", "education", "developer platform", "development platform")},
}


def load_benchmark() -> dict[str, Any]:
    """Load the v2 benchmark."""
    with open(BENCHMARK_PATH, 'r') as f:
        return json.load(f)


def load_snapshot(robot_id: str) -> dict[str, Any] | None:
    """Load cached page snapshot."""
    snapshot_dir = FIXTURES_DIR / robot_id
    if not snapshot_dir.exists():
        return None
    
    metadata_path = snapshot_dir / "metadata.json"
    html_path = snapshot_dir / "page.html"
    text_path = snapshot_dir / "page.txt"
    
    if not metadata_path.exists():
        return None
    
    with open(metadata_path, "r") as f:
        metadata = json.load(f)
    
    html = ""
    if html_path.exists():
        with open(html_path, "r", encoding="utf-8") as f:
            html = f.read()
    
    text = ""
    if text_path.exists():
        with open(text_path, "r", encoding="utf-8") as f:
            text = f.read()
    
    return {
        "metadata": metadata,
        "html": html,
        "text": text,
    }


GENERIC_NAME_TOKENS = {"a", "an", "the", "and", "of", "robot", "robotic", "robotics", "system", "serie", "autonomous"}


def name_tokens(name: str) -> list[str]:
    """Lowercase alphanumeric tokens; ™/®/punctuation dropped; a trailing plural 's' removed."""
    tokens = re.findall(r"[a-z0-9]+", re.sub(r"[™®©]", "", (name or "").lower()))
    return [t[:-1] if len(t) > 3 and t.endswith("s") and not t.endswith("ss") else t for t in tokens]


def names_match(target: str, name: str) -> bool:
    """Equal token lists, or one is a contiguous run inside the other that is not only generic words."""
    t, n = name_tokens(target), name_tokens(name)
    if not t or not n:
        return False
    if t == n:
        return True
    short, long_ = (n, t) if len(n) <= len(t) else (t, n)
    if all(tok in GENERIC_NAME_TOKENS for tok in short):
        return False
    return any(long_[i:i + len(short)] == short for i in range(len(long_) - len(short) + 1))


def matched_record_indexes(products: list[dict[str, Any]], target: str, aliases: list[str] = ()) -> list[int]:
    """Records, in extraction order, whose name matches target_product or any target_alias."""
    names = [target, *aliases]
    return [i for i, p in enumerate(products)
            if any(names_match(n, p.get("product_name", "")) for n in names)]


def select_target_record(products: list[dict[str, Any]], target: str, aliases: list[str] = ()) -> int | None:
    """The first matching record is the one the entry is scored on."""
    matched = matched_record_indexes(products, target, aliases)
    return matched[0] if matched else None


def _empty_extraction(offering_type: str, note: str) -> dict[str, Any]:
    return {
        "offering_type": offering_type,
        "form": "",
        "primary_class": "",
        "primary_function": {},
        "secondary_functions": [],
        "industries": [],
        "unsupported_facts": [],
        "unclassified_notes": note,
    }


def extract_robot_taxonomy_values(
    url: str,
    page_text: str,
    product_name_hint: str | None = None,
    target_product: str | None = None,
    target_aliases: list[str] = (),
) -> tuple[dict[str, Any], dict[str, Any]]:
    """
    Extract taxonomy values using semantic extraction.
    
    Returns:
        (extracted_values, metadata)
        
    extracted_values format:
        {
            "offering_type": str,
            "form": str,
            "primary_class": str,
            "primary_function": {"value": str, "confidence": float, "evidence": str},
            "secondary_functions": [{"value": str, "confidence": float, "evidence": str}],
            "industries": [{"value": str, "confidence": float, "evidence": str}],
            "unclassified_notes": str
        }
    """
    result = extract_robot_taxonomy(
        url=url,
        page_text=page_text,
        product_name_hint=product_name_hint,
        cache_key_extra="v1"
    )
    
    products = result.get("products", [])
    page = result.get("page")
    metadata = {**result.get("extraction_metadata", {}),
                "page": page,
                "product_names": [p.get("product_name", "") for p in products]}
    page_offering = (page or {}).get("offering_type", "")
    if target_product is not None:
        matched = matched_record_indexes(products, target_product, target_aliases)
        metadata["target_product"] = target_product
        metadata["target_aliases"] = list(target_aliases)
        metadata["matched_record_indexes"] = matched
        metadata["matched_records"] = [_flatten_product(products[i]) for i in matched]
        metadata["target_record_index"] = matched[0] if matched else None
        metadata["target_not_extracted"] = not matched
        if not matched:
            return _empty_extraction(page_offering if not products else "", "target_not_extracted"), metadata
        return metadata["matched_records"][0], metadata
    if not products:
        return _empty_extraction(page_offering, "No products extracted"), metadata
    return _flatten_product(products[0]), metadata


def _flatten_product(product: dict[str, Any]) -> dict[str, Any]:
    """Unsupported single-value fields arrive as None and score as empty."""
    def value(field: str) -> str:
        fact = product.get(field)
        return fact.get("value", "") if isinstance(fact, dict) else ""

    return {
        "offering_type": value("offering_type"),
        "form": value("form"),
        "primary_class": value("primary_class"),
        "primary_function": product.get("primary_function") or {},
        "secondary_functions": product.get("secondary_functions", []),
        "industries": product.get("industries", []),
        "unsupported_facts": product.get("unsupported_facts", []),
        "unclassified_notes": product.get("unclassified_notes", ""),
    }


def score_negative_control(
    extracted: dict[str, Any], expected: dict[str, Any], metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Check only the fields the answer key states for a control.

    When the key states a page_type, the control must also produce no robot record.
    `buyer_matches` is not checkable here because this runner does no matching.
    """
    metadata = metadata or {}
    checks = []
    passed = True
    for field in ("offering_type", "primary_class"):
        if field in expected:
            ok = extracted.get(field) == expected[field]
            passed = passed and ok
            checks.append(f"{field}={extracted.get(field)!r} expected {expected[field]!r} -> {'ok' if ok else 'FAIL'}")
    if "page_type" in expected:
        assigned = (metadata.get("page") or {}).get("page_type")
        ok = assigned == expected["page_type"]
        passed = passed and ok
        checks.append(f"page_type={assigned!r} expected {expected['page_type']!r} -> {'ok' if ok else 'FAIL'}")
        records = metadata.get("product_names", [])
        ok = not records
        passed = passed and ok
        checks.append(f"robot records={len(records)} expected 0 -> {'ok' if ok else 'FAIL'}")
    if not checks:
        return {"pass": False, "checks": ["no checkable taxonomy fields in answer key"]}
    if "buyer_matches" in expected:
        checks.append("buyer_matches not checked (no matching in this runner)")
    return {"pass": passed, "checks": checks}


def score_gap_probe(extracted: dict[str, Any], probe: dict[str, Any]) -> dict[str, Any]:
    """Probe passes if unclassified_notes names the gap. Taxonomy fields the
    key states are scored with the frozen scorer and reported beside it;
    functions are never scored on a probe."""
    notes = (extracted.get("unclassified_notes") or "").lower()
    rule = GAP_RULES.get(probe["id"], {})
    terms = rule.get("terms", ())
    hits = [t for t in terms if t in notes]
    fields = {}
    if "offering_type_ok" in probe:
        ok, reason = score_offering_type(extracted.get("offering_type", ""), probe["offering_type_ok"])
        fields["offering_type"] = {"pass": ok, "reason": reason}
    if "form_ok" in probe:
        ok, reason = score_form(extracted.get("form", ""), probe["form_ok"])
        fields["form"] = {"pass": ok, "reason": reason}
    if "primary_class_ok" in probe:
        ok, reason = score_primary_class(extracted.get("primary_class", ""), probe["primary_class_ok"])
        fields["primary_class"] = {"pass": ok, "reason": reason}
    industries = [i["value"] if isinstance(i, dict) else i for i in extracted.get("industries", [])]
    ok, reason, _ = score_industries(
        industries, probe["industries_required"], probe.get("industries_any", []),
        probe.get("industries_must_not", []), probe.get("industries_ok_extra", []),
    )
    fields["industries"] = {"pass": ok, "reason": reason}
    forbidden = sorted(with_parents(industries) & set(probe.get("industries_must_not", [])))
    gap_pass = bool(hits) and not (rule.get("forbid_must_not") and forbidden)
    return {
        "gap_pass": gap_pass,
        "gap_named": bool(hits),
        "forbidden_industries_found": forbidden,
        "forbid_must_not": bool(rule.get("forbid_must_not")),
        "gap_terms_matched": hits,
        "gap_terms_checked": list(terms),
        "unclassified_notes": extracted.get("unclassified_notes", ""),
        "fields": fields,
    }


def test_robot(
    robot: dict[str, Any],
    use_product_hint: bool = False,
    group: str | None = None,
) -> dict[str, Any]:
    """
    Test one robot and return taxonomy-based scores.
    
    Returns:
        {
            "id": str,
            "company": str,
            "url": str,
            "bucket": "FETCH_FAILED" | "EXTRACTION_FAILED" | "PASSED",
            "score": dict (from score_robot),
            "extracted": dict (taxonomy values),
            "elapsed_sec": float,
            "used_product_hint": bool,
        }
    """
    robot_id = robot['id']
    url = robot['url']
    
    # Handle negative controls which have different structure
    group = group or ('negative_control' if 'expected' in robot else 'robot')
    is_negative_control = group == 'negative_control'
    is_gap_probe = group == 'gap_probe'
    if is_negative_control:
        product_name = None
        display_name = robot.get('description', robot_id)
    else:
        product_name = robot.get('target_product') if use_product_hint else None
        display_name = f"{robot.get('company', 'Unknown')} - {robot.get('target_product', 'Unknown')}"
    
    print(f"\n{'='*80}")
    print(f"Testing {robot_id}: {display_name}")
    print(f"URL: {url}")
    if use_product_hint and product_name:
        print(f"Product hint: {product_name}")
    
    # Load snapshot
    snapshot = load_snapshot(robot_id)
    
    if snapshot is None:
        print(f"❌ FETCH FAILED: No snapshot found for {robot_id}")
        return {
            'id': robot_id,
            'company': robot.get('company', ''),
            'url': url,
            'bucket': 'FETCH_FAILED',
            'fetch_error': 'No snapshot found',
            'used_product_hint': use_product_hint,
        }
    
    # Check snapshot status
    metadata = snapshot['metadata']
    page_text = snapshot['text']

    if robot.get('unreadable_reason'):
        print(f"⚠️  Unreadable per answer key: {robot['unreadable_reason']}")
        return {
            'id': robot_id,
            'company': robot.get('company', ''),
            'url': metadata.get('final_url') or url,
            'bucket': 'FETCH_FAILED',
            'fetch_error': 'unreadable_reason',
            'unreadable_reason': robot['unreadable_reason'],
            'snapshot_date': metadata.get('fetch_date'),
            'used_product_hint': use_product_hint,
        }

    if robot.get('target_not_on_page'):
        reason = robot['target_not_on_page']
        print(f"⚠️  target_not_on_page: {reason}")
        return {
            'id': robot_id,
            'company': robot.get('company', ''),
            'url': metadata.get('final_url') or url,
            'bucket': 'TARGET_NOT_ON_PAGE',
            'target_not_on_page': reason,
            'snapshot_date': metadata.get('fetch_date'),
            'used_product_hint': use_product_hint,
        }
    
    if metadata.get('status_code') != 200:
        error_msg = metadata.get('error', 'Unknown error')
        print(f"⚠️  Snapshot fetch failed: HTTP {metadata.get('status_code')} - {error_msg[:80]}")
        return {
            'id': robot_id,
            'company': robot.get('company', ''),
            'url': url,
            'bucket': 'FETCH_FAILED',
            'fetch_error': error_msg,
            'snapshot_date': metadata.get('fetch_date'),
            'used_product_hint': use_product_hint,
        }
    
    word_count = len(page_text.strip().split())
    if word_count < THIN_CONTENT_WORD_THRESHOLD:
        print(f"⚠️  Snapshot has thin content ({word_count} words)")
        return {
            'id': robot_id,
            'company': robot.get('company', ''),
            'url': url,
            'bucket': 'FETCH_FAILED',
            'fetch_error': f'Thin content ({word_count} words)',
            'snapshot_date': metadata.get('fetch_date'),
            'used_product_hint': use_product_hint,
        }
    
    html = snapshot['html']
    metadata_snapshot = snapshot['metadata']
    url = metadata_snapshot.get('final_url') or url
    target_aliases = [] if is_negative_control else list(robot.get('target_aliases', []))
    print(f"Using snapshot ({word_count} words, fetched {metadata_snapshot.get('fetch_date', 'unknown')}, final URL {url})")
    if target_aliases:
        print(f"Target aliases: {target_aliases}")
    
    # Run extraction
    try:
        t0 = time.time()
        
        extracted, metadata = extract_robot_taxonomy_values(
            url=url,
            page_text=page_text,
            product_name_hint=product_name,
            target_product=None if is_negative_control else robot.get('target_product'),
            target_aliases=target_aliases,
        )
        
        elapsed = time.time() - t0
        
        print(f"\nExtraction time: {elapsed:.1f}s")
        print(f"Tokens: {metadata.get('tokens_used', 0)} ({metadata.get('input_tokens', 0)} in, {metadata.get('output_tokens', 0)} out)")
        if metadata.get('page'):
            print(f"Page type: {metadata['page'].get('page_type')}  records: {metadata.get('product_names')}")
        print(f"Extracted: offering_type={extracted.get('offering_type', 'N/A')}, "
              f"form={extracted.get('form', 'N/A')}, "
              f"primary_class={extracted.get('primary_class', 'N/A')}")
        
        primary_func = extracted.get('primary_function', {})
        primary_func_value = primary_func.get('value') if isinstance(primary_func, dict) else primary_func
        
        secondary_funcs = extracted.get('secondary_functions', [])
        secondary_func_values = [f.get('value') if isinstance(f, dict) else f for f in secondary_funcs]
        
        functions_display = f"[{primary_func_value}]"
        if secondary_func_values:
            functions_display += f" + secondaries: {secondary_func_values}"
        
        industries_list = [i.get('value') if isinstance(i, dict) else i 
                           for i in extracted.get('industries', [])]
        
        print(f"Functions: {functions_display}")
        print(f"Industries: {industries_list}")
        
        if extracted.get('unclassified_notes'):
            print(f"Unclassified notes: {extracted['unclassified_notes']}")
        
        # Score against expected (only for regular robots, not negative controls)
        gap = None
        all_matched_scores = None
        if not is_negative_control:
            idx = metadata.get('target_record_index')
            print(f"Target record: {'NOT EXTRACTED' if idx is None else repr(metadata['product_names'][idx])}")
            print(f"Matched records: {[metadata['product_names'][i] for i in metadata.get('matched_record_indexes', [])]}")
        if not is_negative_control and metadata.get('target_not_extracted'):
            score = None
            bucket = 'TARGET_NOT_EXTRACTED'
            print(f"❌ target_not_extracted: {robot.get('target_product')!r} not among {metadata.get('product_names')}")
        elif is_gap_probe:
            score = None
            gap = score_gap_probe(extracted, robot)
            bucket = 'GAP_NAMED' if gap['gap_pass'] else 'GAP_NOT_NAMED'
            print(f"{'✅' if gap['gap_pass'] else '❌'} Gap probe: matched {gap['gap_terms_matched']}"
                  + (f", forbidden industries {gap['forbidden_industries_found']}" if gap['forbid_must_not'] else ""))
            for field, fs in gap['fields'].items():
                print(f"  {field}: {'ok' if fs['pass'] else 'FAIL'} ({fs['reason']})")
        elif not is_negative_control:
            score = score_robot(extracted, robot)
            all_matched_scores = [score_robot(rec, robot) for rec in metadata.get('matched_records', [])]
            
            bucket = 'PASSED' if score['robot_pass'] else 'EXTRACTION_FAILED'
            
            if score['robot_pass']:
                print(f"✅ PASSED")
            else:
                print(f"❌ FAILED:")
                for field in ['offering_type', 'form', 'primary_class', 'functions', 'industries']:
                    field_score = score[field]
                    if not field_score['pass']:
                        print(f"  - {field}: {field_score['reason']}")
        else:
            score = None
            neg = score_negative_control(extracted, robot['expected'], metadata)
            bucket = 'NEG_PASS' if neg['pass'] else 'NEG_FAIL'
            print(f"{'✅' if neg['pass'] else '❌'} Negative control: {'; '.join(neg['checks'])}")
        
        return {
            'id': robot_id,
            'company': robot.get('company', ''),
            'description': robot.get('description', ''),
            'url': url,
            'bucket': bucket,
            'score': score,
            'all_matched_scores': all_matched_scores,
            'extracted': extracted,
            'metadata': metadata,
            'snapshot_date': metadata_snapshot.get('fetch_date'),
            'elapsed_sec': elapsed,
            'used_product_hint': use_product_hint,
            'is_negative_control': is_negative_control,
            'negative_control_score': neg if is_negative_control else None,
            'gap_probe_score': gap,
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'id': robot_id,
            'company': robot.get('company', ''),
            'description': robot.get('description', ''),
            'url': url,
            'bucket': 'EXTRACTION_FAILED',
            'error': str(e),
            'snapshot_date': snapshot['metadata'].get('fetch_date') if snapshot else None,
            'used_product_hint': use_product_hint,
            'is_negative_control': is_negative_control,
        }


def unsupported_by_field(results: list[dict[str, Any]]) -> dict[str, int]:
    """Count facts the evidence policy blanked or dropped, by field."""
    counts = {f: 0 for f in UNSUPPORTED_FIELDS}
    for r in results:
        for fact in (r.get('extracted') or {}).get('unsupported_facts') or []:
            counts[fact.get('field', 'unknown')] = counts.get(fact.get('field', 'unknown'), 0) + 1
    return counts


def per_field_accuracy_all_matched(results: list[dict[str, Any]]) -> dict[str, dict[str, int]]:
    """Pass/total per field over every alias-matched record, not just the scored first one."""
    out = {f: {'pass': 0, 'total': 0} for f in SCORED_FIELDS}
    for r in results:
        for s in r.get('all_matched_scores') or []:
            for f in SCORED_FIELDS:
                out[f]['total'] += 1
                out[f]['pass'] += bool(s[f]['pass'])
    return out


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Robots, gap probes and negative controls are summarized separately, never pooled."""
    by_group = {g: [r for r in results if r.get('group') == g] for _, g in GROUPS}
    robots = by_group['robot']
    readable = [r for r in robots if r.get('bucket') not in ('FETCH_FAILED', 'TARGET_NOT_ON_PAGE')]

    def verdict(r: dict[str, Any], pass_bucket: str) -> str:
        if r.get('bucket') == 'FETCH_FAILED':
            return 'NOT READ'
        if 'error' in r:
            return 'CRASHED'
        if r.get('bucket') == 'TARGET_NOT_EXTRACTED':
            return 'TARGET_NOT_EXTRACTED'
        return 'PASS' if r.get('bucket') == pass_bucket else 'FAIL'

    def page_types(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
        out = {}
        for r in rows:
            assigned = ((r.get('metadata') or {}).get('page') or {}).get('page_type')
            expected = r.get('expected_page_type')
            out[r['id']] = {
                'expected': expected,
                'assigned': 'NOT READ' if r.get('bucket') == 'FETCH_FAILED' else assigned,
                'match': None if expected is None or r.get('bucket') == 'FETCH_FAILED' else assigned == expected,
            }
        return out

    return {
        'robots': {
            'total': len(robots),
            'unreadable': [r['id'] for r in robots if r.get('bucket') == 'FETCH_FAILED'],
            'unreadable_reasons': {r['id']: r.get('unreadable_reason') or r.get('fetch_error')
                                   for r in robots if r.get('bucket') == 'FETCH_FAILED'},
            'target_not_on_page': {r['id']: r.get('target_not_on_page')
                                   for r in robots if r.get('bucket') == 'TARGET_NOT_ON_PAGE'},
            'readable': len(readable),
            'crashed': [r['id'] for r in readable if 'error' in r],
            'passed': [r['id'] for r in readable if r.get('bucket') == 'PASSED'],
            'failed': [r['id'] for r in readable if r.get('bucket') != 'PASSED'],
            'target_not_extracted': [r['id'] for r in readable if r.get('bucket') == 'TARGET_NOT_EXTRACTED'],
            'target_records': {r['id']: {'target': (r.get('metadata') or {}).get('target_product'),
                                         'records': (r.get('metadata') or {}).get('product_names'),
                                         'aliases': (r.get('metadata') or {}).get('target_aliases'),
                                         'matched_indexes': (r.get('metadata') or {}).get('matched_record_indexes'),
                                         'index': (r.get('metadata') or {}).get('target_record_index')}
                               for r in readable if 'metadata' in r},
            'per_field_accuracy': compute_per_field_accuracy(robots),
            'per_field_accuracy_all_matched_records': per_field_accuracy_all_matched(robots),
            'unsupported_by_field': unsupported_by_field(robots),
            'page_types': page_types(robots),
        },
        'taxonomy_gap_probes': {
            'verdicts': {r['id']: verdict(r, 'GAP_NAMED') for r in by_group['gap_probe']},
            'fields': {r['id']: {f: v['pass'] for f, v in r['gap_probe_score']['fields'].items()}
                       for r in by_group['gap_probe'] if r.get('gap_probe_score')},
            'unsupported_by_field': unsupported_by_field(by_group['gap_probe']),
            'page_types': page_types(by_group['gap_probe']),
        },
        'negative_controls': {
            'verdicts': {r['id']: verdict(r, 'NEG_PASS') for r in by_group['negative_control']},
            'unsupported_by_field': unsupported_by_field(by_group['negative_control']),
            'checks': {r['id']: (r.get('negative_control_score') or {}).get('checks', [r.get('error') or r.get('fetch_error')])
                       for r in by_group['negative_control']},
            'page_types': page_types(by_group['negative_control']),
        },
    }


def main():
    """Run the v2 benchmark."""
    import argparse
    global BENCHMARK_PATH, FIXTURES_DIR

    parser = argparse.ArgumentParser(description="Run Understanding v2 benchmark (taxonomy-based)")
    parser.add_argument("--robot", type=str, help="Test a specific robot by ID")
    parser.add_argument("--hint", choices=["on", "off"], default="on",
                        help="Pass the answer key's target_product to the extractor")
    parser.add_argument("--benchmark", type=Path, default=BENCHMARK_PATH)
    parser.add_argument("--fixtures", type=Path, default=FIXTURES_DIR)
    parser.add_argument("--output", type=Path,
                        default=Path("reports") / "understanding_v2_benchmark_results.json")
    args = parser.parse_args()
    BENCHMARK_PATH, FIXTURES_DIR = args.benchmark, args.fixtures
    use_hint = args.hint == "on"

    taxonomy = load_taxonomy()
    benchmark = load_benchmark()

    print("=" * 80)
    print(f"Understanding v2 Benchmark — hint {args.hint.upper()}")
    print("=" * 80)
    print(f"Benchmark: {BENCHMARK_PATH} ({benchmark['version']})")
    print(f"Taxonomy: {taxonomy['name']} {taxonomy['version']}")
    print("Groups: " + ", ".join(f"{key} {len(benchmark.get(key, []))}" for key, _ in GROUPS))
    print(f"Snapshots: {FIXTURES_DIR}")

    cases = [(r, group) for key, group in GROUPS for r in benchmark.get(key, [])]
    if args.robot:
        cases = [(r, g) for r, g in cases if r['id'] == args.robot]
        if not cases:
            print(f"❌ ID '{args.robot}' not found in benchmark")
            return 1

    results = []
    for case, group in cases:
        result = test_robot(case, use_product_hint=use_hint, group=group)
        result['group'] = group
        result['expected_page_type'] = case.get('expected_page_type') or (case.get('expected') or {}).get('page_type')
        results.append(result)
    summary = summarize(results)
    rob = summary['robots']

    total_tokens = sum(r.get('metadata', {}).get('tokens_used', 0) for r in results)
    total_elapsed = sum(r.get('elapsed_sec', 0) for r in results)

    print("\n" + "=" * 80)
    print(f"Summary — hint {args.hint.upper()}")
    print("=" * 80)
    print(f"Robots: {len(rob['passed'])} of {rob['readable']} readable passed "
          f"({rob['total']} total, {len(rob['unreadable'])} unreadable: {rob['unreadable']}, "
          f"crashed: {rob['crashed']})")
    for rid, reason in rob['unreadable_reasons'].items():
        print(f"  unreadable {rid}: {reason}")
    print(f"Target not on page: {rob['target_not_on_page']}")
    print(f"Target not extracted: {len(rob['target_not_extracted'])} {rob['target_not_extracted']}")
    print("Per-field accuracy (first alias-matched record per entry):")
    for field, acc in rob['per_field_accuracy'].items():
        print(f"  {field:20s}: {acc:5.1%}")
    print("Per-field accuracy (all alias-matched records):")
    for field, c in rob['per_field_accuracy_all_matched_records'].items():
        print(f"  {field:20s}: {c['pass']}/{c['total']}")
    print("Robot failures:")
    for r in results:
        if r['id'] in rob['failed']:
            score = r.get('score') or {}
            if r.get('bucket') == 'TARGET_NOT_EXTRACTED':
                reasons = [f"target_not_extracted (records: {r['metadata'].get('product_names')})"]
            else:
                reasons = [f"{f}: {score[f]['reason']}" for f in
                           ('offering_type', 'form', 'primary_class', 'functions', 'industries')
                           if f in score and not score[f]['pass']] or [r.get('error', 'no score')]
            print(f"  {r['id']}: " + " | ".join(reasons))
    print(f"Robot fields blanked as unsupported: {rob['unsupported_by_field']}")
    print("Taxonomy gap probes:")
    for pid, verdict in summary['taxonomy_gap_probes']['verdicts'].items():
        print(f"  {pid}: {verdict}  fields: {summary['taxonomy_gap_probes']['fields'].get(pid)}")
    print(f"  blanked as unsupported: {summary['taxonomy_gap_probes']['unsupported_by_field']}")
    print("Negative controls:")
    for nid, verdict in summary['negative_controls']['verdicts'].items():
        print(f"  {nid}: {verdict}  checks: {summary['negative_controls']['checks'].get(nid)}")
    print(f"  blanked as unsupported: {summary['negative_controls']['unsupported_by_field']}")
    print("Page types assigned:")
    for label, key in (("robots", "robots"), ("gap probes", "taxonomy_gap_probes"),
                       ("negative controls", "negative_controls")):
        print(f"  {label}:")
        for cid, pt in summary[key]['page_types'].items():
            mark = '' if pt['match'] is None else (' ok' if pt['match'] else ' MISMATCH')
            print(f"    {cid}: {pt['assigned']} (expected {pt['expected']}){mark}")
    print(f"Tokens: {total_tokens:,}  Time: {total_elapsed:.1f}s")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump({
            'benchmark_path': str(BENCHMARK_PATH),
            'benchmark_version': benchmark['version'],
            'taxonomy_version': taxonomy['version'],
            'hint': args.hint,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'summary': summary,
            'cost_and_latency': {'total_tokens': total_tokens, 'total_elapsed_sec': total_elapsed},
            'results': results,
        }, f, indent=2)
    print(f"\nDetailed results: {args.output}")
    return 0


if __name__ == '__main__':
    sys.exit(main())
