# Instagram Scraper Implementation - Initial Critique

## Overview

Critical analysis of `what_needs_to_be_created.md` cross-referenced with:
1. Instagram API documentation (1.md - 8.md)
2. SDK conventions (Amazon, LinkedIn scrapers)
3. Core SDK infrastructure (base.py, api_client.py)

---

## Critical Issues

### Issue #1: DatasetAPIClient Does NOT Support Discovery Query Params

**Severity: BLOCKER** ✅ **FIXED**

The current `DatasetAPIClient.trigger()` method only supports these query params:
- `dataset_id`
- `include_errors`
- `sdk_function`

**Discovery endpoints require additional params:**
```
?type=discover_new&discover_by=user_name
?type=discover_new&discover_by=url
?type=discover_new&discover_by=url_all_reels
```

**Current api_client.py (lines 64-73):**
```python
params = {
    "dataset_id": dataset_id,
    "include_errors": str(include_errors).lower(),
}

if sdk_function:
    params["sdk_function"] = sdk_function
```

**Problem:** No way to pass `type` or `discover_by` parameters.

**Solutions:**
1. Modify `DatasetAPIClient.trigger()` to accept `extra_params: Dict` argument
2. Create separate `trigger_discovery()` method in DatasetAPIClient
3. Override API call in `InstagramSearchScraper._execute_search()` bypassing DatasetAPIClient

**Recommendation:** Option 1 is cleanest - add `extra_params` to `trigger()`.

**Resolution:** Added `extra_params: Optional[Dict[str, str]] = None` parameter to `DatasetAPIClient.trigger()` in `api_client.py`.

---

### Issue #2: Empty String vs Omit for Optional Parameters

**Severity: MEDIUM** ✅ **FIXED**

Instagram API documentation shows empty strings for optional params:

```json
{"url":"https://www.instagram.com/espn","start_date":"","end_date":""}
```

**Questions:**
- Should SDK send `"start_date": ""` or omit the key entirely?
- Are empty strings required by the API?
- Does the API treat `""` differently from missing key?

**Current SDK convention (LinkedIn search.py):**
```python
if start_dates and i < len(start_dates):
    item["start_date"] = start_dates[i]
# Omits key if None
```

**Recommendation:** Follow existing SDK convention - omit None values. Test with API to verify behavior.

**Resolution:** Created `probe_tests/test_instagram_optional_params.py` to test API behavior. All three approaches work (omit, empty strings, partial). Safe to follow SDK convention and omit None values.

---

### Issue #3: Missing COST_PER_RECORD for Instagram

**Severity: LOW** ✅ **FIXED**

LinkedIn has `COST_PER_RECORD_LINKEDIN` in constants.py. Instagram doesn't have one defined.

**In plan:**
```python
MIN_POLL_TIMEOUT = DEFAULT_TIMEOUT_SHORT  # 180s like LinkedIn
```

**Missing:**
```python
COST_PER_RECORD = ???  # Not specified
```

**Recommendation:** Add `COST_PER_RECORD_INSTAGRAM` to constants.py or use default.

**Resolution:** `COST_PER_RECORD_INSTAGRAM = 0.002` already exists in `constants.py` (same as LinkedIn).

---

### Issue #4: reels() vs reels_all() - Unclear Distinction

**Severity: MEDIUM** ⏸️ **DEFERRED**

From documentation:
- `reels()` uses `discover_by=url` (6.md)
- `reels_all()` uses `discover_by=url_all_reels` (7.md)

**The plan says:**
- `reels()` - "Discover reels from profile"
- `reels_all()` - "Discover all reels from profile"

**But what's the actual difference?**

Looking at 6.md vs 7.md - both have same input structure and same output. The API difference is just the `discover_by` value.

**Possible interpretations:**
1. `url` = Recent reels only, `url_all_reels` = All reels including archived
2. `url` = Featured reels, `url_all_reels` = Complete reel history
3. They might be functionally identical?

**Recommendation:** Clarify with Bright Data what the actual difference is. Consider:
- Renaming to `reels()` and `reels_archived()` or `reels_all_history()`
- Adding docstring clarifying the difference
- Or combining into one method with a `include_all: bool` parameter

**Resolution:** DEFERRED - Implement both methods as documented (`reels()` with `discover_by=url` and `reels_all()` with `discover_by=url_all_reels`). Test and clarify difference later.

---

### Issue #5: Date Format Inconsistency

**Severity: MEDIUM** ✅ **FIXED**

**Instagram API uses:** `MM-DD-YYYY` (e.g., "01-01-2025")
**ISO standard:** `YYYY-MM-DD` (e.g., "2025-01-01")
**LinkedIn SDK uses:** `yyyy-mm-dd` (ISO format)

From 4.md:
```json
"start_date":"01-01-2025","end_date":"03-01-2025"
```

**Plan correctly notes this but doesn't propose handling:**

Options:
1. Accept only Instagram format, document in docstring
2. Accept ISO format, convert internally to Instagram format
3. Accept both formats, auto-detect and convert

**Recommendation:** Option 2 - Accept ISO format (consistent with rest of SDK), convert internally:
```python
def _format_date(self, date: str) -> str:
    """Convert YYYY-MM-DD to MM-DD-YYYY for Instagram API."""
    if "-" in date and len(date) == 10:
        parts = date.split("-")
        if len(parts[0]) == 4:  # ISO format
            return f"{parts[1]}-{parts[2]}-{parts[0]}"
    return date
```

**Resolution:** Added `validate_instagram_date()` function in `src/brightdata/utils/validation.py` to validate MM-DD-YYYY format. Instagram scraper will require users to pass Instagram's native format and validate it.

---

### Issue #6: posts_to_not_include Parameter Serialization

**Severity: LOW**

From 4.md:
```json
"posts_to_not_include":["3529568342229145484"]
```

**Plan shows:**
```python
posts_to_not_include: Optional[List[str]] = None
```

**Question:** How is this serialized when there are multiple items?

**Assumption:** It's a JSON array in the payload, which should work fine. But verify the API accepts empty list `[]` vs omitting the key.

---

### Issue #7: Method Naming Convention Mismatch

**Severity: LOW**

**LinkedIn uses:**
- `profiles()` - plural for URL-based extraction
- `profiles_sync()` - sync version

**Plan proposes same for Instagram:**
- `profiles()`, `posts()`, `reels()`, `comments()`

**But LinkedIn search uses:**
- `profiles(firstName, lastName)` - parameter-based
- `posts(profile_url, ...)` - parameter-based

**Naming collision risk:**
- `InstagramScraper.profiles(url)` - URL-based
- `InstagramSearchScraper.profiles(user_name)` - Discovery-based

**This is actually fine** - they're in different classes accessed via different paths:
- `client.scrape.instagram.profiles(url)`
- `client.search.instagram.profiles(user_name)`

No issue here, just noting for awareness.

---

### Issue #8: BaseWebScraper._trigger_scrape_async Uses Default Dataset ID

**Severity: MEDIUM** ✅ **FIXED**

Looking at base.py line 282-286:
```python
snapshot_id = await self.api_client.trigger(
    payload=payload,
    dataset_id=self.DATASET_ID,  # Uses class default
    include_errors=True,
    sdk_function=sdk_function,
)
```

**Problem:** For Instagram, different content types use different dataset IDs:
- Profiles: `gd_l1vikfch901nx3by4`
- Posts: `gd_lk5ns7kz21pck8jpis`
- Reels: `gd_lyclm20il4r5helnj`
- Comments: `gd_ltppn085pokosxh13`

**But `_trigger_scrape_async` always uses `self.DATASET_ID`.**

**Solution:** LinkedIn handles this by passing `dataset_id` parameter to internal methods:
```python
async def _scrape_urls(self, url, dataset_id, timeout):
    # Uses passed dataset_id, not self.DATASET_ID
```

**Plan should note:** Use `_scrape_urls()` pattern like LinkedIn, not raw `_trigger_scrape_async()`.

**Resolution:** Added optional `dataset_id: Optional[str] = None` parameter to `_trigger_scrape_async()` in `base.py`. Falls back to `self.DATASET_ID` if not provided (backwards compatible).

---

### Issue #9: Missing Input Field Variation

**Severity: MEDIUM**

From documentation, different endpoints use different input field names:

| Endpoint | Input Field |
|----------|-------------|
| Profiles by URL (1.md) | `url` |
| Profiles by username (2.md) | `user_name` |
| Posts by URL (3.md) | `url` |
| Posts discovery (4.md) | `url` (profile URL) |
| Reels by URL (5.md) | `url` |
| Reels discovery (6.md, 7.md) | `url` (profile URL) |
| Comments (8.md) | `url` |

**Note:** For Profiles discovery, the field is `user_name` (with underscore), not `username`.

**Plan correctly shows:**
```python
async def profiles(self, user_name: Union[str, List[str]], ...)
```

But this needs careful payload construction:
```python
payload = [{"user_name": name} for name in user_names]  # NOT "username"
```

---

### Issue #10: num_of_posts Parameter Naming

**Severity: LOW**

Instagram API uses `num_of_posts` (from 4.md, 7.md):
```json
{"url":"...","num_of_posts":10}
```

**Plan uses same naming (correct):**
```python
num_of_posts: Optional[int] = None
```

**LinkedIn uses different naming:**
- No equivalent parameter

**This is fine** - Instagram-specific parameter. Just noting the API uses unconventional naming (`num_of_posts` vs `max_posts` or `limit`).

---

## SDK Convention Mismatches

### Mismatch #1: Search Scraper Pattern

**Amazon/LinkedIn pattern:**
```python
class LinkedInSearchScraper:
    def __init__(self, bearer_token, engine=None):
        self.bearer_token = bearer_token
        self.engine = engine or AsyncEngine(bearer_token)
        self.api_client = DatasetAPIClient(self.engine)
        self.workflow_executor = WorkflowExecutor(...)
```

**Plan follows this correctly.** No issue.

---

### Mismatch #2: _execute_search Method

**LinkedIn has:**
```python
async def _execute_search(self, payload, dataset_id, timeout) -> ScrapeResult:
    sdk_function = get_caller_function_name()
    result = await self.workflow_executor.execute(...)
    return result
```

**Plan needs to note:** Instagram discovery needs to pass extra query params (`type`, `discover_by`) that workflow_executor/api_client don't currently support.

---

## Documentation Discrepancies

### Discrepancy #1: Profile URL Format Variations

Documentation shows different URL formats:
- `https://www.instagram.com/cats_of_world_/` (with trailing slash)
- `https://www.instagram.com/dogsofinstagram` (without trailing slash)
- `https://instagram.com/h2otamon` (without www)

**Recommendation:** SDK should normalize URLs or be tolerant of variations.

**Resolution:** NO ACTION NEEDED - The Bright Data API handles URL format variations internally. No SDK-side normalization required.

---

### Discrepancy #2: post_type Values

From 4.md, valid values appear to be:
- `"Post"` - Regular posts (capital P)
- `"Reel"` - Reels (capital R)

**But also seen empty string:**
```json
"post_type":""
```

**Recommendation:** Document valid values in docstring. Consider enum or literal type hint:
```python
post_type: Optional[Literal["Post", "Reel"]] = None
```

---

## Summary of Required Changes

### Before Implementation

1. ✅ **Modify DatasetAPIClient.trigger()** to accept `extra_params` for discovery endpoints - DONE
2. ⏸️ **Clarify reels() vs reels_all()** distinction with Bright Data - DEFERRED (implement both, test later)
3. ✅ **Decide on date format handling** - DONE (require MM-DD-YYYY, validate with `validate_instagram_date()`)
4. ✅ **Add COST_PER_RECORD_INSTAGRAM** to constants.py - ALREADY EXISTS

### During Implementation

1. ✅ **Use `_scrape_urls()` pattern** - DONE (`_trigger_scrape_async` now accepts optional `dataset_id`)
2. **Handle `user_name` field** (not `username`) for profile discovery - TODO
3. ✅ **Test empty string vs omit** for optional parameters - DONE (safe to omit)
4. ✅ **Normalize URL formats** - NOT NEEDED (API handles variations)

### Documentation Needs

1. **Clarify date format** in docstrings (accept ISO, converted internally)
2. **Document post_type values** ("Post", "Reel")
3. **Explain reels vs reels_all** difference

---

## Risk Assessment

| Issue | Severity | Blocks Implementation? | Status |
|-------|----------|----------------------|--------|
| DatasetAPIClient discovery params | HIGH | ~~YES~~ NO | ✅ FIXED |
| Empty string handling | MEDIUM | NO | ✅ FIXED (tested, safe to omit) |
| COST_PER_RECORD missing | LOW | NO | ✅ FIXED (already exists) |
| reels/reels_all confusion | MEDIUM | NO | ⏸️ DEFERRED |
| Date format | MEDIUM | NO | ✅ FIXED (validation added) |
| num_of_posts naming | LOW | NO | No change needed |
| URL normalization | LOW | NO | ✅ NOT NEEDED |
| _trigger_scrape_async dataset_id | MEDIUM | NO | ✅ FIXED |

---

## Recommended Implementation Order (Revised)

1. ✅ **First: Modify DatasetAPIClient** to support `extra_params` for discovery - DONE
2. **Then: Create `__init__.py`** - TODO
3. **Then: Create `scraper.py`** (URL-based, no discovery params needed) - TODO
4. **Then: Create `search.py`** (Discovery-based, uses modified DatasetAPIClient) - TODO
5. **Finally: Test both** URL-based and discovery methods - TODO

---

## Implementation Ready

All blocking issues have been resolved. The codebase is ready for Instagram scraper implementation:
- `api_client.py` supports `extra_params` for discovery endpoints
- `base.py` supports optional `dataset_id` for multi-dataset scrapers
- `validation.py` has `validate_instagram_date()` for date format validation
- `constants.py` has `COST_PER_RECORD_INSTAGRAM`
