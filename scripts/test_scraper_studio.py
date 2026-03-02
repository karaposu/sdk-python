"""
Test Scraper Studio API - trigger sahibinden.com scraper.

Usage:
    python scripts/test_scraper_studio.py
"""

import os
import sys
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE = "https://api.brightdata.com"
TOKEN = os.environ.get("BRIGHTDATA_API_TOKEN")

# Known job ID from the first successful run
JOB_ID = "j_mly4pzxd1mj4u0gjj8"

# Target URL to scrape
TARGET_URL = "https://www.sahibinden.com/ilan/emlak-konut-satilik-ziraat-bankasi-ndan-hurma-mahallesi-nde-mesken-1296526183/detay"

HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}


def get_collector_id():
    """Get the collector ID from a known job."""
    print(f"[1] Fetching collector ID from job {JOB_ID}...")
    resp = requests.get(f"{API_BASE}/dca/log/{JOB_ID}", headers=HEADERS)
    resp.raise_for_status()
    data = resp.json()
    collector = data.get("collector") or data.get("Collector")
    print(f"    Collector: {collector}")
    print(f"    Status: {data.get('status') or data.get('Status')}")
    print(f"    Success rate: {data.get('success_rate') or data.get('Success_rate')}")
    return collector


def trigger_sync(collector_id):
    """Real-time sync - blocks until result or timeout."""
    print("\n[2] Triggering real-time sync crawl...")
    print(f"    Collector: {collector_id}")
    print(f"    URL: {TARGET_URL}")

    resp = requests.post(
        f"{API_BASE}/dca/crawl",
        headers=HEADERS,
        params={"collector": collector_id, "timeout": "50s"},
        json={"url": TARGET_URL},
    )

    if resp.status_code == 200:
        data = resp.json()
        print("\n[OK] Got data directly!")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        return data
    elif resp.status_code == 202:
        data = resp.json()
        response_id = data.get("response_id")
        print(f"    Timed out, got response_id: {response_id}")
        return poll_result(response_id)
    else:
        print(f"    Error {resp.status_code}: {resp.text}")
        return None


def poll_result(response_id, timeout=180, interval=5):
    """Poll for real-time async result."""
    print(f"\n[3] Polling for result (response_id={response_id})...")
    start = time.time()

    while time.time() - start < timeout:
        resp = requests.get(
            f"{API_BASE}/dca/get_result",
            headers=HEADERS,
            params={"response_id": response_id},
        )

        if resp.status_code == 200:
            data = resp.json()
            if data:
                elapsed = time.time() - start
                print(f"\n[OK] Got data after {elapsed:.1f}s")
                print(json.dumps(data, indent=2, ensure_ascii=False))
                return data

        print(f"    Still waiting... ({time.time() - start:.0f}s)")
        time.sleep(interval)

    print(f"    Timed out after {timeout}s")
    return None


def main():
    if not TOKEN:
        print("Error: Set BRIGHTDATA_API_TOKEN environment variable")
        sys.exit(1)

    print(f"Token: {TOKEN[:8]}...{TOKEN[-4:]}")
    print(f"Target: {TARGET_URL}\n")

    # Step 1: Get collector ID
    collector_id = get_collector_id()
    if not collector_id:
        print("Error: Could not get collector ID")
        sys.exit(1)

    # Step 2: Trigger scrape
    result = trigger_sync(collector_id)

    if result:
        # Save to file
        out_path = "scripts/scraper_studio_result.json"
        with open(out_path, "w", encoding="utf-8") as f:
            (
                json.dumps(result, f, indent=2, ensure_ascii=False)
                if isinstance(result, str)
                else json.dump(result, f, indent=2, ensure_ascii=False)
            )
        print(f"\nSaved to {out_path}")
    else:
        print("\nNo result received")


if __name__ == "__main__":
    main()
