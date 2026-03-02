# Concurrency Issues with Client Utility Methods

**Date**: 2025-01-10
**Issue**: "Connector is closed" errors when running utility methods concurrently
**Affected Methods**: `list_zones()`, `get_account_info()`, `delete_zone()`, `test_connection()`

---

## 🔴 The Problem

### Current Implementation Pattern

```python
# client.py
class BrightDataClient:
    async def list_zones(self) -> List[Dict[str, Any]]:
        async with self.engine:  # ❌ Problem: Creates new context
            if self._zone_manager is None:
                self._zone_manager = ZoneManager(self.engine)
            return await self._zone_manager.list_zones()

    async def get_account_info(self, refresh: bool = False) -> AccountInfo:
        async with self.engine:  # ❌ Problem: Creates new context
            async with self.engine.get_from_url(...) as response:
                # ...

    async def test_connection(self) -> bool:
        async with self.engine:  # ❌ Problem: Creates new context
            async with self.engine.get_from_url(...) as response:
                # ...
```

### The Issue

Each utility method calls `async with self.engine:`, which enters the AsyncEngine's context manager. This causes problems in concurrent scenarios:

#### Scenario 1: Concurrent calls outside client context
```python
client = BrightDataClient()

# ❌ FAILS: Each method races to initialize/close engine
results = await asyncio.gather(
    client.list_zones(),        # Enters engine context
    client.get_account_info(),  # Enters engine context (race!)
    client.test_connection()    # Enters engine context (race!)
)
# Error: "Connector is closed" - one task closes while others are running
```

#### Scenario 2: Concurrent calls inside client context
```python
async with BrightDataClient() as client:
    # Engine is ALREADY in context here from __aenter__

    # ❌ FAILS: Methods try to re-enter already-entered context
    results = await asyncio.gather(
        client.list_zones(),        # Tries to __aenter__ again
        client.get_account_info(),  # Tries to __aenter__ again
    )
# Error: "Connector is closed" or undefined behavior
```

### Root Cause Analysis

**AsyncEngine Context Manager** (`core/engine.py`):
```python
class AsyncEngine:
    async def __aenter__(self):
        """Initialize session and connector"""
        if self._session is None:
            self._connector = aiohttp.TCPConnector(limit=100, ...)
            self._session = aiohttp.ClientSession(connector=self._connector, ...)
        return self

    async def __aexit__(self, *args):
        """Close session and connector"""
        if self._session:
            await self._session.close()
        if self._connector:
            await self._connector.close()
```

**Problems**:
1. **Multiple `__aenter__` calls**: When concurrent tasks each call `async with self.engine:`, the first task initializes the session, but subsequent tasks might try to use it after the first task's `__aexit__` closes it.

2. **Race condition on cleanup**: If Task A exits the context (`__aexit__`) while Task B is still using the session, Task B gets "Connector is closed".

3. **No reference counting**: The context manager doesn't track how many tasks are using it, so it closes on the first exit.

4. **Idempotency assumption violated**: The comment says "Engine context manager is idempotent" (line 377 in client.py), but it's NOT truly idempotent for concurrent usage.

### Error Messages

```
RuntimeError: Session is closed
RuntimeError: Connector is closed
aiohttp.client_exceptions.ClientConnectionError: Connector is closed
```

---

## 🎯 Which Design Approaches Solve This?

Let's analyze each design approach from `current_async_design.md` and see how they handle this issue:

---

### ✅ **Approach 1: Pure Async (Drop Sync Wrappers)**

**Status**: **SOLVES THE ISSUE** ✅

**How it solves it**:
```python
class BrightDataClient:
    async def __aenter__(self):
        """Client manages engine lifecycle"""
        await self.engine.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self.engine.__aexit__(*args)

    # Utility methods DON'T manage engine context
    async def list_zones(self) -> List[Dict[str, Any]]:
        # ✅ Assumes engine is already initialized by client context
        if self._zone_manager is None:
            self._zone_manager = ZoneManager(self.engine)
        return await self._zone_manager.list_zones()

    async def get_account_info(self) -> AccountInfo:
        # ✅ Directly use engine (no context manager)
        async with self.engine.get_from_url(...) as response:
            # ...

# Usage
async with BrightDataClient() as client:
    # Engine initialized ONCE by client
    results = await asyncio.gather(
        client.list_zones(),        # ✅ Works
        client.get_account_info(),  # ✅ Works
        client.test_connection()    # ✅ Works
    )
    # Engine cleaned up ONCE by client
```

**Key Change**:
- Engine lifecycle managed ONLY by BrightDataClient context manager
- Utility methods assume engine is already initialized
- No nested `async with self.engine:` calls

**Why it works**:
- Single initialization point (client `__aenter__`)
- Single cleanup point (client `__aexit__`)
- No race conditions
- All concurrent operations share the same session

---

### ✅ **Approach 2: Async First with Sync Adapter**

**Status**: **SOLVES THE ISSUE** ✅

Same solution as Approach 1 for async interface:

```python
# Primary async interface (clean)
class BrightDataClient:
    async def list_zones(self):
        # No engine context management
        return await self._zone_manager.list_zones()

# Sync adapter (handles context separately)
class SyncBrightDataClient:
    def __enter__(self):
        self._loop = asyncio.new_event_loop()
        self._loop.run_until_complete(self._client.__aenter__())
        return self

    def list_zones(self):
        # Loop already running, engine already initialized
        return self._loop.run_until_complete(
            self._client.list_zones()
        )
```

**Why it works**:
- Async client manages engine lifecycle cleanly
- Sync adapter manages its own event loop
- No conflicts between concurrent operations

---

### ❌ **Approach 3: Thread-Based Sync + Event Loop Manager**

**Status**: **PARTIALLY SOLVES** ⚠️

```python
class EventLoopManager:
    """Manages persistent event loop in background thread"""
    def start(self):
        self._thread = threading.Thread(target=self._run_loop)
        self._thread.start()

    def _run_loop(self):
        self._loop = asyncio.new_event_loop()
        self._loop.run_forever()

    def run_coroutine(self, coro):
        future = asyncio.run_coroutine_threadsafe(coro, self._loop)
        return future.result()
```

**Why it partially solves**:
- ✅ Persistent event loop avoids repeated initialization
- ✅ Can handle concurrent sync calls
- ❌ Still needs proper engine lifecycle management in client
- ❌ Thread safety issues if engine methods aren't thread-safe

**Would need additional fix**:
```python
class BrightDataClient:
    _engine_lock = asyncio.Lock()  # Add lock

    async def list_zones(self):
        async with self._engine_lock:  # Protect concurrent access
            # Still need to avoid nested engine contexts
            return await self._zone_manager.list_zones()
```

---

### ❌ **Approach 4: Lazy Async (Coroutine Return)**

**Status**: **DOESN'T SOLVE** ❌

This approach doesn't address the engine lifecycle issue:

```python
class BrightDataClient:
    def list_zones(self):
        """Returns coroutine"""
        return self._list_zones_impl()

    async def _list_zones_impl(self):
        async with self.engine:  # ❌ Still has the problem
            # ...
```

**Why it doesn't solve**:
- Coroutine still has nested `async with self.engine:`
- Same race conditions occur when awaiting multiple coroutines

---

### ❌ **Approach 5: Callback-Based Async**

**Status**: **DOESN'T SOLVE** ❌

```python
def list_zones_callback(self, on_success, on_error):
    async def _execute():
        async with self.engine:  # ❌ Still has the problem
            result = await self._list_zones()
            on_success(result)
    asyncio.create_task(_execute())
```

**Why it doesn't solve**:
- Underlying implementation still has nested contexts
- Race conditions still occur
- Just hides the problem behind callbacks

---

### ✅ **Approach 6: Generator-Based Async (Streaming)**

**Status**: **SOLVES THE ISSUE** ✅

```python
class BrightDataClient:
    async def __aenter__(self):
        await self.engine.__aenter__()
        return self

    async def list_zones_stream(self) -> AsyncIterator[Dict]:
        """Stream zones as they're fetched"""
        # ✅ Assumes engine already initialized
        zones = await self._zone_manager.list_zones()
        for zone in zones:
            yield zone

# Usage
async with BrightDataClient() as client:
    zones = []
    accounts = []

    # Can run concurrently with other operations
    async for zone in client.list_zones_stream():
        zones.append(zone)
```

**Why it works**:
- Still relies on client-level engine management
- No nested contexts
- Can stream results progressively

---

### ⚠️ **Approach 7: Current Hybrid (Keep as-is with improvements)**

**Status**: **NEEDS FIXES** ⚠️

The current approach CAN work, but needs fixes:

#### Option A: Reference Counting Context Manager

```python
class AsyncEngine:
    def __init__(self, token):
        self._token = token
        self._session = None
        self._connector = None
        self._context_count = 0  # Track active contexts
        self._lock = asyncio.Lock()

    async def __aenter__(self):
        async with self._lock:
            self._context_count += 1
            if self._context_count == 1:
                # First context - initialize
                self._connector = aiohttp.TCPConnector(...)
                self._session = aiohttp.ClientSession(...)
        return self

    async def __aexit__(self, *args):
        async with self._lock:
            self._context_count -= 1
            if self._context_count == 0:
                # Last context - cleanup
                if self._session:
                    await self._session.close()
                if self._connector:
                    await self._connector.close()

# Now utility methods can safely use nested contexts
async def list_zones(self):
    async with self.engine:  # ✅ Safe with reference counting
        return await self._zone_manager.list_zones()
```

**Pros**:
- ✅ Minimal code changes
- ✅ Maintains current API
- ✅ Handles concurrent usage

**Cons**:
- ❌ More complex engine implementation
- ❌ Lock overhead on every context enter/exit
- ❌ Still not as clean as Approach 1/2

#### Option B: Remove Engine Contexts from Utility Methods

```python
class BrightDataClient:
    async def list_zones(self):
        # ✅ Remove nested context, assume engine is ready
        if self._zone_manager is None:
            self._zone_manager = ZoneManager(self.engine)
        return await self._zone_manager.list_zones()

    async def get_account_info(self):
        # ✅ Direct engine usage, no context
        async with self.engine.get_from_url(...) as response:
            # ...

    # For standalone usage (no client context), provide explicit method
    async def initialize(self):
        """Explicitly initialize engine for standalone usage"""
        await self.engine.__aenter__()

    async def cleanup(self):
        """Explicitly cleanup engine for standalone usage"""
        await self.engine.__aexit__(None, None, None)
```

**Usage**:
```python
# Pattern 1: With client context (recommended)
async with BrightDataClient() as client:
    results = await asyncio.gather(
        client.list_zones(),
        client.get_account_info()
    )

# Pattern 2: Standalone (manual lifecycle)
client = BrightDataClient()
await client.initialize()
try:
    zones = await client.list_zones()
finally:
    await client.cleanup()
```

**Pros**:
- ✅ Clean solution
- ✅ Fixes concurrency issues
- ✅ Maintains flexibility

**Cons**:
- ❌ Breaking change (utility methods require client context or manual init)
- ❌ Less convenient for one-off calls

---

## 📊 Comparison Matrix

| Approach | Solves Issue? | Code Changes | Performance | Complexity | Backward Compatible? |
|----------|---------------|--------------|-------------|------------|---------------------|
| **1. Pure Async** | ✅ Yes | Medium | Excellent | Low | ❌ No |
| **2. Async + Sync Adapter** | ✅ Yes | Medium | Excellent | Medium | ❌ No |
| **3. Thread-Based** | ⚠️ Partial | High | Good | High | ✅ Yes |
| **4. Lazy Async** | ❌ No | Low | Good | Low | ✅ Yes |
| **5. Callback** | ❌ No | High | Medium | High | ❌ No |
| **6. Streaming** | ✅ Yes | Medium | Excellent | Medium | ❌ No |
| **7A. Reference Counting** | ✅ Yes | Medium | Good | Medium | ✅ Yes |
| **7B. Remove Nested Contexts** | ✅ Yes | Small | Excellent | Low | ⚠️ Maybe |

---

## 🎯 Recommended Solutions

### Solution 1: **Reference Counting Engine** (Backward Compatible)

**Immediate fix** that maintains current API:

```python
# core/engine.py
class AsyncEngine:
    def __init__(self, token, ...):
        # ... existing code ...
        self._context_count = 0
        self._context_lock = asyncio.Lock()

    async def __aenter__(self):
        async with self._context_lock:
            self._context_count += 1
            if self._context_count == 1:
                # First entry - initialize
                self._connector = aiohttp.TCPConnector(
                    limit=100,
                    limit_per_host=20,
                    ttl_dns_cache=300
                )
                self._session = aiohttp.ClientSession(
                    connector=self._connector,
                    headers={"Authorization": f"Bearer {self._api_token}"}
                )
        return self

    async def __aexit__(self, *args):
        async with self._context_lock:
            self._context_count -= 1
            if self._context_count == 0:
                # Last exit - cleanup
                if self._session:
                    await self._session.close()
                    self._session = None
                if self._connector:
                    await self._connector.close()
                    self._connector = None

# No other code changes needed!
```

**Testing**:
```python
async def test_concurrent_utility_methods():
    """Test that concurrent calls work"""
    client = BrightDataClient()

    # ✅ Should work now
    results = await asyncio.gather(
        client.list_zones(),
        client.get_account_info(),
        client.test_connection()
    )

    assert len(results) == 3
    print("✅ Concurrent utility methods work!")
```

### Solution 2: **Pure Async Pattern** (Long-term, best practice)

**Clean redesign** for v2.0:

```python
# client.py
class BrightDataClient:
    async def __aenter__(self):
        """Initialize engine once"""
        await self.engine.__aenter__()
        return self

    async def __aexit__(self, *args):
        """Cleanup engine once"""
        await self.engine.__aexit__(*args)

    # Utility methods assume engine is initialized
    async def list_zones(self):
        if self._zone_manager is None:
            self._zone_manager = ZoneManager(self.engine)
        return await self._zone_manager.list_zones()

    async def get_account_info(self):
        async with self.engine.get_from_url(...) as response:
            # Direct usage, no nested context
            pass

# Usage (enforces proper pattern)
async with BrightDataClient() as client:
    # ✅ All concurrent operations work
    results = await asyncio.gather(
        client.list_zones(),
        client.get_account_info(),
        client.scrape.amazon.products_async(url),
        client.search.google_async(query)
    )
```

---

## 🧪 Test Cases to Add

```python
# probe_tests/async/advanced/test_29_utility_method_concurrency.py

import asyncio
import pytest
from brightdata import BrightDataClient

async def test_concurrent_list_zones():
    """Test multiple list_zones calls concurrently"""
    client = BrightDataClient()

    results = await asyncio.gather(
        client.list_zones(),
        client.list_zones(),
        client.list_zones()
    )

    assert len(results) == 3
    assert all(isinstance(r, list) for r in results)

async def test_concurrent_mixed_utility_methods():
    """Test different utility methods concurrently"""
    client = BrightDataClient()

    zones, info, connection = await asyncio.gather(
        client.list_zones(),
        client.get_account_info(),
        client.test_connection()
    )

    assert isinstance(zones, list)
    assert isinstance(info, dict)
    assert isinstance(connection, bool)

async def test_concurrent_with_scraping():
    """Test utility methods concurrent with scraping"""
    async with BrightDataClient() as client:
        results = await asyncio.gather(
            client.list_zones(),
            client.get_account_info(),
            client.scrape.amazon.products_async("https://amazon.com/dp/B123"),
        )

        assert len(results) == 3

async def test_rapid_utility_method_calls():
    """Stress test with rapid concurrent calls"""
    client = BrightDataClient()

    tasks = []
    for _ in range(50):
        tasks.extend([
            client.list_zones(),
            client.get_account_info(),
            client.test_connection()
        ])

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Should not have "Connector is closed" errors
    errors = [r for r in results if isinstance(r, Exception)]
    assert len(errors) == 0, f"Got errors: {errors}"
```

---

## 📝 Summary

### The Problem
- Utility methods use `async with self.engine:` which causes "Connector is closed" errors in concurrent scenarios
- Race conditions on engine initialization/cleanup
- Not truly idempotent for concurrent usage

### Best Solutions

**Short-term (v1.x - Backward Compatible)**:
- ✅ **Solution 1: Reference Counting Engine** - Minimal changes, maintains API

**Long-term (v2.0 - Clean Design)**:
- ✅ **Solution 2: Pure Async Pattern** - Remove nested contexts, enforce client context manager

### Why These Approaches Work
1. **Pure Async (Approach 1 & 2)**: Single engine lifecycle managed by client context
2. **Reference Counting**: Engine tracks how many contexts are active
3. **Streaming (Approach 6)**: Same as Pure Async, just different data delivery

### Action Items
1. ✅ **Immediate**: Implement reference counting in AsyncEngine
2. ✅ **Short-term**: Add comprehensive concurrency tests
3. ✅ **Long-term**: Plan v2.0 with Pure Async pattern
4. ✅ **Documentation**: Update examples to show concurrent usage patterns

---

**Last Updated**: 2025-01-10
**Status**: Analysis complete, implementation pending
**Priority**: High (affects concurrent usage)
