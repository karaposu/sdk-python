# SERP API Endpoints Overview

## Two Ways to Get SERP Data

### Sync Endpoint: `/request`
**Blocks** until scraping is complete, then returns data immediately.

```bash
POST https://api.brightdata.com/request
Body: {"zone": "serp_zone", "url": "https://google.com/search?q=test"}
Response: Returns data after scraping completes (blocks connection)
```

### Async Endpoint: `/unblocker/req` + `/unblocker/get_result`
**Returns immediately**, poll separately for results.

```bash
# Step 1: Trigger
POST https://api.brightdata.com/unblocker/req?zone=serp_zone
Response: 200 OK, Headers: x-response-id: abc123

# Step 2: Poll (may need multiple attempts)
GET https://api.brightdata.com/unblocker/get_result?zone=serp_zone&response_id=abc123
Response: 202 (pending) or 200 (ready with data)
```

## Critical Discovery: The `format` Parameter

The response structure depends on the `format` parameter, **NOT the endpoint**:

### `format="json"` (Wrapped Response)
```python
{
  "status_code": 200,
  "headers": {...},
  "body": '{"general": {...}, "organic": [...]}'  # ← JSON string
}
```
Body is a **string** containing JSON that needs parsing.

### `format="raw"` (Direct Response)
```python
{
  "general": {...},
  "organic": [...],
  "navigation": {...},
  "top_ads": [...],
  ...
}
```
Data is **already parsed**, ready to use.

### No `format` parameter (Default)
Defaults to wrapped response (like `format="json"`).

## Key Insight

**Both sync and async endpoints return the SAME data structure** when using `format="raw"`.

The difference is **only timing**:
- Sync: Connection stays open until scraping completes
- Async: Connection closes immediately, poll for results

## Returned SERP Data Structure

When using `format="raw"` OR parsing the `body` from `format="json"`, you get:

```python
{
  "general": {
    "search_engine": "google",
    "query": "python programming",
    "language": "en-US",
    "mobile": false,
    "search_type": "text",
    "page_title": "python programming - Google Search",
    "timestamp": "2025-12-30T15:59:32.442Z",
    "results_cnt": 5040000000
  },

  "input": {
    "original_url": "https://www.google.com/search?q=python+programming",
    "q": "python programming"
  },

  "navigation": {
    "all": "All",
    "images": "Images",
    "videos": "Videos",
    "news": "News"
  },

  "organic": [
    {
      "rank": 1,
      "title": "Welcome to Python.org",
      "link": "https://www.python.org/",
      "display_link": "https://www.python.org",
      "description": "The official home of the Python Programming Language.",
      "snippet": "...",
      "rich_snippet": {...}
    },
    // ... more results
  ],

  "top_ads": [
    {
      "title": "Learn Python Online",
      "link": "https://...",
      "display_link": "...",
      "description": "..."
    }
  ],

  "bottom_ads": [...],

  "knowledge": {
    "title": "Python",
    "type": "Programming language",
    "description": "...",
    "image": "...",
    "attributes": {...}
  },

  "overview": {
    "title": "...",
    "snippet": "..."
  },

  "videos": [
    {
      "title": "...",
      "link": "...",
      "thumbnail": "...",
      "duration": "..."
    }
  ],

  "images": [
    {
      "title": "...",
      "link": "...",
      "thumbnail": "...",
      "source": "..."
    }
  ],

  "pagination": {
    "current_page": 1,
    "pages": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
    "next": "..."
  },

  "related": [
    "python programming tutorial",
    "python programming for beginners",
    "python programming examples"
  ]
}
```

## Common Fields Across Search Engines

### Always Present
- `general` - Search metadata (engine, query, language, etc.)
- `input` - Original query parameters
- `organic` - Main search results

### Usually Present
- `top_ads` - Sponsored results at top
- `bottom_ads` - Sponsored results at bottom
- `pagination` - Page navigation
- `related` - Related searches

### Sometimes Present (depends on query)
- `knowledge` - Knowledge panel (entities, people, places)
- `overview` - AI-generated overview/summary
- `videos` - Video results
- `images` - Image results
- `news` - News results
- `maps` - Map/local results
- `shopping` - Shopping results

## Important Notes

1. **Field availability varies** by search engine (Google, Bing, Yandex) and query type
2. **Use `brd_json=1`** in search URL for parsed results: `https://www.google.com/search?q=test&brd_json=1`
3. **Without `brd_json=1`**, you get raw HTML in the body (need to parse yourself)
4. **`format="raw"` is recommended** for direct data access (no extra parsing needed)

## SDK Usage Implications

### For Sync SERP Implementation
- Use `format="raw"` to get direct SERP data
- No need to parse `body` string
- Simpler data handling

### For Async SERP Implementation
- Response is always direct SERP data (no wrapping)
- Same structure as sync with `format="raw"`
- Data normalizer can handle both identically

### Current SDK Behavior

From `src/brightdata/api/web_unlocker.py:115-120`:
```python
payload = {
    "zone": zone,
    "url": url,
    "format": response_format,  # User can specify "json" or "raw"
    "method": method,
}
```

The SDK already supports both formats! Users can choose:
- `format="json"` - Get wrapped response (default)
- `format="raw"` - Get direct data

## Test Evidence

From `test_sync_format_comparison.py`:

```
format="json":  {status_code, headers, body: '...JSON string...'}
format="raw":   {general, organic, navigation, ...} ← Direct data!
```

Both sync and async can return the same direct structure.
