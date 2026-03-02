# Remove GenericScraper Analysis

An analysis of whether `GenericScraper` class can be safely removed.

---

## What GenericScraper Does

**Location**: `src/brightdata/api/scrape_service.py:195-213`

```python
class GenericScraper:
    """Generic web scraper using Web Unlocker API."""

    def __init__(self, client: "BrightDataClient"):
        self._client = client

    async def url(
        self,
        url: Union[str, List[str]],
        country: str = "",
        response_format: str = "raw",
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """Scrape URL(s) asynchronously."""
        return await self._client.scrape_url(  # <-- Just calls scrape_url()
            url=url,
            country=country,
            response_format=response_format,
        )
```

**Total**: 20 lines of code that just forward to `client.scrape_url()`.

---

## The Redundancy

| Method | Parameters | Notes |
|--------|------------|-------|
| `client.scrape_url()` | url, zone, country, response_format, method, timeout | Full control |
| `client.scrape_url()` | url, country, response_format | Hides zone, method, timeout |

`GenericScraper.url()` is strictly less capable than `scrape_url()`.

---

## Impact Analysis

### Files That Would Need Changes

#### 1. Core SDK (4 files)

| File | Changes Required |
|------|------------------|
| `scrape_service.py` | Remove `GenericScraper` class, remove `generic` property |
| `sync_client.py` | Remove `SyncGenericScraper` class, remove `generic` property |
| `client.py` | Update docstrings (2 references) |
| `cli/commands/scrape.py` | Change `client.scrape_url()` → `client.scrape_url()` |

#### 2. Tests (15+ files)

| File | Usages |
|------|--------|
| `tests/e2e/test_client_e2e.py` | 5 usages + test class `TestGenericScraperAccess` |
| `tests/readme.py` | 3 usages |
| `tests/enes/web_unlocker.py` | 4 usages |

#### 3. Probe Tests (20+ files, 50+ usages)

| File | Usages |
|------|--------|
| `probe_tests/test_05_web_unlocker.py` | 6 usages |
| `probe_tests/test_05_web_unlocker_sync.py` | 6 usages |
| `probe_tests/test_06_webscraper_linkedin.py` | 6 usages |
| `probe_tests/test_06_webscraper_linkedin_sync.py` | 6 usages |
| `probe_tests/test_working_zone.py` | 4 usages |
| `probe_tests/test_manual_zones.py` | 2 usages |
| `probe_tests/test_09_error_handling.py` | 2 usages |
| `probe_tests/error_handling/*.py` | 12+ usages |
| `probe_tests/async/*.py` | 8 usages |

#### 4. Documentation (3+ files)

| File | Usages |
|------|--------|
| `README.md` | 5 usages |
| `demo_sdk.py` | 6 usages |
| `fixed.md` | 6 usages |

### Total Impact

| Category | Files | Usages |
|----------|-------|--------|
| Core SDK | 4 | ~6 |
| Tests | 15+ | ~15 |
| Probe Tests | 20+ | ~50 |
| Documentation | 3+ | ~17 |
| **TOTAL** | **~42 files** | **~88 usages** |

---

## Breaking Change Assessment

### Public API Status

```python
# __init__.py does NOT export GenericScraper
# So this is NOT public API:
from brightdata import GenericScraper  # Would fail

# But this IS accessible:
client.scrape_url(...)  # Works - could break external users
```

### Risk Level: **MEDIUM**

- `GenericScraper` class is not exported (low risk)
- But `client.scrape.generic` property is accessible (medium risk)
- Unknown how many external users rely on this pattern
- Follows the hierarchical API pattern users may expect

---

## Options

### Option A: Remove Completely (Recommended)

**Changes:**
1. Delete `GenericScraper` class from `scrape_service.py`
2. Delete `generic` property from `ScrapeService`
3. Delete `SyncGenericScraper` class from `sync_client.py`
4. Delete `generic` property from `SyncScrapeService`
5. Update all 88 usages to use `scrape_url()`

**Pros:**
- Cleaner codebase
- One way to do things
- Less code to maintain

**Cons:**
- Breaking change
- Lots of file updates
- Loses hierarchical API consistency

### Option B: Deprecate First

**Changes:**
1. Add deprecation warning to `GenericScraper.url()`
2. Wait one release cycle
3. Then remove

```python
import warnings

async def url(self, url, country="", response_format="raw"):
    warnings.warn(
        "client.scrape_url() is deprecated. "
        "Use client.scrape_url() instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return await self._client.scrape_url(...)
```

**Pros:**
- Gives users time to migrate
- Less breaking

**Cons:**
- More work (two phases)
- Keeps dead code longer

### Option C: Keep But Simplify

Make `generic` a simple alias:

```python
@property
def generic(self):
    """Alias for scrape_url. Prefer using client.scrape_url() directly."""
    return self._client  # Returns client, so generic.scrape_url() works
```

Wait, that doesn't work because `generic.url()` would become `client.url()`.

Actually, could use a proxy:

```python
class _GenericProxy:
    def __init__(self, client):
        self._client = client

    def url(self, *args, **kwargs):
        return self._client.scrape_url(*args, **kwargs)

    # Alias
    scrape_url = url
```

**Pros:**
- No breaking change
- Minimal code

**Cons:**
- Still maintaining wrapper code
- Confusing to have two ways

---

## Recommendation: Option A (Remove)

The `GenericScraper` class adds no value. It:
- Hides useful parameters
- Adds indirection
- Creates confusion about which method to use

### Migration Path

1. **Update all internal usages first** (tests, probe_tests, docs)
2. **Remove from SDK**
3. **Document in CHANGELOG** as breaking change

### Search & Replace Pattern

```
# Before
client.scrape_url(url)
client.scrape_url(url, country="US")
client.scrape_url(url, response_format="json")
await client.scrape_url(url)

# After
client.scrape_url(url)
client.scrape_url(url, country="US")
client.scrape_url(url, response_format="json")
await client.scrape_url(url)
```

---

## Side Issue: `url_async` Still Used

While analyzing, found many files still use `url_async` instead of `url`:

```
tests/e2e/test_client_e2e.py:110:        result = await client.scrape_url(...)
tests/readme.py:685:            results = await client.scrape_url(...)
tests/enes/web_unlocker.py: (multiple)
probe_tests/error_handling/*.py: (multiple)
probe_tests/async/*.py: (multiple)
```

These should be `url()` not `url_async()` per the naming convention fix.

---

## Files to Modify (Complete List)

### Core SDK
- [ ] `src/brightdata/api/scrape_service.py` - Remove GenericScraper class and generic property
- [ ] `src/brightdata/sync_client.py` - Remove SyncGenericScraper class and generic property
- [ ] `src/brightdata/client.py` - Update docstrings
- [ ] `src/brightdata/cli/commands/scrape.py` - Update to use scrape_url()

### Tests
- [ ] `tests/e2e/test_client_e2e.py`
- [ ] `tests/readme.py`
- [ ] `tests/enes/web_unlocker.py`

### Probe Tests
- [ ] `probe_tests/test_05_web_unlocker.py`
- [ ] `probe_tests/test_05_web_unlocker_sync.py`
- [ ] `probe_tests/test_06_webscraper_linkedin.py`
- [ ] `probe_tests/test_06_webscraper_linkedin_sync.py`
- [ ] `probe_tests/test_working_zone.py`
- [ ] `probe_tests/test_manual_zones.py`
- [ ] `probe_tests/test_09_error_handling.py`
- [ ] `probe_tests/error_handling/test_02_network_errors.py`
- [ ] `probe_tests/error_handling/test_04_http_error_codes.py`
- [ ] `probe_tests/error_handling/test_05_malformed_responses.py`
- [ ] `probe_tests/error_handling/test_06_context_manager_errors.py`
- [ ] `probe_tests/async/test_01_connector_closed_error_web_unlocker.py`

### Documentation
- [ ] `README.md`
- [ ] `demo_sdk.py`
- [ ] `fixed.md`
- [ ] `critic.md`

---

## Summary

| Question | Answer |
|----------|--------|
| Is GenericScraper necessary? | **No** - just wraps scrape_url() |
| Does it add value? | **No** - hides useful parameters |
| Is it part of public API? | **Partially** - accessible but not exported |
| Should we remove it? | **Yes** |
| Is it safe to remove? | **Yes, with updates to ~42 files** |
| Breaking change? | **Yes, for users of client.scrape_url()** |
