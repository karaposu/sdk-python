# SERP Pagination Enhancement

## Issue Summary

**Reporter**: ycq0125
**SDK Version**: 2.1.1
**Date**: January 2026

## Problem Statement

When users request more than 10 results from Google SERP (e.g., `num_results=100`), the SDK currently does not properly paginate through multiple result pages. Google returns approximately 10 results per page, so fetching 100 results requires 10 separate page requests.

### Current Behavior

```python
result = await client.search.google(
    query="homeless",
    num_results=100,  # User expects 100 results
    language="en",
    location="United States"
)
# Actually returns only ~10 results (single page)
```

### Expected Behavior

The SDK should automatically paginate and aggregate results to return the requested number of results.

## Root Cause Analysis

1. **URL Builder Issue**: `GoogleURLBuilder.build()` uses `&num={num_results}` parameter, but Google caps this at ~10 results per page regardless of the value.

2. **No Pagination Logic**: `BaseSERPService._search_single_async()` makes a single request and returns. There's no logic to:
   - Parse pagination metadata from response
   - Calculate page offsets
   - Make additional requests for subsequent pages
   - Aggregate results from multiple pages

3. **Missing `start` Parameter**: Google pagination uses `&start=N` to offset results. The current URL builder doesn't support this parameter.

## User's Patch Summary

The user provided a working patch that:

1. **Adds `start` parameter to URL builder** - Enables page offset (`&start=10`, `&start=20`, etc.)

2. **Implements two pagination modes**:
   - **Sequential**: Follow `next_page_link` from response, one request at a time
   - **Concurrent**: Calculate all page offsets upfront, fire requests in parallel

3. **Adds `concurrent_pagination` flag** - New parameter to enable parallel fetching

4. **Auto-detects page step size** - Reads `pagination.next_page_start` from first page response to determine results-per-page (usually 10)

## Key Files to Modify

- `src/brightdata/api/serp/url_builder.py` - Add `start` parameter
- `src/brightdata/api/serp/base.py` - Add pagination logic
- `src/brightdata/api/serp/google.py` - Google-specific pagination handling
- `src/brightdata/api/search_service.py` - Expose new parameters

## Success Criteria

```python
# Should return ~100 organic results (or as many as available)
result = await client.search.google(
    query="homeless",
    num_results=100,
    language="en",
    location="United States"
)
assert len(result.data) >= 50  # At least 5 pages worth
```
