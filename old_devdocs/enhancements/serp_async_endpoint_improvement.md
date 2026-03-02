# SERP Async Endpoint Support

## Executive Summary

Add support for Bright Data's async unblocker endpoints (`/unblocker/req` + `/unblocker/get_result`) to the SDK's SERP implementation, allowing users to choose between sync (blocking) and async (non-blocking) modes.

## Current State

### What We Have Now

The SDK only supports **sync mode** for SERP:

```python
# Current implementation
client.search.google(query="python", zone="my_serp_zone")
# Uses: POST /request → blocks until results ready → returns data
```

**Implementation:** `src/brightdata/api/serp/base.py`

```python
async def _search_single_async(...):
    payload = {"zone": zone, "url": search_url, "format": "json", "method": "GET"}

    async with self.engine.post_to_url(
        f"{self.engine.BASE_URL}/request",  # Sync endpoint
        json_data=payload,
    ) as response:
        # Waits for complete response
        data = await response.json()
```

### Limitations

1. **Blocking requests** - Must wait for scrape to complete
2. **No webhook support** - Can't receive results via callback
3. **Not optimal for batch** - Can't trigger multiple and collect later
4. **No background processing** - Can't continue work while scraping

## Discovery: Async Endpoints Exist

### Test Results

From `test_serp_async_vs_sync.py`:

| Mode | Endpoint | Trigger Time | Total Time | Response Structure |
|------|----------|--------------|------------|-------------------|
| **Sync** | `/request` | N/A | 2.89s | `{status_code, headers, body}` |
| **Async** | `/unblocker/req` + `/unblocker/get_result` | 0.71s | 13.80s | `{general, organic, knowledge, ...}` |

### Key Findings

1. ✅ **Both work on same zone** - Async setting in dashboard is informational, not restrictive
2. ✅ **Returns `response_id`** in header `x-response-id` (not in body like `snapshot_id`)
3. ✅ **Polling required** - HTTP 202 "Request is pending" until ready
4. ✅ **Different response structure** - Async returns parsed SERP data directly

### Async Flow

```bash
# Step 1: Trigger
POST /unblocker/req?customer=xxx&zone=serp_api4
Headers: x-response-id: s4w7t1767082074477rtu2rth43mk8
Status: 200

# Step 2: Poll (may need multiple attempts)
GET /unblocker/get_result?customer=xxx&zone=serp_api4&response_id=s4w7t1767082074477rtu2rth43mk8
Status: 202 (pending) or 200 (ready)

# Step 3: Get results when ready
Status: 200
Body: {general: {...}, organic: [...], ...}
```

## Proposed Solution

### API Design

Add `mode` parameter to SERP methods:

```python
# Option 1: Sync (default, backwards compatible)
result = await client.search.google(
    query="python programming",
    zone="my_serp_zone",
    mode="sync"  # or omit for default
)

# Option 2: Async (non-blocking)
result = await client.search.google(
    query="python programming",
    zone="my_serp_zone",
    mode="async",
    poll_interval=2,
    poll_timeout=30
)

# Option 3: Async with manual control
response_id = await client.search.google_trigger(
    query="python programming",
    zone="my_serp_zone"
)

# Later...
status = await client.search.google_status(response_id)
result = await client.search.google_fetch(response_id)
```

### Implementation Plan

#### 1. Create Async Unblocker Client

**New file:** `src/brightdata/api/async_unblocker.py`

```python
class AsyncUnblockerClient:
    """Client for async unblocker endpoints (/unblocker/req + /unblocker/get_result)"""

    TRIGGER_ENDPOINT = "/unblocker/req"
    FETCH_ENDPOINT = "/unblocker/get_result"

    def __init__(self, engine: AsyncEngine, customer_id: str):
        self.engine = engine
        self.customer_id = customer_id

    async def trigger(
        self,
        zone: str,
        url: str,
        flags: Optional[str] = None
    ) -> Optional[str]:
        """
        Trigger async request.

        Returns:
            response_id from x-response-id header
        """
        params = {"customer": self.customer_id, "zone": zone}
        payload = {"url": url}
        if flags:
            payload["flags"] = flags

        async with self.engine.post_to_url(
            f"{self.engine.BASE_URL}{self.TRIGGER_ENDPOINT}",
            params=params,
            json_data=payload
        ) as response:
            response_id = response.headers.get("x-response-id")
            return response_id

    async def get_status(
        self,
        zone: str,
        response_id: str
    ) -> str:
        """
        Check if response is ready.

        Returns:
            "pending" (202) or "ready" (200) or "error"
        """
        params = {
            "customer": self.customer_id,
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
        """Fetch results (only when status is ready)"""
        params = {
            "customer": self.customer_id,
            "zone": zone,
            "response_id": response_id
        }

        async with self.engine.get_from_url(
            f"{self.engine.BASE_URL}{self.FETCH_ENDPOINT}",
            params=params
        ) as response:
            if response.status == 200:
                return await response.json()
            else:
                raise APIError(f"Response not ready: {response.status}")
```

#### 2. Update SERP Base Service

**File:** `src/brightdata/api/serp/base.py`

```python
class BaseSERPService:

    def __init__(
        self,
        engine: AsyncEngine,
        url_builder: BaseURLBuilder,
        data_normalizer: BaseDataNormalizer,
        customer_id: Optional[str] = None,  # NEW
        timeout: Optional[int] = None,
        max_retries: int = 3,
    ):
        self.engine = engine
        self.url_builder = url_builder
        self.data_normalizer = data_normalizer
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self.max_retries = max_retries

        # NEW: Async unblocker client
        if customer_id:
            self.async_client = AsyncUnblockerClient(engine, customer_id)
        else:
            self.async_client = None

    async def search(
        self,
        query: Union[str, List[str]],
        zone: str,
        location: Optional[str] = None,
        language: str = "en",
        device: str = "desktop",
        num_results: int = 10,
        mode: str = "sync",  # NEW: "sync" or "async"
        poll_interval: int = 2,  # NEW: for async mode
        poll_timeout: int = 30,   # NEW: for async mode
        **kwargs,
    ) -> Union[SearchResult, List[SearchResult]]:
        """
        Perform search with sync or async mode.

        Args:
            mode: "sync" (default) uses /request, "async" uses /unblocker/req
            poll_interval: Seconds between polls (async mode only)
            poll_timeout: Max wait time (async mode only)
        """
        is_single = isinstance(query, str)
        query_list = [query] if is_single else query

        self._validate_zone(zone)
        self._validate_queries(query_list)

        if mode == "async":
            if not self.async_client:
                raise ValueError(
                    "Async mode requires customer_id. "
                    "Pass customer_id when creating the client."
                )

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
                return await self._search_multiple_async_unblocker(...)

        else:  # mode == "sync" (existing behavior)
            if len(query_list) == 1:
                return await self._search_single_async(...)  # Existing method
            else:
                return await self._search_multiple_async(...)  # Existing method

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

        # Trigger async request
        response_id = await self.async_client.trigger(zone=zone, url=search_url)

        if not response_id:
            return SearchResult(
                success=False,
                query={"q": query},
                error="Failed to trigger async request",
                search_engine=self.SEARCH_ENGINE,
                trigger_sent_at=trigger_sent_at,
                data_fetched_at=datetime.now(timezone.utc),
            )

        response_id_received_at = datetime.now(timezone.utc)

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

            status = await self.async_client.get_status(zone, response_id)

            if status == "ready":
                data_fetched_at = datetime.now(timezone.utc)
                data = await self.async_client.fetch_result(zone, response_id)

                # Data is already parsed SERP format from async endpoint
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

            # Still pending
            await asyncio.sleep(poll_interval)
```

#### 3. Add Manual Control Methods

For advanced users who want to trigger and fetch separately:

```python
class BaseSERPService:

    async def search_trigger(
        self,
        query: str,
        zone: str,
        location: Optional[str] = None,
        language: str = "en",
        device: str = "desktop",
        num_results: int = 10,
        **kwargs,
    ) -> Optional[str]:
        """
        Trigger async search without waiting.

        Returns:
            response_id for later fetching
        """
        if not self.async_client:
            raise ValueError("Async operations require customer_id")

        search_url = self.url_builder.build(
            query=query,
            location=location,
            language=language,
            device=device,
            num_results=num_results,
            **kwargs,
        )

        return await self.async_client.trigger(zone=zone, url=search_url)

    async def search_status(
        self,
        zone: str,
        response_id: str
    ) -> str:
        """Check status of async search."""
        if not self.async_client:
            raise ValueError("Async operations require customer_id")

        return await self.async_client.get_status(zone, response_id)

    async def search_fetch(
        self,
        zone: str,
        response_id: str
    ) -> SearchResult:
        """Fetch results from completed async search."""
        if not self.async_client:
            raise ValueError("Async operations require customer_id")

        data = await self.async_client.fetch_result(zone, response_id)
        normalized_data = self.data_normalizer.normalize(data)

        return SearchResult(
            success=True,
            query={"q": ""},  # Not available without storing context
            data=normalized_data.get("results", []),
            total_found=normalized_data.get("total_results"),
            search_engine=self.SEARCH_ENGINE,
            data_fetched_at=datetime.now(timezone.utc),
        )
```

#### 4. Update Client Initialization

**File:** `src/brightdata/client.py`

```python
class AsyncBrightDataClient:

    def __init__(
        self,
        token: Optional[str] = None,
        customer_id: Optional[str] = None,  # NEW
        timeout: int = 60,
        ...
    ):
        """
        Args:
            customer_id: Required for async unblocker mode (e.g., "hl_67e5ed38")
        """
        self.engine = AsyncEngine(bearer_token=token, timeout=timeout)
        self.customer_id = customer_id

        # Initialize services
        self.search = SearchServices(
            engine=self.engine,
            customer_id=customer_id  # Pass to enable async mode
        )
```

### Configuration Options

#### Option A: Environment Variable

```python
# .env
BRIGHTDATA_CUSTOMER_ID=hl_67e5ed38

# Code
client = AsyncBrightDataClient()  # Auto-reads from env
```

#### Option B: Explicit Parameter

```python
client = AsyncBrightDataClient(
    token="...",
    customer_id="hl_67e5ed38"  # Required for async mode
)
```

#### Option C: Extract from Token/Zone

If customer_id can be derived from existing data (need to investigate).

## Usage Examples

### Sync Mode (Current Behavior, Default)

```python
async with AsyncBrightDataClient(token="...") as client:
    # Blocks until results ready (default mode)
    result = await client.search.google(
        query="python programming",
        zone="my_serp_zone"
    )
    print(result.data)
```

### Async Mode (New)

```python
async with AsyncBrightDataClient(
    token="...",
    customer_id="hl_67e5ed38"
) as client:
    # Non-blocking, polls for results
    result = await client.search.google(
        query="python programming",
        zone="my_serp_zone",
        mode="async",
        poll_interval=2,
        poll_timeout=30
    )
    print(result.data)
```

### Manual Control (Advanced)

```python
async with AsyncBrightDataClient(
    token="...",
    customer_id="hl_67e5ed38"
) as client:
    # Trigger multiple searches
    response_ids = []
    for query in ["python", "javascript", "golang"]:
        rid = await client.search.google_trigger(
            query=query,
            zone="my_serp_zone"
        )
        response_ids.append((query, rid))

    # Do other work...

    # Collect results later
    results = []
    for query, rid in response_ids:
        while True:
            status = await client.search.google_status("my_serp_zone", rid)
            if status == "ready":
                result = await client.search.google_fetch("my_serp_zone", rid)
                results.append(result)
                break
            await asyncio.sleep(2)
```

### Batch with Webhooks (Future)

```python
# Trigger with webhook callback
response_id = await client.search.google_trigger(
    query="python programming",
    zone="my_serp_zone",
    webhook_url="https://myapp.com/serp-callback"
)

# Server receives results when ready
# POST https://myapp.com/serp-callback
# {"response_id": "...", "data": {...}}
```

## Migration Guide

### For Existing Users

**No breaking changes!** Default behavior unchanged:

```python
# This still works exactly as before
result = await client.search.google(query="test", zone="my_zone")
```

### For New Async Users

```python
# Step 1: Add customer_id
client = AsyncBrightDataClient(
    token="your_token",
    customer_id="hl_67e5ed38"  # Find in Bright Data dashboard
)

# Step 2: Use mode="async"
result = await client.search.google(
    query="test",
    zone="my_zone",
    mode="async"
)
```

## Implementation Checklist

- [ ] Create `AsyncUnblockerClient` class
- [ ] Update `BaseSERPService` with `mode` parameter
- [ ] Implement `_search_single_async_unblocker` method
- [ ] Implement `_search_multiple_async_unblocker` method
- [ ] Add manual control methods (`search_trigger`, `search_status`, `search_fetch`)
- [ ] Update `AsyncBrightDataClient` to accept `customer_id`
- [ ] Update `SyncBrightDataClient` wrapper
- [ ] Add tests for async mode
- [ ] Add tests for manual control
- [ ] Update documentation
- [ ] Add examples to README

## Open Questions

1. **How to get customer_id?**
   - From environment variable?
   - From Bright Data API?
   - Manual configuration only?

2. **Should we support both modes simultaneously?**
   - E.g., `client.search.google()` (sync) vs `client.search_async.google()` (async)
   - Or single unified API with `mode` parameter?

3. **Webhook support?**
   - Should we add webhook URL parameter?
   - How to handle webhook verification/security?

4. **Response structure handling?**
   - Async returns direct SERP data
   - Sync returns wrapped HTTP response
   - Should we normalize to same structure?

5. **Apply same pattern to Web Unlocker?**
   - Web Unlocker also supports `/unblocker/req` + `/unblocker/get_result`
   - Should we add async mode there too?

## Benefits

1. ✅ **Non-blocking requests** - Continue work while scraping
2. ✅ **Webhook support** - Receive results via callback
3. ✅ **Batch optimization** - Trigger many, collect later
4. ✅ **Backwards compatible** - Existing code unaffected
5. ✅ **Flexible** - Choose mode per request

## Risks

1. **Complexity** - Two code paths to maintain
2. **Customer ID requirement** - Extra configuration burden
3. **Different response structures** - Need careful normalization
4. **Testing overhead** - More scenarios to test

## Timeline Estimate

- **Phase 1: Core Implementation** - 2-3 days
  - `AsyncUnblockerClient` class
  - `BaseSERPService` updates
  - Basic async mode support

- **Phase 2: Manual Control** - 1 day
  - `search_trigger`, `search_status`, `search_fetch` methods

- **Phase 3: Testing** - 1-2 days
  - Unit tests
  - Integration tests
  - Manual verification

- **Phase 4: Documentation** - 1 day
  - API docs
  - Examples
  - Migration guide

**Total: 5-7 days**

## Alternatives Considered

### Alternative 1: Separate Client Classes

```python
# Sync client (existing)
sync_client = BrightDataClient(token="...")

# Async client (new)
async_client = BrightDataAsyncClient(token="...", customer_id="...")
```

**Pros:** Clear separation, no mode confusion
**Cons:** Code duplication, user confusion about which to use

### Alternative 2: Async-Only, Remove Sync

```python
# Force everyone to use async mode
client.search.google(query="test", zone="zone")  # Always uses /unblocker/req
```

**Pros:** Simpler codebase
**Cons:** Breaking change, slower for simple use cases

### Alternative 3: Auto-Detect Mode

```python
# SDK decides based on context (webhook present, etc.)
client.search.google(query="test", zone="zone", webhook="...")  # Auto async
client.search.google(query="test", zone="zone")  # Auto sync
```

**Pros:** Smart, minimal config
**Cons:** Hidden behavior, harder to debug

## Recommendation

Implement **Option 1** (mode parameter) because:
- ✅ Backwards compatible
- ✅ Explicit and clear
- ✅ Flexible per-request control
- ✅ Minimal breaking changes
- ✅ Easy to test and maintain
