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

from app.services.robot_job_capability_match import match_robot_url_v1
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


def extract_robot_taxonomy_values(result: dict[str, Any]) -> dict[str, Any]:
    """
    Extract taxonomy values from match_robot_url_v1 result.
    
    For now, this is a stub that returns empty values.
    The real implementation will come when semantic extraction is wired.
    
    Returns:
        {
            "offering_type": str,
            "form": str,
            "primary_class": str,
            "functions": [{"value": str, "confidence": float, "evidence": str}],
            "industries": [{"value": str, "confidence": float, "evidence": str}],
        }
    """
    # TODO: Replace with actual taxonomy extraction
    return {
        "offering_type": "",
        "form": "",
        "primary_class": "",
        "functions": [],
        "industries": [],
    }


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
    product_name = robot.get('target_product') if use_product_hint else None
    
    print(f"\n{'='*80}")
    print(f"Testing {robot_id}: {robot['company']} - {robot['target_product']}")
    print(f"URL: {url}")
    if use_product_hint:
        print(f"Product hint: {product_name}")
    
    # Load snapshot
    snapshot = load_snapshot(robot_id)
    
    if snapshot is None:
        print(f"❌ FETCH FAILED: No snapshot found for {robot_id}")
        return {
            'id': robot_id,
            'company': robot['company'],
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
            'company': robot['company'],
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
            'company': robot['company'],
            'url': url,
            'bucket': 'FETCH_FAILED',
            'fetch_error': f'Thin content ({word_count} words)',
            'snapshot_date': metadata.get('fetch_date'),
            'used_product_hint': use_product_hint,
        }
    
    html = snapshot['html']
    print(f"Using snapshot ({word_count} words, fetched {metadata.get('fetch_date', 'unknown')})")
    
    # Run extraction
    try:
        t0 = time.time()
        
        result = match_robot_url_v1(
            url,
            page_text=page_text,
            page_html=html,
            product_name=product_name
        )
        
        elapsed = time.time() - t0
        
        # Extract taxonomy values from result
        extracted = extract_robot_taxonomy_values(result)
        
        print(f"\nExtraction time: {elapsed:.1f}s")
        print(f"Extracted: offering_type={extracted.get('offering_type', 'N/A')}, "
              f"form={extracted.get('form', 'N/A')}, "
              f"primary_class={extracted.get('primary_class', 'N/A')}")
        print(f"Functions: {[f.get('value') if isinstance(f, dict) else f for f in extracted.get('functions', [])]}")
        print(f"Industries: {[i.get('value') if isinstance(i, dict) else i for i in extracted.get('industries', [])]}")
        
        # Score against expected
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
        
        return {
            'id': robot_id,
            'company': robot['company'],
            'url': url,
            'bucket': bucket,
            'score': score,
            'extracted': extracted,
            'snapshot_date': metadata.get('fetch_date'),
            'elapsed_sec': elapsed,
            'used_product_hint': use_product_hint,
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return {
            'id': robot_id,
            'company': robot['company'],
            'url': url,
            'bucket': 'EXTRACTION_FAILED',
            'error': str(e),
            'snapshot_date': snapshot['metadata'].get('fetch_date'),
            'used_product_hint': use_product_hint,
        }


def main():
    """Run the v2 benchmark."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Understanding v2 benchmark (taxonomy-based)")
    parser.add_argument("--robot", type=str, help="Test a specific robot by ID")
    args = parser.parse_args()
    
    taxonomy = load_taxonomy()
    benchmark = load_benchmark()
    
    print("="*80)
    print("Understanding v2 Benchmark (Taxonomy-Based)")
    print("="*80)
    print(f"Benchmark version: {benchmark['version']}")
    print(f"Taxonomy: {taxonomy['name']} {taxonomy['version']}")
    print(f"Total robots: {len(benchmark['robots'])}")
    print(f"Using snapshots from {FIXTURES_DIR}")
    print()
    
    # Filter robots if --robot specified
    robots_to_test = benchmark['robots']
    if args.robot:
        robots_to_test = [r for r in robots_to_test if r['id'] == args.robot]
        if not robots_to_test:
            print(f"❌ ID '{args.robot}' not found in benchmark")
            return 1
    
    # Test with product hints (will also run without hints later)
    print("="*80)
    print("Testing WITH product hints")
    print("="*80)
    
    results_with_hint = []
    for robot in robots_to_test:
        result = test_robot(robot, use_product_hint=True)
        results_with_hint.append(result)
    
    # Compute per-field accuracy
    accuracy = compute_per_field_accuracy(results_with_hint)
    
    # Summary
    fetch_failed = [r for r in results_with_hint if r.get('bucket') == 'FETCH_FAILED']
    extraction_failed = [r for r in results_with_hint if r.get('bucket') == 'EXTRACTION_FAILED']
    passed = [r for r in results_with_hint if r.get('bucket') == 'PASSED']
    
    total = len(results_with_hint)
    
    print("\n" + "="*80)
    print("Summary (WITH product hints)")
    print("="*80)
    print(f"\nThree-Bucket Breakdown:")
    print(f"  FETCH FAILED:       {len(fetch_failed):2d}/{total} ({100*len(fetch_failed)/total:.0f}%)")
    print(f"  EXTRACTION FAILED:  {len(extraction_failed):2d}/{total} ({100*len(extraction_failed)/total:.0f}%)")
    print(f"  PASSED:             {len(passed):2d}/{total} ({100*len(passed)/total:.0f}%)")
    
    print(f"\nPer-Field Accuracy:")
    for field, acc in accuracy.items():
        print(f"  {field:20s}: {acc:5.1%}")
    
    # Save results
    results_path = Path("reports") / "understanding_v2_benchmark_results.json"
    results_path.parent.mkdir(exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump({
            'benchmark_version': benchmark['version'],
            'taxonomy_version': taxonomy['version'],
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'summary': {
                'total': total,
                'fetch_failed': len(fetch_failed),
                'extraction_failed': len(extraction_failed),
                'passed': len(passed),
            },
            'per_field_accuracy': accuracy,
            'results': results_with_hint,
        }, f, indent=2)
    
    print(f"\nDetailed results: {results_path}")
    
    return 0 if len(extraction_failed) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
