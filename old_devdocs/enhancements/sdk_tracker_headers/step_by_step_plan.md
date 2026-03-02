# SDK Tracker Headers - Step-by-Step Implementation Plan

## Overview

This plan implements the proposal in `sdk_usage_tracker_proposal.md` to migrate from mixed tracking mechanisms (query params and JSON body) to unified custom header tracking (`X-SDK-Function: xxx`).

**Goals:**
- Track all operations: SERP, Web Scrapers, Web Unlocker
- Unified tracking via HTTP headers
- Clean, industry-standard implementation

---

## Current State Analysis

Before implementing, understand the **current** tracking mechanisms:

| API Type | Current Method | Location | File |
|----------|---------------|----------|------|
| Dataset API (Web Scrapers) | Query param `?sdk_function=xxx` | `params["sdk_function"]` | `api_client.py:70` |
| SERP API (sync mode) | JSON body `{"sdk_function": "xxx"}` | `payload["sdk_function"]` | `serp/base.py:191` |
| Web Unlocker (sync mode) | JSON body `{"sdk_function": "xxx"}` | `payload["sdk_function"]` | `web_unlocker.py:181` |
| Async Unblocker | **NOT TRACKED** | - | `async_unblocker.py` |

**Key insight:** Async mode for SERP and Web Unlocker currently has NO tracking.

---

## Phase 1: Add Static Headers to Engine

### Step 1.1: Update `_version.py` Import Structure

**File:** `src/brightdata/_version.py`

Ensure version is importable:
```python
__version__ = "2.1.0"
```

No changes needed - already correct.

---

### Step 1.2: Add Static X-SDK Headers to AsyncEngine

**File:** `src/brightdata/core/engine.py`

**Current code (lines 89-97):**
```python
self._session = aiohttp.ClientSession(
    connector=connector,
    timeout=self.timeout,
    headers={
        "Authorization": f"Bearer {self.bearer_token}",
        "Content-Type": "application/json",
        "User-Agent": "brightdata-sdk/2.0.0",  # BUG: hardcoded wrong version
    },
)
```

**Updated code:**

First, add imports at top of file:
```python
import platform
from .._version import __version__
```

Then update session creation:
```python
self._session = aiohttp.ClientSession(
    connector=connector,
    timeout=self.timeout,
    headers={
        "Authorization": f"Bearer {self.bearer_token}",
        "Content-Type": "application/json",
        "User-Agent": f"brightdata-sdk/{__version__}",
        # Static tracking headers
        "X-SDK-Name": "brightdata-python",
        "X-SDK-Version": __version__,
        "X-SDK-Platform": f"Python/{platform.python_version()}",
    },
)
```

**Changes:**
1. Import `__version__` from `_version.py` (fixes hardcoded version bug)
2. Import `platform` for Python version
3. Add `X-SDK-Name`, `X-SDK-Version`, `X-SDK-Platform` headers

---

## Phase 2: Update Dataset API Client (Web Scrapers)

Web Scrapers use the Dataset API and currently pass `sdk_function` via **query params**.

### Step 2.1: Update DatasetAPIClient

**File:** `src/brightdata/scrapers/api_client.py`

**Current code (lines 64-74):**
```python
params = {
    "dataset_id": dataset_id,
    "include_errors": str(include_errors).lower(),
}

if sdk_function:
    params["sdk_function"] = sdk_function  # Query param - REMOVE

async with self.engine.post_to_url(
    self.TRIGGER_URL, json_data=payload, params=params
) as response:
```

**Updated code:**
```python
params = {
    "dataset_id": dataset_id,
    "include_errors": str(include_errors).lower(),
}

# Send sdk_function via header instead of query param
headers = {"X-SDK-Function": sdk_function} if sdk_function else {}

async with self.engine.post_to_url(
    self.TRIGGER_URL, json_data=payload, params=params, headers=headers
) as response:
```

**Changes:**
1. Remove `sdk_function` from query params
2. Add `X-SDK-Function` header

---

### Step 2.2: Verify Scraper Base Class (No Changes Needed)

**File:** `src/brightdata/scrapers/base.py`

The `sdk_function` flow is already correct:
```python
sdk_function = get_caller_function_name()

result = await self.workflow_executor.execute(
    payload=payload,
    dataset_id=self.DATASET_ID,
    sdk_function=sdk_function,  # Flows through to DatasetAPIClient
    ...
)
```

No changes needed - it flows through to `DatasetAPIClient.trigger()`.

---

## Phase 3: Update SERP API

SERP currently sends `sdk_function` in the **JSON body** (not query params).

### Step 3.1: Update Sync Mode in BaseSERPService

**File:** `src/brightdata/api/serp/base.py`

**Current code in `_search_single_async` (lines 182-198):**
```python
payload = {
    "zone": zone,
    "url": search_url,
    "format": response_format,
    "method": "GET",
}

sdk_function = get_caller_function_name()
if sdk_function:
    payload["sdk_function"] = sdk_function  # JSON body - REMOVE

async def _make_request():
    async with self.engine.post_to_url(
        f"{self.engine.BASE_URL}{self.ENDPOINT}",
        json_data=payload,
        timeout=aiohttp.ClientTimeout(total=self.timeout),
    ) as response:
```

**Updated code:**
```python
payload = {
    "zone": zone,
    "url": search_url,
    "format": response_format,
    "method": "GET",
}

sdk_function = get_caller_function_name()
# Send via header instead of JSON body
headers = {"X-SDK-Function": sdk_function} if sdk_function else {}

async def _make_request():
    async with self.engine.post_to_url(
        f"{self.engine.BASE_URL}{self.ENDPOINT}",
        json_data=payload,
        timeout=aiohttp.ClientTimeout(total=self.timeout),
        headers=headers,  # Add headers parameter
    ) as response:
```

**Changes:**
1. Remove `sdk_function` from JSON payload
2. Add `X-SDK-Function` header to request

---

### Step 3.2: Update Async Mode in BaseSERPService

**File:** `src/brightdata/api/serp/base.py`

**Current code in `_search_single_async_unblocker` (line 349):**
```python
# Trigger async request (no customer_id needed - derived from token)
response_id = await self.async_unblocker.trigger(zone=zone, url=search_url)
```

**Updated code:**
```python
sdk_function = get_caller_function_name()

# Trigger async request with tracking
response_id = await self.async_unblocker.trigger(
    zone=zone,
    url=search_url,
    sdk_function=sdk_function,  # Pass for tracking
)
```

**Changes:**
1. Capture `sdk_function` before calling trigger
2. Pass `sdk_function` to `async_unblocker.trigger()`

---

## Phase 4: Update Web Unlocker API

Web Unlocker currently sends `sdk_function` in the **JSON body** (not query params).

### Step 4.1: Update Sync Mode in WebUnlockerService

**File:** `src/brightdata/api/web_unlocker.py`

**Current code in `_scrape_single_async` (lines 169-186):**
```python
payload: Dict[str, Any] = {
    "zone": zone,
    "url": url,
    "format": response_format,
    "method": method,
}

if country:
    payload["country"] = country.upper()

sdk_function = get_caller_function_name()
if sdk_function:
    payload["sdk_function"] = sdk_function  # JSON body - REMOVE

try:
    async with self.engine.post_to_url(
        f"{self.engine.BASE_URL}{self.ENDPOINT}", json_data=payload
    ) as response:
```

**Updated code:**
```python
payload: Dict[str, Any] = {
    "zone": zone,
    "url": url,
    "format": response_format,
    "method": method,
}

if country:
    payload["country"] = country.upper()

sdk_function = get_caller_function_name()
# Send via header instead of JSON body
headers = {"X-SDK-Function": sdk_function} if sdk_function else {}

try:
    async with self.engine.post_to_url(
        f"{self.engine.BASE_URL}{self.ENDPOINT}",
        json_data=payload,
        headers=headers,  # Add headers parameter
    ) as response:
```

**Changes:**
1. Remove `sdk_function` from JSON payload
2. Add `X-SDK-Function` header to request

---

### Step 4.2: Update Async Mode in WebUnlockerService

**File:** `src/brightdata/api/web_unlocker.py`

**Current code in `_scrape_single_async_unblocker` (lines 302-312):**
```python
# Trigger async request
try:
    response_id = await self.async_unblocker.trigger(
        zone=zone,
        url=url,
        format=response_format,
        method=method,
        country=country.upper() if country else None,
    )
```

**Updated code:**
```python
sdk_function = get_caller_function_name()

# Trigger async request with tracking
try:
    response_id = await self.async_unblocker.trigger(
        zone=zone,
        url=url,
        format=response_format,
        method=method,
        country=country.upper() if country else None,
        sdk_function=sdk_function,  # Pass for tracking
    )
```

**Changes:**
1. Capture `sdk_function` before calling trigger
2. Pass `sdk_function` to `async_unblocker.trigger()`

---

## Phase 5: Update Async Unblocker Client

This client is used by both SERP and Web Unlocker for async mode.

### Step 5.1: Update trigger() Method

**File:** `src/brightdata/api/async_unblocker.py`

**Current signature (lines 68-74):**
```python
async def trigger(
    self,
    zone: str,
    url: str,
    customer: Optional[str] = None,
    **kwargs,  # Additional params like country, format, etc.
) -> Optional[str]:
```

**Updated signature:**
```python
async def trigger(
    self,
    zone: str,
    url: str,
    customer: Optional[str] = None,
    sdk_function: Optional[str] = None,  # Add parameter
    **kwargs,  # Additional params like country, format, etc.
) -> Optional[str]:
```

**Current request code (lines 107-113):**
```python
async with self.engine.post_to_url(
    f"{self.engine.BASE_URL}{self.TRIGGER_ENDPOINT}", params=params, json_data=payload
) as response:
    # Extract response_id from x-response-id header
    response_id = response.headers.get("x-response-id")
    return response_id
```

**Updated request code:**
```python
# Send sdk_function via header
headers = {"X-SDK-Function": sdk_function} if sdk_function else {}

async with self.engine.post_to_url(
    f"{self.engine.BASE_URL}{self.TRIGGER_ENDPOINT}",
    params=params,
    json_data=payload,
    headers=headers,  # Add headers
) as response:
    # Extract response_id from x-response-id header
    response_id = response.headers.get("x-response-id")
    return response_id
```

**Changes:**
1. Add `sdk_function` parameter to method signature
2. Send `X-SDK-Function` header with request

---

## Phase 6: Testing

### Step 6.1: Create Unit Tests for Tracking Headers

**File:** `tests/unit/test_tracking_headers.py` (new file)

```python
import pytest
import platform
from unittest.mock import AsyncMock, MagicMock, patch

from brightdata._version import __version__


class TestStaticTrackingHeaders:
    """Test static SDK headers are set on session."""

    @pytest.mark.asyncio
    async def test_static_headers_set_on_session(self):
        """Verify X-SDK-Name, X-SDK-Version, X-SDK-Platform are set."""
        with patch("aiohttp.ClientSession") as mock_session:
            from brightdata.core.engine import AsyncEngine

            engine = AsyncEngine(bearer_token="test_token")
            await engine.__aenter__()

            # Verify session was created with correct headers
            call_kwargs = mock_session.call_args[1]
            headers = call_kwargs["headers"]

            assert headers["X-SDK-Name"] == "brightdata-python"
            assert headers["X-SDK-Version"] == __version__
            assert headers["X-SDK-Platform"] == f"Python/{platform.python_version()}"
            assert f"brightdata-sdk/{__version__}" in headers["User-Agent"]

            await engine.__aexit__(None, None, None)


class TestDynamicTrackingHeaders:
    """Test X-SDK-Function header is sent per-request."""

    @pytest.mark.asyncio
    async def test_dataset_api_sends_header_not_query_param(self):
        """Verify DatasetAPIClient sends header, not query param."""
        # Mock engine.post_to_url and verify:
        # - headers contains X-SDK-Function
        # - params does NOT contain sdk_function
        pass

    @pytest.mark.asyncio
    async def test_serp_sends_header_not_json_body(self):
        """Verify SERP sends header, not JSON body payload."""
        # Mock engine.post_to_url and verify:
        # - headers contains X-SDK-Function
        # - json_data does NOT contain sdk_function
        pass

    @pytest.mark.asyncio
    async def test_web_unlocker_sends_header_not_json_body(self):
        """Verify Web Unlocker sends header, not JSON body payload."""
        # Mock engine.post_to_url and verify:
        # - headers contains X-SDK-Function
        # - json_data does NOT contain sdk_function
        pass

    @pytest.mark.asyncio
    async def test_async_unblocker_sends_header(self):
        """Verify AsyncUnblockerClient.trigger() sends header."""
        # Mock engine.post_to_url and verify:
        # - headers contains X-SDK-Function
        pass


class TestAsyncModeTracking:
    """Test tracking works in async mode (was previously missing)."""

    @pytest.mark.asyncio
    async def test_serp_async_mode_passes_sdk_function(self):
        """Verify SERP async mode passes sdk_function to unblocker."""
        pass

    @pytest.mark.asyncio
    async def test_web_unlocker_async_mode_passes_sdk_function(self):
        """Verify Web Unlocker async mode passes sdk_function to unblocker."""
        pass
```

---

### Step 6.2: Integration Test Verification

Manually verify headers are received by the API:

1. Enable debug logging in aiohttp
2. Make test requests to each API type:
   - Web Scraper (Dataset API)
   - SERP sync mode
   - SERP async mode
   - Web Unlocker sync mode
   - Web Unlocker async mode
3. Verify `X-SDK-Function` header appears in request logs
4. Verify `sdk_function` is NOT in query params or JSON body

---

## Summary Checklist

### Files to Modify

| File | Change | Phase |
|------|--------|-------|
| `src/brightdata/core/engine.py` | Add static headers, fix version import | 1 |
| `src/brightdata/scrapers/api_client.py` | Replace query param with header | 2 |
| `src/brightdata/api/serp/base.py` | Replace JSON body with header, pass to async | 3 |
| `src/brightdata/api/web_unlocker.py` | Replace JSON body with header, pass to async | 4 |
| `src/brightdata/api/async_unblocker.py` | Add sdk_function param and header | 5 |
| `tests/unit/test_tracking_headers.py` | New test file | 6 |

### Files to Verify (No Changes Expected)

| File | Verification |
|------|--------------|
| `src/brightdata/_version.py` | Already has `__version__ = "2.1.0"` |
| `src/brightdata/scrapers/base.py` | Already passes sdk_function through workflow |
| `src/brightdata/scrapers/workflow.py` | Already passes sdk_function to api_client |

---

## Migration Summary

| API | Before | After |
|-----|--------|-------|
| Dataset API | Query param `?sdk_function=xxx` | Header `X-SDK-Function: xxx` |
| SERP (sync) | JSON body `{"sdk_function": "xxx"}` | Header `X-SDK-Function: xxx` |
| SERP (async) | **Not tracked** | Header `X-SDK-Function: xxx` |
| Web Unlocker (sync) | JSON body `{"sdk_function": "xxx"}` | Header `X-SDK-Function: xxx` |
| Web Unlocker (async) | **Not tracked** | Header `X-SDK-Function: xxx` |

---

## Estimated Effort

| Phase | Effort | Priority |
|-------|--------|----------|
| Phase 1: Static Headers | 15 min | High |
| Phase 2: Dataset API | 15 min | High |
| Phase 3: SERP | 30 min | High |
| Phase 4: Web Unlocker | 30 min | High |
| Phase 5: Async Unblocker | 15 min | High |
| Phase 6: Testing | 1-2 hours | High |

**Total: ~3-4 hours**

---

## Success Criteria

1. All requests include static headers: `X-SDK-Name`, `X-SDK-Version`, `X-SDK-Platform`
2. All operation requests include `X-SDK-Function` header
3. `sdk_function` removed from query params (Dataset API)
4. `sdk_function` removed from JSON payloads (SERP, Web Unlocker)
5. Async mode now tracks operations (previously missing)
6. All existing tests pass
7. New tracking header tests pass
