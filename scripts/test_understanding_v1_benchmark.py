"""
Benchmark test runner for Understanding v1.

Tests match_robot_url_v1 against robot_benchmark_set.json using OFFLINE SNAPSHOTS.
No live network calls - uses pre-cached pages from tests/fixtures/robot_pages/.

Scores:
- Product class extraction (flexible matching with parent/child classes)
- Capability derivation (≥2 expected capabilities)
- Buyer vertical matching (at least one match)
- Must-not-match filtering (zero forbidden matches)

Reports three buckets:
- FETCH FAILED: Network/snapshot issue or thin content (doesn't count against v1)
- EXTRACTION FAILED: Zero facts extracted or wrong classification (v1 problem)
- PASSED: Meets all criteria

Usage:
    # Offline mode (uses snapshots):
    python3 scripts/test_understanding_v1_benchmark.py
    
    # Test specific robot:
    python3 scripts/test_understanding_v1_benchmark.py --robot hc-01
    
    # Live mode (requires internet):
    python3 scripts/test_understanding_v1_benchmark.py --live
"""
import json
import sys
import time
from pathlib import Path
from typing import Any

from app.services.robot_job_capability_match import match_robot_url_v1
from scripts.benchmark_scoring import score_product_class, score_capabilities


BENCHMARK_PATH = Path("tests/fixtures/robot_benchmark_set_e5e6.json")
FIXTURES_DIR = Path("tests/fixtures/robot_pages")

# Thin content threshold: pages with fewer words are treated as FETCH_FAILED
THIN_CONTENT_WORD_THRESHOLD = 150


def load_benchmark() -> dict[str, Any]:
    """Load the benchmark set."""
    with open(BENCHMARK_PATH, 'r') as f:
        return json.load(f)


def load_snapshot(robot_id: str) -> dict[str, Any] | None:
    """
    Load cached page snapshot for a robot.
    
    Returns:
        {
            "metadata": {...},
            "html": "...",
            "text": "...",
        }
        or None if snapshot doesn't exist.
    """
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


def map_capability_to_ontology(plain_english: str) -> str:
    """Map plain English capability names to ontology terms."""
    mapping = {
        "mobile_navigation": "mobile",
        "manipulation_arm": "manipulate",
        "elevator_use": "elevator",
        "item_delivery": "material_transport",
        "clinical_support_tasks": "healthcare_task",
        "secure_cargo": "carry",
        "uv_disinfection": "disinfect",
        "semi_mobile": "mobile",
        "pick_and_place": "manipulate",
        "material_transport": "material_transport",
        "assembly": "manipulate",
        "outdoor_unstructured": "outdoor",
        "equipment_retrofit": "retrofit",
        "floor_printing": "construction_layout",
        "precision_positioning": "mobile",
        "rebar_tying": "construction_task",
        "rebar_placement": "construction_task",
        "gantry_system": "mobile",
        "outdoor": "outdoor",
        "spray_application": "manipulate",
        "surface_finishing": "construction_task",
        "tray_delivery": "material_transport",
        "table_service": "serving_task",
        "customer_interaction": "humanoid",
        "dual_arm_manipulation": "dual_arm",
        "beverage_preparation": "beverage_prep",
        "autonomous_floor_scrubbing": "scrub",
        "large_area_coverage": "mobile",
        "autonomy_retrofit": "retrofit",
        "floor_cleaning": "scrub",
        "inventory_scanning": "shelf_scan",
        "frying": "food_prep",
        "food_preparation": "food_prep",
        "meal_assembly": "food_prep",
        "portioning": "manipulate",
        "conveyor_line_integration": "manipulate",
        "order_picking_assist": "pick_pack",
        "fleet_management": "mobile",
        "box_handling": "manipulate",
        "truck_unloading": "trailer_unload",
        "bipedal_mobility": "humanoid",
        "tote_handling": "tote_transport",
        "mobile_patrol": "mobile",
        "video_surveillance": "inspect",
        "anomaly_detection": "inspect",
        "indoor_patrol": "mobile",
        "access_control_check": "inspect",
        "remote_monitoring": "inspect",
        "follow_me": "mobile",
        "autonomous_hauling": "material_transport",
        "computer_vision_weeding": "agriculture_weed",
        "laser_actuation": "manipulate",
        "tractor_implement": "agriculture_tractor",
        "legged_mobility": "mobile",
        "thermal_inspection": "inspect",
        "acoustic_inspection": "inspect",
        "hazardous_environment": "industrial_runtime",
        "climbing": "mobile",
        "ultrasonic_testing": "inspect",
        "data_analytics": "inspect",
        "shelf_scanning": "shelf_scan",
        "inventory_analytics": "shelf_scan",
        "sidewalk_navigation": "mobile",
        "fleet_operations": "mobile",
        "machine_tending": "load_unload",
        "palletizing": "pallet_move",
        "welding": "manipulate",
        "collaborative_safety": "mobile",
        "case_packing": "manipulate",
        "raas_model": "mobile",
        "dexterous_manipulation": "dexterous",
        "general_purpose": "humanoid",
    }
    return mapping.get(plain_english, plain_english)


def test_negative_control(control: dict[str, Any], use_live: bool = False) -> dict[str, Any]:
    """Test a negative control and check expected behavior."""
    control_id = control['id']
    url = control['url']
    
    print(f"\n{'='*80}")
    print(f"Testing NEGATIVE CONTROL {control_id}")
    print(f"URL: {url}")
    print(f"Expected: {control['expected_behavior'][:80]}...")
    
    # Load snapshot or check live
    snapshot = None if use_live else load_snapshot(control_id)
    
    if snapshot is None and not use_live:
        print(f"❌ FETCH FAILED: No snapshot found for {control_id}")
        return {
            'id': control_id,
            'description': control['description'],
            'url': url,
            'bucket': 'FETCH_FAILED',
            'fetch_error': 'No snapshot found',
            'pass': False,
        }
    
    if snapshot:
        metadata = snapshot['metadata']
        if metadata.get('status_code') != 200:
            print(f"⚠️  Snapshot fetch failed: {metadata.get('error', 'Unknown')[:80]}")
            return {
                'id': control_id,
                'description': control['description'],
                'url': url,
                'bucket': 'FETCH_FAILED',
                'fetch_error': metadata.get('error', 'Unknown'),
                'snapshot_date': metadata.get('fetch_date'),
                'pass': False,
            }
        
        page_text = snapshot['text']
        word_count = len(page_text.strip().split())
        if word_count < THIN_CONTENT_WORD_THRESHOLD:
            print(f"⚠️  Thin content ({word_count} words)")
            return {
                'id': control_id,
                'description': control['description'],
                'url': url,
                'bucket': 'FETCH_FAILED',
                'fetch_error': f'Thin content ({word_count} words)',
                'snapshot_date': metadata.get('fetch_date'),
                'pass': False,
            }
        
        print(f"Using snapshot ({word_count} words, fetched {metadata.get('fetch_date', 'unknown')})")
    else:
        print(f"Using live URL (--live mode)")
    
    # Run extraction
    try:
        t0 = time.time()
        result = match_robot_url_v1(url)
        elapsed = time.time() - t0
        
        state = result.get('state', 'unknown')
        job_count = result.get('job_count', 0)
        
        print(f"\nResult: state={state}, jobs={job_count}, time={elapsed:.1f}s")
        
        # Negative controls should either:
        # 1. Extract nothing (state=could_not_understand or needs_product_choice)
        # 2. Extract with low confidence and source_type flag
        # 3. Not match to buyer opportunities
        
        passed = state in ['could_not_understand', 'needs_product_choice'] or job_count == 0
        bucket = 'PASSED' if passed else 'EXTRACTION_FAILED'
        
        if passed:
            print(f"✓ PASSED: Correctly identified as non-robot or low-confidence")
        else:
            print(f"❌ FAILED: Incorrectly matched {job_count} jobs")
        
        return {
            'id': control_id,
            'description': control['description'],
            'url': url,
            'bucket': bucket,
            'state': state,
            'job_count': job_count,
            'snapshot_date': snapshot['metadata'].get('fetch_date') if snapshot else None,
            'pass': passed,
            'elapsed_sec': elapsed,
        }
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return {
            'id': control_id,
            'description': control['description'],
            'url': url,
            'bucket': 'EXTRACTION_FAILED',
            'error': str(e),
            'snapshot_date': snapshot['metadata'].get('fetch_date') if snapshot else None,
            'pass': False,
        }


def test_robot(robot: dict[str, Any], use_live: bool = False) -> dict[str, Any]:
    """Test one robot and return results."""
    robot_id = robot['id']
    url = robot['url']
    
    print(f"\n{'='*80}")
    print(f"Testing {robot_id}: {robot['company']} - {robot['product']}")
    print(f"URL: {url}")
    print(f"Expected class: {robot['expected_product_class']}")
    
    # Load snapshot or check live
    snapshot = None if use_live else load_snapshot(robot_id)
    
    if snapshot is None and not use_live:
        print(f"❌ FETCH FAILED: No snapshot found for {robot_id}")
        print(f"   Run: python3 scripts/snapshot_robot_pages.py")
        return {
            'id': robot_id,
            'company': robot['company'],
            'url': url,
            'bucket': 'FETCH_FAILED',
            'fetch_error': 'No snapshot found',
            'pass': False,
        }
    
    if snapshot:
        # Check snapshot status
        metadata = snapshot['metadata']
        page_text = snapshot['text']
        
        # Fetch failures: DNS, SSL, HTTP errors, blocked
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
                'pass': False,
            }
        
        # HTTP 200 but thin/useless text (navigation only, cookie banners, etc.)
        word_count = len(page_text.strip().split())
        if word_count < THIN_CONTENT_WORD_THRESHOLD:
            print(f"⚠️  Snapshot has thin content ({word_count} words < {THIN_CONTENT_WORD_THRESHOLD} threshold)")
            return {
                'id': robot_id,
                'company': robot['company'],
                'url': url,
                'bucket': 'FETCH_FAILED',
                'fetch_error': f'Thin content ({word_count} words, likely navigation/cookie banner only)',
                'snapshot_date': metadata.get('fetch_date'),
                'pass': False,
            }
        
        html = snapshot['html']
        print(f"Using snapshot (fetched {metadata.get('fetch_date', 'unknown')}, {len(page_text)} chars)")
    else:
        page_text = None
        html = None
        print(f"Using live URL (--live mode)")
    
    # Run Understanding v1
    try:
        t0 = time.time()
        
        # In offline mode, pass cached page text
        if snapshot and not use_live:
            # Assert we're passing snapshot text
            word_count = len(page_text.strip().split())
            if word_count == 0:
                raise ValueError(f"Snapshot text is empty for {robot_id}")
            
            result = match_robot_url_v1(
                url,
                page_text=page_text,
                page_html=html
            )
        else:
            # Live mode - fetch URL directly
            result = match_robot_url_v1(url)
        
        elapsed = time.time() - t0
        
        state = result.get('state', 'unknown')
        company = result.get('company_name', 'Unknown')
        job_count = result.get('job_count', 0)
        capabilities = result.get('capabilities', [])
        robot_caps = result.get('robot_capabilities', {}) or {}
        
        # In offline mode with snapshot, verify extraction received non-empty text
        # If we got 0 capabilities and state=needs_product_choice, check if profile was built with text
        if snapshot and not use_live:
            # Log to help debug if extraction silently got empty input
            if len(capabilities) == 0 and state in ['needs_product_choice', 'could_not_understand']:
                print(f"⚠️  Zero capabilities extracted. Snapshot had {len(page_text)} chars ({len(page_text.split())} words)")
                # This is a legitimate failure - extraction saw the text but couldn't extract
                # Not a silent fetch failure like before
        
        print(f"\nResult: state={state}, company={company}, jobs={job_count}, time={elapsed:.1f}s")
        print(f"Extracted type: {robot_caps.get('type', 'Unknown')}")
        cap_keys = [c.get('key') for c in capabilities]
        print(f"Capabilities ({len(cap_keys)}): {cap_keys[:10]}")
        
        # Check if extraction failed (zero facts)
        if len(capabilities) == 0 or state == 'could_not_understand':
            print(f"❌ EXTRACTION FAILED: Zero capabilities derived")
            return {
                'id': robot_id,
                'company': robot['company'],
                'url': url,
                'bucket': 'EXTRACTION_FAILED',
                'state': state,
                'capabilities_count': 0,
                'snapshot_date': snapshot['metadata'].get('fetch_date') if snapshot else None,
                'pass': False,
                'elapsed_sec': elapsed,
            }
        
        # Score product class (flexible matching with parent/child classes)
        extracted_class = robot_caps.get('type', '').lower().replace(' ', '_') if robot_caps.get('type') else ''
        expected_class = robot['expected_product_class']
        class_match = score_product_class(extracted_class, expected_class)
        
        # Score capabilities (flexible matching via ontology)
        cap_keys = [c.get('key') for c in capabilities]
        matched_count, matched_labels = score_capabilities(cap_keys, robot['expected_capabilities'])
        cap_score = matched_count >= 2
        
        # Check jobs (buyer verticals)
        jobs = result.get('jobs', [])[:10]
        job_companies = [j.get('company_name', '').lower() for j in jobs]
        job_industries = [j.get('industry', '').lower() for j in jobs]
        
        # Check must_not_match
        must_not = robot.get('must_not_match', [])
        forbidden_match = any(
            any(forbidden in (comp + ' ' + ind) for comp, ind in zip(job_companies, job_industries))
            for forbidden in must_not
        )
        
        passed = class_match and cap_score and job_count > 0 and not forbidden_match
        bucket = 'PASSED' if passed else 'EXTRACTION_FAILED'
        
        if not passed:
            reasons = []
            if not class_match:
                reasons.append(f"class mismatch (got '{extracted_class}' expected '{expected_class}')")
            if not cap_score:
                reasons.append(f"only {len(matched_caps)}/2 caps matched")
            if job_count == 0:
                reasons.append("no jobs matched")
            if forbidden_match:
                reasons.append("matched forbidden vertical")
            print(f"❌ FAILED: {'; '.join(reasons)}")
        else:
            print(f"✓ PASSED")
        
        return {
            'id': robot_id,
            'company': robot['company'],
            'url': url,
            'bucket': bucket,
            'state': state,
            'extracted_company': company,
            'extracted_class': extracted_class,
            'expected_class': expected_class,
            'class_match': class_match,
            'capabilities_extracted': cap_keys,
            'expected_capabilities': robot['expected_capabilities'],
            'matched_capabilities': matched_labels,
            'cap_count': matched_count,
            'cap_score': cap_score,
            'job_count': job_count,
            'forbidden_match': forbidden_match,
            'snapshot_date': snapshot['metadata'].get('fetch_date') if snapshot else None,
            'pass': passed,
            'elapsed_sec': elapsed,
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
            'snapshot_date': snapshot['metadata'].get('fetch_date') if snapshot else None,
            'pass': False,
        }


def main():
    """Run the benchmark."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Understanding v1 benchmark")
    parser.add_argument("--live", action="store_true", 
                        help="Fetch live URLs instead of using snapshots (requires internet)")
    parser.add_argument("--robot", type=str, 
                        help="Test a specific robot by ID")
    args = parser.parse_args()
    
    benchmark = load_benchmark()
    
    print("="*80)
    print("Understanding v1 Benchmark")
    print("="*80)
    print(f"Benchmark version: {benchmark['version']}")
    print(f"Total robots: {len(benchmark['robots'])}")
    
    if args.live:
        print(f"⚠️  LIVE MODE: Will fetch URLs from internet")
    else:
        print(f"📦 OFFLINE MODE: Using snapshots from {FIXTURES_DIR}")
        if not FIXTURES_DIR.exists():
            print(f"❌ ERROR: Snapshot directory not found!")
            print(f"   Run: python3 scripts/snapshot_robot_pages.py")
            return 1
    
    # Filter robots if --robot specified
    robots_to_test = benchmark['robots']
    negative_controls = benchmark.get('negative_controls', [])
    
    if args.robot:
        # Check if it's a robot or negative control
        robots_to_test = [r for r in robots_to_test if r['id'] == args.robot]
        negative_controls = [n for n in negative_controls if n['id'] == args.robot]
        if not robots_to_test and not negative_controls:
            print(f"❌ ID '{args.robot}' not found in benchmark")
            return 1
    
    # Test robots
    results = []
    for robot in robots_to_test:
        result = test_robot(robot, use_live=args.live)
        results.append(result)
    
    # Test negative controls
    for control in negative_controls:
        result = test_negative_control(control, use_live=args.live)
        results.append(result)
    
    # Bucket results
    fetch_failed = [r for r in results if r.get('bucket') == 'FETCH_FAILED']
    extraction_failed = [r for r in results if r.get('bucket') == 'EXTRACTION_FAILED']
    passed = [r for r in results if r.get('bucket') == 'PASSED']
    
    # Summary
    print("\n" + "="*80)
    print("Summary")
    print("="*80)
    
    total = len(results)
    print(f"\nThree-Bucket Breakdown:")
    print(f"  FETCH FAILED:       {len(fetch_failed):2d}/{total} ({100*len(fetch_failed)/total:.0f}%)")
    print(f"  EXTRACTION FAILED:  {len(extraction_failed):2d}/{total} ({100*len(extraction_failed)/total:.0f}%)")
    print(f"  PASSED:             {len(passed):2d}/{total} ({100*len(passed)/total:.0f}%)")
    
    if fetch_failed:
        print(f"\n❌ FETCH FAILED ({len(fetch_failed)}):")
        for r in fetch_failed:
            print(f"  - {r['id']}: {r['company']} - {r.get('fetch_error', 'Unknown')}")
    
    if extraction_failed:
        print(f"\n⚠️  EXTRACTION FAILED ({len(extraction_failed)}):")
        for r in extraction_failed:
            reasons = []
            if r.get('capabilities_count') == 0:
                reasons.append("zero capabilities")
            if r.get('state') == 'could_not_understand':
                reasons.append("could_not_understand")
            if not r.get('class_match', True):
                reasons.append(f"class '{r.get('extracted_class')}' ≠ '{r.get('expected_class')}'")
            if r.get('cap_count', 0) < 2:
                reasons.append(f"only {r.get('cap_count', 0)} caps matched")
            if r.get('job_count', 0) == 0:
                reasons.append("no jobs")
            print(f"  - {r['id']}: {r['company']} - {', '.join(reasons) or 'unknown'}")
    
    if passed:
        print(f"\n✓ PASSED ({len(passed)}):")
        for r in passed:
            print(f"  - {r['id']}: {r['company']}")
    
    # Detailed results JSON
    results_path = Path("reports") / "understanding_v1_benchmark_results.json"
    results_path.parent.mkdir(exist_ok=True)
    with open(results_path, 'w') as f:
        json.dump({
            'benchmark_version': benchmark['version'],
            'test_mode': 'live' if args.live else 'offline',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            'summary': {
                'total': total,
                'fetch_failed': len(fetch_failed),
                'extraction_failed': len(extraction_failed),
                'passed': len(passed),
            },
            'results': results,
        }, f, indent=2)
    
    print(f"\nDetailed results: {results_path}")
    
    # Return 0 only if zero extraction failures
    return 0 if len(extraction_failed) == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
