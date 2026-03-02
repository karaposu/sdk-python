# Async + Sync Adapter Implementation (Approach 2)

> **REVISED**: Updated based on plan critique findings (2025-12-11)

## High-Level Summary

**Goal**: Fix the fundamentally broken async design by implementing a clean separation between async and sync clients.

**What We're Building**:
1. **Pure async `BrightDataClient`** - Single session lifecycle managed at client level, NO nested contexts
2. **Separate `SyncBrightDataClient`** - Adapter with persistent event loop for sync users

**Why This Matters**:
- Current design has race conditions causing "Connector is closed" errors
- Current sync wrappers create new event loops per call (10-50x slower)
- Current nested `async with self.engine:` in **sync wrapper methods** breaks concurrent operations

**Key Finding from Code Analysis**:
- The async methods (`products_async`, `reviews_async`, etc.) are **already correctly implemented** without nested contexts
- The problem is in **sync wrapper methods** (`products()`, `reviews()`, etc.) which have `async with self.engine:` + `asyncio.run()`
- Client methods (`list_zones`, `get_account_info`, etc.) DO have nested contexts that need removal

---

## High-Level Implementation Steps

### Phase 1: Create SyncBrightDataClient (NEW FILE)
1. New class that wraps `BrightDataClient`
2. Creates persistent event loop in `__enter__`
3. Initializes async client in the loop
4. All methods use `loop.run_until_complete()`
5. Provides complete sync wrappers for all scrape/search/crawler services
6. Proper cleanup in `__exit__`

### Phase 2: Add Context Manager to BaseWebScraper
1. Add `__aenter__`/`__aexit__` to `BaseWebScraper`
2. Enables standalone scraper usage pattern
3. Engine lifecycle managed by scraper when used directly

### Phase 3: Fix SERP Base Class
1. Remove broken `search()` sync method from `BaseSERPService`
2. Sync access only through `SyncSearchService`

### Phase 4: Pure Async BrightDataClient
1. Remove ALL `async with self.engine:` from client methods
2. Remove ALL sync wrappers (`*_sync()` methods, `_run_async_with_cleanup()`)
3. Client's `__aenter__` initializes engine ONCE
4. Client's `__aexit__` cleans up engine ONCE
5. All methods assume engine is already initialized
6. Add `_ensure_initialized()` helper for clear errors

### Phase 5: Update Services Layer
1. Remove `async with self._client.engine:` from service sync methods
2. Remove all `asyncio.run()` calls from services
3. Keep async methods as primary (rename `*_async` to `*`)
4. Add backward compatibility aliases (`products_async = products`)

### Phase 6: Update Scrapers Layer
1. Remove sync wrapper methods (NOT async methods - they're already correct!)
2. Remove `asyncio.run()` from sync wrappers
3. Add backward compatibility aliases for renamed methods
4. Fix ScrapeJob to handle closed engine gracefully

### Phase 7: Update Exports & Documentation
1. Export both clients from `__init__.py`
2. Update documentation with both patterns
3. Add migration examples
4. Document breaking changes

---

## Current Behavior vs Expected New Behavior

### 1. Client Lifecycle Management

**Current (Broken)**:
```python
class BrightDataClient:
    async def list_zones(self):
        async with self.engine:  # NESTED CONTEXT - causes race conditions
            return await self._zone_manager.list_zones()

    async def get_account_info(self):
        async with self.engine:  # ANOTHER NESTED CONTEXT - conflicts!
            ...
```

**Expected (Fixed)**:
```python
class BrightDataClient:
    async def __aenter__(self):
        await self.engine.__aenter__()  # Initialize ONCE here
        return self

    async def list_zones(self):
        self._ensure_initialized()  # Clear error if not in context
        return await self._zone_manager.list_zones()

    async def get_account_info(self):
        self._ensure_initialized()
        ...
```

### 2. Concurrent Operations

**Current (Broken)**:
```python
client = BrightDataClient()
results = await asyncio.gather(
    client.list_zones(),        # Enters engine context
    client.get_account_info(),  # Enters engine context (RACE!)
)
# Error: "Connector is closed"
```

**Expected (Fixed)**:
```python
async with BrightDataClient() as client:
    results = await asyncio.gather(
        client.list_zones(),        # Uses shared session
        client.get_account_info(),  # Uses shared session
        client.scrape.amazon.products(url),  # Uses shared session
    )
# All work correctly!
```

### 3. Sync Method Performance

**Current (Slow)**:
```python
# Each call creates NEW event loop
zones = client.list_zones_sync()      # Loop 1: create -> use -> destroy
info = client.get_account_info_sync() # Loop 2: create -> use -> destroy
conn = client.test_connection_sync()  # Loop 3: create -> use -> destroy
# 3 loops, 3 sessions, NO connection reuse
# ~150ms overhead just for loop management
```

**Expected (Fast)**:
```python
with SyncBrightDataClient() as client:
    zones = client.list_zones()       # Uses persistent loop
    info = client.get_account_info()  # Uses persistent loop
    conn = client.test_connection()   # Uses persistent loop
# 1 loop, 1 session, connection pooling works
# ~5ms overhead total
```

### 4. Scraper Sync Wrapper Patterns

**Current (Nested Context in SYNC wrappers only)**:
```python
class AmazonScraper:
    async def products_async(self, url, ...):
        # ✅ Already correct - no nested context!
        return await self._scrape_urls(url=url, ...)

    def products(self, url, ...):
        async def _run():
            async with self.engine:  # ❌ NESTED CONTEXT HERE
                return await self.products_async(url, ...)
        return asyncio.run(_run())  # ❌ NEW LOOP!
```

**Expected (Clean)**:
```python
class AmazonScraper:
    async def products(self, url, ...):
        # Async method - no sync wrapper on scraper itself
        return await self._scrape_urls(url=url, ...)

    # Backward compatibility alias
    products_async = products

# Sync access via SyncBrightDataClient:
with SyncBrightDataClient() as client:
    result = client.scrape.amazon.products(url)  # Via SyncAmazonScraper
```

### 5. SERP Service Patterns

**Current (Broken sync method)**:
```python
class BaseSERPService:
    def search(self, *args, **kwargs):
        # ❌ No engine context - will fail!
        return asyncio.run(self.search_async(*args, **kwargs))
```

**Expected (Clean)**:
```python
class BaseSERPService:
    # Only async method - no sync wrapper
    async def search(self, query, ...):
        ...

# Sync access via SyncSearchService:
with SyncBrightDataClient() as client:
    result = client.search.google(query)
```

### 6. Connection Pooling

**Current (Broken)**:
```
100 API calls in sync mode:
- 100 event loops created/destroyed
- 100 ClientSessions created/destroyed
- 100 TCP connections opened/closed
- NO connection reuse
- Time: ~60-90 seconds for overhead alone
```

**Expected (Working)**:
```
100 API calls in sync mode:
- 1 event loop (persistent)
- 1 ClientSession (persistent)
- ~10 TCP connections (pooled, reused)
- Full connection pooling
- Time: ~5 seconds overhead total
```

### 7. Error Messages

**Current (Confusing)**:
```
RuntimeError: Connector is closed
RuntimeError: Session is closed
aiohttp.client_exceptions.ClientConnectionError
```

**Expected (Clear)**:
```python
# Without context manager:
RuntimeError: BrightDataClient not initialized.
Use: async with BrightDataClient() as client: ...

# Or for sync:
RuntimeError: SyncBrightDataClient not initialized.
Use: with SyncBrightDataClient() as client: ...
```

---

## Edge Cases to Consider

### 1. Standalone Scraper Usage
**Scenario**: User creates scraper directly without client
```python
scraper = AmazonScraper(bearer_token="...")
result = await scraper.products(url)  # Needs engine
```
**Solution**: Add context manager to `BaseWebScraper`:
```python
async with AmazonScraper() as scraper:
    result = await scraper.products(url)
```

**Implementation**:
```python
class BaseWebScraper:
    async def __aenter__(self):
        await self.engine.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.engine.__aexit__(exc_type, exc_val, exc_tb)
```

### 2. Multiple Clients in Same Process
**Scenario**: User creates multiple clients
```python
async with BrightDataClient(token1) as client1:
    async with BrightDataClient(token2) as client2:
        # Both should work independently
```
**Solution**: Each client has its own engine instance - no shared state

### 3. Nested Context Manager Calls
**Scenario**: User accidentally nests contexts
```python
async with BrightDataClient() as client:
    async with client:  # Double entry
        ...
```
**Solution**: Engine's idempotent check handles this (already in place)

### 4. Using Client Without Context Manager
**Scenario**: User forgets context manager
```python
client = BrightDataClient()
await client.list_zones()  # Should fail clearly
```
**Solution**: `_ensure_initialized()` checks `self.engine._session is None` and raises:
```
RuntimeError: BrightDataClient not initialized.
Use: async with BrightDataClient() as client: ...
```

### 5. Sync Client Inside Async Context
**Scenario**: User tries to use SyncBrightDataClient in async code
```python
async def main():
    with SyncBrightDataClient() as client:  # Creates loop inside loop
        client.list_zones()
```
**Solution**: Detect running loop in `__init__` and raise clear error:
```python
try:
    asyncio.get_running_loop()
    raise RuntimeError(
        "SyncBrightDataClient cannot be used inside async context. "
        "Use BrightDataClient with async/await instead."
    )
except RuntimeError as e:
    if "no running event loop" not in str(e).lower():
        raise  # Re-raise our custom error
    # No running loop - correct for sync usage
```

### 6. Long-Running Operations Across Sessions (ScrapeJob)
**Scenario**: User triggers job, exits context, tries to fetch later
```python
async with BrightDataClient() as client:
    job = await client.scrape.amazon.products_trigger(url)
# Context closed

# Later...
async with BrightDataClient() as client:
    result = await job.fetch()  # Job has old engine reference
```
**Solution**: ScrapeJob checks engine state and raises clear error:
```python
async def fetch(self, format="json") -> Any:
    if self._api_client.engine._session is None:
        raise RuntimeError(
            f"Cannot fetch results: client session closed.\n"
            f"Use snapshot_id '{self.snapshot_id}' with a new client:\n"
            f"  async with BrightDataClient() as client:\n"
            f"      result = await client._api_client.fetch_result('{self.snapshot_id}')"
        )
    return await self._api_client.fetch_result(self.snapshot_id, format=format)
```

### 7. Service Object Lifecycle
**Scenario**: User stores service reference outside context
```python
async with BrightDataClient() as client:
    scraper = client.scrape.amazon

# Later use scraper (engine closed)
await scraper.products(url)  # Fails
```
**Solution**: Methods that use engine will fail with clear error from `_ensure_initialized()` or engine's own check

### 8. Rate Limiter Across Concurrent Operations
**Scenario**: Multiple concurrent operations should share rate limiter
```python
async with BrightDataClient(rate_limit=10) as client:
    await asyncio.gather(
        client.scrape.amazon.products(url1),
        client.scrape.amazon.products(url2),
        # ... 20 concurrent calls
    )
```
**Solution**: All operations share single engine's rate limiter (already works with shared engine)

### 9. Exception During Context Exit
**Scenario**: Exception during cleanup
```python
async with BrightDataClient() as client:
    await client.list_zones()
    raise ValueError("User error")
# Does engine cleanup properly?
```
**Solution**: `__aexit__` must handle cleanup even when exception passed in (already handled by aiohttp)

### 10. Timeout During Polling
**Scenario**: Poll timeout while waiting for scrape
```python
async with BrightDataClient() as client:
    result = await client.scrape.amazon.products(url, poll_timeout=5)
    # Times out - engine still usable?
```
**Solution**: Polling timeout is application-level, doesn't affect engine lifecycle. Engine remains usable.

### 11. Ctrl+C / KeyboardInterrupt
**Scenario**: User cancels during operation
```python
async with BrightDataClient() as client:
    await client.scrape.amazon.products(url)  # User presses Ctrl+C
```
**Solution**: asyncio handles CancelledError, `__aexit__` still called for cleanup

### 12. Thread Safety of SyncBrightDataClient
**Scenario**: Multiple threads use same sync client
```python
with SyncBrightDataClient() as client:
    with ThreadPoolExecutor() as pool:
        pool.map(lambda url: client.scrape.amazon.products(url), urls)
```
**Solution**: `loop.run_until_complete` is NOT thread-safe. Document that SyncBrightDataClient is single-threaded. For multi-threaded, use separate clients per thread.

### 13. Backward Compatibility for Method Renames
**Scenario**: Existing code uses `*_async` method names
```python
result = await scraper.products_async(url)  # Should still work
```
**Solution**: Add backward compatibility aliases:
```python
async def products(self, url, ...):
    ...

# Backward compatibility alias
products_async = products
```

---

## Summary

| Aspect | Current | After Implementation |
|--------|---------|---------------------|
| **Session lifecycle** | Nested contexts (broken) | Single client-level context |
| **Concurrent calls** | Race conditions | Works correctly |
| **Sync performance** | New loop per call | Persistent loop |
| **Connection pooling** | Broken | Works |
| **API surface** | Dual methods (async + sync) | Clean separation |
| **Code complexity** | High (mixed patterns) | Lower (clear ownership) |
| **Standalone scrapers** | Not supported | Supported via context manager |
| **Backward compatibility** | N/A | Aliases for renamed methods |

---

## Breaking Changes

1. **Sync methods removed from `BrightDataClient`**: Use `SyncBrightDataClient` instead
2. **Sync methods removed from scrapers**: Use `SyncBrightDataClient` instead
3. **Method renames**: `*_async` methods renamed to `*` (aliases provided for compatibility)
4. **Context manager required**: Both clients must be used with context manager

---

**Next Step**: See `low_level.md` for detailed implementation changes.
