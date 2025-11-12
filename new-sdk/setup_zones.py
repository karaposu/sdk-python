#!/usr/bin/env python3
"""
Quick script to list and create Bright Data zones.
"""

import os
import sys
import requests
import json
from pathlib import Path

# Load .env
try:
    from dotenv import load_dotenv
    env_file = Path(__file__).parent.parent / '.env'
    if env_file.exists():
        load_dotenv(env_file)
except ImportError:
    pass

api_token = os.getenv("BRIGHTDATA_API_TOKEN") or os.getenv("BRIGHTDATA_API_KEY")

if not api_token:
    print("❌ No API token found!")
    sys.exit(1)

headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}

print("=" * 80)
print("BRIGHT DATA ZONE MANAGEMENT")
print("=" * 80)
print()

# List existing zones
print("📋 Listing existing zones...")
print("-" * 80)

try:
    response = requests.get(
        'https://api.brightdata.com/zone/get_active_zones',
        headers=headers,
        timeout=10
    )
    
    if response.status_code == 200:
        zones = response.json() or []
        print(f"✅ Found {len(zones)} zones:")
        print()
        
        for i, zone in enumerate(zones, 1):
            zone_name = zone.get('name', 'N/A')
            zone_type = zone.get('plan', {}).get('type', 'N/A')
            status = zone.get('status', 'N/A')
            print(f"  {i}. {zone_name}")
            print(f"     Type: {zone_type}")
            print(f"     Status: {status}")
            print()
        
        zone_names = {z.get('name') for z in zones}
        
        # Check if sdk_unlocker exists
        if 'sdk_unlocker' not in zone_names:
            print("⚠️  Zone 'sdk_unlocker' not found!")
            print()
            print("🔧 Creating 'sdk_unlocker' zone automatically...")
            print("-" * 80)
            
            payload = {
                "plan": {
                    "type": "unblocker"
                },
                "zone": {
                    "name": "sdk_unlocker",
                    "type": "unblocker"
                }
            }
            
            create_response = requests.post(
                'https://api.brightdata.com/zone',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if create_response.status_code in [200, 201]:
                print("✅ Zone 'sdk_unlocker' created successfully!")
                print()
                print("Zone details:")
                try:
                    print(json.dumps(create_response.json(), indent=2))
                except:
                    print(create_response.text)
            elif create_response.status_code == 409:
                print("✅ Zone 'sdk_unlocker' already exists!")
            else:
                print(f"❌ Failed to create zone: {create_response.status_code}")
                print(f"Response: {create_response.text}")
        else:
            print("✅ Zone 'sdk_unlocker' already exists!")
            
    elif response.status_code == 401:
        print("❌ Authentication failed! Check your API token.")
        print(f"Response: {response.text}")
    else:
        print(f"❌ Failed to get zones: {response.status_code}")
        print(f"Response: {response.text}")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("Done!")
print("=" * 80)

