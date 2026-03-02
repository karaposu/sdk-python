# SDK Usage Tracking - Proposal

## Two Tracking Needs

Bright Data needs to track two things from SDK requests:

| Need | Question | Header |
|------|----------|--------|
| **SDK Identity** | "Which SDK and version?" | `User-Agent` (existing) |
| **Function Tracking** | "Which function was called?" | `X-SDK-Function` (new) |

---

## 1. User-Agent Header (No Changes)

**Purpose:** Identify SDK name and version

**Current implementation:**
```python
"User-Agent": "brightdata-sdk/2.0.0"
```

**After (bug fix only):**
```python
"User-Agent": f"brightdata-sdk/{__version__}"  # Dynamic version
```

**What stays the same:**
- Format: `brightdata-sdk/X.X.X`
- Purpose: SDK identity & version tracking
- Location: Session-level header

**Only change:** Fix hardcoded `2.0.0` → use actual version from `_version.py`

**Analytics this provides:**
```
User-Agent: brightdata-sdk/2.1.0
└── "Request came from Python SDK version 2.1.0"
```

---

## 2. X-SDK-Function Header (New)

**Purpose:** Track which SDK function was called

**Current implementation (inconsistent, problematic):**

| API | Current Method | Problem |
|-----|---------------|---------|
| Dataset API | Query param `?sdk_function=xxx` | Tracking in URL |
| SERP API | JSON body `{"sdk_function": "xxx"}` | Tracking in payload |
| Web Unlocker | JSON body `{"sdk_function": "xxx"}` | Tracking in payload |
| Async mode | **Not tracked at all** | Missing data |

**Proposed implementation (unified):**
```python
# New header added per-request
"X-SDK-Function": "products"  # or "google", "scrape", etc.
```

**What changes:**
- Remove `sdk_function` from query params (Dataset API)
- Remove `sdk_function` from JSON body (SERP, Web Unlocker)
- Add `X-SDK-Function` header to all requests
- Fix async mode tracking gap

**Analytics this provides:**
```
X-SDK-Function: products
└── "User called amazon.products() function"

X-SDK-Function: google
└── "User called search.google() function"
```

---

## Summary of Changes

| Component | Before | After |
|-----------|--------|-------|
| `User-Agent` header | `brightdata-sdk/2.0.0` (hardcoded) | `brightdata-sdk/2.1.0` (dynamic) |
| `User-Agent` format | `brightdata-sdk/X.X.X` | **Same** (no change) |
| `sdk_function` query param | Used by Dataset API | **Removed** |
| `sdk_function` JSON body | Used by SERP/Web Unlocker | **Removed** |
| `X-SDK-Function` header | Did not exist | **New** - tracks function calls |
| Async mode tracking | Missing | **Fixed** |

---

## Resulting HTTP Request

```http
POST /datasets/v3/trigger?dataset_id=gd_abc123 HTTP/1.1
Host: api.brightdata.com
Authorization: Bearer xxx
Content-Type: application/json
User-Agent: brightdata-sdk/2.1.0        ← SDK identity (unchanged format)
X-SDK-Function: products                ← Function tracking (NEW)

{"url": "https://amazon.com/dp/B123"}
```

**Note:**
- `User-Agent` format unchanged
- `sdk_function` no longer in URL or JSON body
- New `X-SDK-Function` header handles function tracking

---

## Why This Approach?

### Why keep User-Agent as-is?
- Already working for SDK identity tracking
- Standard HTTP header
- Bright Data backend already logs it
- No reason to change

### Why add X-SDK-Function header?
- **Consistency:** Single mechanism for all APIs (was 3 different ways)
- **Clean separation:** Tracking metadata in headers, API data in params/body
- **Industry standard:** AWS, Google, Stripe use custom headers for tracking
- **Fixes gap:** Async mode now tracked (was missing)

---

## Backend Analytics

With these two headers, Bright Data can answer:

| Question | How to Answer |
|----------|---------------|
| How many SDK users? | Count requests with `User-Agent: brightdata-sdk/*` |
| Which SDK versions? | Group by `User-Agent` |
| Which functions most used? | Group by `X-SDK-Function` |
| SDK vs raw API usage? | Requests with vs without `User-Agent: brightdata-sdk/*` |

---

## Implementation Summary

1. **User-Agent:** Fix version bug only (no format change)
2. **X-SDK-Function:** New header, replaces query param and JSON body tracking
3. **Async mode:** Add tracking (was missing)
