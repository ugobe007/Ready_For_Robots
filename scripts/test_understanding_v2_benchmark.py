"""
Taxonomy-based benchmark runner (v2).

Tests extraction against robot_benchmark_set.v2.json using exact-match
taxonomy validation. Scorer is FROZEN - no tuning against results.

Usage:
    python3 scripts/test_understanding_v2_benchmark.py
    python3 scripts/test_understanding_v2_benchmark.py --robot hc-01
"""
import json
import sys
import time
from pathlib import Path
from typing import Any

from app.services.robot_understanding_v1.taxonomy_extraction import extract_robot_taxonomy
from scripts.benchmark_scoring_v2 import (
    score_robot,
    compute_per_field_accuracy,
    load_taxonomy,
)


BENCHMARK_PATH = Path("tests/fixtures/robot_benchmark_set.v2.json")
FIXTURES_DIR = Path("tests/fixtures/robot_pages")
THIN_CONTENT_WORD_THRESHOLD = 150


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


def extract_robot_taxonomy_values(
    url: str,
    page_text: str,
    product_name_hint: str | None = None
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
    
    # Extract first product (or empty if none)
    products = result.get("products", [])
    if not products:
        return {
            "offering_type": "",
            "form": "",
            "primary_class": "",
            "primary_function": {},
            "secondary_functions": [],
            "industries": [],
            "unclassified_notes": "No products extracted"
        }, result.get("extraction_metadata", {})
    
    # If product_name_hint provided, try to find matching product
    if product_name_hint:
        hint_lower = product_name_hint.lower()
        for product in products:
            product_name_lower = product.get("product_name", "").lower()
            # Match if either string contains the other (bidirectional)
            if hint_lower in product_name_lower or product_name_lower in hint_lower:
                return {
                    "offering_type": product["offering_type"]["value"],
                    "form": product["form"]["value"],
                    "primary_class": product["primary_class"]["value"],
                    "primary_function": product.get("primary_function", {}),
                    "secondary_functions": product.get("secondary_functions", []),
                    "industries": product.get("industries", []),
                    "unclassified_notes": product.get("unclassified_notes", "")
                }, result.get("extraction_metadata", {})
    
    # Return first product
    product = products[0]
    return {
        "offering_type": product["offering_type"]["value"],
        "form": product["form"]["value"],
        "primary_class": product["primary_class"]["value"],
        "primary_function": product.get("primary_function", {}),
        "secondary_functions": product.get("secondary_functions", []),
        "industries": product.get("industries", []),
        "unclassified_notes": product.get("unclassified_notes", "")
    }, result.get("extraction_metadata", {})


def score_negative_control(extracted: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    """Check only the taxonomy fields the answer key states for a control.

    `buyer_matches` is not checkable here because this runner does no matching.
    """
    checks = []
    passed = True
    for field in ("offering_type", "primary_class"):
        if field in expected:
            ok = extracted.get(field) == expected[field]
            passed = passed and ok
            checks.append(f"{field}={extracted.get(field)!r} expected {expected[field]!r} -> {'ok' if ok else 'FAIL'}")
    if not checks:
        return {"pass": False, "checks": ["no checkable taxonomy fields in answer key"]}
    if "buyer_matches" in expected:
        checks.append("buyer_matches not checked (no matching in this runner)")
    return {"pass": passed, "checks": checks}


def test_robot(
    robot: dict[str, Any],
    use_product_hint: bool = False
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
    is_negative_control = 'expected' in robot
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
    print(f"Using snapshot ({word_count} words, fetched {metadata_snapshot.get('fetch_date', 'unknown')})")
    
    # Run extraction
    try:
        t0 = time.time()
        
        extracted, metadata = extract_robot_taxonomy_values(
            url=url,
            page_text=page_text,
            product_name_hint=product_name
        )
        
        elapsed = time.time() - t0
        
        print(f"\nExtraction time: {elapsed:.1f}s")
        print(f"Tokens: {metadata.get('tokens_used', 0)} ({metadata.get('input_tokens', 0)} in, {metadata.get('output_tokens', 0)} out)")
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
        if not is_negative_control:
            score = score_robot(extracted, robot)
            
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
            neg = score_negative_control(extracted, robot['expected'])
            bucket = 'NEG_PASS' if neg['pass'] else 'NEG_FAIL'
            print(f"{'✅' if neg['pass'] else '❌'} Negative control: {'; '.join(neg['checks'])}")
        
        return {
            'id': robot_id,
            'company': robot.get('company', ''),
            'description': robot.get('description', ''),
            'url': url,
            'bucket': bucket,
            'score': score,
            'extracted': extracted,
            'metadata': metadata,
            'snapshot_date': metadata_snapshot.get('fetch_date'),
            'elapsed_sec': elapsed,
            'used_product_hint': use_product_hint,
            'is_negative_control': is_negative_control,
            'negative_control_score': neg if is_negative_control else None,
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


def summarize(results: list[dict[str, Any]]) -> dict[str, Any]:
    """Robots and negative controls are summarized separately, never pooled."""
    robots = [r for r in results if not r.get('is_negative_control') and not r['id'].startswith('neg-')]
    negs = [r for r in results if r.get('is_negative_control') or r['id'].startswith('neg-')]
    readable = [r for r in robots if r.get('bucket') != 'FETCH_FAILED']
    return {
        'robots': {
            'total': len(robots),
            'unreadable': [r['id'] for r in robots if r.get('bucket') == 'FETCH_FAILED'],
            'readable': len(readable),
            'passed': [r['id'] for r in readable if r.get('bucket') == 'PASSED'],
            'failed': [r['id'] for r in readable if r.get('bucket') != 'PASSED'],
            'per_field_accuracy': compute_per_field_accuracy(robots),
        },
        'negative_controls': {
            r['id']: ('NOT READ' if r.get('bucket') == 'FETCH_FAILED'
                      else 'PASS' if r.get('bucket') == 'NEG_PASS' else 'FAIL')
            for r in negs
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
    print(f"Robots: {len(benchmark['robots'])}, negative controls: {len(benchmark.get('negative_controls', []))}")
    print(f"Snapshots: {FIXTURES_DIR}")

    cases = benchmark['robots'] + benchmark.get('negative_controls', [])
    if args.robot:
        cases = [r for r in cases if r['id'] == args.robot]
        if not cases:
            print(f"❌ ID '{args.robot}' not found in benchmark")
            return 1

    results = [test_robot(r, use_product_hint=use_hint) for r in cases]
    summary = summarize(results)
    rob = summary['robots']

    total_tokens = sum(r.get('metadata', {}).get('tokens_used', 0) for r in results)
    total_elapsed = sum(r.get('elapsed_sec', 0) for r in results)

    print("\n" + "=" * 80)
    print(f"Summary — hint {args.hint.upper()}")
    print("=" * 80)
    print(f"Robots: {len(rob['passed'])} of {rob['readable']} readable passed "
          f"({rob['total']} total, {len(rob['unreadable'])} unreadable: {rob['unreadable']})")
    for field, acc in rob['per_field_accuracy'].items():
        print(f"  {field:20s}: {acc:5.1%}")
    print("Robot failures:")
    for r in results:
        if r['id'] in rob['failed']:
            score = r.get('score') or {}
            reasons = [f"{f}: {score[f]['reason']}" for f in
                       ('offering_type', 'form', 'primary_class', 'functions', 'industries')
                       if f in score and not score[f]['pass']] or [r.get('error', 'no score')]
            print(f"  {r['id']}: " + " | ".join(reasons))
    print("Negative controls:")
    for nid, verdict in summary['negative_controls'].items():
        print(f"  {nid}: {verdict}")
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
