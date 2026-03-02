# Architecture Comparison: brightdata vs sdk-python

## Executive Summary

After inspecting both SDKs, the older `brightdata` SDK has a **MUCH BETTER architecture** for async operations than the newer `sdk-python`. The key difference: **brightdata creates fresh sessions per operation**, while sdk-python tries to reuse a shared engine with conflicting context management.

## The Key Architectural Difference

### brightdata SDK (BETTER) ✅
```python
# From brightdata/webscraper_api/engine.py lines 93-98
async def trigger(self, payload, ...):
    # Creates a NEW session for EVERY call
    async with aiohttp.ClientSession(
        timeout=self._timeout,
        headers=headers,
        trust_env=True,
    ) as sess:
        # ... do the operation
```

**Result**: Every operation is independent. No shared state conflicts. True concurrency works!

### sdk-python (PROBLEMATIC) ❌
```python
# From sdk-python client.py line 489
async def list_zones(self):
    async with self.engine:  # Tries to manage SHARED engine
        return await self._zone_manager.list_zones()
```

**Result**: Operations fight over shared engine context. Concurrent calls fail with "Connector is closed" errors.

## Detailed Comparison

### 1. Session Management

#### brightdata (Stateless) ✅
- **Per-operation sessions**: Each API call creates its own `ClientSession`
- **No persistent connections**: Sessions are created and destroyed per operation
- **No context conflicts**: Operations can't interfere with each other
- Code evidence (engine.py):
  - `trigger()` - lines 94-98: new session
  - `get_status()` - lines 210-214: new session
  - `fetch_result()` - lines 243-247: new session

#### sdk-python (Stateful) ❌
- **Shared engine**: Single `AsyncEngine` instance with persistent session
- **Context manager conflicts**: Each method tries to control the shared engine
- **Race conditions**: Operations interfere when run concurrently
- Code evidence:
  - All operations use `self.engine` (shared state)
  - Each tries `async with self.engine:` (conflicting management)

### 2. Concurrency Handling

#### brightdata ✅
```python
# From async_poll.py - Clean concurrent polling
async def fetch_snapshots_async(scraper, snapshot_ids, ...):
    async with aiohttp.ClientSession() as session:
        tasks = [
            fetch_snapshot_async(scraper, sid, session=session, ...)
            for sid in snapshot_ids
        ]
        return await asyncio.gather(*tasks)
```
- Creates ONE session for efficiency
- Shares it explicitly via parameter passing
- All tasks use the same session cooperatively
- No context manager conflicts

#### sdk-python ❌
```python
# Attempts concurrent operations fail
await asyncio.gather(
    client.list_zones(),      # Each creates own context
    client.get_account_info(), # Conflicts!
    client.test_connection()   # "Connector is closed"
)
```

### 3. Resource Management

#### brightdata ✅
- **Explicit cleanup**: Sessions are short-lived, cleaned up immediately
- **No resource leaks**: Each operation cleans up after itself
- **Simple lifecycle**: Create → Use → Destroy per operation

#### sdk-python ❌
- **Complex lifecycle**: Engine created on init, managed throughout
- **Cleanup timing issues**: Who closes the engine and when?
- **Resource leak potential**: Long-lived connections, unclear ownership

## Why brightdata's Approach is Superior

### 1. True Statelessness
- No shared state between operations
- Each operation is independent
- Perfect for concurrent execution

### 2. Simplicity
- No complex context management
- No need to coordinate between operations
- Easier to reason about

### 3. Reliability
- No race conditions
- No "Connector is closed" errors
- Predictable behavior

### 4. Performance Trade-offs
While creating new sessions has overhead, brightdata optimizes by:
- Allowing session sharing when beneficial (via parameters)
- Using connection pooling at the aiohttp level
- Keeping operations lightweight

## The Irony

The OLDER `brightdata` SDK (less polished, less documented) has BETTER architecture than the newer `sdk-python`:

- `brightdata`: Simple, stateless, works with concurrency
- `sdk-python`: Complex, stateful, breaks with concurrency

## Lessons Learned

### What sdk-python Should Adopt from brightdata

1. **Stateless Operations**
   ```python
   # Good (brightdata style)
   async def list_zones(self):
       async with aiohttp.ClientSession() as sess:
           return await sess.get("/zones")
   ```

2. **Explicit Session Sharing** (when needed)
   ```python
   # Good - explicit parameter passing
   async def operation(self, session=None):
       if session is None:
           async with aiohttp.ClientSession() as sess:
               return await self._do_work(sess)
       return await self._do_work(session)
   ```

3. **No Shared Engine State**
   - Remove the singleton engine pattern
   - Each operation manages its own connection

## Code Examples

### brightdata: Concurrent Operations Work ✅
```python
# This WORKS in brightdata
results = asyncio.run(
    fetch_snapshots_async(scraper, snapshot_ids, poll=15)
)
# All operations complete successfully
```

### sdk-python: Concurrent Operations Fail ❌
```python
# This FAILS in sdk-python
results = await asyncio.gather(
    client.list_zones(),
    client.get_account_info(),
    client.test_connection()
)
# Error: "Connector is closed"
```

## Recommendation

The `sdk-python` should **abandon its current architecture** and adopt the simpler, more reliable approach from `brightdata`:

1. **Remove the shared AsyncEngine**
2. **Create sessions per operation**
3. **Allow explicit session sharing when needed**
4. **Eliminate context manager conflicts**

This would be a breaking change but would result in a much more reliable SDK that actually delivers on the promise of async operations.

## Conclusion

The `brightdata` SDK, despite being older and less polished, has fundamentally better architecture for async operations. It chose **simplicity over cleverness** and **statelessness over optimization**, resulting in an SDK that actually works correctly with concurrent operations.

The `sdk-python` tried to be too clever with its shared engine and context management, creating an architecture that looks good on paper but fails in practice. Sometimes, simpler is better.
