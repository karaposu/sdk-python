# Complete Comparison: All Async Approaches

After analyzing both the `sdk-python` codebase and the `brightdata` package, we've identified **THREE main viable approaches** for handling async in the SDK.

---

## 🎯 The Three Approaches

### Approach 1: Pure Async (Minimalist)
**Async-only SDK with persistent session, no sync support**

### Approach 2: Async + Sync Adapter (Pragmatic)
**Async core with persistent session + Separate SyncBrightDataClient class**

### Approach 3: Stateless Sessions (Simple)
**No persistent session - create fresh session per API call**

---

## 📊 Side-by-Side Comparison

| Aspect | Approach 1: Pure Async | Approach 2: Async + Sync Adapter | Approach 3: Stateless Sessions |
|--------|----------------------|----------------------------------|-------------------------------|
| **Session Management** | Persistent (context manager) | Persistent (context manager) | Fresh session per call |
| **Lifecycle Ownership** | Client (`async with client:`) | Client (`async with client:`) | No lifecycle (stateless) |
| **Sync Support** | ❌ No official support | ✅ SyncBrightDataClient | ⚠️ asyncio.run() wrappers |
| **"Connector is closed"** | ✅ Fixed (no nested contexts) | ✅ Fixed (no nested contexts) | ✅ No issue (no shared session) |
| **asyncio.run() issue** | ✅ Avoided (no sync wrappers) | ✅ Fixed (persistent loop in adapter) | ❌ Still has it |
| **Connection Pooling** | ✅ Yes | ✅ Yes | ❌ No |
| **Performance (async)** | ✅ Excellent | ✅ Excellent | ⚠️ Moderate (overhead) |
| **Performance (sync)** | ⚠️ Users on their own | ✅ Good (persistent loop) | ❌ Poor (new session each call) |
| **Complexity** | ✅ Simplest codebase | ⚠️ More code (2 clients) | ✅ Simple (no lifecycle) |
| **Breaking Change** | ❌ Yes | ⚠️ Minimal (import change) | ❌ Yes |
| **Best For** | New projects, async-first teams | Production apps, mixed teams | Simple scripts, low-volume |

---

## 🔍 Detailed Breakdown

### Approach 1: Pure Async

```python
# brightdata/__init__.py
from .client import BrightDataClient

__all__ = ["BrightDataClient"]

# client.py
class BrightDataClient:
    async def __aenter__(self):
        await self.engine.__aenter__()  # Init session ONCE
        return self

    async def __aexit__(self, *args):
        await self.engine.__aexit__(*args)  # Close session ONCE

    async def list_zones(self):
        # ✅ No nested context - assumes engine initialized
        return await self._zone_manager.list_zones()

    async def scrape_amazon_products(self, url):
        return await self._scrape(url)

# Usage - async only
async with BrightDataClient() as client:
    # ✅ Concurrent operations work
    results = await asyncio.gather(
        client.list_zones(),
        client.get_account_info(),
        client.scrape.amazon.products(url)
    )
```

**Characteristics**:
- 🎯 One client class, async-only
- 🎯 Client manages engine lifecycle at top level
- 🎯 No nested `async with self.engine:`
- 🎯 No sync wrappers

**Who uses this**: Modern async libraries like `httpx.AsyncClient`, `aiohttp.ClientSession`

---

### Approach 2: Async + Sync Adapter

```python
# brightdata/__init__.py
from .client import BrightDataClient
from .sync_client import SyncBrightDataClient

__all__ = ["BrightDataClient", "SyncBrightDataClient"]

# client.py (Pure async - same as Approach 1)
class BrightDataClient:
    async def __aenter__(self):
        await self.engine.__aenter__()
        return self

    async def list_zones(self):
        return await self._zone_manager.list_zones()

# sync_client.py (NEW - Separate adapter)
class SyncBrightDataClient:
    """Sync adapter with persistent event loop"""

    def __init__(self, token=None, **kwargs):
        self._async_client = BrightDataClient(token, **kwargs)
        self._loop = None

    def __enter__(self):
        # Create persistent loop ONCE
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # Initialize async client in the loop
        self._loop.run_until_complete(
            self._async_client.__aenter__()
        )
        return self

    def __exit__(self, *args):
        # Cleanup
        self._loop.run_until_complete(
            self._async_client.__aexit__(*args)
        )
        self._loop.close()

    def list_zones(self):
        # ✅ Reuse SAME loop for all calls
        return self._loop.run_until_complete(
            self._async_client.list_zones()
        )

# Usage - async
async with BrightDataClient() as client:
    result = await client.scrape.amazon.products(url)

# Usage - sync
with SyncBrightDataClient() as client:
    result = client.scrape.amazon.products(url)
```

**Characteristics**:
- 🎯 Two client classes (async + sync)
- 🎯 Async client is pure (same as Approach 1)
- 🎯 Sync adapter wraps async client
- 🎯 Persistent loop in sync adapter

**Who uses this**: `httpx` (AsyncClient + Client), `playwright` (async + sync)

---

### Approach 3: Stateless Sessions

```python
# brightdata/__init__.py
from .engine import BrightdataEngine
from .auto import scrape_url, scrape_url_async

__all__ = ["BrightdataEngine", "scrape_url", "scrape_url_async"]

# engine.py
class BrightdataEngine:
    """Process-wide engine—**no** shared session, all sessions are per-call."""

    def __init__(self, bearer_token=None, *, timeout=40):
        self._token = bearer_token or os.getenv("BRIGHTDATA_TOKEN")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        # ❌ NO self._session!

    async def trigger(self, payload, *, dataset_id: str) -> Optional[str]:
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
            async with sess.post(url, params=params, json=payload) as resp:
                data = await resp.json()
                return data.get("snapshot_id")
        # Session closed immediately

    async def get_status(self, snapshot_id: str) -> str:
        """Another fresh session"""
        url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
        headers = {"Authorization": f"Bearer {self._token}"}

        async with aiohttp.ClientSession(
            timeout=self._timeout,
            headers=headers,
        ) as sess:
            async with sess.get(url) as resp:
                data = await resp.json()
                return data.get("status", "unknown")

# Usage - async
engine = BrightdataEngine(token)
snapshot_id = await engine.trigger(payload)
status = await engine.get_status(snapshot_id)

# Usage - sync (still uses asyncio.run)
def scrape_url(url):
    return asyncio.run(scrape_url_async(url))
```

**Characteristics**:
- 🎯 No persistent session
- 🎯 No context manager on engine
- 🎯 Fresh `ClientSession` per API call
- 🎯 Completely stateless

**Who uses this**: Simple scripts, lightweight tools, the `brightdata` package

---

## 💡 Issue Resolution Matrix

| Issue | Approach 1 | Approach 2 | Approach 3 |
|-------|-----------|-----------|-----------|
| **"Connector is closed"** | ✅ Fixed (no nested contexts) | ✅ Fixed (no nested contexts) | ✅ No issue (no shared state) |
| **asyncio.run() creates loops** | ✅ Avoided (no sync wrappers) | ✅ Fixed (persistent loop) | ❌ Still has it |
| **No connection pooling** | ✅ Has pooling | ✅ Has pooling | ❌ No pooling |
| **Breaking change for sync users** | ❌ Yes | ⚠️ Minimal | ❌ Yes |

---

## 🎓 When to Use Each Approach

### Use Approach 1 (Pure Async) When:

✅ Building a **new SDK** from scratch
✅ Your users are **technical** and comfortable with async
✅ You want the **cleanest possible codebase**
✅ You're okay with **breaking changes**
✅ You want to **force best practices**
✅ **Performance** is critical

**Examples**: Modern libraries like `httpx.AsyncClient`, `aiohttp`, `asyncpg`

---

### Use Approach 2 (Async + Sync Adapter) When:

✅ You have **existing users** who need sync
✅ You want to **minimize breaking changes**
✅ You need to support **both use cases** officially
✅ You want **easier adoption** for new users
✅ You can handle **slightly more code**
✅ You value **pragmatism over purity**
✅ You want a clear **migration path** to pure async later

**Examples**: `httpx` (AsyncClient + Client), `playwright` (async + sync)

**Recommended for sdk-python** ⭐

---

### Use Approach 3 (Stateless Sessions) When:

✅ Making **infrequent API calls** (1-5 per process)
✅ Building **simple scripts/tools** where simplicity > performance
✅ You want to **avoid lifecycle complexity** entirely
✅ Your use case is **low-volume** (not 100s of requests)
✅ You're building a **CLI tool** or one-off script

**Examples**: Simple automation scripts, internal tools, prototypes

**NOT recommended for sdk-python** (performance matters)

---

## 📈 Performance Comparison

### Scenario: 100 sequential API calls

| Approach | Event Loops | ClientSessions | TCP Connections | Estimated Time |
|----------|------------|----------------|----------------|----------------|
| **Approach 1 (async)** | 1 | 1 | ~10 (pooled) | ~20s ⚡ |
| **Approach 2 (async)** | 1 | 1 | ~10 (pooled) | ~20s ⚡ |
| **Approach 2 (sync)** | 1 | 1 | ~10 (pooled) | ~35s |
| **Approach 3 (async)** | 1 | 100 | 100 (new each time) | ~45s 🐢 |
| **Approach 3 (sync)** | 100 | 100 | 100 | ~70s 🐌 |

### Scenario: 100 concurrent API calls

| Approach | Event Loops | ClientSessions | TCP Connections | Estimated Time |
|----------|------------|----------------|----------------|----------------|
| **Approach 1 (async)** | 1 | 1 | ~10 (pooled) | ~5s ⚡⚡⚡ |
| **Approach 2 (async)** | 1 | 1 | ~10 (pooled) | ~5s ⚡⚡⚡ |
| **Approach 2 (sync)** | N/A | N/A | N/A | Can't do concurrency |
| **Approach 3 (async)** | 1 | 100 | 100 | ~8s 🐢 |
| **Approach 3 (sync)** | N/A | N/A | N/A | Can't do concurrency |

---

## 🔧 Implementation Complexity

### Lines of Code Estimate

| Approach | Core Client | Sync Support | Tests | Total |
|----------|------------|--------------|-------|-------|
| **Approach 1** | 500 | 0 | 300 | ~800 |
| **Approach 2** | 500 | 200 | 400 | ~1100 |
| **Approach 3** | 300 | 100 | 250 | ~650 |

### Maintenance Burden

| Approach | Complexity | Maintenance | Future-Proof |
|----------|-----------|-------------|--------------|
| **Approach 1** | ✅ Low | ✅ Easy | ✅ Yes |
| **Approach 2** | ⚠️ Medium | ⚠️ Moderate | ✅ Yes (can remove sync later) |
| **Approach 3** | ✅ Low | ✅ Easy | ⚠️ Limited (performance ceiling) |

---

## 🎯 Recommendation for sdk-python

### Primary Recommendation: **Approach 2** (Async + Sync Adapter)

**Why?**

1. ✅ **Fixes both issues**:
   - "Connector is closed" → Remove nested contexts
   - "asyncio.run creates loops" → Persistent loop in sync adapter

2. ✅ **Serves both audiences**:
   - Async users: Pure async client with excellent performance
   - Sync users: Official sync adapter with good performance

3. ✅ **Minimal breaking changes**:
   - Async users: `async with BrightDataClient()` (same as before)
   - Sync users: Change import to `SyncBrightDataClient`

4. ✅ **Future-proof**:
   - Can remove `SyncBrightDataClient` in v3.0 if desired
   - Async client is already pure from day 1
   - Clear migration path

5. ✅ **Industry standard**:
   - Same pattern as `httpx`, `playwright`
   - Users understand this pattern

### Alternative: **Approach 1** (Pure Async)

**Consider if:**
- You're building v2.0 with major breaking changes anyway
- Your user base is primarily async-savvy
- You want the absolute simplest codebase
- You're willing to provide migration support for sync users

### Not Recommended: **Approach 3** (Stateless Sessions)

**Why not?**
- ❌ Performance regression vs current implementation
- ❌ No connection pooling benefits
- ❌ Doesn't align with high-volume scraping use case
- ❌ Still doesn't solve asyncio.run() issue properly

---

## 📋 Summary Table

| Criteria | Winner |
|----------|--------|
| **Simplest codebase** | Approach 1 (Pure Async) |
| **Best async performance** | Tie: Approach 1 & 2 |
| **Best sync support** | Approach 2 (Sync Adapter) |
| **Easiest migration** | Approach 2 (Sync Adapter) |
| **Most future-proof** | Tie: Approach 1 & 2 |
| **Lowest maintenance** | Approach 1 (Pure Async) |
| **Best for production** | Approach 2 (Sync Adapter) ⭐ |

---

## 🚀 Migration Path

### Recommended: Phased Approach

```
v2.0 (Now): Implement Approach 2
├─ BrightDataClient (pure async)
├─ SyncBrightDataClient (adapter)
└─ Fix nested context issues

v2.5 (6-12 months): Deprecation warnings
├─ BrightDataClient (pure async)
└─ SyncBrightDataClient (⚠️ deprecated)

v3.0 (2+ years): Optional pure async
├─ Option A: Remove SyncBrightDataClient (Approach 1)
└─ Option B: Move to separate package (brightdata-sync)
```

---

**Conclusion**: For `sdk-python`, **Approach 2 (Async + Sync Adapter)** is the best choice because it fixes both issues, serves both audiences, and provides a clear path to pure async in the future if desired.

---

**Last Updated**: 2025-01-10
**Analysis Based On**:
- `/Users/ns/Desktop/projects/sdk-python` (current implementation)
- `/Users/ns/Desktop/projects/brightdata/brightdata` (stateless sessions approach)
