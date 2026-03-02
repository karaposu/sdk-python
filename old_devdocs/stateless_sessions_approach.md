# The Stateless Sessions Approach (brightdata package)

**Question**: How did the `brightdata` package at `/Users/ns/Desktop/projects/brightdata/brightdata` solve async?

**Answer**: They use a **"Stateless Sessions"** pattern - creating a fresh `aiohttp.ClientSession` for every API call instead of maintaining a persistent session.

---

## 🔍 What They Did

### Core Pattern: No Persistent Session

**brightdata/webscraper_api/engine.py**:
```python
class BrightdataEngine:
    """Process-wide engine—**no** shared session, all sessions are per-call."""

    def __init__(self, bearer_token: Optional[str] = None, *, timeout: int = 40):
        self._token = bearer_token or os.getenv("BRIGHTDATA_TOKEN")
        self._timeout = aiohttp.ClientTimeout(total=timeout)
        # ❌ NO self._session here!

    async def trigger(self, payload: List[dict], *, dataset_id: str, ...) -> Optional[str]:
        """POST to /trigger (always async mode) → returns snapshot_id or None."""
        url = "https://api.brightdata.com/datasets/v3/trigger"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        # ✅ Create NEW session for THIS call only
        async with aiohttp.ClientSession(
            timeout=self._timeout,
            headers=headers,
            trust_env=True,
        ) as sess:
            async with sess.post(url, params=params, json=payload) as resp:
                resp.raise_for_status()
                data = await resp.json()

        # Session is now closed
        return data.get("snapshot_id")

    async def get_status(self, snapshot_id: str) -> str:
        """One GET to /progress/{snapshot_id} → returns status string."""
        url = f"https://api.brightdata.com/datasets/v3/progress/{snapshot_id}"
        headers = {"Authorization": f"Bearer {self._token}"}

        # ✅ Another NEW session for this call
        async with aiohttp.ClientSession(
            timeout=self._timeout,
            headers=headers,
            trust_env=True,
        ) as sess:
            async with sess.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                return data.get("status", "unknown").lower()

    async def fetch_result(self, snapshot_id: str) -> ScrapeResult:
        """GET /snapshot/{snapshot_id} and return a ScrapeResult."""
        url = f"https://api.brightdata.com/datasets/v3/snapshot/{snapshot_id}?format=json"
        headers = {"Authorization": f"Bearer {self._token}"}

        # ✅ Yet another NEW session
        async with aiohttp.ClientSession(
            timeout=self._timeout,
            headers=headers,
            trust_env=True,
        ) as sess:
            async with sess.get(url) as resp:
                resp.raise_for_status()
                data = await resp.json()
                # ... process data ...
                return scrape_result
```

### Key Characteristics

1. **No Persistent Session**: Each method creates its own `ClientSession`
2. **No Engine Context Manager**: No `async with engine:` pattern
3. **Stateless**: Engine is just a collection of async methods
4. **No Shared Resources**: No shared TCPConnector or connection pool

---

## 🎯 How This Solves "Connector is closed"

### The Problem (In sdk-python)

```python
# sdk-python/core/engine.py (BROKEN)
class AsyncEngine:
    async def __aenter__(self):
        await self._session.__aenter__()  # Open session ONCE
        return self

    async def __aexit__(self, *args):
        await self._session.__aexit__(*args)  # Close session ONCE

# sdk-python/client.py (BROKEN)
async def list_zones(self):
    async with self.engine:  # ❌ Nested context - tries to enter AGAIN
        return await self._zone_manager.list_zones()

# Result: Race condition when called concurrently
results = await asyncio.gather(
    client.list_zones(),       # Enters/exits engine
    client.get_account_info(), # Enters/exits engine (CONFLICT!)
)
# Error: "Connector is closed"
```

### The Solution (In brightdata package)

```python
# No persistent session = No lifecycle management = No race conditions!

engine = BrightdataEngine(token)

# Each call is completely independent
results = await asyncio.gather(
    engine.get_status(snap1),  # Creates session → use → close
    engine.get_status(snap2),  # Creates session → use → close
    engine.get_status(snap3),  # Creates session → use → close
)
# ✅ Works perfectly! Each call has its own session
```

**Why it works**:
- No shared session to manage
- No nested context managers
- Each call is completely isolated
- No race conditions possible

---

## 🔧 The `_run_blocking()` Helper

**brightdata/webscraper_api/base_specialized_scraper.py**:

```python
def _run_blocking(coro):
    """
    Run a coroutine from sync context.
    Handles the case where we're already inside an event loop.
    """
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # Inside existing loop - run in thread pool
        import concurrent.futures as cf
        with cf.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(lambda: asyncio.run(coro)).result()

    # No running loop - use asyncio.run()
    return asyncio.run(coro)
```

This is clever! It:
1. Checks if there's already a running event loop
2. If YES: Runs the coroutine in a separate thread to avoid `asyncio.run()` conflict
3. If NO: Uses `asyncio.run()` normally

**But**: Still creates a new loop for each sync call (same performance issue as sdk-python).

---

## 📊 Comparison: Stateless vs Persistent Session

### Persistent Session (sdk-python approach)

```python
class AsyncEngine:
    def __init__(self, token):
        self._session = aiohttp.ClientSession(...)  # Create ONCE

    async def __aenter__(self):
        await self._session.__aenter__()  # Open ONCE
        return self

    async def get_from_url(self, url):
        # ✅ Reuse the SAME session for all calls
        return await self._session.get(url)
```

**Pros**:
- ✅ Connection pooling - reuses TCP connections
- ✅ Better performance for multiple requests
- ✅ Lower resource usage

**Cons**:
- ❌ Complex lifecycle management
- ❌ Race conditions with nested contexts
- ❌ "Connector is closed" errors

### Stateless Sessions (brightdata approach)

```python
class BrightdataEngine:
    def __init__(self, token):
        self._token = token  # Just store config
        # ❌ NO session created here!

    async def get_status(self, snapshot_id):
        # ✅ Create NEW session for THIS call
        async with aiohttp.ClientSession(...) as sess:
            return await sess.get(url)
```

**Pros**:
- ✅ Simple - no lifecycle management
- ✅ No race conditions
- ✅ No "Connector is closed" errors

**Cons**:
- ❌ No connection pooling - new TCP connection each time
- ❌ Performance overhead (session creation cost)
- ❌ Higher resource usage

---

## 📈 Performance Implications

### Scenario: Make 100 API calls

#### Persistent Session (sdk-python)
```python
async with AsyncEngine(token) as engine:
    # ✅ 1 ClientSession
    # ✅ 1 TCPConnector
    # ✅ Connection pool with reused connections
    for i in range(100):
        await engine.get_from_url(url)
    # Time: ~20 seconds (with connection reuse)
```

#### Stateless Sessions (brightdata)
```python
engine = BrightdataEngine(token)
# ❌ 100 ClientSessions (created/destroyed)
# ❌ 100 TCPConnectors (created/destroyed)
# ❌ 100 new TCP connections (no reuse)
for i in range(100):
    await engine.get_status(snapshot_id)
# Time: ~35 seconds (session creation overhead)
```

**Takeaway**: Stateless sessions trade **simplicity** for **performance**.

---

## 🎓 When to Use Stateless Sessions

### Good Use Cases

1. **Infrequent API calls** - If you only make 1-2 calls, the overhead is negligible
2. **Simple tools/scripts** - Where simplicity > performance
3. **Avoiding complexity** - When you don't want to manage lifecycle
4. **Short-lived processes** - CLI tools that run quickly

### Bad Use Cases

1. **High-volume scraping** - Making 100s or 1000s of requests
2. **Long-running services** - Applications that run continuously
3. **Performance-critical apps** - Where latency matters
4. **Connection-limited APIs** - Where connection limits are strict

---

## 🔍 What About the asyncio.run() Issue?

### Does Stateless Sessions Solve This?

**NO!** The brightdata package still has this issue:

```python
# brightdata/auto.py
def scrape_urls(urls, ...) -> Dict[str, ScrapeResult]:
    # ❌ Still uses asyncio.run() - creates new loop!
    return asyncio.run(
        scrape_urls_async(urls, ...)
    )

# Each call to scrape_urls() creates a new event loop
result1 = scrape_urls([url1])  # Loop 1: create → use → close
result2 = scrape_urls([url2])  # Loop 2: create → use → close
result3 = scrape_urls([url3])  # Loop 3: create → use → close
```

So even though they avoided the "Connector is closed" issue, they **still have the asyncio.run() performance problem**.

---

## 💡 Comparison: All Approaches

| Aspect | Persistent Session (sdk-python goal) | Stateless Sessions (brightdata) | Persistent Session (broken sdk-python) |
|--------|-------------------------------------|--------------------------------|---------------------------------------|
| **Session lifecycle** | Managed by context manager | No lifecycle - create per call | Managed but broken (nested contexts) |
| **"Connector is closed"** | ✅ Fixed (no nested contexts) | ✅ No issue (no shared session) | ❌ Broken (nested contexts) |
| **Connection pooling** | ✅ Yes | ❌ No | ✅ Yes (when it works) |
| **Performance** | ✅ Best | ⚠️ Moderate | ⚠️ Unpredictable (race conditions) |
| **Complexity** | ⚠️ Moderate | ✅ Simple | ❌ Complex (buggy) |
| **asyncio.run() issue** | ✅ Avoided (persistent loop in SyncAdapter) | ❌ Still has it | ❌ Has it |
| **Best for** | Production apps | Simple scripts | ❌ Nothing (broken) |

---

## 🎯 The Real Difference

### brightdata Package Strategy

```
┌─────────────────────────────┐
│   BrightdataEngine          │
│   (No persistent state)     │
├─────────────────────────────┤
│ async def trigger():        │
│   ├─ Create ClientSession   │
│   ├─ Make request           │
│   └─ Close ClientSession    │
│                             │
│ async def get_status():     │
│   ├─ Create ClientSession   │
│   ├─ Make request           │
│   └─ Close ClientSession    │
└─────────────────────────────┘

NO lifecycle management needed!
Each call is isolated.
```

### sdk-python Strategy (Goal: Fixed)

```
┌─────────────────────────────────┐
│   AsyncEngine                   │
│   (Persistent ClientSession)    │
├─────────────────────────────────┤
│ async def __aenter__():         │
│   └─ Create ClientSession ONCE  │
│                                 │
│ async def get_from_url():       │
│   └─ Reuse SAME ClientSession   │
│                                 │
│ async def __aexit__():          │
│   └─ Close ClientSession ONCE   │
└─────────────────────────────────┘
         ▲
         │ Client manages lifecycle
         │
┌────────┴─────────────────────────┐
│   BrightDataClient               │
│   (Context manager)              │
├──────────────────────────────────┤
│ async def __aenter__():          │
│   └─ await self.engine.__aenter__() │
│                                  │
│ async def list_zones():          │
│   └─ No nested context!          │
│                                  │
│ async def __aexit__():           │
│   └─ await self.engine.__aexit__() │
└──────────────────────────────────┘

Lifecycle managed at CLIENT level only.
Engine is initialized ONCE per client context.
```

---

## 🤔 Should sdk-python Use Stateless Sessions?

### Arguments FOR

1. ✅ Simple implementation - no context manager complexity
2. ✅ No "Connector is closed" issues
3. ✅ Easier to maintain
4. ✅ Works well for simple use cases

### Arguments AGAINST

1. ❌ Performance regression - slower than persistent sessions
2. ❌ No connection pooling benefits
3. ❌ Higher resource usage
4. ❌ Doesn't align with aiohttp best practices
5. ❌ Still doesn't solve asyncio.run() issue

### Recommendation

**NO** - Don't use stateless sessions for sdk-python because:
- The current codebase is designed for persistent sessions
- Users expect high performance for bulk scraping
- Connection pooling is valuable for production use
- The "Connector is closed" issue can be fixed properly by removing nested contexts

**Better**: Fix the persistent session approach by:
1. Remove nested `async with self.engine:` from methods
2. Client manages engine lifecycle at top level only
3. Provide `SyncBrightDataClient` adapter for sync users

---

## 📋 Summary

### What brightdata Package Did

1. **Stateless Sessions**: Create new `aiohttp.ClientSession` per API call
2. **No Engine Context Manager**: No lifecycle management needed
3. **Dual Interface**: Both sync and async methods on every scraper
4. **_run_blocking() Helper**: Smart wrapper for sync calls

### How It Compares

- ✅ Solves "Connector is closed" (no shared session)
- ❌ Still has asyncio.run() issue (sync wrappers use it)
- ⚠️ Trades performance for simplicity
- ✅ Good for simple scripts, not for high-volume apps

### For sdk-python

**This is NOT the right approach** because:
- Performance matters for bulk scraping
- Connection pooling is valuable
- Persistent sessions are the aiohttp best practice
- The "Connector is closed" issue can be fixed properly

**Instead, use Approach 2** (Async + Sync Adapter with persistent sessions).

---

**Last Updated**: 2025-01-10
**Source**: Analysis of `/Users/ns/Desktop/projects/brightdata/brightdata`
