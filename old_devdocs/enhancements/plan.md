# Async SERP Implementation Plan

## Executive Summary

Add async mode to SERP API using Bright Data's `/unblocker/req` + `/unblocker/get_result` endpoints. Based on testing and analysis, this is a straightforward enhancement with minimal breaking changes.

**Key Insights:**
- ✅ customer_id NOT required (derived from token)
- ✅ `format="raw"` makes sync and async return identical structures
- ✅ Can reuse existing polling patterns and data normalization
- ✅ Backwards compatible - mode parameter defaults to "sync"

## Problem Analysis

### Core Challenge
Users need async mode for:
1. **Non-blocking operations** - Continue work while scraping
2. **Batch optimization** - Trigger multiple, collect later
3. **Webhook support** - Receive results via callback (future)

### Key Constraints
- Must maintain backwards compatibility (default sync behavior)
- Must follow existing SDK patterns (AsyncEngine, BaseSERPService)
- Must normalize responses (sync and async return different structures)
- Must be simple to use (minimal configuration)

### Critical Success Factors
1. Zero breaking changes for existing users
2. Simple API - just add `mode="async"` parameter
3. Reuse existing infrastructure (AsyncEngine, polling, normalizers)
4. Clear documentation and examples

## Architecture Analysis

### What We Can Reuse

#### 1. AsyncEngine (✅ Ready)
```python
# src/brightdata/core/engine.py
class AsyncEngine:
    - Bearer token auth (works for unblocker endpoints)
    - Rate limiting
    - Error handling
    - Session management
```

**Verdict:** No changes needed - works for both `/request` and `/unblocker/*`

#### 2. BaseSERPService (✅ Extend)
```python
# src/brightdata/api/serp/base.py
class BaseSERPService:
    - URL building (self.url_builder)
    - Data normalization (self.data_normalizer)
    - Error handling
    - Validation
```

**Verdict:** Add mode parameter, keep existing methods

#### 3. Data Normalizers (✅ Ready)
```python
# src/brightdata/api/serp/data_normalizer.py
- normalize() already handles SERP structure
- Works with format="raw" output (direct SERP data)
```

**Verdict:** No changes needed!

#### 4. Polling Pattern (⚠️ Adapt)
```python
# src/brightdata/utils/polling.py
poll_until_ready() - designed for datasets API with snapshot_id
```

**Verdict:** Need new polling for unblocker (uses response_id, different endpoints)

### What We Need to Create

#### 1. AsyncUnblockerClient
Small helper for `/unblocker/req` + `/unblocker/get_result` endpoints.

**Why separate class?**
- Clear separation of concerns
- Reusable for Web Unlocker async mode
- Easy to test in isolation
- Follows existing service pattern

#### 2. Async Polling Logic
Different from datasets polling:
- Datasets: `GET /datasets/v3/progress/{snapshot_id}` → status
- Unblocker: `GET /unblocker/get_result?zone=X&response_id=Y` → 202 or 200

#### 3. Mode Parameter Handling
Add to BaseSERPService.search():
- `mode="sync"` (default) → `/request` endpoint
- `mode="async"` → `/unblocker/req` + polling

## Implementation Options

### Option 1: Minimal Integration ⭐ **RECOMMENDED**

**Approach:** Add mode parameter to existing BaseSERPService

```python
class BaseSERPService:
    def __init__(self, engine, url_builder, data_normalizer, ...):
        self.engine = engine
        self.async_unblocker = AsyncUnblockerClient(engine)  # NEW

    async def search(self, query, zone, mode="sync", ...):
        if mode == "async":
            return await self._search_async_unblocker(...)
        else:
            return await self._search_single_async(...)  # Existing
```

**Pros:**
- ✅ Minimal code changes
- ✅ Backwards compatible (default mode="sync")
- ✅ Reuses all existing infrastructure
- ✅ Simple for users (just add one parameter)

**Cons:**
- ⚠️ BaseSERPService has two code paths
- ⚠️ Slightly more complex logic

**Verdict:** Best balance of simplicity and functionality



## Recommended Solution: Option 1

Implement minimal integration with mode parameter.

---

## Phase 1: Core Implementation

### Step 1.1: Create AsyncUnblockerClient

**File:** `src/brightdata/api/async_unblocker.py` (NEW)

**Purpose:** Handle `/unblocker/req` and `/unblocker/get_result` endpoints

```python
"""Async unblocker client for non-blocking requests."""

from typing import Optional, Any
from ..core.engine import AsyncEngine
from ..exceptions import APIError


class AsyncUnblockerClient:
    """
    Client for async unblocker endpoints.

    Supports both SERP and Web Unlocker async modes using:
    - POST /unblocker/req → returns x-response-id header
    - GET /unblocker/get_result → polls for results
    """

    TRIGGER_ENDPOINT = "/unblocker/req"
    FETCH_ENDPOINT = "/unblocker/get_result"

    def __init__(self, engine: AsyncEngine):
        """
        Initialize async unblocker client.

        Args:
            engine: AsyncEngine instance with bearer token auth
        """
        self.engine = engine

    async def trigger(
        self,
        zone: str,
        url: str,
        **kwargs  # Additional params like country, format, etc.
    ) -> Optional[str]:
        """
        Trigger async unblocker request.

        Args:
            zone: Zone name
            url: Target URL to scrape/search
            **kwargs: Additional request parameters

        Returns:
            response_id from x-response-id header, or None if failed
        """
        params = {"zone": zone}
        payload = {"url": url}

        # Merge additional params
        payload.update(kwargs)

        async with self.engine.post_to_url(
            f"{self.engine.BASE_URL}{self.TRIGGER_ENDPOINT}",
            params=params,
            json_data=payload
        ) as response:
            # Extract response_id from header
            response_id = response.headers.get("x-response-id")
            return response_id

    async def get_status(
        self,
        zone: str,
        response_id: str
    ) -> str:
        """
        Check if response is ready.

        Args:
            zone: Zone name
            response_id: Response ID from trigger()

        Returns:
            "ready" (200), "pending" (202), or "error"
        """
        params = {
            "zone": zone,
            "response_id": response_id
        }

        async with self.engine.get_from_url(
            f"{self.engine.BASE_URL}{self.FETCH_ENDPOINT}",
            params=params
        ) as response:
            if response.status == 200:
                return "ready"
            elif response.status == 202:
                return "pending"
            else:
                return "error"

    async def fetch_result(
        self,
        zone: str,
        response_id: str
    ) -> Any:
        """
        Fetch results when ready.

        Args:
            zone: Zone name
            response_id: Response ID from trigger()

        Returns:
            Response data (already parsed JSON)

        Raises:
            APIError: If response not ready or fetch fails
        """
        params = {
            "zone": zone,
            "response_id": response_id
        }

        async with self.engine.get_from_url(
            f"{self.engine.BASE_URL}{self.FETCH_ENDPOINT}",
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            elif response.status == 202:
                raise APIError("Response not ready yet (HTTP 202)")
            else:
                error_text = await response.text()
                raise APIError(f"Fetch failed (HTTP {response.status}): {error_text}")
```

**Why this design?**
- ✅ Simple and focused
- ✅ No customer_id needed (derived from bearer token)
- ✅ Reusable for both SERP and Web Unlocker
- ✅ Easy to test
- ✅ Matches existing service patterns

### Step 1.2: Update BaseSERPService

**File:** `src/brightdata/api/serp/base.py` (MODIFY)

**Changes:**

#### Change 1: Import AsyncUnblockerClient

```python
# Line ~10
from ...api.async_unblocker import AsyncUnblockerClient
```

#### Change 2: Update __init__

```python
# Line ~32-54
def __init__(
    self,
    engine: AsyncEngine,
    url_builder: BaseURLBuilder,
    data_normalizer: BaseDataNormalizer,
    timeout: Optional[int] = None,
    max_retries: int = 3,
):
    self.engine = engine
    self.url_builder = url_builder
    self.data_normalizer = data_normalizer
    self.timeout = timeout or self.DEFAULT_TIMEOUT
    self.max_retries = max_retries

    # NEW: Async unblocker client for async mode
    self.async_unblocker = AsyncUnblockerClient(engine)
```

#### Change 3: Add mode parameter to search()

```python
# Line ~56-112
async def search(
    self,
    query: Union[str, List[str]],
    zone: str,
    location: Optional[str] = None,
    language: str = "en",
    device: str = "desktop",
    num_results: int = 10,
    mode: str = "sync",          # NEW
    poll_interval: int = 2,      # NEW
    poll_timeout: int = 30,      # NEW
    **kwargs,
) -> Union[SearchResult, List[SearchResult]]:
    """
    Perform search asynchronously.

    Args:
        query: Search query string or list of queries
        zone: Bright Data zone for SERP API
        location: Geographic location
        language: Language code
        device: Device type
        num_results: Number of results to return
        mode: "sync" (default, blocking) or "async" (non-blocking with polling)
        poll_interval: Seconds between polls (async mode only)
        poll_timeout: Max wait time in seconds (async mode only)
        **kwargs: Engine-specific parameters

    Returns:
        SearchResult for single query, List[SearchResult] for multiple
    """
    is_single = isinstance(query, str)
    query_list = [query] if is_single else query

    self._validate_zone(zone)
    self._validate_queries(query_list)

    # Route based on mode
    if mode == "async":
        if len(query_list) == 1:
            return await self._search_single_async_unblocker(
                query=query_list[0],
                zone=zone,
                location=location,
                language=language,
                device=device,
                num_results=num_results,
                poll_interval=poll_interval,
                poll_timeout=poll_timeout,
                **kwargs,
            )
        else:
            return await self._search_multiple_async_unblocker(
                queries=query_list,
                zone=zone,
                location=location,
                language=language,
                device=device,
                num_results=num_results,
                poll_interval=poll_interval,
                poll_timeout=poll_timeout,
                **kwargs,
            )
    else:  # mode == "sync" (existing behavior)
        if len(query_list) == 1:
            return await self._search_single_async(...)  # Existing method
        else:
            return await self._search_multiple_async(...)  # Existing method
```

#### Change 4: Implement _search_single_async_unblocker()

```python
# Add after _search_multiple_async (line ~270)
async def _search_single_async_unblocker(
    self,
    query: str,
    zone: str,
    location: Optional[str],
    language: str,
    device: str,
    num_results: int,
    poll_interval: int,
    poll_timeout: int,
    **kwargs,
) -> SearchResult:
    """Execute single search using async unblocker endpoints."""
    trigger_sent_at = datetime.now(timezone.utc)

    # Build search URL
    search_url = self.url_builder.build(
        query=query,
        location=location,
        language=language,
        device=device,
        num_results=num_results,
        **kwargs,
    )

    # Trigger async request (no customer_id needed!)
    response_id = await self.async_unblocker.trigger(zone=zone, url=search_url)

    if not response_id:
        return SearchResult(
            success=False,
            query={"q": query},
            error="Failed to trigger async request (no response_id)",
            search_engine=self.SEARCH_ENGINE,
            trigger_sent_at=trigger_sent_at,
            data_fetched_at=datetime.now(timezone.utc),
        )

    # Poll until ready
    start_time = datetime.now(timezone.utc)

    while True:
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        if elapsed > poll_timeout:
            return SearchResult(
                success=False,
                query={"q": query},
                error=f"Polling timeout after {poll_timeout}s",
                search_engine=self.SEARCH_ENGINE,
                trigger_sent_at=trigger_sent_at,
                data_fetched_at=datetime.now(timezone.utc),
            )

        status = await self.async_unblocker.get_status(zone, response_id)

        if status == "ready":
            data_fetched_at = datetime.now(timezone.utc)

            # Fetch results
            data = await self.async_unblocker.fetch_result(zone, response_id)

            # Data from async endpoint is already parsed SERP format
            # (when using format="raw" or default)
            normalized_data = self.data_normalizer.normalize(data)

            return SearchResult(
                success=True,
                query={"q": query, "location": location, "language": language},
                data=normalized_data.get("results", []),
                total_found=normalized_data.get("total_results"),
                search_engine=self.SEARCH_ENGINE,
                country=location,
                results_per_page=num_results,
                trigger_sent_at=trigger_sent_at,
                data_fetched_at=data_fetched_at,
            )

        elif status == "error":
            return SearchResult(
                success=False,
                query={"q": query},
                error="Async request failed",
                search_engine=self.SEARCH_ENGINE,
                trigger_sent_at=trigger_sent_at,
                data_fetched_at=datetime.now(timezone.utc),
            )

        # Still pending - wait and retry
        await asyncio.sleep(poll_interval)


async def _search_multiple_async_unblocker(
    self,
    queries: List[str],
    zone: str,
    location: Optional[str],
    language: str,
    device: str,
    num_results: int,
    poll_interval: int,
    poll_timeout: int,
    **kwargs,
) -> List[SearchResult]:
    """Execute multiple searches using async unblocker."""
    tasks = [
        self._search_single_async_unblocker(
            query=q,
            zone=zone,
            location=location,
            language=language,
            device=device,
            num_results=num_results,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
            **kwargs,
        )
        for q in queries
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    processed_results = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append(
                SearchResult(
                    success=False,
                    query={"q": queries[i]},
                    error=f"Exception: {str(result)}",
                    search_engine=self.SEARCH_ENGINE,
                    trigger_sent_at=datetime.now(timezone.utc),
                    data_fetched_at=datetime.now(timezone.utc),
                )
            )
        else:
            processed_results.append(result)

    return processed_results
```

### Step 1.3: Remove customer_id Requirement

**File:** `src/brightdata/client.py` (MODIFY)

**Change:** Remove customer_id since it's not needed

```python
# Line ~74-86
def __init__(
    self,
    token: Optional[str] = None,
    # REMOVE: customer_id: Optional[str] = None,
    timeout: int = DEFAULT_TIMEOUT,
    web_unlocker_zone: Optional[str] = None,
    serp_zone: Optional[str] = None,
    browser_zone: Optional[str] = None,
    auto_create_zones: bool = True,
    validate_token: bool = False,
    rate_limit: Optional[float] = None,
    rate_period: float = 1.0,
):
    self.token = self._load_token(token)
    # REMOVE: self.customer_id = customer_id or os.getenv("BRIGHTDATA_CUSTOMER_ID")
    # ... rest unchanged
```

**Rationale:** Testing proved customer_id is NOT required - Bright Data derives it from bearer token.

---

## Phase 2: Testing

### Step 2.1: Unit Tests for AsyncUnblockerClient

**File:** `tests/unit/test_async_unblocker.py` (NEW)

```python
"""Unit tests for AsyncUnblockerClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from brightdata.api.async_unblocker import AsyncUnblockerClient


@pytest.mark.asyncio
async def test_trigger_success():
    """Test successful trigger returns response_id."""
    engine = MagicMock()
    response = MagicMock()
    response.headers.get.return_value = "test_response_id_123"
    engine.post_to_url = AsyncMock(return_value=AsyncContextManager(response))

    client = AsyncUnblockerClient(engine)
    response_id = await client.trigger(zone="test_zone", url="https://example.com")

    assert response_id == "test_response_id_123"


@pytest.mark.asyncio
async def test_get_status_ready():
    """Test status check returns 'ready' for HTTP 200."""
    engine = MagicMock()
    response = MagicMock()
    response.status = 200
    engine.get_from_url = AsyncMock(return_value=AsyncContextManager(response))

    client = AsyncUnblockerClient(engine)
    status = await client.get_status(zone="test_zone", response_id="abc123")

    assert status == "ready"


@pytest.mark.asyncio
async def test_get_status_pending():
    """Test status check returns 'pending' for HTTP 202."""
    engine = MagicMock()
    response = MagicMock()
    response.status = 202
    engine.get_from_url = AsyncMock(return_value=AsyncContextManager(response))

    client = AsyncUnblockerClient(engine)
    status = await client.get_status(zone="test_zone", response_id="abc123")

    assert status == "pending"


@pytest.mark.asyncio
async def test_fetch_result_success():
    """Test fetch returns data for HTTP 200."""
    engine = MagicMock()
    response = MagicMock()
    response.status = 200
    response.json = AsyncMock(return_value={"data": "test"})
    engine.get_from_url = AsyncMock(return_value=AsyncContextManager(response))

    client = AsyncUnblockerClient(engine)
    data = await client.fetch_result(zone="test_zone", response_id="abc123")

    assert data == {"data": "test"}
```

### Step 2.2: Integration Tests

**File:** `tests/integration/test_serp_async_mode.py` (NEW)

```python
"""Integration tests for SERP async mode."""

import pytest
from brightdata import BrightDataClient


@pytest.mark.integration
@pytest.mark.asyncio
async def test_google_search_sync_mode():
    """Test sync mode still works (backwards compatibility)."""
    async with BrightDataClient() as client:
        result = await client.search.google(
            query="python programming",
            zone=client.serp_zone,
            mode="sync"  # Explicit sync
        )

        assert result.success
        assert len(result.data) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_google_search_async_mode():
    """Test async mode with polling."""
    async with BrightDataClient() as client:
        result = await client.search.google(
            query="python programming",
            zone=client.serp_zone,
            mode="async",
            poll_interval=2,
            poll_timeout=30
        )

        assert result.success
        assert len(result.data) > 0


@pytest.mark.integration
@pytest.mark.asyncio
async def test_google_search_default_is_sync():
    """Test default mode is sync (backwards compatibility)."""
    async with BrightDataClient() as client:
        # No mode parameter - should default to sync
        result = await client.search.google(
            query="test",
            zone=client.serp_zone
        )

        assert result.success
```

---

## Phase 3: Documentation

### Step 3.1: Update README.md

**File:** `README.md` (MODIFY)

Add async mode examples:

```markdown
### Async Mode (Non-blocking)

For non-blocking operations, use `mode="async"`:

```python
async with BrightDataClient() as client:
    # Non-blocking - polls for results in background
    result = await client.search.google(
        query="python programming",
        zone="my_serp_zone",
        mode="async",
        poll_interval=2,   # Check every 2 seconds
        poll_timeout=30    # Give up after 30 seconds
    )

    print(result.data)
```

**When to use async mode:**
- You want to continue working while scraping
- You're triggering multiple searches in batch
- You want webhook support (future feature)

**Note:** Async mode uses the same zone as sync mode - no special configuration needed!
```

### Step 3.2: Create Migration Guide

**File:** `docs/async_mode_guide.md` (NEW)

```markdown
# Async Mode Guide

## Overview

Async mode allows non-blocking SERP requests using Bright Data's unblocker endpoints.

## Sync vs Async

| Feature | Sync Mode | Async Mode |
|---------|-----------|------------|
| Endpoint | `/request` | `/unblocker/req` + `/unblocker/get_result` |
| Behavior | Blocks until ready | Returns immediately, poll for results |
| Use case | Simple queries | Batch operations, background tasks |
| Response | Same | Same (normalized) |
| Configuration | None | `mode="async"` |

## Usage Examples

### Default (Sync Mode)

```python
result = await client.search.google(
    query="test",
    zone="my_zone"
)
# Blocks until results ready, then returns
```

### Async Mode

```python
result = await client.search.google(
    query="test",
    zone="my_zone",
    mode="async",
    poll_interval=2,
    poll_timeout=30
)
# Triggers request, polls every 2s, times out after 30s
```
## Configuration

No special configuration needed! Async mode works with:
- ✅ Same zones as sync mode
- ✅ Same bearer token authentication
- ✅ Same data format (normalized)

## Performance

- **Trigger time:** ~0.7s (async) vs ~2.9s (sync blocking)
- **Total time:** Depends on scraping complexity
- **Optimal batch size:** 10-50 concurrent requests

## Error Handling

```python
result = await client.search.google(
    query="test",
    zone="my_zone",
    mode="async",
    poll_timeout=10
)

if not result.success:
    print(f"Error: {result.error}")
    # Common errors:
    # - "Polling timeout after 10s"
    # - "Async request failed"
    # - "Failed to trigger async request"
```
```
