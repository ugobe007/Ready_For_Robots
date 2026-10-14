"""Print per-robot benchmark results as a markdown table."""
import json
import sys
from pathlib import Path

def main():
    results_path = Path("reports/understanding_v1_benchmark_results.json")
    
    if not results_path.exists():
        print(f"Error: {results_path} not found")
        print("Run: python3 scripts/test_understanding_v1_benchmark.py")
        return 1
    
    with open(results_path) as f:
        data = json.load(f)
    
    results = data['results']
    summary = data['summary']
    
    print("\n## Regex Baseline Results (Corrected Scorer)\n")
    print(f"**Test mode:** {data['test_mode']}")
    print(f"**Timestamp:** {data['timestamp']}")
    print(f"**Benchmark version:** {data['benchmark_version']}\n")
    
    print(f"**Summary:** {summary['passed']}/{summary['total']} passed "
          f"({summary['fetch_failed']} fetch failed, {summary['extraction_failed']} extraction failed)\n")
    
    # Group by bucket
    fetch_failed = [r for r in results if r.get('bucket') == 'FETCH_FAILED']
    extraction_failed = [r for r in results if r.get('bucket') == 'EXTRACTION_FAILED']
    passed = [r for r in results if r.get('bucket') == 'PASSED']
    
    # Print table
    print("| ID | Company/Description | Expected Class | Extracted Class | Cap Matches | Jobs | Bucket | Notes |")
    print("|----|--------------------|---------------|----------------|------------|------|--------|-------|")
    
    for r in results:
        robot_id = r['id']
        company_or_desc = r.get('company') or r.get('description', 'Unknown')
        expected_class = r.get('expected_class', 'N/A')
        extracted_class = r.get('extracted_class', r.get('extracted_type', 'N/A'))
        cap_count = r.get('cap_count', 0)
        matched_caps = r.get('matched_capabilities', [])
        job_count = r.get('job_count', 0)
        bucket = r.get('bucket', 'UNKNOWN')
        
        # Build notes
        notes = []
        if r.get('fetch_error'):
            notes.append(r['fetch_error'][:40])
        elif r.get('state') == 'could_not_understand':
            notes.append('could_not_understand')
        elif r.get('capabilities_count') == 0:
            notes.append('zero capabilities')
        elif not r.get('class_match', True):
            notes.append('class mismatch')
        
        if r.get('matched_via'):
            matched_via_str = ', '.join(f"{k}→{v}" for k, v in list(r['matched_via'].items())[:2])
            if matched_via_str:
                notes.append(f"via: {matched_via_str}")
        
        notes_str = '; '.join(notes[:2]) if notes else '—'
        
        # Emoji for bucket
        bucket_emoji = {
            'PASSED': '✓',
            'EXTRACTION_FAILED': '⚠️',
            'FETCH_FAILED': '❌'
        }.get(bucket, '?')
        
        print(f"| {robot_id} | {company_or_desc[:30]} | {expected_class[:20]} | "
              f"{extracted_class[:15]} | {cap_count} ({len(matched_caps)}) | {job_count} | "
              f"{bucket_emoji} {bucket} | {notes_str[:60]} |")
    
    print("\n### Legend")
    print("- **Cap Matches**: non-generic matches (generic match count)")
    print("- ✓ PASSED: All criteria met")
    print("- ⚠️ EXTRACTION_FAILED: Extracted but didn't meet criteria")
    print("- ❌ FETCH_FAILED: Network/snapshot issue")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
