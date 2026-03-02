"""
Poll Scraper Studio for completed job data and save as JSON.

Usage:
    python scripts/poll_scraper_result.py
"""

import os
import json
import time
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("BRIGHTDATA_API_TOKEN")
BASE = "https://api.brightdata.com"
HEADERS = {"Authorization": f"Bearer {TOKEN}"}

JOB_ID = "j_mly4pzxd1mj4u0gjj8"
TIMEOUT = 180
INTERVAL = 10

print(f"Polling job {JOB_ID}...")
start = time.time()

while time.time() - start < TIMEOUT:
    resp = requests.get(
        f"{BASE}/dca/dataset",
        headers=HEADERS,
        params={"id": JOB_ID},
    )

    if resp.status_code == 200:
        data = resp.json()
        out = "scripts/scraper_studio_result.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"\nDone! Saved to {out}")
        print(json.dumps(data, indent=2, ensure_ascii=False)[:3000])
        break
    elif resp.status_code == 202:
        elapsed = int(time.time() - start)
        print(f"  Still building... ({elapsed}s)")
        time.sleep(INTERVAL)
    else:
        print(f"Error {resp.status_code}: {resp.text}")
        break
else:
    print(f"Timed out after {TIMEOUT}s")
