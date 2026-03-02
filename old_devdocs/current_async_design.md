# Current Async Design - Brightdata Python SDK

**Date**: 2025-01-10
**Purpose**: Document the current async architecture and explore alternative approaches

---

## 📋 Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Core Async Components](#core-async-components)
3. [Async Flow Patterns](#async-flow-patterns)
4. [Dual Interface Pattern (Async/Sync)](#dual-interface-pattern-asyncsync)
5. [Resource Management](#resource-management)
6. [Concurrency Patterns](#concurrency-patterns)
7. [Alternative Async Approaches](#alternative-async-approaches)
8. [Trade-offs & Recommendations](#trade-offs--recommendations)

---

## 1. High-Level Architecture

### Current Design Philosophy

The SDK uses **layered async architecture** with clear separation of concerns:

```
┌─────────────────────────────────────────────────────────┐
│                   USER APPLICATION                       │
│         (Can be sync or async application)              │
└────────────────────┬────────────────────────────────────┘
                     │
         ┌───────────▼──────────────┐
         │  BrightDataClient        │ ◄── Entry point with context manager
         │  (async with support)    │     Manages engine lifecycle
         └───────────┬──────────────┘
                     │
         ┌───────────▼──────────────┐
         │   Service Namespaces     │
         │  .scrape / .search       │ ◄── High-level service interfaces
         │  .crawler / .web         │     Lazy-loaded on access
         └───────────┬──────────────┘
                     │
    ┌────────────────┴────────────────┐
    │                                  │
    ▼                                  ▼
┌───────────┐                   ┌──────────────┐
│ Scrapers  │                   │ SERP/WebUnl  │
│ (Amazon,  │                   │ (Direct API) │
│ LinkedIn, │                   │              │
│ etc.)     │                   │              │
└─────┬─────┘                   └───────┬──────┘
      │                                  │
      ▼                                  │
┌──────────────────┐                    │
│ WorkflowExecutor │                    │
│ (Trigger/Poll/   │                    │
│  Fetch pattern)  │                    │
└─────┬────────────┘                    │
      │                                  │
      ▼                                  │
┌──────────────────┐                    │
│ DatasetAPIClient │                    │
│ (Low-level HTTP) │                    │
└─────┬────────────┘                    │
      │                                  │
      └──────────────┬───────────────────┘
                     │
         ┌───────────▼──────────────┐
         │     AsyncEngine          │ ◄── Core async engine
         │  - aiohttp.ClientSession │     Shared across all operations
         │  - aiolimiter.Limiter    │     Connection pooling & rate limiting
         │  - TCPConnector          │
         └──────────────────────────┘
```

### Key Design Decisions

1. **Context Manager Pattern**: `async with BrightDataClient()` manages engine lifecycle
2. **Shared Engine**: All services/scrapers share ONE AsyncEngine instance for resource efficiency
3. **Lazy Loading**: Service namespaces and scrapers instantiated only when accessed
4. **Dual Interface**: Every async method has a sync wrapper for ease of use
5. **Workflow Abstraction**: Trigger/Poll/Fetch pattern encapsulated in reusable components

---

## 2. Core Async Components

### 2.1 AsyncEngine (`core/engine.py`)

**Role**: Central async HTTP engine managing all network operations

```python
class AsyncEngine:
    def __init__(self, api_token: str):
        self._session: Optional[aiohttp.ClientSession] = None
        self._rate_limiter = AsyncLimiter(max_rate=100, time_period=1)
        self._connector = None  # Created on __aenter__

    async def __aenter__(self):
        """Initialize session with connection pooling"""
        self._connector = aiohttp.TCPConnector(
            limit=100,           # Max concurrent connections
            limit_per_host=20,   # Per host limit
            ttl_dns_cache=300    # DNS cache TTL
        )
        self._session = aiohttp.ClientSession(
            connector=self._connector,
            headers={"Authorization": f"Bearer {self._api_token}"}
        )
        return self

    async def __aexit__(self, *args):
        """Clean up resources"""
        if self._session:
            await self._session.close()
        if self._connector:
            await self._connector.close()
```

**Key Features**:
- ✅ Connection pooling (max 100 connections, 20 per host)
- ✅ Built-in rate limiting (100 req/s with aiolimiter)
- ✅ DNS caching (5 min TTL)
- ✅ Automatic resource cleanup
- ✅ Context manager pattern for lifecycle management

**Async Methods**:
- `async def get(path)` - GET request
- `async def post(path, json_data)` - POST request
- `async def delete(path)` - DELETE request
- `async def get_from_url(url)` - Direct URL GET
- `async def post_to_url(url, json_data)` - Direct URL POST

### 2.2 BrightDataClient (`client.py`)

**Role**: Main entry point, orchestrates services and manages engine lifecycle

```python
class BrightDataClient:
    def __init__(self, token: Optional[str] = None, **kwargs):
        self.token = token or os.getenv("BRIGHTDATA_API_TOKEN")
        self.engine = AsyncEngine(self.token)

        # Service namespaces (lazy-loaded)
        self._scrape_service: Optional[ScrapeService] = None
        self._search_service: Optional[SearchService] = None
        # ... other services

    async def __aenter__(self):
        """Initialize engine"""
        await self.engine.__aenter__()
        return self

    async def __aexit__(self, *args):
        """Cleanup engine"""
        await self.engine.__aexit__(*args)

    @property
    def scrape(self) -> ScrapeService:
        """Lazy-load scrape service"""
        if self._scrape_service is None:
            self._scrape_service = ScrapeService(self)
        return self._scrape_service
```

**Key Features**:
- ✅ Lazy service instantiation
- ✅ Single engine shared across all services
- ✅ Environment variable fallback for token
- ✅ Context manager for resource management

### 2.3 WorkflowExecutor (`scrapers/workflow.py`)

**Role**: Encapsulates Trigger→Poll→Fetch workflow pattern

```python
class WorkflowExecutor:
    async def execute(
        self,
        payload: List[Dict],
        dataset_id: str,
        poll_interval: int = 10,
        poll_timeout: int = 600,
        include_errors: bool = True
    ) -> ScrapeResult:
        """
        Standard async workflow:
        1. Trigger job → get snapshot_id
        2. Poll status until ready
        3. Fetch results when ready
        """
        # Trigger
        snapshot_id = await self.api_client.trigger(
            payload, dataset_id, include_errors
        )

        # Poll + Fetch
        result = await poll_until_ready(
            get_status_func=self.api_client.get_status,
            fetch_result_func=self.api_client.fetch_result,
            snapshot_id=snapshot_id,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout
        )

        return result
```

**Key Features**:
- ✅ Reusable workflow logic
- ✅ Automatic polling with configurable intervals
- ✅ Timeout handling
- ✅ Error tracking and timing metrics

### 2.4 Polling Utility (`utils/polling.py`)

**Role**: Generic async polling mechanism

```python
async def poll_until_ready(
    get_status_func: Callable[[str], Awaitable[str]],
    fetch_result_func: Callable[[str], Awaitable[Any]],
    snapshot_id: str,
    poll_interval: int = 10,
    poll_timeout: int = 600,
    **kwargs
) -> ScrapeResult:
    """
    Poll until ready, handling:
    - Status checking with configurable intervals
    - Timeout detection
    - Error state handling
    - Automatic result fetching when ready
    """
    start_time = datetime.now(timezone.utc)

    while True:
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        if elapsed > poll_timeout:
            return ScrapeResult(success=False, error="Timeout")

        status = await get_status_func(snapshot_id)

        if status == "ready":
            data = await fetch_result_func(snapshot_id)
            return ScrapeResult(success=True, data=data, ...)
        elif status in ("error", "failed"):
            return ScrapeResult(success=False, error=f"Job failed: {status}")

        await asyncio.sleep(poll_interval)
```

**Key Features**:
- ✅ Callback-based (dependency injection)
- ✅ Configurable polling intervals
- ✅ Timeout handling
- ✅ Timing metadata collection

---

## 3. Async Flow Patterns

### 3.1 Standard Scrape Flow (Datasets API)

```python
# User code (async)
async with BrightDataClient() as client:
    result = await client.scrape.amazon.products_async(
        url="https://amazon.com/dp/B123"
    )

# Internal flow:
# 1. AmazonScraper.products_async()
#    └─> WorkflowExecutor.execute()
#        ├─> DatasetAPIClient.trigger()
#        │   └─> AsyncEngine.post_to_url() → HTTP POST to trigger
#        │       └─> aiohttp.ClientSession.post()
#        │           └─> Rate limiter applied
#        │           └─> Returns snapshot_id
#        │
#        ├─> poll_until_ready()
#        │   └─> Loop: DatasetAPIClient.get_status()
#        │       └─> AsyncEngine.get_from_url() → HTTP GET for status
#        │           └─> await asyncio.sleep(10) between polls
#        │
#        └─> DatasetAPIClient.fetch_result()
#            └─> AsyncEngine.get_from_url() → HTTP GET for data
#                └─> Return ScrapeResult
```

### 3.2 Web Unlocker Flow (Direct API)

```python
# User code (async)
async with BrightDataClient() as client:
    result = await client.web.scrape_async(
        url="https://example.com",
        zone="my_zone"
    )

# Internal flow:
# 1. WebUnlockerService.scrape_async()
#    └─> WebUnlockerService._scrape_single_async()
#        └─> AsyncEngine.post_to_url() → HTTP POST
#            └─> aiohttp.ClientSession.post()
#                └─> Rate limiter applied
#                └─> Return ScrapeResult immediately (no polling)
```

### 3.3 SERP Search Flow

```python
# User code (async)
async with BrightDataClient() as client:
    result = await client.search.google_async(
        query="python tutorial",
        location="United States"
    )

# Internal flow:
# 1. SearchService.google_async()
#    └─> GoogleSERPService.search_async()
#        └─> BaseSERPService._search_single_async()
#            └─> retry_with_backoff()
#                └─> AsyncEngine.post_to_url() → HTTP POST
#                    └─> aiohttp.ClientSession.post()
#                        └─> Rate limiter applied
#                        └─> Return SearchResult immediately
```

### 3.4 Manual Control Flow (Trigger/Poll/Fetch)

```python
# User code (async) - manual control
async with BrightDataClient() as client:
    # Trigger
    job = await client.scrape.amazon.products_trigger_async(url="...")
    print(f"Job ID: {job.snapshot_id}")

    # Do other work...
    await some_other_async_work()

    # Check status
    status = await job.status_async()

    # Wait for completion
    await job.wait_async(timeout=300)

    # Fetch results
    data = await job.fetch_async()
```

---

## 4. Dual Interface Pattern (Async/Sync)

### Current Implementation

**Every async method has a sync wrapper**:

```python
# Async version
async def products_async(self, url: str) -> ScrapeResult:
    return await self._scrape_urls(url, dataset_id=self.DATASET_ID)

# Sync version
def products(self, url: str) -> ScrapeResult:
    async def _run():
        async with self.engine:
            return await self.products_async(url)

    return asyncio.run(_run())
```

### Sync Wrapper Patterns

**Pattern 1**: BaseAPI._execute_sync()
```python
def _execute_sync(self, *args, **kwargs):
    try:
        asyncio.get_running_loop()
        raise RuntimeError("Cannot call sync from async context")
    except RuntimeError:
        async def _run():
            async with self.engine:
                return await self._execute_async(*args, **kwargs)
        return asyncio.run(_run())
```

**Pattern 2**: BaseWebScraper._run_blocking()
```python
def _run_blocking(coro):
    try:
        asyncio.get_running_loop()
        # Already in event loop - use thread pool
        with concurrent.futures.ThreadPoolExecutor() as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    except RuntimeError:
        # No event loop - use asyncio.run directly
        return asyncio.run(coro)
```

**Pros**:
- ✅ Easy migration for sync codebases
- ✅ Both interfaces feel natural
- ✅ No forced async adoption

**Cons**:
- ❌ Code duplication (2x methods)
- ❌ asyncio.run() creates NEW event loop each time
- ❌ Cannot benefit from concurrent execution in sync mode
- ❌ Larger API surface area

---

## 5. Resource Management

### 5.1 Connection Pooling

```python
# AsyncEngine uses aiohttp.TCPConnector
self._connector = aiohttp.TCPConnector(
    limit=100,              # Global connection limit
    limit_per_host=20,      # Per-host connection limit
    ttl_dns_cache=300,      # DNS cache for 5 minutes
    enable_cleanup_closed=True
)
```

**Benefits**:
- Connection reuse across requests
- Reduced overhead from TCP handshakes
- DNS caching reduces lookup latency

### 5.2 Rate Limiting

```python
# AsyncEngine uses aiolimiter
from aiolimiter import AsyncLimiter

self._rate_limiter = AsyncLimiter(
    max_rate=100,     # 100 requests
    time_period=1     # per second
)

# Applied before every request
async def _apply_rate_limit(self):
    await self._rate_limiter.acquire()
```

**Benefits**:
- Prevents API rate limit violations
- Automatic request throttling
- No manual delay management needed

### 5.3 Context Manager Lifecycle

```python
# Proper resource cleanup
async with BrightDataClient() as client:
    # Engine initialized (__aenter__)
    # - ClientSession created
    # - TCPConnector initialized
    # - Rate limiter ready

    result = await client.scrape.amazon.products_async(url)

    # Engine cleaned up (__aexit__)
    # - Session closed
    # - Connections released
    # - Resources freed
```

**Benefits**:
- Guaranteed cleanup even on exceptions
- No resource leaks
- Clear lifecycle boundaries

---

## 6. Concurrency Patterns

### 6.1 Concurrent Operations (User Level)

**Multiple URLs**:
```python
async with BrightDataClient() as client:
    # Internally uses asyncio.gather
    results = await client.scrape.amazon.products_async(
        url=["url1", "url2", "url3"]  # List of URLs
    )
    # All 3 operations run concurrently
```

**Manual Concurrency**:
```python
async with BrightDataClient() as client:
    tasks = [
        client.scrape.amazon.products_async("url1"),
        client.scrape.linkedin.profiles_async("url2"),
        client.search.google_async("query1")
    ]

    results = await asyncio.gather(*tasks)
    # All 3 operations run concurrently
```

### 6.2 Internal Concurrency (SDK Level)

**WebUnlockerService** (api/web_unlocker.py:185):
```python
async def _scrape_multiple_async(self, urls: List[str], ...):
    tasks = [
        self._scrape_single_async(url, ...)
        for url in urls
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

**BaseSERPService** (api/serp/base.py:225):
```python
async def _search_multiple_async(self, queries: List[str], ...):
    tasks = [
        self._search_single_async(query, ...)
        for q in queries
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 6.3 Polling Pattern

**Sequential but non-blocking**:
```python
# Multiple jobs polling concurrently
async with BrightDataClient() as client:
    # Trigger all jobs
    jobs = [
        await client.scrape.amazon.products_trigger_async(url)
        for url in urls
    ]

    # Wait for all concurrently
    tasks = [job.wait_async(timeout=300) for job in jobs]
    await asyncio.gather(*tasks)

    # Fetch all results
    results = [await job.fetch_async() for job in jobs]
```

---

## 7. Alternative Async Approaches

### Approach 1: **Pure Async (Drop Sync Wrappers)**

**Description**: Remove all sync methods, force users to use async

```python
# ONLY async interface
class AmazonScraper:
    async def products(self, url: str) -> ScrapeResult:
        return await self._scrape_urls(url)

    # No sync wrapper!
```

**Pros**:
- ✅ Simpler codebase (50% fewer methods)
- ✅ Forces async best practices
- ✅ Users benefit from true concurrency
- ✅ Better performance (no asyncio.run overhead)

**Cons**:
- ❌ Breaking change for sync users
- ❌ Requires async adoption across user's codebase
- ❌ Higher learning curve

**Use Case**: Best for new async-first applications, data pipelines, web scraping services

---

### Approach 2: **Async First with Optional Sync Adapter**

**Description**: Primary interface is async, but provide a SyncAdapter class

```python
# Primary interface (async)
class BrightDataClient:
    async def scrape_amazon(self, url: str) -> ScrapeResult:
        return await self._scrape(url)

# Optional sync adapter
class SyncBrightDataClient:
    def __init__(self):
        self._client = BrightDataClient()
        self._loop = None

    def __enter__(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._client.__aenter__())
        return self

    def __exit__(self, *args):
        self._loop.run_until_complete(self._client.__aexit__(*args))
        self._loop.close()

    def scrape_amazon(self, url: str) -> ScrapeResult:
        return self._loop.run_until_complete(
            self._client.scrape_amazon(url)
        )

# Usage
# Async users
async with BrightDataClient() as client:
    result = await client.scrape_amazon(url)

# Sync users
with SyncBrightDataClient() as client:
    result = client.scrape_amazon(url)
```

**Pros**:
- ✅ Clean separation of concerns
- ✅ Async code stays clean
- ✅ Sync users have clear adapter
- ✅ Can optimize each path independently

**Cons**:
- ❌ Two client classes to maintain
- ❌ Documentation burden
- ❌ Sync adapter still has asyncio.run limitations

**Use Case**: Good compromise for SDKs targeting both audiences

---

### Approach 3: **Thread-Based Sync + Event Loop Manager**

**Description**: Sync methods run in dedicated thread with persistent event loop

```python
class EventLoopManager:
    """Manages persistent event loop in background thread"""
    def __init__(self):
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._thread: Optional[threading.Thread] = None
        self._started = threading.Event()

    def start(self):
        """Start event loop in background thread"""
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        self._started.wait()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        self._started.set()
        self._loop.run_forever()

    def run_coroutine(self, coro):
        """Run coroutine in background loop"""
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()

    def stop(self):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join()

# Usage in SDK
class BrightDataClient:
    _event_loop_manager = EventLoopManager()

    def __init__(self):
        if not self._event_loop_manager._loop:
            self._event_loop_manager.start()

    # Sync method using persistent loop
    def scrape_amazon(self, url: str) -> ScrapeResult:
        coro = self.scrape_amazon_async(url)
        return self._event_loop_manager.run_coroutine(coro)
```

**Pros**:
- ✅ Persistent event loop (better performance)
- ✅ No asyncio.run overhead
- ✅ True background execution
- ✅ Sync methods can run concurrently

**Cons**:
- ❌ Thread management complexity
- ❌ More complex lifecycle management
- ❌ Potential thread safety issues
- ❌ Harder to debug

**Use Case**: For SDKs where sync performance is critical

---

### Approach 4: **Lazy Async (Coroutine Return)**

**Description**: Return coroutines directly, let users decide when to await

```python
class BrightDataClient:
    def scrape_amazon(self, url: str):
        """Returns awaitable coroutine"""
        return self._scrape_amazon_impl(url)

    async def _scrape_amazon_impl(self, url: str) -> ScrapeResult:
        # Actual implementation
        pass

# Usage
# Async users
result = await client.scrape_amazon(url)

# Or batch
results = await asyncio.gather(
    client.scrape_amazon(url1),
    client.scrape_amazon(url2)
)

# Sync users (still need asyncio.run, but more flexible)
result = asyncio.run(client.scrape_amazon(url))
```

**Pros**:
- ✅ Most flexible for users
- ✅ Cleaner method signatures
- ✅ Easier to compose operations
- ✅ Less code duplication

**Cons**:
- ❌ Confusing API (returns unawaited coroutine)
- ❌ Easy to forget await (runtime warning)
- ❌ No clear sync option

**Use Case**: Advanced async libraries, not recommended for SDKs

---

### Approach 5: **Callback-Based Async**

**Description**: Provide callback interface alongside async

```python
class BrightDataClient:
    # Async interface
    async def scrape_amazon_async(self, url: str) -> ScrapeResult:
        return await self._scrape(url)

    # Callback interface
    def scrape_amazon_callback(
        self,
        url: str,
        on_success: Callable[[ScrapeResult], None],
        on_error: Callable[[Exception], None]
    ):
        """Non-blocking callback interface"""
        async def _execute():
            try:
                result = await self.scrape_amazon_async(url)
                on_success(result)
            except Exception as e:
                on_error(e)

        # Schedule in background
        asyncio.create_task(_execute())

# Usage
def handle_result(result):
    print(f"Got result: {result.data}")

def handle_error(error):
    print(f"Error: {error}")

client.scrape_amazon_callback(url, handle_result, handle_error)
```

**Pros**:
- ✅ Non-blocking even in sync context
- ✅ Familiar to JS developers
- ✅ Good for event-driven apps

**Cons**:
- ❌ Callback hell potential
- ❌ Harder to compose
- ❌ Less Pythonic
- ❌ Error handling complexity

**Use Case**: GUI applications, event-driven systems

---

### Approach 6: **Generator-Based Async (Streaming)**

**Description**: Use async generators for streaming results

```python
class BrightDataClient:
    async def scrape_amazon_stream(
        self,
        urls: List[str]
    ) -> AsyncIterator[ScrapeResult]:
        """Stream results as they complete"""
        tasks = [
            self._scrape_single(url)
            for url in urls
        ]

        # Yield results as they complete
        for coro in asyncio.as_completed(tasks):
            result = await coro
            yield result

# Usage
async for result in client.scrape_amazon_stream(urls):
    print(f"Got result: {result.url}")
    # Process immediately without waiting for all
```

**Pros**:
- ✅ Memory efficient for large batches
- ✅ Progressive results
- ✅ Better UX (show progress)
- ✅ Can process results as they arrive

**Cons**:
- ❌ More complex API
- ❌ Requires async iteration
- ❌ Harder to collect all results

**Use Case**: Large batch operations, real-time dashboards

---

### Approach 7: **Current Hybrid (Keep as-is with improvements)**

**Description**: Keep dual interface but optimize implementation

```python
class BrightDataClient:
    # Async (primary)
    async def scrape_amazon_async(self, url: str) -> ScrapeResult:
        return await self._scrape(url)

    # Sync (convenience)
    def scrape_amazon(self, url: str) -> ScrapeResult:
        # Check if we can reuse existing loop
        if hasattr(self, '_sync_runner'):
            return self._sync_runner.run(
                self.scrape_amazon_async(url)
            )
        return asyncio.run(self.scrape_amazon_async(url))
```

**Pros**:
- ✅ No breaking changes
- ✅ Maintains backward compatibility
- ✅ Incremental improvements possible
- ✅ Both audiences served

**Cons**:
- ❌ Still has duplication
- ❌ asyncio.run limitations remain
- ❌ Sync performance not ideal

**Use Case**: Current SDK (evolutionary approach)

---

## 8. Trade-offs & Recommendations

### For Brightdata SDK Specifically

**Context**: This is an SDK wrapping web scraping services that:
- Makes HTTP requests to external APIs
- Has I/O-bound workloads
- Benefits greatly from concurrency
- Used in various contexts (scripts, web apps, data pipelines)

### Recommended Approach: **Hybrid Evolution** (Modified Approach 2)

**Phase 1**: Keep current design, document async best practices
- ✅ No breaking changes
- ✅ Educate users on async benefits
- ✅ Improve async examples in docs

**Phase 2**: Introduce optional async-optimized mode
- Add `AsyncBrightDataClient` (async-only, cleaner)
- Keep `BrightDataClient` (dual interface)
- Let users choose based on needs

**Phase 3**: Deprecate sync wrappers (v2.0)
- Mark sync methods as deprecated
- Provide migration guide
- Give 6-12 months notice

### Why This Approach?

1. **SDK Nature**: Wraps remote APIs → async is natural fit
2. **Concurrency Benefits**: Users scraping 100s of URLs benefit massively from async
3. **I/O-Bound**: Network latency dominates → async shines here
4. **Modern Python**: Async/await is standard in Python 3.7+
5. **Ecosystem**: FastAPI, aiohttp, etc. are all async

### Performance Comparison

```python
# Sync (current)
with BrightDataClient() as client:
    results = []
    for url in 100_urls:
        result = client.scrape.amazon.products(url)  # Sequential!
        results.append(result)
# Time: ~500 seconds (5s per URL * 100)

# Async (optimal)
async with BrightDataClient() as client:
    tasks = [
        client.scrape.amazon.products_async(url)
        for url in 100_urls
    ]
    results = await asyncio.gather(*tasks)  # Concurrent!
# Time: ~20 seconds (max 20 concurrent, ~5s per batch)
```

**25x faster with async!**

### Alternative Recommendations by Use Case

| Use Case | Best Approach | Reason |
|----------|---------------|--------|
| **Data Pipelines** | Pure Async (Approach 1) | Max performance, batch processing |
| **Web Apps (FastAPI)** | Pure Async (Approach 1) | Native async integration |
| **Jupyter Notebooks** | Current Hybrid (Approach 7) | Sync convenience important |
| **CLI Tools** | Sync Adapter (Approach 2) | Clear sync path |
| **High-Volume Scraping** | Streaming (Approach 6) | Memory efficient |
| **Legacy Integration** | Thread-Based (Approach 3) | Performance + compatibility |

---

## 9. Conclusion

### Current Design Strengths
- ✅ Well-structured layered architecture
- ✅ Clear separation of concerns
- ✅ Reusable async components
- ✅ Good resource management
- ✅ Both sync and async support

### Current Design Weaknesses
- ❌ Code duplication (sync wrappers)
- ❌ Suboptimal sync performance
- ❌ asyncio.run creates new loops
- ❌ Larger API surface

### Recommended Next Steps
1. **Document async patterns better** - Show users the performance benefits
2. **Add async examples** - More async usage patterns in docs
3. **Consider AsyncBrightDataClient** - Optional async-only interface
4. **Benchmark and measure** - Prove async benefits with real numbers
5. **Plan v2.0 evolution** - Long-term plan to deprecate sync wrappers

---

**Last Updated**: 2025-01-10
**Version**: SDK v1.x
**Status**: Living document
