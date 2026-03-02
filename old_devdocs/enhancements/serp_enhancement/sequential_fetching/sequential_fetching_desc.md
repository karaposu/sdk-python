# Sequential Pagination Approach

## Overview

Sequential pagination fetches SERP results one page at a time, following the `next_page_link` provided in each response until the desired `num_results` is reached or no more results are available.

## How It Works

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Request                             │
│         query="python tutorial", num_results=50                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Page 1 Request                             │
│         GET google.com/search?q=python+tutorial&brd_json=1      │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Page 1 Response                            │
│  {                                                              │
│    "organic": [...10 results...],                               │
│    "pagination": {                                              │
│      "next_page_link": "/search?q=python+tutorial&start=10"     │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Have 10 results │
                    │ Need 50 total   │
                    │ Continue? YES   │
                    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Page 2 Request                             │
│   GET google.com/search?q=python+tutorial&start=10&brd_json=1   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                           ... repeat ...
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Page 5 Response                            │
│  {                                                              │
│    "organic": [...10 results...],                               │
│    "pagination": {                                              │
│      "next_page_link": "/search?q=python+tutorial&start=50"     │
│    }                                                            │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │ Have 50 results │
                    │ Need 50 total   │
                    │ Continue? NO    │
                    └─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Return Aggregated Results                   │
│              SearchResult with 50 organic results               │
└─────────────────────────────────────────────────────────────────┘
```

## Algorithm

```python
async def search_with_pagination(query, num_results, ...):
    all_results = []
    current_url = build_initial_url(query)

    while len(all_results) < num_results:
        # 1. Fetch current page
        page_data = await fetch_page(current_url)

        # 2. Extract organic results
        organic = page_data.get("organic", [])

        # 3. No results? We're done
        if not organic:
            break

        # 4. Accumulate results
        all_results.extend(organic)

        # 5. Get next page link
        next_link = page_data.get("pagination", {}).get("next_page_link")

        # 6. No next page? We're done
        if not next_link:
            break

        # 7. Build next URL (ensure brd_json=1 is preserved)
        current_url = build_next_page_url(next_link)

    # Return up to num_results (may have slightly more from last page)
    return all_results[:num_results]
```

## Stop Conditions

The loop stops when ANY of these conditions is met:

| Condition | Reason |
|-----------|--------|
| `len(all_results) >= num_results` | Got enough results |
| `organic` is empty | No more results from Google |
| `next_page_link` is None | No more pages available |
| `loop_count > MAX_PAGES` | Safety limit (e.g., 20 pages max) |
| Timeout exceeded | Prevent infinite waiting |

## URL Building

### Initial URL

```python
def build_initial_url(query, language, location, ...):
    url = f"https://www.google.com/search?q={quote_plus(query)}"
    url += "&brd_json=1"  # Enable Bright Data JSON parsing
    url += f"&hl={language}"
    if location:
        url += f"&gl={location_code}"
    return url
```

### Next Page URL

The `next_page_link` from Google response is a relative path like:
```
/search?q=python+tutorial&start=10&sa=N&...
```

We need to:
1. Convert to absolute URL
2. Ensure `brd_json=1` is present (for Bright Data parsing)
3. Preserve language/location parameters

```python
def build_next_page_url(next_link, language, location):
    # Parse the relative URL
    parsed = urlparse(next_link)
    params = parse_qs(parsed.query)

    # Ensure Bright Data parsing is enabled
    params["brd_json"] = ["1"]

    # Ensure language/location persist
    if language:
        params["hl"] = [language]
    if location:
        params["gl"] = [location_code]

    # Rebuild URL
    new_query = urlencode(params, doseq=True)
    return f"https://www.google.com{parsed.path}?{new_query}"
```

## Response Structure

Google's parsed SERP response (via `brd_json=1`):

```json
{
  "organic": [
    {
      "title": "Python Tutorial - W3Schools",
      "link": "https://www.w3schools.com/python/",
      "snippet": "Learn Python programming...",
      "position": 1
    },
    ...
  ],
  "pagination": {
    "current_page": 1,
    "next_page_link": "/search?q=python+tutorial&start=10",
    "next_page_start": 10,
    "other_pages": {
      "2": "/search?q=python+tutorial&start=10",
      "3": "/search?q=python+tutorial&start=20"
    }
  },
  "search_information": {
    "total_results": 1250000000,
    "time_taken": 0.45
  }
}
```

## Result Aggregation

Final `SearchResult` combines data from all pages:

```python
SearchResult(
    success=True,
    query={"q": query, "location": location, "language": language},
    data=aggregated_organic_results,  # Combined from all pages
    total_found=len(aggregated_organic_results),
    search_engine="google",
    results_per_page=num_results,  # Requested amount
    trigger_sent_at=first_request_time,
    data_fetched_at=last_response_time,
)
```

## Safety Limits

```python
MAX_PAGES = 20          # Never fetch more than 20 pages
MAX_RESULTS = 200       # Cap total results
PAGE_TIMEOUT = 30       # Per-page timeout in seconds
TOTAL_TIMEOUT = 300     # Total operation timeout (5 min)
```

## Error Handling

| Error | Behavior |
|-------|----------|
| Single page fails | Return results collected so far + set `success=False` |
| Rate limited | Retry with backoff, then fail gracefully |
| Timeout | Return partial results with warning |
| Empty first page | Return empty results, `success=True` |

## Integration Points

### Files to Modify

1. **`url_builder.py`** - Add `build_next_page_url()` method to `GoogleURLBuilder`

2. **`base.py`** - Add `_search_with_pagination()` method to `BaseSERPService`

3. **`google.py`** - Override pagination handling if Google-specific logic needed

4. **`search_service.py`** - No changes needed (passes through to service)

### Minimal Code Changes

The key insight: most pagination logic goes in `BaseSERPService`, keeping engine-specific services thin.

```python
# base.py additions
class BaseSERPService:
    PAGE_SIZE = 10
    MAX_PAGES = 20

    async def _search_single_async(self, query, num_results, ...):
        # If single page is enough, use existing logic
        if num_results <= self.PAGE_SIZE:
            return await self._fetch_single_page(...)

        # Otherwise, paginate
        return await self._search_with_pagination(
            query=query,
            num_results=num_results,
            ...
        )

    async def _search_with_pagination(self, query, num_results, ...):
        # New method - sequential pagination logic
        ...
```

## Example Usage

```python
# User code - unchanged API
async with BrightDataClient() as client:
    # Request 50 results - SDK handles pagination internally
    result = await client.search.google(
        query="python tutorial",
        num_results=50,
        language="en",
        location="United States"
    )

    print(f"Got {len(result.data)} results")
    for item in result.data:
        print(f"  {item['position']}: {item['title']}")
```

Output:
```
Got 50 results
  1: Python Tutorial - W3Schools
  2: The Python Tutorial — Python 3.12 documentation
  ...
  50: Learn Python - Free Interactive Python Tutorial
```
