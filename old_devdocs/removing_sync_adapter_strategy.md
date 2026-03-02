# Can We Remove SyncBrightDataClient Later?

**Question**: If we provide SyncBrightDataClient now, can we remove it later to go "pure async"?

**Short Answer**: YES, but it's a breaking change for sync users.

**Key Insight**: Because it's a SEPARATE class, removing it is MUCH easier than removing sync methods from a mixed class.

---

## 🎯 The Key Difference

### Current Approach (Mixed)
```python
class BrightDataClient:
    # Async and sync MIXED in same class
    async def products_async(self, url): ...
    def products(self, url): ...  # Sync wrapper

    async def list_zones(self): ...
    def list_zones_sync(self): ...  # Sync wrapper

# If we remove sync methods:
# ❌ BREAKS: client.products(url)
# ❌ BREAKS: client.list_zones_sync()
# ❌ Users importing BrightDataClient are affected
# ❌ No clear migration path
```

### Separate Adapter Approach
```python
# brightdata/client.py
class BrightDataClient:
    # Pure async, ALWAYS been clean
    async def products(self, url): ...
    async def list_zones(self): ...

# brightdata/sync_client.py (SEPARATE FILE)
class SyncBrightDataClient:
    # Wrapper around async client
    def products(self, url): ...
    def list_zones(self): ...

# If we remove SyncBrightDataClient:
# ✅ BrightDataClient unchanged (already pure async)
# ❌ Only affects users who imported SyncBrightDataClient
# ✅ Clear migration: change import + add async/await
# ✅ Can provide deprecation warnings
```

---

## 📊 Impact Analysis: Removing SyncBrightDataClient

### Who Gets Affected?

```python
# ❌ BREAKS - Users who imported sync client
from brightdata import SyncBrightDataClient

with SyncBrightDataClient() as client:
    result = client.scrape.amazon.products(url)
# After removal: ImportError


# ✅ UNAFFECTED - Users who already use async client
from brightdata import BrightDataClient

async with BrightDataClient() as client:
    result = await client.scrape.amazon.products(url)
# Works perfectly, no changes needed!
```

### Comparison: Mixed vs Separate

| Aspect | Current (Mixed) | Separate Adapter |
|--------|----------------|------------------|
| **What breaks when removing sync?** | Everyone using `client.method()` | Only users who imported `SyncBrightDataClient` |
| **Can we track who's affected?** | ❌ No, all use same class | ✅ Yes, separate import |
| **Can we deprecate gradually?** | ⚠️ Hard, methods mixed | ✅ Easy, separate module |
| **Migration path clarity** | ❌ Unclear (same class) | ✅ Clear (different import) |
| **Can we version separately?** | ❌ No | ✅ Yes (sync adapter could be separate package) |

---

## 🗓️ Recommended Deprecation Timeline

### Phase 1: v2.0 (2025) - Introduce Separation

```python
# brightdata/__init__.py
from .client import BrightDataClient  # Pure async
from .sync_client import SyncBrightDataClient  # Adapter

__all__ = ["BrightDataClient", "SyncBrightDataClient"]

# Documentation
"""
BrightDataClient - Async client (recommended)
SyncBrightDataClient - Sync adapter for legacy code
"""
```

**Message**: "We recommend async for best performance, but provide sync adapter for migration."

### Phase 2: v2.5 (2026) - Deprecation Warning

```python
# brightdata/sync_client.py
import warnings

class SyncBrightDataClient:
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "SyncBrightDataClient is deprecated and will be removed in v4.0. "
            "Please migrate to async BrightDataClient. "
            "See migration guide: https://docs.brightdata.com/migrate-to-async",
            DeprecationWarning,
            stacklevel=2
        )
        # ... rest of implementation
```

**Message**: "Sync adapter is deprecated, please migrate to async."

### Phase 3: v3.0 (2027) - Final Warning

```python
# brightdata/sync_client.py
import warnings

class SyncBrightDataClient:
    def __init__(self, *args, **kwargs):
        warnings.warn(
            "SyncBrightDataClient will be REMOVED in v4.0 (in 6 months). "
            "This is your last warning. Migrate to async NOW. "
            "Migration guide: https://docs.brightdata.com/migrate-to-async",
            FutureWarning,  # More severe
            stacklevel=2
        )
        # ... implementation
```

**Message**: "Last chance - migrate now or your code will break in v4.0."

### Phase 4: v4.0 (2028) - Removal

```python
# brightdata/__init__.py
from .client import BrightDataClient

# SyncBrightDataClient removed!

__all__ = ["BrightDataClient"]

# brightdata/sync_client.py - DELETED
```

If users try to import:
```python
from brightdata import SyncBrightDataClient
# ImportError: cannot import name 'SyncBrightDataClient'
```

**Message**: "Pure async only. We warned you for 2 years!"

---

## 💡 Alternative: Separate Package Strategy

### Option A: Move to Separate Package (Softest)

Instead of removing, move sync adapter to separate package:

```bash
# Core package (pure async)
pip install brightdata

# Optional sync adapter (separate)
pip install brightdata-sync
```

```python
# Pure async (main package)
from brightdata import BrightDataClient

async with BrightDataClient() as client:
    result = await client.scrape.amazon.products(url)


# Sync adapter (optional package)
from brightdata_sync import SyncBrightDataClient

with SyncBrightDataClient() as client:
    result = client.scrape.amazon.products(url)
```

**Benefits**:
- ✅ Main package stays pure and clean
- ✅ Sync users can keep using adapter indefinitely
- ✅ We don't maintain it in core anymore
- ✅ Community can maintain sync adapter if they want
- ✅ No one's code breaks

### Option B: Community-Maintained Adapter

```python
# Official SDK (pure async)
pip install brightdata

# Community package (if someone wants to maintain it)
pip install brightdata-sync-adapter  # Not official
```

---

## 🎓 Comparison: Can We Go Pure Async Later?

### Current Architecture (Mixed)

```
┌─────────────────────────────────┐
│    BrightDataClient             │
│    (Everything mixed)           │
├─────────────────────────────────┤
│ async def products_async()      │  ◄── Remove these?
│ def products()  ←── SYNC        │      ❌ Breaks everyone
│                                 │
│ async def list_zones()          │
│ def list_zones_sync() ←── SYNC │      ❌ No clear migration
└─────────────────────────────────┘

Removing sync methods = Major breaking change
Hard to track who uses what
```

### Separate Adapter Architecture

```
┌─────────────────────────────────┐
│   BrightDataClient              │
│   (Pure async, ALWAYS)          │
├─────────────────────────────────┤
│ async def products()            │  ◄── Never changes
│ async def list_zones()          │      ✅ Clean forever
└─────────────────────────────────┘
        ▲
        │ Wraps
        │
┌───────┴─────────────────────────┐
│   SyncBrightDataClient          │  ◄── Can remove later
│   (Separate file/package)       │      ✅ Clear impact
├─────────────────────────────────┤
│ def products()                  │      ✅ Easy to deprecate
│ def list_zones()                │      ✅ Optional
└─────────────────────────────────┘

Removing adapter = Clean, contained change
Easy to track users (separate import)
```

---

## 📈 Real-World Examples

### How Other Libraries Handle This

#### Example 1: requests → httpx
```python
# Old sync library (requests)
import requests
response = requests.get("https://api.example.com")

# New async library (httpx)
import httpx

# Async (recommended)
async with httpx.AsyncClient() as client:
    response = await client.get("https://api.example.com")

# Sync (adapter provided)
with httpx.Client() as client:  # Separate class
    response = client.get("https://api.example.com")
```

They provide BOTH, separately, forever. Users choose.

#### Example 2: asyncio (Python itself)
```python
# Before Python 3.7
loop = asyncio.get_event_loop()
result = loop.run_until_complete(coro())

# Python 3.7+ (simplified)
result = asyncio.run(coro())  # New function

# Python 3.10+
# Old APIs still work but deprecated
# Message: "Use asyncio.run() instead"
```

Python deprecated old APIs gradually over 3+ years.

#### Example 3: SQLAlchemy
```python
# SQLAlchemy 1.x (sync)
from sqlalchemy import create_engine
engine = create_engine("postgresql://...")
result = engine.execute("SELECT * FROM users")

# SQLAlchemy 2.x (async first)
from sqlalchemy.ext.asyncio import create_async_engine

# Async (recommended)
engine = await create_async_engine("postgresql+asyncpg://...")
result = await engine.execute("SELECT * FROM users")

# Sync (still works, separate path)
from sqlalchemy import create_engine  # Still available
engine = create_engine("postgresql://...")
```

They kept sync working but async is "the way forward."

---

## 🎯 Strategy Recommendation

### Recommended Approach: "Separation → Deprecation → Optional Removal"

```
v2.0 (2025): Separate
├─ BrightDataClient (pure async)
└─ SyncBrightDataClient (adapter)

v2.5 (2026): Deprecate
├─ BrightDataClient (pure async)
└─ SyncBrightDataClient (⚠️ deprecated)

v3.0 (2027): Strong Warning
├─ BrightDataClient (pure async)
└─ SyncBrightDataClient (⚠️⚠️ final warning)

v4.0 (2028): Two Options
├─ Option A: Remove entirely (pure async only)
└─ Option B: Move to separate package (brightdata-sync)
```

### Why This Works

1. **v2.0**: Async client is already pure, sync is separate
   - No mixing, clean architecture
   - Users can choose based on their needs

2. **v2.5-v3.0**: Deprecation warnings
   - Users have 1-2 years to migrate
   - Clear warnings tell them what to do
   - Migration guide available

3. **v4.0**: Pure async (or move sync to separate package)
   - Async users unaffected (been pure since v2.0)
   - Sync users had 2+ years to migrate
   - Optional: sync adapter lives as separate package

---

## 💡 Key Insight

### The Question Reframed

**Your question**: "Can we remove SyncBrightDataClient later?"

**Real question**: "Does providing SyncBrightDataClient lock us in forever?"

**Answer**: NO! Because it's separate:

```python
# The async client is ALREADY pure in v2.0
class BrightDataClient:
    # No sync code here, never was!
    async def products(self, url): ...

# The sync adapter is OPTIONAL, SEPARATE
class SyncBrightDataClient:
    # Can remove/move later without touching async client
    def products(self, url): ...
```

### Contrast with Current

```python
# Current: Removing sync methods affects EVERYONE
class BrightDataClient:
    # Mixed async/sync
    async def products_async(self, url): ...
    def products(self, url): ...  # Removing this breaks everyone

# Can't remove without major breakage
```

---

## 📋 Decision Matrix

| Question | Current (Mixed) | Separate Adapter |
|----------|----------------|------------------|
| Can we remove sync later? | ⚠️ Yes, but breaks everyone | ✅ Yes, only affects sync users |
| Can we track impact? | ❌ No | ✅ Yes (separate import) |
| Can we deprecate gradually? | ⚠️ Hard | ✅ Easy |
| Is async client pure now? | ❌ No (has sync baggage) | ✅ Yes (separate from day 1) |
| Can we version independently? | ❌ No | ✅ Yes |
| Can community maintain sync? | ❌ No | ✅ Yes (separate package) |

---

## 🎓 Final Answer

### Can We Remove SyncBrightDataClient Later?

**YES**, and it's MUCH easier than removing sync from a mixed class because:

1. ✅ **BrightDataClient is already pure async** from day 1
   - No sync baggage to remove later
   - Async users never affected

2. ✅ **Clear separation** makes impact obvious
   - Only affects `from brightdata import SyncBrightDataClient`
   - Easy to track with import analysis

3. ✅ **Gradual deprecation** is possible
   - Add warnings in v2.5
   - Remove in v4.0 (2+ years notice)
   - Or move to separate package

4. ✅ **Optional exit strategy**: Don't remove, just move
   - Move to `brightdata-sync` package
   - Community can maintain if they want
   - We don't maintain it in core

### The Strategy

```
Phase 1: Provide both (separate)
         ↓
Phase 2: Deprecate sync adapter (warnings)
         ↓
Phase 3: Remove OR move to separate package
         ↓
Phase 4: Pure async (or async + optional community sync package)
```

**Bottom line**: Providing SyncBrightDataClient does NOT lock us in. It's a bridge, not a burden.

---

**Last Updated**: 2025-01-10
