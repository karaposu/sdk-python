# 5 Things That Could Improve the Codebase (Or Maybe Not)

A critical analysis of potential improvements, balanced with reasons why the current design might be intentional.

---

## 1. Inconsistent Async/Sync Method Naming

### The Issue

The codebase uses **three different naming conventions** for async/sync methods:

| Pattern | Example | Used By |
|---------|---------|---------|
| `method()` async, `method_sync()` sync | `products()`, `products_sync()` | Amazon, LinkedIn scrapers |
| `method_async()` async, `method()` sync | `profiles_async()`, `profiles()` | Instagram, Facebook scrapers |
| `method()` async only (no sync) | `posts()` in LinkedInScraper | Some LinkedIn methods |

This creates confusion about which method to call and what behavior to expect.

```python
# Amazon: async is the "default" name
await scraper.products(url)      # async
scraper.products_sync(url)       # sync

# Instagram: sync is the "default" name
await scraper.profiles_async(url)  # async
scraper.profiles()                 # sync
```

### The Improvement

Standardize on one pattern across all scrapers. The most Pythonic approach would be:

```python
# Clear, explicit naming
await scraper.products(url)       # async (default in async-first SDK)
scraper.products_sync(url)        # sync (explicitly marked)
```

### Why It Might Be This Way

1. **Evolutionary development**: Different scrapers were added at different times by different contributors. The inconsistency is organic, not designed.

2. **User feedback driven**: Instagram/Facebook might have been built after user feedback that sync should be the "easy" default (no `_sync` suffix required).

3. **Migration in progress**: The git status shows active work on sync/async. This might already be in the process of being fixed.

4. **Platform usage patterns**: Some platforms (Instagram) might be used more in sync contexts (scripts), while others (Amazon) in async contexts (web apps). The naming might reflect expected usage.

---

## 2. Massive Boilerplate in sync_client.py

### The Issue

The `sync_client.py` file contains **~750 lines** of nearly identical wrapper code:

```python
# This pattern repeats 80+ times
def products(self, url, **kwargs):
    return self._loop.run_until_complete(self._async.products(url, **kwargs))

def products_trigger(self, url, **kwargs):
    return self._loop.run_until_complete(self._async.products_trigger(url, **kwargs))

def products_status(self, snapshot_id):
    return self._loop.run_until_complete(self._async.products_status(snapshot_id))
# ... and so on for every single method
```

This could be reduced to ~50 lines with metaprogramming:

```python
def _make_sync_wrapper(async_method):
    @functools.wraps(async_method)
    def wrapper(self, *args, **kwargs):
        coro = getattr(self._async, async_method.__name__)(*args, **kwargs)
        return self._loop.run_until_complete(coro)
    return wrapper
```

### The Improvement

Use `__getattr__`, metaclasses, or a decorator pattern to auto-generate sync wrappers.

### Why It Might Be This Way

1. **Explicit is better than implicit**: Python philosophy. Every sync method is visible, documented, and has clear type hints. IDEs can autocomplete them. No magic.

2. **Type safety**: Auto-generated methods don't get proper type hints. With explicit methods, `SyncAmazonScraper.products()` has correct `-> ScrapeResult` return type hints.

3. **Debugging clarity**: When something breaks, the stack trace points to an actual method, not a generated one. Easier to debug.

4. **Documentation**: Each method can have its own docstring if needed. Generated methods would share documentation or have none.

5. **Customization escape hatch**: Some sync wrappers might need special handling (like the async suffix inconsistency in Instagram). Explicit code allows per-method customization.

6. **IDE/tooling support**: Static analysis tools, documentation generators, and IDEs work better with explicit methods than dynamically generated ones.

---

## 3. Dataset IDs Scattered as Magic Strings

### The Issue

Dataset IDs are hardcoded throughout scraper files:

```python
# linkedin/scraper.py
DATASET_ID = "gd_l1viktl72bvl7bjuj0"  # People Profiles
DATASET_ID_COMPANIES = "gd_l1vikfnt1wgvvqz95w"  # Companies
DATASET_ID_JOBS = "gd_lpfll7v5hcqtkxl6l"  # Jobs

# amazon/scraper.py
DATASET_ID = "gd_l7q7dkf244hwjntr0"  # Amazon Products
DATASET_ID_REVIEWS = "gd_le8e811kzy4ggddlq"  # Amazon Reviews

# instagram/scraper.py
DATASET_ID = "gd_l1vikfch901nx3by4"  # Profiles
DATASET_ID_POSTS = "gd_lk5ns7kz21pck8jpis"  # Posts
```

No central registry. No validation. No easy way to see all datasets.

### The Improvement

Create a central `datasets.py` or enum:

```python
class BrightDataDatasets(Enum):
    AMAZON_PRODUCTS = "gd_l7q7dkf244hwjntr0"
    AMAZON_REVIEWS = "gd_le8e811kzy4ggddlq"
    LINKEDIN_PROFILES = "gd_l1viktl72bvl7bjuj0"
    # ... etc

# Usage
class AmazonScraper:
    DATASET_ID = BrightDataDatasets.AMAZON_PRODUCTS.value
```

### Why It Might Be This Way

1. **Single responsibility**: Each scraper "owns" its datasets. A LinkedIn scraper developer doesn't need to know about Amazon datasets. Colocation keeps related things together.

2. **Rarely changes**: Dataset IDs are assigned by Bright Data and essentially never change. The cost of scattered strings is low when they're stable.

3. **Independence**: If scrapers are ever split into separate packages, they remain self-contained without shared dependencies.

4. **Documentation proximity**: The comment explaining what each dataset does is right next to the ID. A central file would separate IDs from context.

5. **No runtime benefit**: A central registry adds a lookup step without providing runtime validation (the ID is still a string that could be wrong).

---

## 4. Dual Type Systems: TypedDict (types.py) AND Dataclasses (payloads.py)

### The Issue

The codebase has **two parallel type definition systems**:

```python
# types.py - TypedDict approach (marked deprecated but still exists)
class AmazonProductPayload(TypedDict, total=False):
    url: str
    reviews_count: NotRequired[int]

# payloads.py - Dataclass approach (the "new" way)
@dataclass
class AmazonProductPayload(URLPayload):
    url: str
    reviews_count: Optional[int] = None

    def __post_init__(self):
        # Validation logic
```

Both files have ~200+ lines of similar definitions. The TypedDict versions are marked deprecated but still maintained.

**Worse**: Neither is actually used by the scrapers! Scrapers build raw dicts directly:

```python
# instagram/scraper.py line 430
payload = [{"url": u} for u in url_list]  # Not using any Payload class
```

### The Improvement

1. Delete `types.py` (or move non-payload types elsewhere)
2. Actually use `payloads.py` classes in scrapers for input validation
3. Have one source of truth for payload structure

### Why It Might Be This Way

1. **Backward compatibility**: Users might be importing from `types.py`. Removing it would break their code. The deprecation allows a gradual migration.

2. **TypedDict for type hints, Dataclass for validation**: TypedDict is lighter weight for pure type checking. Dataclasses add runtime overhead. Some users might want just type hints.

3. **Payloads are for public API**: The dataclass payloads might be intended for users who want validation, while internal code uses raw dicts for performance.

4. **Work in progress**: The header in `payloads.py` says it "replaces" TypedDict. The migration might simply be incomplete.

5. **External validation**: Bright Data's API validates payloads anyway. Client-side validation is redundant work—nice for UX but not strictly necessary.

---

## 5. Mixed Error Handling Strategy

### The Issue

The codebase uses two different error handling strategies inconsistently:

**Strategy A: Return error in result object**
```python
# workflow.py
if not snapshot_id:
    return ScrapeResult(
        success=False,
        error="Failed to trigger scrape - no snapshot_id returned",
        ...
    )
```

**Strategy B: Raise exception**
```python
# base.py
if not snapshot_id:
    raise APIError("Failed to trigger scrape - no snapshot_id returned")
```

The same error condition is handled differently in different places. Users can't know whether to:
- Check `result.success` and `result.error`
- Catch exceptions
- Do both

### The Improvement

Pick one strategy and apply it consistently:

```python
# Option 1: Always exceptions (Pythonic for errors)
try:
    result = await client.scrape.amazon.products(url)
except BrightDataError as e:
    handle_error(e)

# Option 2: Always result objects (like Go, Rust)
result = await client.scrape.amazon.products(url)
if not result.success:
    handle_error(result.error)
```

### Why It Might Be This Way

1. **Different error types**: "No snapshot_id" is an unexpected error (exception). "Scrape timed out" is an expected outcome (result). The distinction might be intentional.

2. **Batch vs single operations**: For single URL scrapes, exceptions work well. For batch scrapes (100 URLs), you don't want one failure to abort everything—you want partial results with some `success=False`.

3. **WorkflowExecutor is defensive**: It catches exceptions internally and converts them to result objects, so callers always get a result. This is a deliberate design for reliability.

4. **User preference**: Some users prefer exceptions (try/except), others prefer result checking (if/else). Supporting both gives flexibility.

5. **Fail-fast vs fail-safe contexts**: CLI tools should raise exceptions (fail fast). Library usage might want result objects (fail safe).

---

## Summary

| Issue | Improvement Impact | Likelihood of Intentional Design | Status |
|-------|-------------------|----------------------------------|--------|
| Async/sync naming inconsistency | High | Low (evolutionary debt) | **FIXED** |
| Sync wrapper boilerplate | Medium | Medium (explicit > implicit) | Not addressed |
| Scattered dataset IDs | Low | High (ownership/colocation) | Not addressed |
| Dual type systems | Medium | Medium (migration in progress) | Not addressed |
| Mixed error handling | High | High (different use cases) | Not addressed |

The key insight: **Some "problems" are actually trade-offs**. Before "fixing" any of these, consider whether the current design serves a purpose that isn't immediately obvious. Talk to the original developers if possible—there may be undocumented requirements or constraints that led to these decisions.

---

## Update (Dec 2025)

**Issue #1 (Async/sync naming inconsistency) has been fixed.** All scrapers now follow the Amazon pattern:

```python
# Consistent naming across all scrapers:
await scraper.profiles(url)       # async (primary)
scraper.profiles_sync(url)        # sync wrapper

await scraper.profiles_trigger(url)  # async trigger
scraper.profiles_trigger_sync(url)   # sync trigger
```

Files updated:
- `src/brightdata/scrapers/instagram/scraper.py`
- `src/brightdata/scrapers/instagram/search.py`
- `src/brightdata/scrapers/facebook/scraper.py`
- `src/brightdata/sync_client.py`
