# Naming Inconsistency Fix

## Problem

The SDK has inconsistent method naming across scrapers:

| Scraper | Current Async | Current Sync | Pattern |
|---------|---------------|--------------|---------|
| **Amazon (scraper)** | `products()` | N/A | async only |
| **Amazon (search)** | `products()` | N/A | async only |
| **LinkedIn** | `profiles_async()` | `profiles()` | `_async` suffix |
| **Instagram** | `profiles_async()` | `profiles()` | `_async` suffix |
| **Facebook** | `posts_by_profile_async()` | `posts_by_profile()` | `_async` suffix |
| **ChatGPT** | `prompt_async()` | `prompt()` | `_async` suffix |

This is confusing because:
1. Amazon uses `products()` for async, LinkedIn uses `profiles()` for SYNC
2. Users can't predict method names without checking docs
3. IDE autocomplete shows inconsistent patterns

---

## Target State

Since the SDK is **async-native**, async should be the default (no suffix):

```
method()       = async (default, no suffix)
method_sync()  = sync wrapper
```

| Scraper | Async Method | Sync Method |
|---------|--------------|-------------|
| Amazon (scraper) | `products()` | `products_sync()` |
| Amazon (search) | `products()` | `products_sync()` |
| LinkedIn | `profiles()` | `profiles_sync()` |
| Instagram | `profiles()` | `profiles_sync()` |
| Facebook | `posts_by_profile()` | `posts_by_profile_sync()` |
| ChatGPT | `prompt()` | `prompt_sync()` |

---

## Files to Update

### 1. LinkedIn Scraper (`scrapers/linkedin/scraper.py`)

**Current:**
```python
async def posts_async(self, url, timeout):
    ...

def posts(self, url, timeout):
    return asyncio.run(self.posts_async(url, timeout))
```

**Target:**
```python
async def posts(self, url, timeout):
    ...

def posts_sync(self, url, timeout):
    return asyncio.run(self.posts(url, timeout))
```

**Methods to rename:**
- `posts_async()` → `posts()`
- `posts()` → `posts_sync()`
- `jobs_async()` → `jobs()`
- `jobs()` → `jobs_sync()`
- `profiles_async()` → `profiles()`
- `profiles()` → `profiles_sync()`
- `companies_async()` → `companies()`
- `companies()` → `companies_sync()`

**Trigger/Status/Fetch methods:**
- `posts_trigger_async()` → `posts_trigger()`
- `posts_trigger()` → `posts_trigger_sync()`
- `posts_status_async()` → `posts_status()`
- `posts_status()` → `posts_status_sync()`
- `posts_fetch_async()` → `posts_fetch()`
- `posts_fetch()` → `posts_fetch_sync()`
- (same pattern for jobs, profiles, companies)

### 2. LinkedIn Search (`scrapers/linkedin/search.py`)

**Methods to rename:**
- `posts_async()` → `posts()`
- `profiles_async()` → `profiles()`
- `jobs_async()` → `jobs()`
- Add `posts_sync()`, `profiles_sync()`, `jobs_sync()`

### 3. Instagram Scraper (`scrapers/instagram/scraper.py`)

**Methods to rename:**
- `profiles_async()` → `profiles()`
- `profiles()` → `profiles_sync()`
- `posts_async()` → `posts()`
- `posts()` → `posts_sync()`
- `comments_async()` → `comments()`
- `comments()` → `comments_sync()`
- `reels_async()` → `reels()`
- `reels()` → `reels_sync()`

**Trigger/Status/Fetch methods:**
- Same pattern as LinkedIn

### 4. Instagram Search (`scrapers/instagram/search.py`)

**Methods to rename:**
- `posts_async()` → `posts()`
- `reels_async()` → `reels()`
- Add `posts_sync()`, `reels_sync()`

### 5. Facebook Scraper (`scrapers/facebook/scraper.py`)

**Methods to rename:**
- `posts_by_profile_async()` → `posts_by_profile()`
- `posts_by_profile()` → `posts_by_profile_sync()`
- `posts_by_group_async()` → `posts_by_group()`
- `posts_by_group()` → `posts_by_group_sync()`
- `posts_by_url_async()` → `posts_by_url()`
- `posts_by_url()` → `posts_by_url_sync()`
- `comments_async()` → `comments()`
- `comments()` → `comments_sync()`
- `reels_async()` → `reels()`
- `reels()` → `reels_sync()`

**Trigger/Status/Fetch methods:**
- Same pattern

### 6. ChatGPT Scraper (`scrapers/chatgpt/scraper.py`)

**Methods to rename:**
- `prompt_async()` → `prompt()`
- `prompt()` → `prompt_sync()`
- `prompts_async()` → `prompts()`
- `prompts()` → `prompts_sync()`

**Trigger/Status/Fetch methods:**
- Same pattern

### 7. ChatGPT Search (`scrapers/chatgpt/search.py`)

Check and align with pattern.

### 8. Amazon Scraper (`scrapers/amazon/scraper.py`)

**Already correct for async, need to add sync:**
- `products()` - already async ✓
- Add `products_sync()`
- `reviews()` - already async ✓
- Add `reviews_sync()`
- `sellers()` - already async ✓
- Add `sellers_sync()`

**Trigger/Status/Fetch - already correct:**
- `products_trigger()` - async ✓
- Add `products_trigger_sync()`
- etc.

### 9. Amazon Search (`scrapers/amazon/search.py`)

**Already correct for async, need to add sync:**
- `products()` - already async ✓
- Add `products_sync()`

### 10. SyncBrightDataClient (`sync_client.py`)

Update all method calls to use new names:
- `self._async.profiles_async()` → `self._async.profiles()`
- etc.

### 11. Base Scraper (`scrapers/base.py`)

Check `scrape()` and `scrape_async()` - may need to swap.

---

## Backward Compatibility

### Option A: Breaking Change (Recommended for v2.x)

Just rename everything. Users on v1.x can pin version.

**Pros:** Clean API, no confusion
**Cons:** Breaking change

### Option B: Deprecation Period

Keep old names as aliases with deprecation warnings:

```python
async def profiles(self, url, timeout):
    """Main async method."""
    ...

# Deprecated alias
async def profiles_async(self, url, timeout):
    """Deprecated: Use profiles() instead."""
    warnings.warn(
        "profiles_async() is deprecated, use profiles() instead",
        DeprecationWarning,
        stacklevel=2
    )
    return await self.profiles(url, timeout)

def profiles_sync(self, url, timeout):
    """Sync wrapper."""
    return asyncio.run(self.profiles(url, timeout))
```

**Pros:** Gradual migration
**Cons:** More code, confusing during transition

### Recommendation

Go with **Option A** (breaking change) since:
1. SDK is still in early development (v2.0.0)
2. Better to fix now than accumulate tech debt
3. Clear documentation of changes in CHANGELOG

---

## Implementation Order

### Phase 1: Core Scrapers
1. **Update Amazon scraper** - Add `_sync` methods (it's already correct for async)
2. **Update LinkedIn scraper** - Rename all methods
3. **Update Instagram scraper** - Rename all methods
4. **Update Facebook scraper** - Rename all methods
5. **Update ChatGPT scraper** - Rename all methods

### Phase 2: Search Scrapers
6. **Update LinkedIn search** - Rename methods
7. **Update Instagram search** - Rename methods
8. **Update Amazon search** - Add `_sync` methods
9. **Update ChatGPT search** - Rename methods

### Phase 3: Client Adapters
10. **Update SyncBrightDataClient** - Fix all method calls to use new names

### Phase 4: Probe Tests
11. **Update LinkedIn probe tests** - `test_06_webscraper_linkedin.py`, `test_06_webscraper_linkedin_sync.py`
12. **Update LinkedIn search probe tests** - `test_07_webscraper_linkedin_search.py`, `test_07_webscraper_linkedin_search_sync.py`
13. **Update Amazon probe tests** - `test_06_webscraper_amazon_sync.py`, `test_07_webscraper_amazon_search_sync.py`
14. **Update ChatGPT probe tests** - `test_08_chatgpt.py`, `test_08_chatgpt_sync.py`
15. **Review other probe tests** - `test_01_initialization.py`, `test_09_error_handling.py`, etc.

### Phase 5: Documentation
16. **Update README.md** - Examples with new method names
17. **Update fixed.md** - Examples with new method names
18. **Update docstrings** - All scraper docstrings

---

## Probe Tests to Update

All probe tests that call scraper methods need updating:

### LinkedIn Tests
| File | Changes Needed |
|------|----------------|
| `test_06_webscraper_linkedin.py` | `profiles_async()` → `profiles()`, `posts_async()` → `posts()` |
| `test_06_webscraper_linkedin_sync.py` | `profiles()` → `profiles_sync()`, `posts()` → `posts_sync()` |
| `test_07_webscraper_linkedin_search.py` | `jobs_async()` → `jobs()`, `profiles_async()` → `profiles()` |
| `test_07_webscraper_linkedin_search_sync.py` | `jobs()` → `jobs_sync()`, `profiles()` → `profiles_sync()` |

### Amazon Tests
| File | Changes Needed |
|------|----------------|
| `test_06_webscraper_amazon.py` | No change (already uses `products()` for async) |
| `test_06_webscraper_amazon_sync.py` | `products()` → `products_sync()` |
| `test_07_webscraper_amazon_search.py` | No change (already uses `products()` for async) |
| `test_07_webscraper_amazon_search_sync.py` | `products()` → `products_sync()` |

### ChatGPT Tests
| File | Changes Needed |
|------|----------------|
| `test_08_chatgpt.py` | `prompt_async()` → `prompt()` |
| `test_08_chatgpt_sync.py` | `prompt()` → `prompt_sync()` |

### Other Tests to Check
| File | Review For |
|------|------------|
| `test_01_initialization.py` | Any scraper method calls |
| `test_09_error_handling.py` | Any scraper method calls |
| `debug_amazon.py` | Amazon method calls |
| `test_trigger_only.py` | Trigger method naming |

### Search Pattern for Updates

```bash
# Find all async method calls that need renaming
grep -r "profiles_async\|posts_async\|jobs_async\|companies_async\|comments_async\|reels_async\|prompt_async\|prompts_async" probe_tests/

# Find all sync method calls that need _sync suffix
grep -r "\.profiles(\|\.posts(\|\.jobs(\|\.companies(\|\.comments(\|\.reels(\|\.prompt(\|\.prompts(" probe_tests/*_sync.py
```

---

## Testing Checklist

After changes, verify:

- [ ] `client.scrape.amazon.products(url)` is async
- [ ] `client.scrape.amazon.products_sync(url)` is sync
- [ ] `client.scrape.linkedin.profiles(url)` is async
- [ ] `client.scrape.linkedin.profiles_sync(url)` is sync
- [ ] `client.scrape.instagram.profiles(url)` is async
- [ ] `client.scrape.instagram.profiles_sync(url)` is sync
- [ ] `client.scrape.facebook.posts_by_profile(url)` is async
- [ ] `client.scrape.facebook.posts_by_profile_sync(url)` is sync
- [ ] `client.scrape.chatgpt.prompt(text)` is async
- [ ] `client.scrape.chatgpt.prompt_sync(text)` is sync
- [ ] `client.search.amazon.products(keyword)` is async
- [ ] `client.search.amazon.products_sync(keyword)` is sync
- [ ] `client.search.linkedin.jobs(keyword)` is async
- [ ] `client.search.linkedin.jobs_sync(keyword)` is sync
- [ ] SyncBrightDataClient works correctly with all methods
- [ ] All probe tests pass

---

## Summary

| Before | After |
|--------|-------|
| `profiles_async()` | `profiles()` |
| `profiles()` (sync) | `profiles_sync()` |
| Inconsistent | Consistent: async = default, sync = `_sync` suffix |
