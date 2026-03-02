# How Sync Users Can Use an Async-Only SDK

**Scenario**: SDK is async-only (Pure Async approach)
**Question**: How do sync users call the methods?

---

## 🎯 Five Options for Sync Users

### Option 1: asyncio.run() Wrapper (Manual, Simple)

**Users write their own wrapper**:

```python
import asyncio
from brightdata import BrightDataClient

# User's sync code
def scrape_amazon_product(url: str):
    """Sync wrapper function"""
    async def _async_impl():
        async with BrightDataClient() as client:
            return await client.scrape.amazon.products(url)

    return asyncio.run(_async_impl())

# Usage
result = scrape_amazon_product("https://amazon.com/dp/B123")
print(result.data)
```

**Pros**:
- ✅ Simple for one-off calls
- ✅ No additional SDK complexity
- ✅ Works immediately

**Cons**:
- ❌ Repetitive (need wrapper for each method)
- ❌ Still creates new loop each call (performance issue)
- ❌ Users need to understand async/await
- ❌ Verbose

---

### Option 2: SyncBrightDataClient Adapter (Recommended)

**We provide a separate sync client class**:

```python
# brightdata/sync_client.py
import asyncio
from typing import Optional
from .client import BrightDataClient

class SyncBrightDataClient:
    """
    Synchronous adapter for BrightDataClient.

    Uses a persistent event loop for all operations, providing
    better performance than repeated asyncio.run() calls.

    Example:
        >>> with SyncBrightDataClient(token="...") as client:
        ...     zones = client.list_zones()
        ...     result = client.scrape_amazon_products(url)
    """

    def __init__(self, token: Optional[str] = None, **kwargs):
        """
        Initialize sync client.

        Args:
            token: API token (optional, loads from environment)
            **kwargs: Additional arguments for BrightDataClient
        """
        self._async_client = BrightDataClient(token=token, **kwargs)
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._closed = False

    def __enter__(self):
        """Initialize persistent event loop"""
        if self._loop is not None:
            raise RuntimeError("Client already entered")

        # Create persistent loop
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # Initialize async client in the loop
        self._loop.run_until_complete(
            self._async_client.__aenter__()
        )

        return self

    def __exit__(self, *args):
        """Cleanup persistent loop"""
        if self._loop is None:
            return

        try:
            # Cleanup async client
            self._loop.run_until_complete(
                self._async_client.__aexit__(*args)
            )
        finally:
            # Close the loop
            self._loop.close()
            self._loop = None
            self._closed = True

    def _run(self, coro):
        """Run coroutine in persistent loop"""
        if self._loop is None:
            raise RuntimeError(
                "Client not initialized. Use 'with SyncBrightDataClient() as client:'"
            )
        return self._loop.run_until_complete(coro)

    # ========================================
    # Utility Methods
    # ========================================

    def list_zones(self):
        """List all zones (sync)"""
        return self._run(self._async_client.list_zones())

    def get_account_info(self, refresh: bool = False):
        """Get account info (sync)"""
        return self._run(self._async_client.get_account_info(refresh))

    def test_connection(self):
        """Test connection (sync)"""
        return self._run(self._async_client.test_connection())

    # ========================================
    # Service Access (Property Wrappers)
    # ========================================

    @property
    def scrape(self):
        """Access scrape services (sync)"""
        return SyncScrapeService(self._async_client.scrape, self._loop)

    @property
    def search(self):
        """Access search services (sync)"""
        return SyncSearchService(self._async_client.search, self._loop)


class SyncScrapeService:
    """Sync wrapper for scrape service"""

    def __init__(self, async_service, loop):
        self._async_service = async_service
        self._loop = loop

    @property
    def amazon(self):
        return SyncAmazonScraper(self._async_service.amazon, self._loop)

    @property
    def linkedin(self):
        return SyncLinkedInScraper(self._async_service.linkedin, self._loop)


class SyncAmazonScraper:
    """Sync wrapper for Amazon scraper"""

    def __init__(self, async_scraper, loop):
        self._async_scraper = async_scraper
        self._loop = loop

    def products(self, url, timeout=240):
        """Scrape Amazon products (sync)"""
        return self._loop.run_until_complete(
            self._async_scraper.products_async(url, timeout)
        )

    def reviews(self, url, **kwargs):
        """Scrape Amazon reviews (sync)"""
        return self._loop.run_until_complete(
            self._async_scraper.reviews_async(url, **kwargs)
        )


# Similar wrappers for other services...
```

**Usage**:

```python
from brightdata import SyncBrightDataClient

# ✅ Sync API - looks exactly like old code
with SyncBrightDataClient() as client:
    # Utility methods
    zones = client.list_zones()
    info = client.get_account_info()

    # Scraping
    result = client.scrape.amazon.products(
        url="https://amazon.com/dp/B123"
    )

    # Search
    search_results = client.search.google(
        query="python tutorial"
    )

    print(f"Found {len(zones)} zones")
    print(f"Product: {result.data['title']}")
```

**Pros**:
- ✅ Persistent loop (good performance)
- ✅ Looks exactly like sync API
- ✅ Easy migration for sync users
- ✅ Connection pooling works
- ✅ Clear separation from async client

**Cons**:
- ❌ Maintenance burden (wrapper methods for all APIs)
- ❌ Two client classes to maintain
- ❌ Still can't use concurrency in sync mode

---

### Option 3: Auto-Generated Sync Wrapper (Advanced)

**Use decorators/metaclasses to auto-generate sync wrappers**:

```python
# brightdata/sync_adapter.py
import asyncio
import inspect
from functools import wraps

def sync_adapter(async_class):
    """
    Decorator that auto-generates sync wrapper for async class.

    Creates a new class with sync versions of all async methods.
    """
    class SyncWrapper:
        def __init__(self, *args, **kwargs):
            self._async_instance = async_class(*args, **kwargs)
            self._loop = None

        def __enter__(self):
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            self._loop.run_until_complete(
                self._async_instance.__aenter__()
            )
            return self

        def __exit__(self, *args):
            self._loop.run_until_complete(
                self._async_instance.__aexit__(*args)
            )
            self._loop.close()

        def __getattr__(self, name):
            """Auto-wrap async methods as sync"""
            attr = getattr(self._async_instance, name)

            # If it's a coroutine function, wrap it
            if inspect.iscoroutinefunction(attr):
                @wraps(attr)
                def sync_wrapper(*args, **kwargs):
                    coro = attr(*args, **kwargs)
                    return self._loop.run_until_complete(coro)
                return sync_wrapper

            # If it's a property/object with methods, wrap recursively
            elif hasattr(attr, '__dict__'):
                return SyncPropertyWrapper(attr, self._loop)

            # Otherwise return as-is
            return attr

    SyncWrapper.__name__ = f"Sync{async_class.__name__}"
    SyncWrapper.__doc__ = f"Synchronous wrapper for {async_class.__name__}"
    return SyncWrapper


class SyncPropertyWrapper:
    """Wraps property objects to make their methods sync"""

    def __init__(self, async_obj, loop):
        self._async_obj = async_obj
        self._loop = loop

    def __getattr__(self, name):
        attr = getattr(self._async_obj, name)

        if inspect.iscoroutinefunction(attr):
            @wraps(attr)
            def sync_wrapper(*args, **kwargs):
                coro = attr(*args, **kwargs)
                return self._loop.run_until_complete(coro)
            return sync_wrapper

        return attr


# Usage - automatically create sync client
from brightdata import BrightDataClient

SyncBrightDataClient = sync_adapter(BrightDataClient)

# Now use it
with SyncBrightDataClient() as client:
    zones = client.list_zones()  # Auto-wrapped!
    result = client.scrape.amazon.products(url)  # Auto-wrapped!
```

**Pros**:
- ✅ No manual wrapper code
- ✅ Automatically wraps all async methods
- ✅ Less maintenance burden
- ✅ DRY principle

**Cons**:
- ❌ Complex implementation
- ❌ Magic behavior (harder to debug)
- ❌ Type hints may not work correctly
- ❌ IDE autocomplete may break

---

### Option 4: nest_asyncio (Jupyter/IPython)

**For Jupyter notebooks, use nest_asyncio**:

```python
# In Jupyter notebook
import nest_asyncio
nest_asyncio.apply()

# Now you can use asyncio.run in notebooks
import asyncio
from brightdata import BrightDataClient

async def scrape():
    async with BrightDataClient() as client:
        return await client.scrape.amazon.products(url)

result = asyncio.run(scrape())  # Works in Jupyter!
```

Or directly use await:

```python
# In Jupyter notebook (IPython has built-in event loop)
from brightdata import BrightDataClient

# Can use await directly at top level!
async with BrightDataClient() as client:
    result = await client.scrape.amazon.products(url)
    print(result.data)
```

**Pros**:
- ✅ Works in Jupyter/IPython
- ✅ Can use await at top level
- ✅ No wrapper needed

**Cons**:
- ❌ Only for notebooks/IPython
- ❌ Requires nest_asyncio package
- ❌ Doesn't help regular scripts

---

### Option 5: Thread Pool Executor (Concurrent Sync)

**Run async code in thread pool**:

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor
from brightdata import BrightDataClient

class ThreadedAsyncClient:
    """
    Runs async client in dedicated thread with event loop.
    Allows concurrent sync calls.
    """

    def __init__(self, token=None):
        self._token = token
        self._executor = ThreadPoolExecutor(max_workers=1)
        self._client = None

    def __enter__(self):
        # Initialize client in background thread
        future = self._executor.submit(self._init_async_client)
        self._client = future.result()
        return self

    def __exit__(self, *args):
        # Cleanup client in background thread
        future = self._executor.submit(self._cleanup_async_client)
        future.result()
        self._executor.shutdown()

    def _init_async_client(self):
        """Run in thread: create loop and initialize client"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        async def init():
            client = BrightDataClient(token=self._token)
            await client.__aenter__()
            return (client, loop)

        return loop.run_until_complete(init())

    def _cleanup_async_client(self):
        """Run in thread: cleanup client and close loop"""
        client, loop = self._client
        loop.run_until_complete(client.__aexit__(None, None, None))
        loop.close()

    def _run_in_thread(self, coro):
        """Run coroutine in background thread's event loop"""
        client, loop = self._client
        future = asyncio.run_coroutine_threadsafe(coro, loop)
        return future.result()

    def list_zones(self):
        client, _ = self._client
        return self._run_in_thread(client.list_zones())

    def scrape_amazon_products(self, url):
        client, _ = self._client
        return self._run_in_thread(
            client.scrape.amazon.products(url)
        )

# Usage
with ThreadedAsyncClient() as client:
    zones = client.list_zones()
    result = client.scrape_amazon_products(url)
```

**Pros**:
- ✅ Can call from multiple threads
- ✅ True background execution
- ✅ Persistent loop in background

**Cons**:
- ❌ Most complex implementation
- ❌ Thread management overhead
- ❌ Still can't use true concurrency from sync code

---

## 📊 Comparison: Which Option for Which User?

| User Type | Recommended Option | Why |
|-----------|-------------------|-----|
| **Simple scripts** | Option 1 (asyncio.run) | Quick, no dependencies |
| **Production apps** | Option 2 (SyncAdapter) | Best performance, clean API |
| **Library maintainers** | Option 2 (SyncAdapter) | Official support |
| **Jupyter users** | Option 4 (nest_asyncio) | Built for notebooks |
| **Advanced users** | Migrate to async | Best long-term solution |
| **Legacy codebases** | Option 2 (SyncAdapter) | Easy migration path |

---

## 🎯 Recommended Approach: Option 2 (SyncBrightDataClient)

### Why Option 2 is Best

1. **Official support**: Users have clear path
2. **Good performance**: Persistent loop
3. **Familiar API**: Looks like old sync API
4. **Migration path**: Easy to adopt
5. **Connection pooling**: Actually works

### Implementation Strategy

```python
# brightdata/__init__.py
from .client import BrightDataClient  # Async client
from .sync_client import SyncBrightDataClient  # Sync adapter

__all__ = ["BrightDataClient", "SyncBrightDataClient"]
```

### Documentation Example

```python
"""
Bright Data SDK

Two client types:

1. BrightDataClient (async) - Recommended for best performance
   - Use with async/await
   - Supports true concurrency
   - Best for production applications

   Example:
       async with BrightDataClient() as client:
           result = await client.scrape.amazon.products(url)

2. SyncBrightDataClient (sync) - For synchronous code
   - Drop-in replacement for sync users
   - Uses persistent event loop internally
   - Easier for simple scripts

   Example:
       with SyncBrightDataClient() as client:
           result = client.scrape.amazon.products(url)
"""
```

---

## 💡 Migration Guide for Sync Users

### Before (Current SDK)

```python
from brightdata import BrightDataClient

client = BrightDataClient()

# Old sync methods
zones = client.list_zones_sync()
result = client.scrape.amazon.products(url)  # Was sync
```

### After (Async-Only SDK) - Option A: Use Sync Adapter

```python
from brightdata import SyncBrightDataClient

# ✅ Same API, just different import and context manager
with SyncBrightDataClient() as client:
    zones = client.list_zones()  # No _sync suffix
    result = client.scrape.amazon.products(url)  # Still sync
```

### After (Async-Only SDK) - Option B: Migrate to Async

```python
from brightdata import BrightDataClient

# Better performance, true concurrency
async with BrightDataClient() as client:
    # Can run multiple operations concurrently!
    zones, result = await asyncio.gather(
        client.list_zones(),
        client.scrape.amazon.products(url)
    )
```

---

## 🎓 Summary

### Question: "How do sync users use async-only SDK?"

**Answer: They have 5 options, but we recommend Option 2**

### Option 2 (SyncBrightDataClient) Provides:

```python
# ✅ Clean sync API
with SyncBrightDataClient() as client:
    result = client.scrape.amazon.products(url)

# ✅ Persistent loop (good performance)
# ✅ Connection pooling works
# ✅ Official SDK support
# ✅ Easy migration
```

### The Strategy

1. **v2.0**: Make main client async-only (BrightDataClient)
2. **Also provide**: SyncBrightDataClient adapter
3. **Documentation**: Show both patterns, recommend async
4. **Migration guide**: Help users transition

### Best of Both Worlds

- Async users: Clean async client, no sync baggage
- Sync users: Official sync adapter, good performance
- Everyone: Clear separation, no confusion

---

**Last Updated**: 2025-01-10
