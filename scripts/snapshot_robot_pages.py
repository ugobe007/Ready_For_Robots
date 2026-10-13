"""
Snapshot robot pages for offline benchmark testing.

Fetches each URL from robot_benchmark_set.json and saves:
- HTML content
- Plain text (extracted)
- Metadata (fetch date, status code, final URL after redirects)

Usage:
    python3 scripts/snapshot_robot_pages.py
    
Run this from a machine with full internet access (not Cloud Agent VM).
Commit the snapshots to tests/fixtures/robot_pages/ for reproducible testing.
"""
import json
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup


FIXTURES_DIR = Path("tests/fixtures/robot_pages")
BENCHMARK_PATH = "/home/ubuntu/.cursor/projects/workspace/uploads/robot_benchmark_set_e5e6.json"


def extract_text(html: str) -> str:
    """Extract plain text from HTML."""
    try:
        soup = BeautifulSoup(html, "html.parser")
        # Remove script and style elements
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        text = soup.get_text(separator=" ", strip=True)
        return text
    except Exception:
        return ""


def fetch_page(url: str, timeout: int = 10) -> dict[str, Any]:
    """
    Fetch a URL and return metadata + content.
    
    Returns:
        {
            "url": original URL,
            "final_url": after redirects,
            "status_code": HTTP status,
            "fetch_date": ISO timestamp,
            "html": raw HTML,
            "text": extracted text,
            "error": error message if failed,
        }
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; ReadyForRobotsCrawler/1.0)",
    }
    
    result = {
        "url": url,
        "fetch_date": datetime.utcnow().isoformat() + "Z",
    }
    
    try:
        resp = requests.get(url, headers=headers, timeout=timeout, allow_redirects=True)
        result["status_code"] = resp.status_code
        result["final_url"] = resp.url
        
        if resp.status_code == 200:
            result["html"] = resp.text
            result["text"] = extract_text(resp.text)
        else:
            result["html"] = ""
            result["text"] = ""
            result["error"] = f"HTTP {resp.status_code}"
        
        return result
        
    except requests.exceptions.Timeout:
        result["status_code"] = 0
        result["final_url"] = url
        result["html"] = ""
        result["text"] = ""
        result["error"] = "Timeout"
        return result
        
    except requests.exceptions.RequestException as e:
        result["status_code"] = 0
        result["final_url"] = url
        result["html"] = ""
        result["text"] = ""
        result["error"] = str(e)[:200]
        return result


def snapshot_robot(robot: dict[str, Any], output_dir: Path) -> dict[str, Any]:
    """
    Snapshot one robot's page.
    
    Returns summary dict for manifest.
    """
    robot_id = robot["id"]
    url = robot["url"]
    
    print(f"Fetching {robot_id}: {robot['company']} - {url}")
    
    # Fetch
    result = fetch_page(url)
    
    # Write files
    robot_dir = output_dir / robot_id
    robot_dir.mkdir(parents=True, exist_ok=True)
    
    # Write HTML
    html_path = robot_dir / "page.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(result.get("html", ""))
    
    # Write text
    text_path = robot_dir / "page.txt"
    with open(text_path, "w", encoding="utf-8") as f:
        f.write(result.get("text", ""))
    
    # Write metadata
    metadata = {
        "id": robot_id,
        "company": robot["company"],
        "product": robot["product"],
        "url": result["url"],
        "final_url": result.get("final_url", result["url"]),
        "status_code": result.get("status_code", 0),
        "fetch_date": result["fetch_date"],
        "error": result.get("error"),
    }
    
    metadata_path = robot_dir / "metadata.json"
    with open(metadata_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    
    status = "✓" if result.get("status_code") == 200 else "✗"
    error_msg = f" ({result.get('error')})" if result.get("error") else ""
    print(f"  {status} HTTP {result.get('status_code', 0)}{error_msg}")
    
    return metadata


def main():
    """Snapshot all robot pages from benchmark."""
    # Create output directory
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load benchmark
    with open(BENCHMARK_PATH, "r") as f:
        benchmark = json.load(f)
    
    print("=" * 80)
    print("Snapshotting Robot Pages for Offline Benchmark")
    print("=" * 80)
    print(f"Benchmark version: {benchmark['version']}")
    print(f"Total robots: {len(benchmark['robots'])}")
    print(f"Output directory: {FIXTURES_DIR}")
    print()
    
    manifest = {
        "snapshot_date": datetime.utcnow().isoformat() + "Z",
        "benchmark_version": benchmark["version"],
        "robots": [],
    }
    
    # Snapshot each robot
    for robot in benchmark["robots"]:
        try:
            metadata = snapshot_robot(robot, FIXTURES_DIR)
            manifest["robots"].append(metadata)
            # Be nice to servers
            time.sleep(1)
        except Exception as e:
            print(f"  ✗ Error: {e}")
            manifest["robots"].append({
                "id": robot["id"],
                "company": robot["company"],
                "url": robot["url"],
                "status_code": 0,
                "error": str(e)[:200],
            })
    
    # Snapshot negative controls
    print("\n" + "=" * 80)
    print("Negative Controls")
    print("=" * 80)
    
    for i, neg in enumerate(benchmark.get("negative_controls", [])):
        robot_id = neg["id"]
        url = neg["url"]
        
        print(f"Fetching {robot_id}: {neg['description'][:50]}... - {url}")
        
        try:
            result = fetch_page(url)
            
            robot_dir = FIXTURES_DIR / robot_id
            robot_dir.mkdir(parents=True, exist_ok=True)
            
            (robot_dir / "page.html").write_text(result.get("html", ""), encoding="utf-8")
            (robot_dir / "page.txt").write_text(result.get("text", ""), encoding="utf-8")
            
            metadata = {
                "id": robot_id,
                "description": neg["description"],
                "url": result["url"],
                "final_url": result.get("final_url", result["url"]),
                "status_code": result.get("status_code", 0),
                "fetch_date": result["fetch_date"],
                "error": result.get("error"),
                "expected_behavior": neg["expected_behavior"],
            }
            
            (robot_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            
            status = "✓" if result.get("status_code") == 200 else "✗"
            print(f"  {status} HTTP {result.get('status_code', 0)}")
            
            time.sleep(1)
            
        except Exception as e:
            print(f"  ✗ Error: {e}")
    
    # Write manifest
    manifest_path = FIXTURES_DIR / "manifest.json"
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, indent=2)
    
    # Summary
    print("\n" + "=" * 80)
    print("Summary")
    print("=" * 80)
    
    successful = sum(1 for r in manifest["robots"] if r.get("status_code") == 200)
    failed = len(manifest["robots"]) - successful
    
    print(f"Successful fetches: {successful}/{len(manifest['robots'])}")
    print(f"Failed fetches: {failed}/{len(manifest['robots'])}")
    
    if failed > 0:
        print("\nFailed URLs:")
        for r in manifest["robots"]:
            if r.get("status_code") != 200:
                print(f"  - {r['id']}: {r['company']} - {r.get('error', 'Unknown error')}")
    
    print(f"\nManifest written to: {manifest_path}")
    print(f"\nTo commit snapshots:")
    print(f"  git add {FIXTURES_DIR}")
    print(f"  git commit -m 'Add robot page snapshots for offline benchmark testing'")
    
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
