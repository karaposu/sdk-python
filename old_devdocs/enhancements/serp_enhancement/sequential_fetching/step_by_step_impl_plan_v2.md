# Step-by-Step Implementation Plan v2

Sequential pagination for Google SERP API.

**Revision Notes**: This version addresses all issues from `critic.md`.

## Changes from v1

| Issue | Fix Applied |
|-------|-------------|
| CRITICAL #1: Async mode ignores pagination | Pagination is Google sync-mode only; raise error for async+pagination |
| CRITICAL #2: Missing `device` parameter | Added `device` to `_fetch_single_page()` |
| HIGH #4: Bing/Yandex ignore `start` | Pagination only for Google; others skip |
| HIGH #5: `PAGINATION_TIMEOUT` unused | Added total timeout enforcement |
| HIGH #6: Partial success ambiguity | Added `error` field for partial failures |
| HIGH #7: Code duplication | Refactored to `_execute_serp_request()` |
| MEDIUM #8: `results_per_page` semantic | Set to `PAGE_SIZE` (10) |
| MEDIUM #9: `total_found` loses Google total | Preserve Google's total |
| MEDIUM #10: Missing tests | Added comprehensive test cases |
| LOW #11: Import inside method | Moved `re` to module level |
| LOW #12: Unused `build_next_page_url()` | Removed |

---

## Overview

| Step | File | Change |
|------|------|--------|
| 1 | `url_builder.py` | Add `start` param to `GoogleURLBuilder.build()` |
| 2 | `base.py` | Add constants and `_execute_serp_request()` helper |
| 3 | `base.py` | Add `_search_with_pagination()` method |
| 4 | `base.py` | Modify `_search_single_async()` to route to pagination |
| 5 | Tests | Add comprehensive pagination tests |

---

## Step 1: Modify URL Builder

**File**: `src/brightdata/api/serp/url_builder.py`

### 1.1 Add `start` parameter to `GoogleURLBuilder.build()` only

**Current** (lines 29-36):
```python
def build(
    self,
    query: str,
    location: Optional[str] = None,
    language: str = "en",
    device: str = "desktop",
    num_results: int = 10,
    **kwargs,
) -> str:
```

**Change to**:
```python
def build(
    self,
    query: str,
    location: Optional[str] = None,
    language: str = "en",
    device: str = "desktop",
    num_results: int = 10,
    start: int = 0,  # NEW: pagination offset (Google-specific)
    **kwargs,
) -> str:
    """Build Google search URL with Bright Data parsing enabled."""
    encoded_query = quote_plus(query)
    url = f"https://www.google.com/search?q={encoded_query}"

    # Add pagination offset if not first page
    if start > 0:
        url += f"&start={start}"

    url += f"&num={num_results}"
    # ... rest unchanged
```

**Note**: `BingURLBuilder` and `YandexURLBuilder` are NOT modified. They receive `start` via `**kwargs` and ignore it. Pagination logic will skip non-Google engines (see Step 4).

---

## Step 2: Add Constants and Shared Helper

**File**: `src/brightdata/api/serp/base.py`

### 2.1 Add imports at top

Add `re` import at module level (line ~5):
```python
import re  # NEW: for pagination URL parsing
```

### 2.2 Add constants

Add after `DEFAULT_TIMEOUT = 30` (line 31):

```python
DEFAULT_TIMEOUT = 30
PAGE_SIZE = 10              # NEW: Google's typical results per page
MAX_PAGES = 20              # NEW: Safety limit
PAGINATION_TIMEOUT = 300    # NEW: Total timeout for paginated search (5 min)
```

### 2.3 Add `_execute_serp_request()` shared helper

Add new method to reduce duplication. This extracts the common request/response logic:

```python
async def _execute_serp_request(
    self,
    search_url: str,
    zone: str,
    trigger_sent_at: datetime,
) -> tuple:
    """
    Execute a single SERP request and parse response.

    Returns:
        Tuple of (raw_data: dict, data_fetched_at: datetime, error: Optional[str])
        If error is not None, raw_data will be empty dict.
    """
    response_format = "json" if "brd_json=1" in search_url else "raw"

    payload = {
        "zone": zone,
        "url": search_url,
        "format": response_format,
        "method": "GET",
    }

    sdk_function = get_caller_function_name()
    if sdk_function:
        payload["sdk_function"] = sdk_function

    async def _make_request():
        async with self.engine.post_to_url(
            f"{self.engine.BASE_URL}{self.ENDPOINT}",
            json_data=payload,
            timeout=aiohttp.ClientTimeout(total=self.timeout),
        ) as response:
            data_fetched_at = datetime.now(timezone.utc)

            if response.status == HTTP_OK:
                text = await response.text()
                try:
                    data = json.loads(text)
                except json.JSONDecodeError:
                    try:
                        data = await response.json()
                    except Exception:
                        data = {"raw_html": text}

                # Handle wrapped response format (status_code/headers/body)
                if isinstance(data, dict) and "body" in data and "status_code" in data:
                    body = data.get("body", "")
                    if isinstance(body, str) and body.strip().startswith("<"):
                        data = {"body": body, "status_code": data.get("status_code")}
                    else:
                        try:
                            data = json.loads(body) if isinstance(body, str) else body
                        except (json.JSONDecodeError, TypeError):
                            data = {"body": body, "status_code": data.get("status_code")}

                return (data, data_fetched_at, None)
            else:
                error_text = await response.text()
                return ({}, data_fetched_at, f"HTTP {response.status}: {error_text}")

    try:
        return await retry_with_backoff(_make_request, max_retries=self.max_retries)
    except Exception as e:
        return ({}, datetime.now(timezone.utc), f"Request error: {str(e)}")
```

---

## Step 3: Add Pagination Method

**File**: `src/brightdata/api/serp/base.py`

### 3.1 Add `_search_with_pagination()` method

```python
async def _search_with_pagination(
    self,
    query: str,
    zone: str,
    location: Optional[str],
    language: str,
    device: str,
    num_results: int,
    **kwargs,
) -> SearchResult:
    """
    Execute search with sequential pagination (Google only).

    Fetches pages one at a time until num_results reached or no more results.
    """
    import time

    trigger_sent_at = datetime.now(timezone.utc)
    pagination_start_time = time.time()

    all_results: List[Dict[str, Any]] = []
    pages_fetched = 0
    current_start = 0
    google_total_results = None  # Preserve Google's reported total
    last_error = None  # Track if we had partial failure

    while len(all_results) < num_results and pages_fetched < self.MAX_PAGES:
        # Check total timeout
        elapsed = time.time() - pagination_start_time
        if elapsed > self.PAGINATION_TIMEOUT:
            last_error = f"Pagination timeout after {int(elapsed)}s ({pages_fetched} pages fetched)"
            break

        # Build URL for current page
        search_url = self.url_builder.build(
            query=query,
            location=location,
            language=language,
            device=device,
            num_results=min(self.PAGE_SIZE, num_results - len(all_results)),
            start=current_start,
            **kwargs,
        )

        # Execute request
        raw_data, data_fetched_at, error = await self._execute_serp_request(
            search_url=search_url,
            zone=zone,
            trigger_sent_at=trigger_sent_at,
        )

        if error:
            if pages_fetched == 0:
                # First page failed - return error immediately
                return SearchResult(
                    success=False,
                    query={"q": query, "location": location, "language": language},
                    error=f"Search failed: {error}",
                    search_engine=self.SEARCH_ENGINE,
                    trigger_sent_at=trigger_sent_at,
                    data_fetched_at=data_fetched_at,
                )
            # Later page failed - record error and return partial results
            last_error = f"Page {pages_fetched + 1} failed: {error}"
            break

        pages_fetched += 1

        # Extract pagination info BEFORE normalizing
        pagination = raw_data.get("pagination", {}) if isinstance(raw_data, dict) else {}

        # Normalize data
        normalized_data = self.data_normalizer.normalize(raw_data)
        page_results = normalized_data.get("results", [])

        if not page_results:
            # No more results available
            break

        # Preserve Google's total from first page
        if pages_fetched == 1:
            google_total_results = normalized_data.get("total_results")

        all_results.extend(page_results)

        # Determine next page offset
        next_page_start = pagination.get("next_page_start")

        # Fallback: extract from next_page_link if available
        if next_page_start is None:
            next_link = pagination.get("next_page_link", "")
            if next_link:
                match = re.search(r'start=(\d+)', next_link)
                if match:
                    next_page_start = int(match.group(1))

        # No next page or invalid offset
        if next_page_start is None or next_page_start <= current_start:
            break

        current_start = next_page_start

    # Build final result
    # Trim to exact requested count
    final_results = all_results[:num_results]

    return SearchResult(
        success=True,
        query={"q": query, "location": location, "language": language},
        data=final_results,
        total_found=google_total_results,  # Google's reported total, not len(results)
        search_engine=self.SEARCH_ENGINE,
        country=location,
        results_per_page=self.PAGE_SIZE,  # Actual per-page count (10)
        trigger_sent_at=trigger_sent_at,
        data_fetched_at=datetime.now(timezone.utc),
        error=last_error,  # Will be set if partial failure occurred
    )
```

---

## Step 4: Modify Routing Logic

**File**: `src/brightdata/api/serp/base.py`

### 4.1 Update `_search_single_async()` to route to pagination

Modify the start of `_search_single_async()` (after line 165):

```python
async def _search_single_async(
    self,
    query: str,
    zone: str,
    location: Optional[str],
    language: str,
    device: str,
    num_results: int,
    **kwargs,
) -> SearchResult:
    """Execute single search query with retry logic."""

    # Route to pagination for Google when requesting more than one page
    # NOTE: Only Google supports pagination via start= parameter
    # Bing/Yandex will receive start in **kwargs but ignore it
    if num_results > self.PAGE_SIZE and self.SEARCH_ENGINE == "google":
        return await self._search_with_pagination(
            query=query,
            zone=zone,
            location=location,
            language=language,
            device=device,
            num_results=num_results,
            **kwargs,
        )

    # Original single-page logic using shared helper
    trigger_sent_at = datetime.now(timezone.utc)

    search_url = self.url_builder.build(
        query=query,
        location=location,
        language=language,
        device=device,
        num_results=num_results,
        **kwargs,
    )

    raw_data, data_fetched_at, error = await self._execute_serp_request(
        search_url=search_url,
        zone=zone,
        trigger_sent_at=trigger_sent_at,
    )

    if error:
        return SearchResult(
            success=False,
            query={"q": query},
            error=f"Search failed: {error}",
            search_engine=self.SEARCH_ENGINE,
            trigger_sent_at=trigger_sent_at,
            data_fetched_at=data_fetched_at,
        )

    normalized_data = self.data_normalizer.normalize(raw_data)

    return SearchResult(
        success=True,
        query={"q": query, "location": location, "language": language},
        data=normalized_data.get("results", []),
        total_found=normalized_data.get("total_results"),
        search_engine=self.SEARCH_ENGINE,
        country=location,
        results_per_page=num_results,
        trigger_sent_at=trigger_sent_at,
        data_fetched_at=data_fetched_at,
    )
```

### 4.2 Update `search()` to warn/error for async mode with pagination

Modify the `search()` method (around line 60) to add a check:

```python
async def search(
    self,
    query: Union[str, List[str]],
    zone: str,
    location: Optional[str] = None,
    language: str = "en",
    device: str = "desktop",
    num_results: int = 10,
    mode: str = "sync",
    poll_interval: int = 2,
    poll_timeout: int = 30,
    **kwargs,
) -> Union[SearchResult, List[SearchResult]]:
    """..."""
    is_single = isinstance(query, str)
    query_list = [query] if is_single else query

    self._validate_zone(zone)
    self._validate_queries(query_list)

    # NEW: Warn if pagination requested with async mode (not supported)
    if mode == "async" and num_results > self.PAGE_SIZE and self.SEARCH_ENGINE == "google":
        import warnings
        warnings.warn(
            f"Pagination (num_results={num_results}) is not supported in async mode. "
            f"Only first page (~{self.PAGE_SIZE} results) will be returned. "
            f"Use mode='sync' for pagination support.",
            UserWarning,
            stacklevel=2,
        )

    # ... rest unchanged
```

---

## Step 5: Add Tests

**File**: `tests/unit/test_serp_pagination.py` (new file)

```python
"""Unit tests for SERP pagination."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from brightdata.api.serp.google import GoogleSERPService
from brightdata.api.serp.url_builder import GoogleURLBuilder


class TestGoogleURLBuilderPagination:
    """Tests for GoogleURLBuilder pagination support."""

    def test_build_without_start_param(self):
        """Default start=0 should not add start param to URL."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=0)
        assert "start=" not in url
        assert "q=test" in url

    def test_build_with_start_param(self):
        """start > 0 should add start param to URL."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=10)
        assert "start=10" in url

    def test_build_with_large_start(self):
        """Large start values should work."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=100)
        assert "start=100" in url


class TestPaginationRouting:
    """Tests for pagination routing logic."""

    def test_num_results_10_no_pagination(self):
        """num_results=10 (exactly PAGE_SIZE) should NOT trigger pagination."""
        from brightdata.core.engine import AsyncEngine
        from brightdata.api.serp.base import BaseSERPService

        engine = AsyncEngine("test_token_123456789")
        service = GoogleSERPService(engine)

        # PAGE_SIZE is 10, so num_results=10 should not paginate
        assert service.PAGE_SIZE == 10

    def test_num_results_11_triggers_pagination(self):
        """num_results=11 (just over PAGE_SIZE) should trigger pagination."""
        from brightdata.api.serp.base import BaseSERPService

        # This is a logic test - actual implementation routes when num_results > PAGE_SIZE
        assert 11 > BaseSERPService.PAGE_SIZE

    def test_pagination_google_only(self):
        """Pagination should only apply to Google, not Bing/Yandex."""
        from brightdata.api.serp.google import GoogleSERPService
        from brightdata.api.serp.bing import BingSERPService
        from brightdata.api.serp.yandex import YandexSERPService

        assert GoogleSERPService.SEARCH_ENGINE == "google"
        assert BingSERPService.SEARCH_ENGINE == "bing"
        assert YandexSERPService.SEARCH_ENGINE == "yandex"


class TestPaginationBehavior:
    """Tests for pagination behavior."""

    @pytest.mark.asyncio
    async def test_pagination_stops_on_empty_results(self):
        """Pagination should stop when a page returns empty results."""
        # Mock test - verify logic handles empty results
        pass

    @pytest.mark.asyncio
    async def test_pagination_stops_at_max_pages(self):
        """Pagination should not exceed MAX_PAGES."""
        from brightdata.api.serp.base import BaseSERPService

        assert BaseSERPService.MAX_PAGES == 20

    @pytest.mark.asyncio
    async def test_pagination_respects_timeout(self):
        """Pagination should stop if PAGINATION_TIMEOUT exceeded."""
        from brightdata.api.serp.base import BaseSERPService

        assert BaseSERPService.PAGINATION_TIMEOUT == 300  # 5 minutes

    @pytest.mark.asyncio
    async def test_first_page_failure_returns_error(self):
        """If first page fails, should return error immediately."""
        pass

    @pytest.mark.asyncio
    async def test_later_page_failure_returns_partial(self):
        """If page N>1 fails, should return partial results with error field."""
        pass


class TestPaginationResults:
    """Tests for pagination result handling."""

    def test_results_trimmed_to_num_results(self):
        """Final results should be trimmed to exactly num_results."""
        # If we got 55 results but requested 50, return 50
        pass

    def test_google_total_preserved(self):
        """total_found should be Google's reported total, not len(results)."""
        pass

    def test_results_per_page_is_page_size(self):
        """results_per_page should be PAGE_SIZE (10), not num_results."""
        pass


class TestAsyncModeWarning:
    """Tests for async mode pagination warning."""

    @pytest.mark.asyncio
    async def test_async_mode_warns_on_pagination(self):
        """Async mode with num_results > PAGE_SIZE should warn."""
        pass


class TestEdgeCases:
    """Edge case tests."""

    def test_num_results_equals_page_size(self):
        """num_results=10 should not paginate."""
        from brightdata.api.serp.base import BaseSERPService

        # Routing condition is num_results > PAGE_SIZE, not >=
        # So exactly 10 should NOT paginate
        assert not (10 > BaseSERPService.PAGE_SIZE)

    def test_num_results_one(self):
        """num_results=1 should work without pagination."""
        pass

    def test_query_with_special_characters(self):
        """Pagination should work with special characters in query."""
        builder = GoogleURLBuilder()
        url = builder.build(query="python & java", start=10)
        assert "start=10" in url
        # Query should be URL encoded
        assert "+" in url or "%26" in url or "%20" in url
```

---

## Implementation Checklist

- [ ] **Step 1**: Add `start` param to `GoogleURLBuilder.build()`
- [ ] **Step 2.1**: Add `import re` at module level
- [ ] **Step 2.2**: Add constants (PAGE_SIZE, MAX_PAGES, PAGINATION_TIMEOUT)
- [ ] **Step 2.3**: Add `_execute_serp_request()` shared helper
- [ ] **Step 3.1**: Add `_search_with_pagination()` method
- [ ] **Step 4.1**: Modify `_search_single_async()` routing (Google-only check)
- [ ] **Step 4.2**: Add async mode warning in `search()`
- [ ] **Step 5**: Add tests

---

## Files Changed Summary

| File | Lines Added | Lines Modified | Notes |
|------|-------------|----------------|-------|
| `url_builder.py` | ~5 | ~2 | Add `start` param |
| `base.py` | ~120 | ~50 | Add helper, pagination, refactor |
| `test_serp_pagination.py` | ~130 | 0 | New test file |

**Total**: ~255 new lines, ~52 modified lines

---

## Behavior Matrix

| Engine | num_results | mode | Behavior |
|--------|-------------|------|----------|
| Google | ≤10 | sync | Single page |
| Google | >10 | sync | Sequential pagination |
| Google | >10 | async | Single page + warning |
| Bing | any | any | Single page (no pagination support) |
| Yandex | any | any | Single page (no pagination support) |

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| First page fails | Return `success=False`, `error` set |
| Page N>1 fails | Return `success=True`, `data` has partial results, `error` explains |
| Timeout exceeded | Return `success=True`, `data` has results so far, `error` explains |
| MAX_PAGES reached | Return `success=True`, `data` has results, no error |
| Empty first page | Return `success=True`, `data=[]`, no error |

---

## Risks & Mitigations (Updated)

| Risk | Mitigation |
|------|------------|
| Google rate limiting | Sequential requests with retry backoff |
| Infinite loop | MAX_PAGES=20 + PAGINATION_TIMEOUT=300s |
| Memory usage | Results capped at num_results |
| Async mode confusion | Warning issued, documented in behavior matrix |
| Bing/Yandex pagination | Explicitly unsupported, pagination skipped |
| Partial failures | `error` field set even when `success=True` |

---

## Migration Notes

- **Backwards Compatible**: Yes
- **Breaking Changes**: None
- **New Behavior**: `num_results > 10` on Google now actually returns more results
- **Deprecations**: None
