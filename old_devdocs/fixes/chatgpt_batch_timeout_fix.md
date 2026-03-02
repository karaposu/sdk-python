# Fix: ChatGPT Batch Prompts Timeout on Fetch

## Problem

ChatGPT batch prompts fail intermittently with the error:
```
❌ Failed: Failed to fetch results:
```

The error message is empty, making diagnosis difficult.

**Pattern observed:**
- ✅ Single prompts: Work perfectly
- ✅ Batch with 1-2 simple prompts: SUCCESS
- ❌ Batch with 3+ prompts: FAILS
- ❌ Batch with web_search enabled: FAILS
- ✅ Batch with 2 prompts (no web search): SUCCESS

**Test results from `test_17_chatgpt_batch_debug.py`:**
```
PHASE 2: 2 prompts, no web search → ✅ SUCCESS
PHASE 3: Manual workflow shows:
  - Trigger: ✅ SUCCESS
  - Polling: ✅ Status becomes 'ready' after 10 checks
  - Fetch: ❌ FAILS with TimeoutError()
PHASE 4: 1 prompt → ✅ SUCCESS, 3 prompts → ❌ FAILS
PHASE 5: 2 prompts with web_search → ❌ FAILS
```

## Root Cause

The issue occurs in the **fetch operation**, not the trigger or polling phases.

### Timeline of the Issue:

1. **Trigger phase** ✅
   - API accepts the batch request
   - Returns snapshot_id
   - Cost: ~20ms

2. **Polling phase** ✅
   - Job processes successfully
   - Status changes: pending → running → ready
   - This can take 20-40 seconds for ChatGPT responses

3. **Fetch phase** ❌
   - Job is ready, data is available
   - SDK attempts to download results via GET request
   - **HTTP request times out after 30 seconds**
   - `TimeoutError()` raised (with empty message)
   - Error gets wrapped as "Failed to fetch results: "

### Why 30 seconds?

In `src/brightdata/core/engine.py:44`:
```python
def __init__(
    self,
    bearer_token: str,
    timeout: int = 30,  # ← Default HTTP timeout
    ...
):
    self.timeout = aiohttp.ClientTimeout(total=timeout)
```

The default HTTP timeout is **30 seconds** for ALL requests (trigger, status checks, fetch).

### Why does fetch timeout?

**Large batch responses take longer to download:**

- **Small batches (1-2 prompts)**: Response ~5-10 KB, downloads in <5s ✅
- **Large batches (3+ prompts)**: Response ~20-50 KB, may take 30-60s ❌
- **Web search enabled**: Each response includes search results, 2-5x larger ❌

The API server generates the data fine (status='ready'), but the HTTP connection times out while downloading the large JSON response.

### Error message is empty because:

In `src/brightdata/utils/polling.py:126-131`:
```python
try:
    data = await fetch_result_func(snapshot_id)
except Exception as e:
    return ScrapeResult(
        success=False,
        error=f"Failed to fetch results: {str(e)}",  # ← str(TimeoutError()) = ""
        ...
    )
```

`TimeoutError()` has no message, so `str(e)` returns empty string.

## Solution

Add configurable timeout support for fetch operations, with a higher default for large batch responses.

### Design decisions:

1. **Separate timeout for fetch vs trigger/poll**
   - Trigger: Quick operation, 30s is fine
   - Status checks: Quick operation, 30s is fine
   - Fetch: Downloads large data, needs 120-300s

2. **Make it configurable**
   - Allow users to override if they have very large batches
   - Default to sensible value (120s) for most cases

3. **Backwards compatible**
   - Don't break existing code
   - Keep default 30s for trigger/poll operations
   - Only increase timeout for fetch

## Code Changes Needed

### 1. Update `DatasetAPIClient.fetch_result()` to accept timeout parameter

**File:** `src/brightdata/scrapers/api_client.py`

**Current code (line 104-121):**
```python
async def fetch_result(self, snapshot_id: str, format: str = "json") -> Any:
    """
    Fetch snapshot results.

    Args:
        snapshot_id: Snapshot identifier
        format: Result format ("json" or "raw")

    Returns:
        Result data (parsed JSON or raw text)

    Raises:
        APIError: If fetch request fails
    """
    url = f"{self.RESULT_URL}/{snapshot_id}"
    params = {"format": format}

    async with self.engine.get_from_url(url, params=params) as response:
```

**New code:**
```python
async def fetch_result(self, snapshot_id: str, format: str = "json", timeout: int = 120) -> Any:
    """
    Fetch snapshot results.

    Args:
        snapshot_id: Snapshot identifier
        format: Result format ("json" or "raw")
        timeout: Timeout in seconds for fetching results (default: 120s for large batches)

    Returns:
        Result data (parsed JSON or raw text)

    Raises:
        APIError: If fetch request fails
        TimeoutError: If fetch takes longer than timeout
    """
    import aiohttp

    url = f"{self.RESULT_URL}/{snapshot_id}"
    params = {"format": format}

    # Use custom timeout for fetch (longer than default 30s) to handle large batch responses
    fetch_timeout = aiohttp.ClientTimeout(total=timeout)

    async with self.engine.get_from_url(url, params=params, timeout=fetch_timeout) as response:
```

**Changes:**
- Add `timeout: int = 120` parameter
- Create `aiohttp.ClientTimeout(total=timeout)`
- Pass `timeout=fetch_timeout` to `get_from_url()`
- Update docstring to document timeout parameter

### 2. Update `poll_until_ready()` to pass fetch timeout

**File:** `src/brightdata/utils/polling.py`

**Current code (line 21-32):**
```python
async def poll_until_ready(
    get_status_func: Callable[[str], Awaitable[str]],
    fetch_result_func: Callable[[str], Awaitable[Any]],
    snapshot_id: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    poll_timeout: int = DEFAULT_POLL_TIMEOUT,
    trigger_sent_at: datetime | None = None,
    snapshot_id_received_at: datetime | None = None,
    platform: str | None = None,
    method: str | None = None,
    cost_per_record: float = 0.001,
) -> ScrapeResult:
```

**New code:**
```python
async def poll_until_ready(
    get_status_func: Callable[[str], Awaitable[str]],
    fetch_result_func: Callable[[str], Awaitable[Any]],
    snapshot_id: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    poll_timeout: int = DEFAULT_POLL_TIMEOUT,
    fetch_timeout: int = 120,  # ← NEW parameter
    trigger_sent_at: datetime | None = None,
    snapshot_id_received_at: datetime | None = None,
    platform: str | None = None,
    method: str | None = None,
    cost_per_record: float = 0.001,
) -> ScrapeResult:
```

**And update the fetch call (line 124-125):**

**Current:**
```python
try:
    data = await fetch_result_func(snapshot_id)
```

**New:**
```python
try:
    # Pass timeout if fetch_result_func supports it
    if callable(getattr(fetch_result_func, '__self__', None)):
        # It's a bound method, we can pass timeout
        data = await fetch_result_func(snapshot_id, timeout=fetch_timeout)
    else:
        # Generic function, call without timeout
        data = await fetch_result_func(snapshot_id)
```

**Alternative simpler approach:**
Just always pass the keyword argument, and let the fetch function use default if it doesn't need custom timeout:
```python
try:
    data = await fetch_result_func(snapshot_id)  # Keep as is, timeout handled in fetch_result
```

Actually, better approach: Update the signature of the callback:

**Current (line 21-23):**
```python
async def poll_until_ready(
    get_status_func: Callable[[str], Awaitable[str]],
    fetch_result_func: Callable[[str], Awaitable[Any]],
```

**Updated to support timeout:**
Since `fetch_result_func` is always `api_client.fetch_result`, and we control that signature, we can:

1. Update `api_client.fetch_result()` to accept `timeout` with default 120
2. Update `poll_until_ready()` to accept `fetch_timeout` parameter
3. Pass it through when calling fetch

**Changes in polling.py:**

```python
async def poll_until_ready(
    get_status_func: Callable[[str], Awaitable[str]],
    fetch_result_func: Callable[[str, int], Awaitable[Any]],  # ← Updated signature
    snapshot_id: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    poll_timeout: int = DEFAULT_POLL_TIMEOUT,
    fetch_timeout: int = 120,  # ← NEW: Default 120s for large responses
    trigger_sent_at: datetime | None = None,
    snapshot_id_received_at: datetime | None = None,
    platform: str | None = None,
    method: str | None = None,
    cost_per_record: float = 0.001,
) -> ScrapeResult:
    """
    Poll snapshot until ready, then fetch results.

    ...existing docstring...

    Args:
        ...existing args...
        fetch_timeout: Timeout in seconds for fetching results (default: 120)
                      Larger batches may need more time to download
    """
```

And at line 124-125:
```python
try:
    data = await fetch_result_func(snapshot_id, fetch_timeout)  # ← Pass timeout
```

### 3. Update `WorkflowExecutor._poll_and_fetch()` to pass fetch_timeout

**File:** `src/brightdata/scrapers/workflow.py`

**Current code (line 117-125):**
```python
async def _poll_and_fetch(
    self,
    snapshot_id: str,
    poll_interval: int,
    poll_timeout: int,
    trigger_sent_at: datetime,
    snapshot_id_received_at: datetime,
    normalize_func: Optional[Callable[[Any], Any]] = None,
) -> ScrapeResult:
```

**New code:**
```python
async def _poll_and_fetch(
    self,
    snapshot_id: str,
    poll_interval: int,
    poll_timeout: int,
    fetch_timeout: int = 120,  # ← NEW parameter
    trigger_sent_at: datetime,
    snapshot_id_received_at: datetime,
    normalize_func: Optional[Callable[[Any], Any]] = None,
) -> ScrapeResult:
```

**And update the poll_until_ready call (line 142-153):**

**Current:**
```python
result = await poll_until_ready(
    get_status_func=self.api_client.get_status,
    fetch_result_func=self.api_client.fetch_result,
    snapshot_id=snapshot_id,
    poll_interval=poll_interval,
    poll_timeout=poll_timeout,
    trigger_sent_at=trigger_sent_at,
    snapshot_id_received_at=snapshot_id_received_at,
    platform=self.platform_name,
    method="web_scraper",
    cost_per_record=self.cost_per_record,
)
```

**New:**
```python
result = await poll_until_ready(
    get_status_func=self.api_client.get_status,
    fetch_result_func=self.api_client.fetch_result,
    snapshot_id=snapshot_id,
    poll_interval=poll_interval,
    poll_timeout=poll_timeout,
    fetch_timeout=fetch_timeout,  # ← NEW: Pass fetch timeout
    trigger_sent_at=trigger_sent_at,
    snapshot_id_received_at=snapshot_id_received_at,
    platform=self.platform_name,
    method="web_scraper",
    cost_per_record=self.cost_per_record,
)
```

### 4. Update `WorkflowExecutor.execute()` to accept and pass fetch_timeout

**File:** `src/brightdata/scrapers/workflow.py`

**Current code (line 46-55):**
```python
async def execute(
    self,
    payload: List[Dict[str, Any]],
    dataset_id: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    poll_timeout: int = DEFAULT_POLL_TIMEOUT,
    include_errors: bool = True,
    normalize_func: Optional[Callable[[Any], Any]] = None,
    sdk_function: Optional[str] = None,
) -> ScrapeResult:
```

**New code:**
```python
async def execute(
    self,
    payload: List[Dict[str, Any]],
    dataset_id: str,
    poll_interval: int = DEFAULT_POLL_INTERVAL,
    poll_timeout: int = DEFAULT_POLL_TIMEOUT,
    fetch_timeout: int = 120,  # ← NEW parameter
    include_errors: bool = True,
    normalize_func: Optional[Callable[[Any], Any]] = None,
    sdk_function: Optional[str] = None,
) -> ScrapeResult:
```

**Update docstring:**
```python
"""
Execute complete trigger/poll/fetch workflow.

Args:
    payload: Request payload for dataset API
    dataset_id: Dataset identifier
    poll_interval: Seconds between status checks
    poll_timeout: Maximum seconds to wait for job completion
    fetch_timeout: Timeout in seconds for downloading results (default: 120)
    include_errors: Include error records
    normalize_func: Optional function to normalize result data
    sdk_function: SDK function name for monitoring

Returns:
    ScrapeResult with data or error
"""
```

**And update the _poll_and_fetch call (line 106-113):**

**Current:**
```python
result = await self._poll_and_fetch(
    snapshot_id=snapshot_id,
    poll_interval=poll_interval,
    poll_timeout=poll_timeout,
    trigger_sent_at=trigger_sent_at,
    snapshot_id_received_at=snapshot_id_received_at,
    normalize_func=normalize_func,
)
```

**New:**
```python
result = await self._poll_and_fetch(
    snapshot_id=snapshot_id,
    poll_interval=poll_interval,
    poll_timeout=poll_timeout,
    fetch_timeout=fetch_timeout,  # ← NEW: Pass through
    trigger_sent_at=trigger_sent_at,
    snapshot_id_received_at=snapshot_id_received_at,
    normalize_func=normalize_func,
)
```

### 5. (Optional) Update ChatGPT scraper to use higher fetch timeout

**File:** `src/brightdata/scrapers/chatgpt/scraper.py`

ChatGPT responses tend to be large, especially with web search. Consider using 180s fetch timeout.

**Current code (line 102-110):**
```python
result = await self.workflow_executor.execute(
    payload=payload,
    dataset_id=self.DATASET_ID,
    poll_interval=poll_interval,
    poll_timeout=timeout,
    include_errors=True,
    sdk_function=sdk_function,
    normalize_func=self.normalize_result,
)
```

**Option A: Use default 120s (no change needed)**

**Option B: Use ChatGPT-specific timeout:**
```python
result = await self.workflow_executor.execute(
    payload=payload,
    dataset_id=self.DATASET_ID,
    poll_interval=poll_interval,
    poll_timeout=timeout,
    fetch_timeout=180,  # ← ChatGPT responses can be large
    include_errors=True,
    sdk_function=sdk_function,
    normalize_func=self.normalize_result,
)
```

Apply same change to `prompts_async()` method (line 252-261).

### 6. Update manual fetch methods to expose timeout

**File:** `src/brightdata/scrapers/base.py`

**Current code (line 326-340):**
```python
async def _fetch_results_async(self, snapshot_id: str, format: str = "json") -> Any:
    """
    Fetch scrape job results (internal async method).

    ...
    """
    return await self.api_client.fetch_result(snapshot_id, format=format)
```

**New code:**
```python
async def _fetch_results_async(
    self,
    snapshot_id: str,
    format: str = "json",
    timeout: int = 120
) -> Any:
    """
    Fetch scrape job results (internal async method).

    Args:
        snapshot_id: Snapshot identifier from trigger operation
        format: Result format ("json" or "raw")
        timeout: Timeout in seconds for fetching results (default: 120)

    Returns:
        Scraped data

    Example:
        >>> data = await scraper._fetch_results_async(snapshot_id, timeout=180)
    """
    return await self.api_client.fetch_result(snapshot_id, format=format, timeout=timeout)
```

This allows advanced users to call fetch with custom timeout if needed.

## Testing

After implementing these changes, run `probe_tests/async/test_17_chatgpt_batch_debug.py`:

**Expected results:**
- Phase 2 (2 prompts): ✅ SUCCESS
- Phase 3 (manual workflow fetch): ✅ SUCCESS (was ❌ FAILS)
- Phase 4 (3 prompts): ✅ SUCCESS (was ❌ FAILS)
- Phase 5 (web_search): ✅ SUCCESS (was ❌ FAILS)

**Verify no regressions:**
```bash
python probe_tests/test_08_chatgpt.py  # Should all pass now
python probe_tests/async/test_11_concurrency_amazon_search.py  # Verify other scrapers still work
python probe_tests/async/test_10_concurrency_google_search.py  # Verify SERP still works
```

## Summary

**Problem:** Large batch responses timeout during fetch (30s default too short)
**Cause:** HTTP client uses 30s timeout for all operations, including large data downloads
**Solution:** Add configurable `fetch_timeout` parameter (default 120s) separate from `poll_timeout`

**Files to modify:**
1. `src/brightdata/scrapers/api_client.py` - Add timeout param to fetch_result()
2. `src/brightdata/utils/polling.py` - Add fetch_timeout param to poll_until_ready()
3. `src/brightdata/scrapers/workflow.py` - Add fetch_timeout to execute() and _poll_and_fetch()
4. `src/brightdata/scrapers/base.py` - Add timeout param to _fetch_results_async()
5. (Optional) `src/brightdata/scrapers/chatgpt/scraper.py` - Use 180s for ChatGPT

**Backwards compatible:** Yes - all new parameters have defaults
