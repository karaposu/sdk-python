# Three Async Approaches for sdk-python

This document examines the fundamental async design issues in the current SDK, explains why they matter, and presents three different approaches to solve them.

---

## 🔴 The Current Design Is Broken

### Issue 1: Confused Lifecycle Ownership

**The Problem**: The current SDK doesn't have clear ownership of the HTTP session lifecycle.

```python
# Current implementation (BROKEN)
class AsyncEngine:
    async def __aenter__(self):
        await self._session.__aenter__()  # Engine owns session
        return self

class BrightDataClient:
    async def list_zones(self):
        async with self.engine:  # ❌ Client ALSO tries to manage engine
            return await self._zone_manager.list_zones()

    async def get_account_info(self):
        async with self.engine:  # ❌ Another method ALSO tries to manage engine
            return await ...
```

**What happens**: Multiple methods try to open/close the SAME session at the SAME time.

```python
# Concurrent calls FAIL
results = await asyncio.gather(
    client.list_zones(),       # Tries to enter/exit engine
    client.get_account_info(), # Tries to enter/exit engine (CONFLICT!)
)
# Error: "Connector is closed"
```

**Root cause**: Nested context managers creating race conditions on shared resources.

---

### Issue 2: Expensive Loop Creation

**The Problem**: Every sync method call creates and destroys an entire event loop.

```python
# Current implementation
def list_zones_sync(self):
    return asyncio.run(self.list_zones())  # ❌ New loop EVERY time!

# What happens internally:
def asyncio.run(coro):
    loop = asyncio.new_event_loop()      # Create loop
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()                      # Destroy loop
```

**Impact**:

```python
# User makes 100 calls:
for i in range(100):
    zones = client.list_zones_sync()

# What actually happens:
# - 100 event loops created
# - 100 event loops destroyed
# - 100 ClientSessions created
# - 100 ClientSessions destroyed
# - 100 new TCP connections
# - NO connection reuse
# - Time wasted: ~5 seconds overhead
```

---

### Issue 3: Dual Interface Confusion

**The Problem**: Every method has both async and sync versions, bloating the API.

```python
# Current API (confusing)
class BrightDataClient:
    # Async versions
    async def list_zones(self): ...
    async def get_account_info(self): ...
    async def scrape_amazon_products_async(self, url): ...

    # Sync versions (duplicate code)
    def list_zones_sync(self): ...
    def get_account_info_sync(self): ...
    def scrape_amazon_products(self, url): ...
```

**Problems**:
- ❌ API surface is 2x larger
- ❌ Maintenance burden is 2x
- ❌ Users confused about which to use
- ❌ Documentation must cover both
- ❌ Tests must cover both

---

### Issue 4: Resource Leaks

**The Problem**: Improper cleanup leads to resource warnings.

```python
# User code:
client = BrightDataClient(token)
zones = client.list_zones_sync()

# What happens:
# 1. Create event loop
# 2. Create ClientSession
# 3. Make request
# 4. Close loop BEFORE session fully closes
# 5. ⚠️ Warning: "Unclosed client session"
# 6. ⚠️ Warning: "Unclosed connector"
```

**Why**: `asyncio.run()` doesn't give aiohttp enough time to clean up before closing the loop.

---

## 💥 Real-World Impact

### Scenario: User Scraping 100 Products

```python
# User's code (looks simple)
client = BrightDataClient(token)

for url in product_urls:  # 100 URLs
    result = client.scrape.amazon.products(url)
    products.append(result)
```

**What Actually Happens**:

```
Call 1:  [create loop] → [create session] → [open TCP conn] → [request] → [close all]
Call 2:  [create loop] → [create session] → [open TCP conn] → [request] → [close all]
Call 3:  [create loop] → [create session] → [open TCP conn] → [request] → [close all]
...
Call 100: [create loop] → [create session] → [open TCP conn] → [request] → [close all]

Total time: ~8-10 minutes (!!!!)
Resource overhead: 100 loops + 100 sessions + 100 connections
Warnings: "Unclosed client session" × 100
```

**What SHOULD Happen**:

```
[create loop ONCE] → [create session ONCE] → [open connection pool]
  ├─ Request 1 (reuse connection)
  ├─ Request 2 (reuse connection)
  ├─ Request 3 (reuse connection)
  └─ ...
[close session ONCE] → [close loop ONCE]

Total time: ~2-3 minutes (3-4x faster!)
Resource overhead: 1 loop + 1 session + ~10 pooled connections
Warnings: None
```

---

## 🎯 Why Good Async Design Matters

### 1. Performance

**Bad design** (current):
- Creates overhead on every call
- No connection reuse
- No connection pooling
- Wasted CPU cycles creating/destroying resources

**Good design**:
- Resources created once, reused many times
- Connection pooling reduces latency
- Async allows true concurrency
- 10-50x faster for bulk operations

---

### 2. Resource Efficiency

**Bad design**:
```
100 API calls = 100 event loops + 100 sessions + 100 TCP connections
Memory usage: ~200MB
File descriptors: 100+
```

**Good design**:
```
100 API calls = 1 event loop + 1 session + ~10 TCP connections (pooled)
Memory usage: ~20MB
File descriptors: ~10
```

---

### 3. Correctness

**Bad design**:
- Race conditions on concurrent operations
- "Connector is closed" errors
- Unpredictable behavior
- Resource leaks and warnings

**Good design**:
- Clear ownership of resources
- Concurrent operations work reliably
- No race conditions
- Proper cleanup, no warnings

---

### 4. User Experience

**Bad design**:
```python
# ❌ Concurrent operations don't work
results = await asyncio.gather(
    client.list_zones(),
    client.get_account_info()
)
# Error: "Connector is closed"

# ❌ Slow sync operations
for url in urls:
    result = client.scrape(url)  # Each call = new loop!
```

**Good design**:
```python
# ✅ Concurrent operations work
async with BrightDataClient(token) as client:
    results = await asyncio.gather(
        client.list_zones(),
        client.get_account_info()
    )  # Works perfectly!

# ✅ Fast sync operations (if supported)
with SyncBrightDataClient(token) as client:
    for url in urls:
        result = client.scrape(url)  # Reuses same loop!
```

---

### 5. Maintainability

**Bad design**:
- Dual async/sync methods (2x code)
- Complex nested contexts
- Hard to debug race conditions
- Confusing API surface

**Good design**:
- Single source of truth
- Clear patterns
- Easy to debug
- Simple API

---

## 📊 Performance Impact Visualization

### Current Design (Broken)

```
User makes 10 API calls:

Call 1: [Loop Created] → [Session] → [TCP] → Request → [TCP Closed] → [Session Closed] → [Loop Closed]

Call 2: [Loop Created] → [Session] → [TCP] → Request → [TCP Closed] → [Session Closed] → [Loop Closed]

Call 3: [Loop Created] → [Session] → [TCP] → Request → [TCP Closed] → [Session Closed] → [Loop Closed]

...and so on for all 10 calls

Time overhead: ~500ms
Resource waste: 10 loops, 10 sessions, 10 connections (all destroyed!)
```

### Good Design (Persistent Resources)

```
User makes 10 API calls:

[Loop Created ONCE] → [Session Created ONCE] → [Connection Pool Created]
   ↓
   ├─ Call 1: Request (reuse connection from pool)
   ├─ Call 2: Request (reuse connection from pool)
   ├─ Call 3: Request (reuse connection from pool)
   ├─ Call 4: Request (reuse connection from pool)
   └─ ... (all 10 calls reuse same resources)
   ↓
[Connection Pool Closed] → [Session Closed ONCE] → [Loop Closed ONCE]

Time overhead: ~50ms (10x faster!)
Resource efficiency: 1 loop, 1 session, ~3-5 pooled connections (reused!)
```

---

## 💡 What We Need

A good async design must:

1. ✅ **Clear lifecycle ownership** - One place manages session lifecycle
2. ✅ **Resource reuse** - Create once, use many times
3. ✅ **Concurrent operations** - Support asyncio.gather() without errors
4. ✅ **Proper cleanup** - No resource leaks or warnings
5. ✅ **Simple API** - Single, clear way to use the SDK
6. ✅ **Good performance** - Connection pooling and minimal overhead

---

## 🔧 The Three Approaches

After analyzing the current design issues, we've identified **three viable approaches** to fix them. Each approach solves the problems differently and has different trade-offs.

---

## Approach 1: Pure Async (Minimalist)

### What It Is

**Async-only SDK with persistent session. No official sync support.**

Remove all sync wrappers. Provide only async methods. Client manages a persistent session via context manager. Users must use `async`/`await`.

### Code Structure

```python
# brightdata/__init__.py
from .client import BrightDataClient

__all__ = ["BrightDataClient"]

# brightdata/client.py
class BrightDataClient:
    """Pure async client - persistent session"""

    def __init__(self, token: str):
        self.token = token
        self.engine = AsyncEngine(token)  # Creates persistent session

    async def __aenter__(self):
        """Initialize session ONCE"""
        await self.engine.__aenter__()
        return self

    async def __aexit__(self, *args):
        """Close session ONCE"""
        await self.engine.__aexit__(*args)

    # All methods are async-only
    async def list_zones(self):
        # ✅ No nested context - assumes session initialized
        return await self._zone_manager.list_zones()

    async def get_account_info(self):
        # ✅ No nested context
        return await self.engine.get_from_url(...)

    async def scrape_amazon_products(self, url):
        return await self._scrape(url)
```

### Usage

```python
# Async users (ONLY way to use it)
async with BrightDataClient(token) as client:
    # Single request
    zones = await client.list_zones()

    # Concurrent requests ✅ WORK NOW
    results = await asyncio.gather(
        client.list_zones(),
        client.get_account_info(),
        client.scrape.amazon.products(url1),
        client.scrape.amazon.products(url2),
    )

# Sync users must write their own wrapper
def my_scrape(url):
    async def _async():
        async with BrightDataClient(token) as client:
            return await client.scrape.amazon.products(url)
    return asyncio.run(_async())
```

### How It Solves the Problems

| Problem | Solution |
|---------|----------|
| **Confused lifecycle** | ✅ Client owns session lifecycle (no nested contexts) |
| **Expensive loops** | ✅ No sync wrappers = no asyncio.run() |
| **Dual interface** | ✅ Single async-only interface |
| **Resource leaks** | ✅ Proper context manager cleanup |

### Pros & Cons

#### ✅ Advantages

1. **Simplest codebase** - Only one client class, no sync wrappers
2. **Smallest API surface** - Half as many methods to maintain
3. **Best async performance** - Pure async with persistent session and connection pooling
4. **Forces best practices** - Users learn modern async/await patterns
5. **Easiest to maintain** - No sync code to worry about
6. **Future-proof** - Async is the direction Python is moving
7. **No ambiguity** - One clear way to use the SDK
8. **Clean architecture** - No dual interface complexity

#### ❌ Disadvantages

1. **Breaking change** - Existing sync users must migrate or write wrappers
2. **Higher learning curve** - Users must understand async/await
3. **Jupyter notebook friction** - Need special handling or `nest_asyncio`
4. **Simple scripts harder** - More boilerplate for simple one-off tasks
5. **No official sync path** - Users figure out sync on their own

### When to Use

- ✅ Building a **new SDK** from scratch
- ✅ Users are **technical** and async-savvy
- ✅ You want the **cleanest architecture**
- ✅ You're okay with **breaking changes**
- ✅ **Performance** is critical
- ✅ You want to **force modern practices**

### Real-World Examples

Libraries that use this approach:
- `httpx.AsyncClient` (async-only client)
- `aiohttp.ClientSession` (async-only)
- `asyncpg` (async-only PostgreSQL)
- `motor` (async-only MongoDB)

---

## Approach 2: Async + Sync Adapter (Pragmatic)

### What It Is

**Async-only core with persistent session + Separate `SyncBrightDataClient` class with persistent event loop.**

The main `BrightDataClient` is pure async (same as Approach 1). A separate `SyncBrightDataClient` class wraps the async client and provides a sync interface using a persistent event loop.

### Code Structure

```python
# brightdata/__init__.py
from .client import BrightDataClient
from .sync_client import SyncBrightDataClient

__all__ = ["BrightDataClient", "SyncBrightDataClient"]

# brightdata/client.py (Pure async - SAME as Approach 1)
class BrightDataClient:
    """Pure async client"""

    def __init__(self, token: str):
        self.token = token
        self.engine = AsyncEngine(token)

    async def __aenter__(self):
        await self.engine.__aenter__()
        return self

    async def __aexit__(self, *args):
        await self.engine.__aexit__(*args)

    async def list_zones(self):
        return await self._zone_manager.list_zones()

# brightdata/sync_client.py (NEW - Sync adapter)
class SyncBrightDataClient:
    """Sync adapter with persistent event loop"""

    def __init__(self, token: str):
        self._async_client = BrightDataClient(token)
        self._loop = None

    def __enter__(self):
        """Create persistent loop ONCE"""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # Initialize async client in the loop
        self._loop.run_until_complete(
            self._async_client.__aenter__()
        )
        return self

    def __exit__(self, *args):
        """Cleanup loop"""
        self._loop.run_until_complete(
            self._async_client.__aexit__(*args)
        )
        self._loop.close()
        self._loop = None

    def list_zones(self):
        """Sync wrapper using persistent loop"""
        return self._loop.run_until_complete(
            self._async_client.list_zones()
        )

    def scrape_amazon_products(self, url):
        """Sync wrapper using persistent loop"""
        return self._loop.run_until_complete(
            self._async_client.scrape.amazon.products(url)
        )
```

### Usage

```python
# Async users (recommended)
async with BrightDataClient(token) as client:
    result = await client.scrape.amazon.products(url)

    # Concurrent operations ✅ WORK NOW
    results = await asyncio.gather(
        client.list_zones(),
        client.get_account_info(),
    )

# Sync users (official support)
with SyncBrightDataClient(token) as client:
    result = client.scrape.amazon.products(url)

    # Sequential operations (fast now!)
    for url in urls:
        result = client.scrape.amazon.products(url)  # ✅ Reuses loop!
```

### How It Solves the Problems

| Problem | Solution |
|---------|----------|
| **Confused lifecycle** | ✅ Client owns session lifecycle (no nested contexts) |
| **Expensive loops** | ✅ Persistent loop in sync adapter (no new loop per call) |
| **Dual interface** | ✅ Separate classes, clear distinction |
| **Resource leaks** | ✅ Proper context manager cleanup in both clients |

### Pros & Cons

#### ✅ Advantages

1. **Both audiences served** - Async users get pure async, sync users get official adapter
2. **Official sync support** - Clear, documented path for sync users
3. **Better sync performance** - Persistent loop (no new loop per call)
4. **Easier migration** - Minimal code changes for existing users (import change)
5. **Clear separation** - Two distinct classes, no confusion
6. **Can remove later** - SyncAdapter is separate, easy to deprecate in future
7. **Lower barrier to entry** - Sync users can adopt without learning async
8. **Connection pooling works in both** - Persistent session in both clients

#### ❌ Disadvantages

1. **Two client classes** - More code to maintain
2. **Larger codebase** - Need to implement sync adapter
3. **Documentation burden** - Must document both patterns
4. **May delay async adoption** - Sync is "too easy" so users don't migrate
5. **More API surface** - Two ways to do things

### When to Use

- ✅ You have **existing users** who need sync
- ✅ You want to **minimize breaking changes**
- ✅ You need to support **both use cases** officially
- ✅ You want **easier adoption** for new users
- ✅ You can handle **slightly more code**
- ✅ You value **pragmatism over purity**
- ✅ You want a **migration path** to pure async later

### Real-World Examples

Libraries that use this approach:
- `httpx` (provides both `AsyncClient` and `Client`)
- `playwright` (provides both async and sync APIs)
- `redis-py` (provides both async and sync clients)

---

## Approach 3: Stateless Sessions (Simple)

### What It Is

**No persistent session - create fresh `aiohttp.ClientSession` for each API call.**

Instead of managing a persistent session, create a brand new `ClientSession` for every API method call. No context manager on the engine.

### Code Structure

```python
# brightdata/__init__.py
from .engine import BrightdataEngine
from .auto import scrape_url, scrape_url_async

__all__ = ["BrightdataEngine", "scrape_url", "scrape_url_async"]

# brightdata/engine.py
class BrightdataEngine:
    """Process-wide engine - NO shared session"""

    def __init__(self, bearer_token: str, timeout: int = 40):
        self._token = bearer_token
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        # ❌ NO self._session!

    async def trigger(self, payload, dataset_id: str) -> Optional[str]:
        """Create NEW session for THIS call only"""
        url = "https://api.brightdata.com/datasets/v3/trigger"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        # ✅ Fresh session per call
        async with aiohttp.ClientSession(
            timeout=self._timeout,
            headers=headers,
        ) as sess:
            async with sess.post(url, json=payload) as resp:
                data = await resp.json()
                return data.get("snapshot_id")
        # Session closed immediately

    async def get_status(self, snapshot_id: str) -> str:
        """Another fresh session"""
        url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
        headers = {"Authorization": f"Bearer {self._token}"}

        # ✅ Another fresh session
        async with aiohttp.ClientSession(
            timeout=self._timeout,
            headers=headers,
        ) as sess:
            async with sess.get(url) as resp:
                data = await resp.json()
                return data.get("status", "unknown")

# Sync wrapper (still uses asyncio.run)
def _run_blocking(coro):
    """Smart wrapper that handles existing event loop"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Inside existing loop - run in thread
        import concurrent.futures as cf
        with cf.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()

    # No running loop - use asyncio.run()
    return asyncio.run(coro)
```

### Usage

```python
# Async users
engine = BrightdataEngine(token)
snapshot_id = await engine.trigger(payload, dataset_id="amazon_products")
status = await engine.get_status(snapshot_id)
result = await engine.fetch_result(snapshot_id)

# Sync users (uses asyncio.run wrapper)
def scrape_url(url):
    return _run_blocking(scrape_url_async(url))

result = scrape_url("https://amazon.com/dp/B123")
```

### How It Solves the Problems

| Problem | Solution |
|---------|----------|
| **Confused lifecycle** | ✅ No lifecycle management (fresh session per call) |
| **Expensive loops** | ⚠️ Partially (still creates loops in sync mode) |
| **Dual interface** | ⚠️ Still has dual interface with sync wrappers |
| **Resource leaks** | ✅ Each session properly closed |

### Pros & Cons

#### ✅ Advantages

1. **Simplest implementation** - No lifecycle management at all
2. **No "Connector is closed" errors** - No shared session to manage
3. **No nested context issues** - No contexts needed
4. **Easy to understand** - Each call is completely independent
5. **Good for simple scripts** - Fire-and-forget style
6. **No race conditions** - Each call has its own isolated session

#### ❌ Disadvantages

1. **No connection pooling** - New TCP connection for every call
2. **Performance overhead** - Session creation cost (~10-50ms per call)
3. **Higher resource usage** - 100 calls = 100 sessions + 100 connections
4. **Still has asyncio.run() issue** - Sync wrappers create new loop each time
5. **Not following aiohttp best practices** - Documentation recommends persistent sessions
6. **Scalability ceiling** - Performance degrades with high request volume

### When to Use

- ✅ Building **simple scripts** or CLI tools
- ✅ Making **infrequent API calls** (1-10 per process)
- ✅ You want **absolute simplicity** over performance
- ✅ **Low-volume** use cases (not 100s of requests)
- ✅ You're building **prototypes** or internal tools
- ✅ You want to **avoid all lifecycle complexity**

### Real-World Examples

This approach is used by:
- Simple automation scripts
- One-off data collection tools
- Internal utilities
- Prototype projects

---

## 📊 Performance Comparison

### Scenario: 100 Sequential API Calls

| Approach | Sessions Created | TCP Connections | Event Loops | Time Estimate |
|----------|-----------------|-----------------|-------------|---------------|
| **Current (broken)** | 100 | 100 | 100 | ~8-10 min 🐌 |
| **Approach 1 (async)** | 1 | ~10 (pooled) | 1 | ~20s ⚡ |
| **Approach 2 (async)** | 1 | ~10 (pooled) | 1 | ~20s ⚡ |
| **Approach 2 (sync)** | 1 | ~10 (pooled) | 1 | ~35s |
| **Approach 3 (async)** | 100 | 100 (new each) | 1 | ~45s 🐢 |
| **Approach 3 (sync)** | 100 | 100 | 100 | ~70s 🐌 |

### Scenario: 100 Concurrent API Calls

| Approach | Sessions Created | TCP Connections | Event Loops | Time Estimate |
|----------|-----------------|-----------------|-------------|---------------|
| **Current (broken)** | N/A | N/A | N/A | ❌ Doesn't work |
| **Approach 1 (async)** | 1 | ~10 (pooled) | 1 | ~5s ⚡⚡⚡ |
| **Approach 2 (async)** | 1 | ~10 (pooled) | 1 | ~5s ⚡⚡⚡ |
| **Approach 2 (sync)** | N/A | N/A | N/A | Can't do concurrency |
| **Approach 3 (async)** | 100 | 100 | 1 | ~8s 🐢 |
| **Approach 3 (sync)** | N/A | N/A | N/A | Can't do concurrency |

---

## 🔧 Complexity Comparison

### Lines of Code Estimate

| Component | Approach 1 | Approach 2 | Approach 3 |
|-----------|-----------|-----------|-----------|
| Core Client | 500 | 500 | 300 |
| Sync Support | 0 | 200 | 100 |
| Tests | 300 | 400 | 250 |
| **Total** | **~800** | **~1100** | **~650** |

### Maintenance Burden

| Aspect | Approach 1 | Approach 2 | Approach 3 |
|--------|-----------|-----------|-----------|
| **Code Complexity** | Low | Medium | Low |
| **Maintenance Effort** | Low | Medium | Low |
| **Documentation** | Medium | High | Low |
| **Testing Surface** | Medium | Large | Small |

---

## 💡 Recommendation for sdk-python

### Primary Recommendation: **Approach 2** (Async + Sync Adapter)

**Why?**

1. ✅ **Solves ALL the problems**:
   - Confused lifecycle → Client owns session
   - Expensive loops → Persistent loop in sync adapter
   - Dual interface → Separate classes, clear distinction
   - Resource leaks → Proper cleanup in both clients

2. ✅ **Serves both audiences**:
   - Async users: Pure async client with excellent performance
   - Sync users: Official sync adapter with good performance

3. ✅ **Minimal breaking changes**:
   - Async users: Same pattern as before
   - Sync users: Simple import change

4. ✅ **Best long-term strategy**:
   - Can deprecate SyncAdapter in future (v3.0)
   - Async client is pure from day 1
   - Clear migration path to Approach 1 if desired

5. ✅ **Industry standard**:
   - Same pattern as `httpx`, `playwright`
   - Users understand this pattern

6. ✅ **Pragmatic choice**:
   - If you care about **all users** (async and sync), Approach 2 is the pragmatic choice
   - Users will write slow sync code anyway with Approach 1 (using `asyncio.run()`)
   - We might as well provide **fast** sync code (persistent loop) instead of leaving users to write **slow** sync code
   - Takes responsibility for good user experience in both modes

**Bottom line**: If users will write slow sync wrappers anyway (Approach 1), we might as well provide fast, official sync support (Approach 2). That's the pragmatic choice! 🎯

### Alternative Recommendation: **Approach 1** (Pure Async)

**Consider if:**
- Building v2.0 with major breaking changes
- User base is primarily async-savvy
- You want the absolute cleanest codebase
- Performance is the top priority

### Consider: **Approach 3** (Stateless Sessions)

**When it makes sense:**

This approach is **ideal** for certain use cases:

✅ **Simple scripts and automation**
- One-off data collection tasks
- CLI tools that run quickly and exit
- Cronjobs that make a few API calls

✅ **Low-volume applications**
- Making 1-10 API calls per process
- Infrequent operations (e.g., hourly checks)
- Internal utilities with minimal traffic

✅ **Prototyping and experimentation**
- Quick proof-of-concept code
- Learning and testing
- Temporary solutions

✅ **When you want absolute simplicity**
- No lifecycle management to think about
- Fire-and-forget style
- Minimal code complexity

**Example use case**: A cronjob that runs every hour, makes 2-3 API calls, and exits. The overhead of creating sessions doesn't matter because it only happens once per hour.

**Why NOT for sdk-python specifically:**
- ❌ SDK is designed for high-volume scraping (100s-1000s of requests)
- ❌ Users expect good performance for bulk operations
- ❌ Connection pooling is valuable for production use cases
- ❌ Doesn't align with the SDK's primary use case

**Bottom line**: Great for simple scripts, but sdk-python's users typically need high-volume scraping where performance matters.

---

## 📋 Summary Table: All Three Approaches

| Criteria | Current (Broken) | Approach 1: Pure Async | Approach 2: Async + Sync Adapter | Approach 3: Stateless Sessions |
|----------|-----------------|----------------------|----------------------------------|-------------------------------|
| **Session Strategy** | Nested contexts (broken) | Persistent (context manager) | Persistent (context manager) | Fresh session per call |
| **Sync Support** | ⚠️ Broken (asyncio.run per call) | ❌ No official support | ✅ SyncBrightDataClient | ⚠️ asyncio.run wrappers |
| **Connection Pooling** | ⚠️ Yes (but broken) | ✅ Yes | ✅ Yes | ❌ No |
| **Async Performance** | 🐌 Poor (race conditions) | ⚡⚡⚡ Excellent | ⚡⚡⚡ Excellent | ⚡ Moderate |
| **Sync Performance** | 🐌 Very Poor | ⚠️ Users handle it | ⚡⚡ Good | 🐌 Poor |
| **Concurrent Requests** | ❌ Broken | ⚡⚡⚡ Excellent | ⚡⚡⚡ Excellent (async only) | ⚡ Works but slower |
| **Code Complexity** | ⚠️ High (confusing) | ✅ Low | ⚠️ Medium | ✅ Low |
| **Maintenance Burden** | ⚠️ High | ✅ Low | ⚠️ Medium | ✅ Low |
| **Breaking Change** | N/A | ❌ Yes | ⚠️ Minimal | ❌ Yes |
| **Learning Curve** | ⚠️ Confusing | ⚠️ Higher | ✅ Lower | ✅ Lower |
| **Lines of Code** | ~1200 | ~800 | ~1100 | ~650 |
| **Confused lifecycle** | ❌ Has problem | ✅ Solved | ✅ Solved | ✅ Solved |
| **Expensive loops** | ❌ Has problem | ✅ Solved | ✅ Solved | ⚠️ Partially solved |
| **Dual interface** | ❌ Has problem | ✅ Solved | ✅ Solved | ⚠️ Still has it |
| **Resource leaks** | ❌ Has problem | ✅ Solved | ✅ Solved | ✅ Solved |
| **Migration Effort** | N/A | ⚠️ High | ✅ Low | ⚠️ High |
| **Future-Proof** | ❌ No | ✅ Yes | ✅ Yes (can remove sync later) | ⚠️ Performance ceiling |
| **Best For** | ❌ Nothing | New projects, async teams | Production apps, mixed teams | Simple scripts, prototypes |
| **Real-World Examples** | - | httpx.AsyncClient, asyncpg | httpx, playwright | Simple automation |
| **Recommendation** | ❌ Must fix | ⭐ Alternative | ⭐⭐⭐ Primary | ❌ Not recommended |

---

## 🚀 Implementation Roadmap

If choosing **Approach 2** (recommended):

### Phase 1: v2.0 (Immediate)
```
✅ Implement pure async BrightDataClient
✅ Remove nested async with self.engine: from methods
✅ Implement SyncBrightDataClient adapter
✅ Update documentation for both clients
✅ Write migration guide
✅ Add tests for concurrent operations
```

### Phase 2: v2.5 (6-12 months)
```
⚠️ Add deprecation warnings to SyncBrightDataClient
📚 Promote async client in documentation
📊 Track usage metrics (async vs sync)
```

### Phase 3: v3.0 (2+ years) - Optional
```
Option A: Remove SyncBrightDataClient (pure async)
Option B: Move to separate package (brightdata-sync)
```

---

**Conclusion**: The current design has fundamental issues with lifecycle management, resource usage, and concurrent operations. **Approach 2 (Async + Sync Adapter)** fixes all these problems while serving both async and sync users, making it the best choice for sdk-python.

---

**Last Updated**: 2025-01-10
**Status**: Recommendation for implementation
