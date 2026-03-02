# Separating Operation Success from Scraping Success

## Problem

Currently, `result.success` indicates whether the **API operation** completed, not whether the **scrape itself** succeeded. This leads to confusing situations:

```python
result = await client.scrape.linkedin.posts(url=POST_URL)

print(f"Success: {result.success}")  # True
print(f"Status: {result.status}")    # ready

# But the actual data contains an error:
# {
#   "error": "Crawler error: Navigation failed...",
#   "error_code": "rate_limit"
# }
```

**User expectation:** `success=True` means "I got the data I wanted"
**Current behavior:** `success=True` means "The API call completed and returned something"

## Current Response Structure

```json
{
  "success": true,
  "status": "ready",
  "data": [
    {
      "timestamp": "2026-02-02T09:44:23.121Z",
      "input": {"url": "..."},
      "error": "Crawler error: Navigation failed...",
      "error_code": "rate_limit"
    }
  ]
}
```

The error is buried inside `data`, not surfaced at the top level.

## Proposed Solution

### Option 1: Two-Level Success Flags

Add a separate flag for scrape-level success:

```python
class ScrapeResult:
    success: bool          # API operation succeeded
    scrape_success: bool   # Actual scrape succeeded (no error in data)
    status: str
    data: Any
    error: Optional[str]   # Top-level error (API failure)
    scrape_error: Optional[str]  # Scrape-level error (from data)
    scrape_error_code: Optional[str]
```

Usage:
```python
result = await client.scrape.linkedin.posts(url=POST_URL)

if result.success and result.scrape_success:
    # Actually got the data
    print(result.data)
elif result.success and not result.scrape_success:
    # API worked but scrape failed
    print(f"Scrape failed: {result.scrape_error} ({result.scrape_error_code})")
else:
    # API itself failed
    print(f"API error: {result.error}")
```

### Option 2: Single Success with Error Extraction

Keep single `success` flag but make it reflect actual scrape success:

```python
# In workflow executor or result processing:
if data and isinstance(data, dict) and 'error' in data:
    return ScrapeResult(
        success=False,  # Mark as failed
        status="error",
        data=data,
        error=data.get('error'),
        error_code=data.get('error_code')
    )
```

This changes `success` to mean "I got usable data" rather than "API responded".

### Option 3: Result Helper Methods

Add helper methods to check scrape status:

```python
class ScrapeResult:
    def has_data(self) -> bool:
        """Returns True if result contains usable data (no errors)."""
        if not self.success:
            return False
        if isinstance(self.data, dict) and 'error' in self.data:
            return False
        if isinstance(self.data, list) and len(self.data) == 1:
            item = self.data[0]
            if isinstance(item, dict) and 'error' in item:
                return False
        return self.data is not None

    def get_scrape_error(self) -> Optional[str]:
        """Extract error message from data if present."""
        if isinstance(self.data, dict) and 'error' in self.data:
            return self.data['error']
        if isinstance(self.data, list) and len(self.data) == 1:
            item = self.data[0]
            if isinstance(item, dict) and 'error' in item:
                return item['error']
        return None
```

Usage:
```python
result = await client.scrape.linkedin.posts(url=POST_URL)

if result.has_data():
    print(result.data)
else:
    print(f"Error: {result.get_scrape_error() or result.error}")
```

## Common Error Codes from Bright Data

| error_code | Meaning |
|------------|---------|
| `rate_limit` | Too many requests, LinkedIn blocked |
| `dead_page` | Page doesn't exist or redirected |
| `login_required` | Content requires authentication |
| `timeout` | Scrape took too long |
| `blocked` | IP or account blocked |

## Recommendation

**Option 1 (Two-Level Flags)** is the clearest solution:
- Backwards compatible (existing `success` checks still work for API failures)
- Explicit distinction between operation and scrape success
- Easy to understand and document

## Implementation Notes

The error extraction logic should be in `ScrapeResult.from_response()` or in the workflow executor when building the result. Check for:

1. Single dict with `error` key
2. List with single item containing `error` key
3. List with multiple items where some have `error` keys (partial failure)

For batch operations, we may need:
```python
result.partial_success: bool  # Some items succeeded, some failed
result.failed_items: List[dict]  # Items that failed with their errors
```

## Impact

Files to modify:
- `src/brightdata/models.py` - ScrapeResult class
- `src/brightdata/scrapers/workflow.py` - Result building logic
- All notebooks - Update examples to check `scrape_success`
