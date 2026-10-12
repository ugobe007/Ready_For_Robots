#!/usr/bin/env python3
"""
Send a test daily jobs report email via the Fly API.

Usage:
    # With ADMIN_KEY in environment
    export ADMIN_KEY="your-admin-key-here"
    python3 scripts/send_test_daily_jobs_email.py

    # Or pass directly
    python3 scripts/send_test_daily_jobs_email.py --admin-key YOUR_KEY

    # Dry run (check API but don't send)
    python3 scripts/send_test_daily_jobs_email.py --dry-run
"""

import argparse
import json
import os
import sys
from typing import Any

try:
    import requests
except ImportError:
    print("❌ requests not installed. Run: pip install requests")
    sys.exit(1)


API_URL = "https://ready-2-robot.fly.dev/api/v1/market-graph/daily-jobs-report-send"


def send_test_email(admin_key: str, force: bool = True, limit: int = 25, dry_run: bool = False) -> dict[str, Any]:
    """Send test daily jobs report email via Fly API."""
    
    if not admin_key:
        raise ValueError("ADMIN_KEY is required")
    
    headers = {
        "Content-Type": "application/json",
        "X-Admin-Key": admin_key,
    }
    
    payload = {
        "force": force,
        "limit": limit,
    }
    
    if dry_run:
        print(f"🔍 DRY RUN - Would send request to: {API_URL}")
        print(f"📦 Payload: {json.dumps(payload, indent=2)}")
        print(f"🔑 Admin Key: {'*' * (len(admin_key) - 4)}{admin_key[-4:]}")
        return {"dry_run": True}
    
    print(f"📧 Sending test email request to: {API_URL}")
    print(f"📦 Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        result = response.json()
        
        print("\n✅ SUCCESS!")
        print(f"📨 Sent: {result.get('sent')}")
        print(f"👤 Recipients: {', '.join(result.get('recipients', []))}")
        print(f"📊 Job Count: {result.get('count')}")
        print(f"📅 Date: {result.get('date')}")
        print(f"🆔 Resend ID: {result.get('resend_id')}")
        print(f"🤖 Engine: {result.get('engine')}")
        print(f"💰 Paid LLM: {result.get('paid_llm')}")
        
        return result
        
    except requests.exceptions.HTTPError as e:
        print(f"\n❌ HTTP Error: {e.response.status_code}")
        try:
            error_detail = e.response.json()
            print(f"📄 Details: {json.dumps(error_detail, indent=2)}")
        except:
            print(f"📄 Response: {e.response.text[:500]}")
        raise
    
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Request Error: {e}")
        raise


def main():
    parser = argparse.ArgumentParser(
        description="Send a test daily jobs report email via Fly API"
    )
    parser.add_argument(
        "--admin-key",
        help="Admin API key (or set ADMIN_KEY env var)",
        default=os.environ.get("ADMIN_KEY", ""),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        default=True,
        help="Force send even if already sent today (default: True)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=25,
        help="Number of jobs to include (default: 25)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be sent without actually sending",
    )
    
    args = parser.parse_args()
    
    admin_key = args.admin_key.strip()
    
    if not admin_key:
        print("❌ Error: ADMIN_KEY required")
        print("\nOptions:")
        print("  1. Set environment variable: export ADMIN_KEY='your-key'")
        print("  2. Pass directly: --admin-key YOUR_KEY")
        print("\nTo get the ADMIN_KEY from Fly:")
        print("  fly secrets list -a ready-2-robot | grep ADMIN_KEY")
        sys.exit(1)
    
    try:
        result = send_test_email(
            admin_key=admin_key,
            force=args.force,
            limit=args.limit,
            dry_run=args.dry_run,
        )
        
        if not args.dry_run:
            print("\n✨ Test email sent successfully!")
            print("📬 Check ugobe07@gmail.com inbox for:")
            print("   - Subject: 'Top 25 hot job opportunities — <date>'")
            print("   - Attachment: daily-jobs-<date>.csv")
            print("\n🔍 Verify:")
            print("   - All jobs explicitly mention robots")
            print("   - No human hiring language (apply, resume, salary, etc.)")
            print("   - Each job has employer name + robot description")
        
    except Exception as e:
        print(f"\n💥 Failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
