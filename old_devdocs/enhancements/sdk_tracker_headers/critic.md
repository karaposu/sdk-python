# SDK Tracker Headers - Implementation Plan Critique

## Executive Summary

After thorough code analysis, I've identified **several significant issues** with the step-by-step plan. The most critical is a **fundamental misunderstanding** of how `sdk_function` is currently sent across different API types.

**Verdict: Plan needs revision before implementation.**

---

## Critical Issues

### Issue #1: SERP and Web Unlocker Use JSON Body, NOT Query Params

**Severity: HIGH - Plan is based on incorrect assumption**

The plan assumes `sdk_function` is sent via query params everywhere. This is **wrong**.

**Actual Current Implementation:**

| API Type | How sdk_function is sent | File | Line |
|----------|--------------------------|------|------|
| Dataset API (Web Scrapers) | Query param `?sdk_function=xxx` | `api_client.py` | 69-70 |
| SERP API | JSON body `{"sdk_function": "xxx"}` | `serp/base.py` | 191 |
| Web Unlocker | JSON body `{"sdk_function": "xxx"}` | `web_unlocker.py` | 181 |
| Async Unblocker | **NOT SENT AT ALL** | `async_unblocker.py` | - |

**Evidence from code:**

```python
# serp/base.py line 189-191
sdk_function = get_caller_function_name()
if sdk_function:
    payload["sdk_function"] = sdk_function  # <-- JSON BODY, not query param!

# web_unlocker.py line 179-181
sdk_function = get_caller_function_name()
if sdk_function:
    payload["sdk_function"] = sdk_function  # <-- JSON BODY, not query param!
```

**Impact:** Phase 4 and Phase 5 describe removing query params that don't exist. The plan needs to describe removing `sdk_function` from JSON payloads instead.

---

### Issue #2: Async Mode Has NO Tracking At All

**Severity: HIGH - Existing gap not addressed**

When using `mode="async"` for SERP or Web Unlocker, the `sdk_function` is **never passed** to `AsyncUnblockerClient.trigger()`.

**Evidence:**

```python
# serp/base.py line 349 - async mode
response_id = await self.async_unblocker.trigger(zone=zone, url=search_url)
# ^ No sdk_function passed!

# web_unlocker.py line 306-312 - async mode
response_id = await self.async_unblocker.trigger(
    zone=zone,
    url=url,
    format=response_format,
    method=method,
    country=country.upper() if country else None,
)
# ^ No sdk_function passed!
```

**Impact:** The plan correctly identifies AsyncUnblockerClient needs updating, but fails to note that callers (SERP and WebUnlocker) also need to pass the sdk_function to trigger().

---

### Issue #3: Version Already Hardcoded and Wrong

**Severity: MEDIUM - Pre-existing bug**

`engine.py` line 95 hardcodes version as `"2.0.0"` but `_version.py` says `"2.1.0"`.

```python
# engine.py line 95
"User-Agent": "brightdata-sdk/2.0.0",  # <-- Wrong! Should be 2.1.0
```

This is a bug that exists regardless of this plan. The plan correctly identifies this needs fixing.

---

### Issue #4: Phase 2 Helper Method is Unnecessary Complexity

**Severity: LOW - Over-engineering**

The proposed `_get_tracking_headers()` method is essentially:

```python
def _get_tracking_headers(self, sdk_function: Optional[str] = None) -> Dict[str, str]:
    headers = {}
    if sdk_function:
        headers["X-SDK-Function"] = sdk_function
    return headers
```

This adds a method for a 3-line operation. Just inline it:

```python
headers = {"X-SDK-Function": sdk_function} if sdk_function else {}
```

**Recommendation:** Remove Phase 2 entirely. Inline the header creation at each call site.

---

### Issue #5: Missing Removal of sdk_function from JSON Payloads

**Severity: HIGH - Incomplete migration**

The plan only mentions removing `sdk_function` from query params (DatasetAPIClient). It does NOT mention removing it from:

1. SERP payload (`serp/base.py` line 191)
2. Web Unlocker payload (`web_unlocker.py` line 181)

**If not removed:** Backend will receive BOTH JSON body AND header, which defeats the purpose of clean migration.

---

## Code Accuracy Issues

### Line Numbers in Plan vs Actual Code

| File | Plan Says | Actual |
|------|-----------|--------|
| `engine.py` | "line ~89-97" | Lines 89-97 (correct) |
| `api_client.py` | "line ~64-73" | Lines 64-73 (correct) |

Line numbers are accurate.

### File Locations

All file paths in the plan are correct.

---

## Missing Considerations

### 1. Async Unblocker Callers Need Updates

The plan says to add `sdk_function` parameter to `AsyncUnblockerClient.trigger()`, but doesn't mention updating the callers:

- `serp/base.py` `_search_single_async_unblocker()` line 349
- `web_unlocker.py` `_scrape_single_async_unblocker()` line 306

These need to pass `sdk_function` to `trigger()`.

### 2. No Test for Payload Cleanup

The test plan includes tests for header presence but no tests verifying:
- `sdk_function` removed from Dataset API query params
- `sdk_function` removed from SERP JSON payload
- `sdk_function` removed from Web Unlocker JSON payload

### 3. Circular Import Risk

The plan proposes:
```python
from .._version import __version__
```

This should be safe, but worth verifying no circular imports exist in the import chain.

### 4. Static Headers at Module Level vs Runtime

The plan adds `platform.python_version()` to session headers. This is evaluated at session creation time, which is correct. However, consider:

```python
import platform
# This is evaluated once at import time, which is fine
"X-SDK-Platform": f"Python/{platform.python_version()}"
```

This is fine - Python version doesn't change during runtime.

---

## Architectural Observations

### Current Tracking is Inconsistent

| API | Current Tracking Method |
|-----|------------------------|
| Dataset API | Query param |
| SERP | JSON body |
| Web Unlocker | JSON body |
| Async Unblocker | None |

Moving to headers standardizes this. Good architectural decision.

### Header Flow Through Engine

The `AsyncEngine` design already supports per-request headers:

```python
# engine.py line 185-186
request_headers = dict(self._session.headers)
if headers:
    request_headers.update(headers)  # Per-request headers merge with session headers
```

This means:
- Static headers (`X-SDK-Name`, `X-SDK-Version`, `X-SDK-Platform`) go on session
- Dynamic header (`X-SDK-Function`) goes per-request

This is the correct approach.

---

## Revised Phase Structure

Based on analysis, here's what the phases should actually cover:

### Phase 1: Engine Static Headers (Correct as-is)
- Add version import
- Add static X-SDK-* headers
- Fix User-Agent version

### Phase 2: Remove - Helper Method Not Needed
- Delete this phase
- Inline header creation is simpler

### Phase 3: Dataset API Client (Correct with clarification)
- Remove `sdk_function` from query params
- Add `X-SDK-Function` header

### Phase 4: SERP API (NEEDS CORRECTION)
- Remove `sdk_function` from JSON payload (NOT query params)
- Add `X-SDK-Function` header to sync mode request
- Pass `sdk_function` to async unblocker trigger

### Phase 5: Web Unlocker API (NEEDS CORRECTION)
- Remove `sdk_function` from JSON payload (NOT query params)
- Add `X-SDK-Function` header to sync mode request
- Pass `sdk_function` to async unblocker trigger

### Phase 5.5: Async Unblocker Client (NEW)
- Add `sdk_function` parameter to `trigger()` method
- Send as `X-SDK-Function` header

### Phase 6: Testing (NEEDS EXPANSION)
- Test static headers on session
- Test X-SDK-Function header on requests
- Test sdk_function REMOVED from query params
- Test sdk_function REMOVED from JSON payloads
- Test async mode passes tracking

---

## Summary of Required Plan Changes

| Section | Issue | Fix Required |
|---------|-------|--------------|
| Phase 3 | Says "query param" | Correct - only Dataset API uses query params |
| Phase 4 | Says "query param" | Wrong - SERP uses JSON body, must remove from payload |
| Phase 5 | Says "query param" | Wrong - Web Unlocker uses JSON body, must remove from payload |
| Phase 2 | Helper method | Remove - unnecessary complexity |
| Phase 4 | Missing caller update | Add: SERP must pass sdk_function to async_unblocker.trigger() |
| Phase 5 | Missing caller update | Add: WebUnlocker must pass sdk_function to async_unblocker.trigger() |
| Phase 6 | Tests incomplete | Add tests for JSON body removal |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Backend not receiving headers | Low | High | Test with debug logging before deploy |
| Breaking existing tracking | Medium | Medium | Coordinate with backend team |
| Circular import | Low | Low | Test imports after changes |
| Missing edge cases | Medium | Low | Comprehensive test coverage |

---

## Recommendation

**Do not proceed with implementation until plan is revised to:**

1. Correctly identify current tracking mechanisms (JSON body vs query params)
2. Include removal of `sdk_function` from JSON payloads for SERP and Web Unlocker
3. Include updates to SERP and Web Unlocker to pass `sdk_function` to async unblocker
4. Remove unnecessary helper method (Phase 2)
5. Expand test coverage to verify removal of old tracking mechanisms

Once revised, the implementation is straightforward and the architectural approach is sound.
