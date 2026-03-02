# Step-by-Step Implementation Plan

Sequential pagination for Google SERP API.

## Overview

| Step | File | Change |
|------|------|--------|
| 1 | `url_builder.py` | Add `start` param + `build_next_page_url()` method |
| 2 | `base.py` | Add `_search_with_pagination()` method |
| 3 | `base.py` | Modify `_search_single_async()` to route to pagination |
| 4 | `data_normalizer.py` | Preserve `pagination` in normalized output |
| 5 | Tests | Add pagination tests |

---

## Step 1: Modify URL Builder

**File**: `src/brightdata/api/serp/url_builder.py`

### 1.1 Add `start` parameter to `GoogleURLBuilder.build()`

**Current** (line 29-63):
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
    start: int = 0,  # NEW: pagination offset
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

### 1.2 Add `build_next_page_url()` method to `GoogleURLBuilder`

Add new method after `build()`:

```python
@staticmethod
def build_next_page_url(
    next_link: str,
    language: str,
    location: Optional[str],
) -> str:
    """
    Build absolute URL from Google's next_page_link.

    Ensures brd_json=1 and language/location params are preserved.

    Args:
        next_link: Relative URL from pagination.next_page_link
        language: Language code (hl parameter)
        location: Location string (will be converted to gl code)

    Returns:
        Absolute Google search URL with all required params
    """
    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed = urlparse(next_link)
    params = parse_qs(parsed.query)

    # Ensure Bright Data JSON parsing is enabled
    params["brd_json"] = ["1"]

    # Preserve language
    if language:
        params["hl"] = [language]

    # Preserve location (convert to code if needed)
    if location:
        location_code = LocationService.parse_location(location, LocationFormat.GOOGLE)
        if location_code:
            params["gl"] = [location_code]

    # Rebuild URL
    new_query = urlencode(params, doseq=True)
    return f"https://www.google.com{parsed.path}?{new_query}"
```

### 1.3 Update imports in `url_builder.py`

Add at top if not present:
```python
from urllib.parse import urlparse, parse_qs, urlencode
```

---

## Step 2: Add Pagination Method to Base Service

**File**: `src/brightdata/api/serp/base.py`

### 2.1 Add constants

Add after `DEFAULT_TIMEOUT = 30` (line 31):

```python
DEFAULT_TIMEOUT = 30
PAGE_SIZE = 10           # NEW: Google's typical results per page
MAX_PAGES = 20           # NEW: Safety limit
PAGINATION_TIMEOUT = 300 # NEW: Total timeout for paginated search (5 min)
```

### 2.2 Add `_search_with_pagination()` method

Add new method after `_search_single_async()` (after line 266):

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
    Execute search with sequential pagination.

    Fetches pages one at a time using next_page_link until
    num_results is reached or no more results available.
    """
    trigger_sent_at = datetime.now(timezone.utc)
    all_results: List[Dict[str, Any]] = []
    pages_fetched = 0
    current_start = 0

    # For aggregating extra data from first page
    first_page_extras = {}

    while len(all_results) < num_results and pages_fetched < self.MAX_PAGES:
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

        # Fetch page
        page_result = await self._fetch_single_page(
            search_url=search_url,
            zone=zone,
            query=query,
            location=location,
            language=language,
            trigger_sent_at=trigger_sent_at,
        )

        if not page_result.success:
            # If first page fails, return the error
            if pages_fetched == 0:
                return page_result
            # If later page fails, return what we have
            break

        pages_fetched += 1

        # Extract results from this page
        page_data = page_result.data or []
        if not page_data:
            # No more results
            break

        all_results.extend(page_data)

        # Capture extras from first page only
        if pages_fetched == 1:
            first_page_extras = page_result._raw_extras or {}

        # Check for next page
        next_start = page_result._next_page_start
        if next_start is None or next_start <= current_start:
            # No next page or invalid offset
            break

        current_start = next_start

    # Build final aggregated result
    return SearchResult(
        success=True,
        query={"q": query, "location": location, "language": language},
        data=all_results[:num_results],  # Trim to exact count
        total_found=len(all_results),
        search_engine=self.SEARCH_ENGINE,
        country=location,
        results_per_page=num_results,
        trigger_sent_at=trigger_sent_at,
        data_fetched_at=datetime.now(timezone.utc),
    )
```

### 2.3 Add `_fetch_single_page()` helper method

Add after `_search_with_pagination()`:

```python
async def _fetch_single_page(
    self,
    search_url: str,
    zone: str,
    query: str,
    location: Optional[str],
    language: str,
    trigger_sent_at: datetime,
) -> SearchResult:
    """
    Fetch a single SERP page.

    Returns SearchResult with additional _next_page_start and _raw_extras
    attributes for pagination handling.
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

                # Handle wrapped response format
                if isinstance(data, dict) and "body" in data and "status_code" in data:
                    body = data.get("body", "")
                    if isinstance(body, str) and body.strip().startswith("<"):
                        data = {"body": body, "status_code": data.get("status_code")}
                    else:
                        try:
                            data = json.loads(body) if isinstance(body, str) else body
                        except (json.JSONDecodeError, TypeError):
                            data = {"body": body, "status_code": data.get("status_code")}

                # Extract pagination info BEFORE normalizing
                pagination = data.get("pagination", {}) if isinstance(data, dict) else {}
                next_page_start = pagination.get("next_page_start")

                # Try to get next_page_start from next_page_link if not directly available
                if next_page_start is None:
                    next_link = pagination.get("next_page_link", "")
                    if next_link and "start=" in next_link:
                        try:
                            # Extract start value from URL
                            import re
                            match = re.search(r'start=(\d+)', next_link)
                            if match:
                                next_page_start = int(match.group(1))
                        except (ValueError, AttributeError):
                            pass

                # Normalize for results
                normalized_data = self.data_normalizer.normalize(data)

                result = SearchResult(
                    success=True,
                    query={"q": query, "location": location, "language": language},
                    data=normalized_data.get("results", []),
                    total_found=normalized_data.get("total_results"),
                    search_engine=self.SEARCH_ENGINE,
                    country=location,
                    results_per_page=self.PAGE_SIZE,
                    trigger_sent_at=trigger_sent_at,
                    data_fetched_at=data_fetched_at,
                )

                # Attach pagination info for internal use
                result._next_page_start = next_page_start
                result._raw_extras = {
                    k: v for k, v in normalized_data.items()
                    if k not in ("results", "total_results")
                }

                return result
            else:
                error_text = await response.text()
                return SearchResult(
                    success=False,
                    query={"q": query},
                    error=f"Search failed (HTTP {response.status}): {error_text}",
                    search_engine=self.SEARCH_ENGINE,
                    trigger_sent_at=trigger_sent_at,
                    data_fetched_at=data_fetched_at,
                )

    try:
        return await retry_with_backoff(_make_request, max_retries=self.max_retries)
    except Exception as e:
        return SearchResult(
            success=False,
            query={"q": query},
            error=f"Search error: {str(e)}",
            search_engine=self.SEARCH_ENGINE,
            trigger_sent_at=trigger_sent_at,
            data_fetched_at=datetime.now(timezone.utc),
        )
```

---

## Step 3: Route to Pagination in `_search_single_async()`

**File**: `src/brightdata/api/serp/base.py`

### 3.1 Modify `_search_single_async()` to check num_results

**Current** (line 156-166):
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
    trigger_sent_at = datetime.now(timezone.utc)
    # ... rest of method
```

**Change to**:
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
    # Route to pagination if requesting more than one page
    if num_results > self.PAGE_SIZE:
        return await self._search_with_pagination(
            query=query,
            zone=zone,
            location=location,
            language=language,
            device=device,
            num_results=num_results,
            **kwargs,
        )

    # Original single-page logic below...
    trigger_sent_at = datetime.now(timezone.utc)
    # ... rest unchanged
```

---

## Step 4: Preserve Pagination in Data Normalizer (Optional)

**File**: `src/brightdata/api/serp/data_normalizer.py`

This step is optional since we extract pagination before normalizing in Step 2.3.
However, if we want pagination data available in normalized output:

### 4.1 Add pagination to `NormalizedSERPData` type

**File**: `src/brightdata/types.py`

Add to `NormalizedSERPData` (line 289-299):
```python
class NormalizedSERPData(TypedDict, total=False):
    """Normalized SERP data structure."""

    results: List[SERPOrganicResult]
    total_results: NotRequired[int]
    featured_snippet: NotRequired[SERPFeaturedSnippet]
    knowledge_panel: NotRequired[SERPKnowledgePanel]
    people_also_ask: NotRequired[List[Dict[str, str]]]
    related_searches: NotRequired[List[str]]
    ads: NotRequired[List[Dict[str, Any]]]
    search_info: NotRequired[Dict[str, Any]]
    pagination: NotRequired[Dict[str, Any]]  # NEW
```

### 4.2 Preserve pagination in `GoogleDataNormalizer.normalize()`

**File**: `src/brightdata/api/serp/data_normalizer.py`

Add after line 96 (after `if "ads" in data:` block):
```python
if "pagination" in data:
    normalized["pagination"] = data["pagination"]
```

---

## Step 5: Add Tests

**File**: `tests/test_serp_pagination.py` (new file)

```python
"""Tests for SERP pagination."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from brightdata.api.serp.google import GoogleSERPService
from brightdata.api.serp.url_builder import GoogleURLBuilder


class TestGoogleURLBuilder:
    """Tests for GoogleURLBuilder pagination support."""

    def test_build_with_start_zero(self):
        """Start=0 should not add start param."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=0)
        assert "start=" not in url
        assert "q=test" in url

    def test_build_with_start_offset(self):
        """Start>0 should add start param."""
        builder = GoogleURLBuilder()
        url = builder.build(query="test", start=10)
        assert "start=10" in url

    def test_build_next_page_url(self):
        """Should build absolute URL with brd_json=1."""
        next_link = "/search?q=test&start=10&sa=N"
        url = GoogleURLBuilder.build_next_page_url(
            next_link=next_link,
            language="en",
            location="United States",
        )
        assert url.startswith("https://www.google.com")
        assert "brd_json=1" in url
        assert "start=10" in url
        assert "hl=en" in url
        assert "gl=us" in url


class TestPagination:
    """Tests for pagination logic."""

    @pytest.mark.asyncio
    async def test_single_page_no_pagination(self):
        """num_results <= PAGE_SIZE should not paginate."""
        # Mock setup...
        pass

    @pytest.mark.asyncio
    async def test_multi_page_pagination(self):
        """num_results > PAGE_SIZE should paginate."""
        # Mock setup...
        pass

    @pytest.mark.asyncio
    async def test_stops_when_no_more_results(self):
        """Should stop when organic results are empty."""
        pass

    @pytest.mark.asyncio
    async def test_stops_when_no_next_page(self):
        """Should stop when next_page_start is None."""
        pass

    @pytest.mark.asyncio
    async def test_respects_max_pages(self):
        """Should not exceed MAX_PAGES."""
        pass
```

---

## Implementation Checklist

- [ ] **Step 1.1**: Add `start` param to `GoogleURLBuilder.build()`
- [ ] **Step 1.2**: Add `build_next_page_url()` method
- [ ] **Step 1.3**: Update imports
- [ ] **Step 2.1**: Add constants (PAGE_SIZE, MAX_PAGES)
- [ ] **Step 2.2**: Add `_search_with_pagination()` method
- [ ] **Step 2.3**: Add `_fetch_single_page()` helper
- [ ] **Step 3.1**: Modify `_search_single_async()` routing
- [ ] **Step 4.1**: (Optional) Add pagination to types
- [ ] **Step 4.2**: (Optional) Preserve pagination in normalizer
- [ ] **Step 5**: Add tests

---

## Files Changed Summary

| File | Lines Added | Lines Modified |
|------|-------------|----------------|
| `url_builder.py` | ~40 | ~5 |
| `base.py` | ~150 | ~10 |
| `data_normalizer.py` | ~2 | 0 |
| `types.py` | ~1 | 0 |
| `test_serp_pagination.py` | ~80 | 0 (new file) |

**Total**: ~270 new lines, ~15 modified lines

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Google rate limiting | Sequential requests with retry backoff |
| Infinite loop | MAX_PAGES=20 safety limit |
| Memory usage | Results aggregated in list, capped at num_results |
| Breaking existing behavior | Only triggers when num_results > PAGE_SIZE |
| Response format changes | Extract pagination before normalize, fallback to regex |

---

## Rollout Plan

1. **Phase 1**: Implement in feature branch, test with mock responses
2. **Phase 2**: Integration test with real Bright Data API
3. **Phase 3**: Update documentation and examples
4. **Phase 4**: Release as part of next minor version (2.3.0)
