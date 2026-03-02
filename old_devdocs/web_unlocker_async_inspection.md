# Web Unlocker Async Mode Inspection

**Date:** 2025-12-31
**Status:** Investigation Complete

## Overview

This document details the findings from testing Bright Data's async endpoints for Web Unlocker vs SERP services.

## Endpoints

### Async Trigger Endpoint
```
POST https://api.brightdata.com/unblocker/req
```

**Query Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `zone` | Yes | Zone name (e.g., `web_unlocker5`, `sdk_serp`) |
| `customer` | See notes | Customer ID (e.g., `hl_67e5ed38`) |

**Request Body (JSON):**
```json
{
  "url": "https://example.com",
  "format": "raw",      // optional: "raw" or "json"
  "method": "GET",      // optional: HTTP method
  "flags": "country-de" // optional: country flag
}
```

**Response:**
- HTTP 200 on success
- `x-response-id` header contains the ID for polling
- Body: `{"response_id": "s1w6t1767178652120riov16c63ojg"}`

### Async Poll/Fetch Endpoint
```
GET https://api.brightdata.com/unblocker/get_result
```

**Query Parameters:**
| Parameter | Required | Description |
|-----------|----------|-------------|
| `zone` | Yes | Zone name (must match trigger) |
| `response_id` | Yes | ID from trigger response |
| `customer` | See notes | Customer ID (must match trigger) |

**Response:**
- HTTP 202 + `"Request is pending"` → Still processing
- HTTP 200 + data → Ready, returns scraped content

## Customer Parameter Findings

### Official Documentation Claims
The Bright Data documentation example includes `customer` parameter:
```bash
curl "https://api.brightdata.com/unblocker/req?customer=hl_67e5ed38&zone=web_unlocker5" ...
```

### Test Results

| Test Case | Customer Param | Result | Time |
|-----------|---------------|--------|------|
| SERP async | ❌ No | ✅ Works | ~3s |
| SERP async | ✅ Yes | ✅ Works | ~3s |
| Web Unlocker async | ❌ No | ✅ Works | ~145s |
| Web Unlocker async | ✅ Yes | ✅ Works | ~134s |

**Conclusion:** The `customer` parameter is **NOT required** for either service. Both SERP and Web Unlocker async work with or without it. The key difference is response time - Web Unlocker takes ~134-145 seconds regardless of customer parameter.

### How to Get Customer ID
```bash
# From /customer/bw endpoint
curl "https://api.brightdata.com/customer/bw" -H "Authorization: Bearer $TOKEN"

# Response includes:
# {"c_67e5ed38": {"customer_id": "hl_67e5ed38", ...}}
```

## Response Time Comparison

### Test Setup
- Continuous polling every 2 seconds
- Same test URL: `https://example.com`
- Both using async endpoints (`/unblocker/req` + `/unblocker/get_result`)

### Results

| Service | Zone Type | Time to Ready | Notes |
|---------|-----------|---------------|-------|
| SERP | `serp` | **~3 seconds** | Ready on first poll |
| Web Unlocker | `unblocker` | **~134 seconds** | ~2.2 minutes |

**Web Unlocker async is ~45x slower than SERP async.**

### Raw Test Output (Web Unlocker)
```
[13:57:31] Triggering request...
  Response ID: s1w6t1767178652120riov16c63ojg

Polling every 2 seconds...
  [2s] Still pending...
  [13s] Still pending...
  [24s] Still pending...
  ...
  [121s] Still pending...
  [132s] Still pending...

[13:59:46] ✅ READY!
  Time elapsed: 134.3 seconds
  Data length: 513 bytes
```

### Raw Test Output (SERP)
```
[10:00:27] Triggering request...
  Response ID: s2w6t1767175634712rh73f36kq1c8

Polling every 2 seconds...
  Poll 1: ✅ READY (59407 bytes)

Time elapsed: ~3 seconds
```

## Sync vs Async Comparison

### Web Unlocker
| Mode | Endpoint | Response Time |
|------|----------|---------------|
| Sync | `POST /request` | **~2-5 seconds** |
| Async | `/unblocker/req` + `/unblocker/get_result` | **~134 seconds** |

**Sync is ~30-60x faster for Web Unlocker!**

### SERP
| Mode | Endpoint | Response Time |
|------|----------|---------------|
| Sync | `POST /request` | ~3-5 seconds |
| Async | `/unblocker/req` + `/unblocker/get_result` | ~3 seconds |

**Similar performance for SERP.**

## Working Examples

### Web Unlocker Async (curl)
```bash
# Step 1: Trigger
RESPONSE_ID=$(curl -s "https://api.brightdata.com/unblocker/req?customer=hl_67e5ed38&zone=web_unlocker5" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url":"https://example.com"}' \
  | jq -r '.response_id')

echo "Response ID: $RESPONSE_ID"

# Step 2: Poll (repeat until HTTP 200)
curl "https://api.brightdata.com/unblocker/get_result?customer=hl_67e5ed38&zone=web_unlocker5&response_id=$RESPONSE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

### SERP Async (curl)
```bash
# Step 1: Trigger
RESPONSE_ID=$(curl -s "https://api.brightdata.com/unblocker/req?zone=sdk_serp" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"url":"https://www.google.com/search?q=test&brd_json=1"}' \
  | jq -r '.response_id')

# Step 2: Poll
curl "https://api.brightdata.com/unblocker/get_result?zone=sdk_serp&response_id=$RESPONSE_ID" \
  -H "Authorization: Bearer $TOKEN"
```

## SDK Implications

### Current Implementation
- `src/brightdata/api/web_unlocker.py` - Has `mode="async"` option
- `src/brightdata/api/async_unblocker.py` - Client for async endpoints
- Default `poll_timeout=30` seconds

### Problems
1. **30-second timeout is too short** for Web Unlocker async (~134 seconds needed)
2. **Async mode is slower than sync** for Web Unlocker (defeats the purpose)
3. **Documentation in code is misleading** about `customer` parameter requirement

### Recommendations

| Option | Description | Pros | Cons |
|--------|-------------|------|------|
| **A. Remove Web Unlocker async** | Delete async mode for Web Unlocker | Simple, avoids confusion | Less feature parity |
| **B. Increase timeout** | Set `poll_timeout=180` for Web Unlocker | Keeps feature | Users wait 2+ min |
| **C. Add warning** | Document that async takes 2+ min | Transparent | Users may still be surprised |

**Recommended: Option A or C** - Web Unlocker sync is faster, so async mode has no practical benefit.

## Token Types

During testing, two token formats were observed:

| Format | Example | Usage |
|--------|---------|-------|
| Hex string | `fb28f17b77e57...` | Standard API token from `.env` |
| UUID | `7011787d-2ad5-424c-ae5f-52d0c3cd3336` | Alternative token format |

Both work with the API.

## Conclusion

1. **SERP async** - Works well, ~3 second response time, recommended
2. **Web Unlocker async** - Works but takes ~134 seconds, **not recommended**
3. **Customer parameter** - Optional for both, doesn't affect success
4. **For Web Unlocker, use sync mode** - It's 30-60x faster than async
