# Web Unlocker Async Mode Implementation

## Executive Summary

Add async mode to Web Unlocker API using the same `AsyncUnblockerClient` pattern we built for SERP. This is a straightforward extension since all infrastructure already exists.


## Background

### What We Already Have

From SERP async implementation (v2.2.0):
- ✅ `AsyncUnblockerClient` - handles `/unblocker/req` + `/unblocker/get_result`
- ✅ Polling logic pattern
- ✅ Error handling
- ✅ Testing patterns
- ✅ Documentation structure

### What We Need to Add

- Update `WebUnlockerService` to support `mode` parameter
- Implement async polling methods
- Add tests
- Update documentation

## Current Web Unlocker Implementation

**File**: `src/brightdata/api/web_unlocker.py`

**Current behavior**: Sync only (uses `/request` endpoint)

```python
async def scrape_async(
    self,
    url: Union[str, List[str]],
    zone: str,
    country: str = "",
    response_format: str = "raw",
    method: str = "GET",
    timeout: Optional[int] = None,
) -> Union[ScrapeResult, List[ScrapeResult]]:
    """Scrape URL(s) using /request endpoint (blocks until ready)."""
```

## Proposed Changes

### Change 1: Add AsyncUnblockerClient to WebUnlockerService

**File**: `src/brightdata/api/web_unlocker.py`

**Line ~27**: Add import
```python
from .async_unblocker import AsyncUnblockerClient
```

**Line ~42**: In `__init__`
```python
def __init__(self, engine: AsyncEngine):
    self.engine = engine
    self.async_unblocker = AsyncUnblockerClient(engine)  # NEW
```

### Change 2: Add Mode Parameter

**Update `scrape_async()` signature:**

```python
async def scrape_async(
    self,
    url: Union[str, List[str]],
    zone: str,
    country: str = "",
    response_format: str = "raw",
    method: str = "GET",
    timeout: Optional[int] = None,
    mode: str = "sync",          # NEW
    poll_interval: int = 2,      # NEW
    poll_timeout: int = 30,      # NEW
) -> Union[ScrapeResult, List[ScrapeResult]]:
    """
    Scrape URL(s) using Web Unlocker API.

    Args:
        url: Single URL or list of URLs
        zone: Zone name
        country: Country code (optional)
        response_format: "raw" (HTML) or "json" (structured)
        method: HTTP method
        timeout: Request timeout
        mode: "sync" (default, blocking) or "async" (non-blocking with polling)
        poll_interval: Seconds between polls (async mode only)
        poll_timeout: Max wait time (async mode only)
    """
```

### Change 3: Route Based on Mode

**In `scrape_async()` method:**

```python
# Existing validation...
validate_zone_name(zone)
validate_response_format(response_format)
# ...

# NEW: Route based on mode
if isinstance(url, list):
    if mode == "async":
        return await self._scrape_multiple_async_unblocker(
            urls=url,
            zone=zone,
            country=country,
            response_format=response_format,
            method=method,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
    else:
        return await self._scrape_multiple_async(...)  # Existing
else:
    if mode == "async":
        return await self._scrape_single_async_unblocker(
            url=url,
            zone=zone,
            country=country,
            response_format=response_format,
            method=method,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
    else:
        return await self._scrape_single_async(...)  # Existing
```

### Change 4: Implement Async Unblocker Methods

**Add after `_scrape_multiple_async()` method (~line 228):**

```python
async def _scrape_single_async_unblocker(
    self,
    url: str,
    zone: str,
    country: str,
    response_format: str,
    method: str,
    poll_interval: int,
    poll_timeout: int,
) -> ScrapeResult:
    """
    Scrape single URL using async unblocker endpoints.

    This method:
    1. Triggers async request via /unblocker/req
    2. Polls /unblocker/get_result until ready or timeout
    3. Fetches and returns scraped content
    """
    trigger_sent_at = datetime.now(timezone.utc)

    # Trigger async request
    response_id = await self.async_unblocker.trigger(
        zone=zone,
        url=url,
        format=response_format,
        method=method,
        country=country.upper() if country else None
    )

    if not response_id:
        return ScrapeResult(
            success=False,
            url=url,
            status="error",
            error="Failed to trigger async request (no response_id received)",
            method="web_unlocker",
            trigger_sent_at=trigger_sent_at,
            data_fetched_at=datetime.now(timezone.utc),
        )

    # Poll until ready or timeout
    start_time = datetime.now(timezone.utc)

    while True:
        elapsed = (datetime.now(timezone.utc) - start_time).total_seconds()

        # Check timeout
        if elapsed > poll_timeout:
            return ScrapeResult(
                success=False,
                url=url,
                status="timeout",
                error=f"Polling timeout after {poll_timeout}s (response_id: {response_id})",
                method="web_unlocker",
                trigger_sent_at=trigger_sent_at,
                data_fetched_at=datetime.now(timezone.utc),
            )

        # Check status
        status = await self.async_unblocker.get_status(zone, response_id)

        if status == "ready":
            # Results ready - fetch them
            data_fetched_at = datetime.now(timezone.utc)

            try:
                data = await self.async_unblocker.fetch_result(zone, response_id)

                root_domain = extract_root_domain(url)
                html_char_size = len(data) if isinstance(data, str) else None

                return ScrapeResult(
                    success=True,
                    url=url,
                    status="ready",
                    data=data,
                    cost=None,
                    method="web_unlocker",
                    trigger_sent_at=trigger_sent_at,
                    data_fetched_at=data_fetched_at,
                    root_domain=root_domain,
                    html_char_size=html_char_size,
                )
            except Exception as e:
                return ScrapeResult(
                    success=False,
                    url=url,
                    status="error",
                    error=f"Failed to fetch results: {str(e)}",
                    method="web_unlocker",
                    trigger_sent_at=trigger_sent_at,
                    data_fetched_at=data_fetched_at,
                )

        elif status == "error":
            return ScrapeResult(
                success=False,
                url=url,
                status="error",
                error=f"Async request failed (response_id: {response_id})",
                method="web_unlocker",
                trigger_sent_at=trigger_sent_at,
                data_fetched_at=datetime.now(timezone.utc),
            )

        # Still pending - wait and retry
        await asyncio.sleep(poll_interval)


async def _scrape_multiple_async_unblocker(
    self,
    urls: List[str],
    zone: str,
    country: str,
    response_format: str,
    method: str,
    poll_interval: int,
    poll_timeout: int,
) -> List[ScrapeResult]:
    """Execute multiple scrapes using async unblocker."""
    tasks = [
        self._scrape_single_async_unblocker(
            url=url,
            zone=zone,
            country=country,
            response_format=response_format,
            method=method,
            poll_interval=poll_interval,
            poll_timeout=poll_timeout,
        )
        for url in urls
    ]

    # Execute all scrapes concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Process results, converting exceptions to ScrapeResult errors
    processed_results: List[ScrapeResult] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append(
                ScrapeResult(
                    success=False,
                    url=urls[i],
                    status="error",
                    error=f"Exception: {str(result)}",
                    trigger_sent_at=datetime.now(timezone.utc),
                    data_fetched_at=datetime.now(timezone.utc),
                )
            )
        else:
            processed_results.append(result)

    return processed_results
```

## Testing Plan

### Unit Tests

**File**: `tests/unit/test_web_unlocker_async.py` (NEW)

Reuse the pattern from `test_serp_async_mode.py`:

```python
"""Unit tests for Web Unlocker async mode."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from brightdata.api.web_unlocker import WebUnlockerService


class TestWebUnlockerAsyncMode:
    """Test Web Unlocker async mode."""

    @pytest.mark.asyncio
    async def test_scrape_sync_mode_explicit(self):
        """Test sync mode still works when explicitly specified."""
        # Mock engine and service
        # Verify sync mode still works
        pass

    @pytest.mark.asyncio
    async def test_scrape_async_mode(self):
        """Test async mode with polling."""
        # Mock AsyncUnblockerClient
        # Verify polling logic
        pass

    @pytest.mark.asyncio
    async def test_async_mode_timeout(self):
        """Test timeout handling."""
        pass
```

### Integration Tests

**File**: `tests/integration/test_web_unlocker_async_mode.py` (NEW)

```python
"""Integration tests for Web Unlocker async mode."""

@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_unlocker_sync_mode(async_client):
    """Test sync mode (backwards compatibility)."""
    result = await async_client.scrape_url(
        "https://example.com",
        zone=async_client.web_unlocker_zone,
        mode="sync"
    )
    assert result.success


@pytest.mark.integration
@pytest.mark.asyncio
async def test_web_unlocker_async_mode(async_client):
    """Test async mode."""
    result = await async_client.scrape_url(
        "https://example.com",
        zone=async_client.web_unlocker_zone,
        mode="async",
        poll_interval=2,
        poll_timeout=30
    )
    assert result.success
```

## Documentation Updates

### README.md

Add section under "Web Scraping":

```markdown
### Web Scraping with Async Mode

For non-blocking scraping:

```python
async with BrightDataClient() as client:
    result = await client.scrape_url(
        "https://example.com",
        mode="async",
        poll_interval=2,
        poll_timeout=30
    )
    print(result.data)
```

**Benefits:**
- Non-blocking requests
- Batch scraping optimization
- Same data structure as sync mode
```

### Update docs/async_mode_guide.md

Add Web Unlocker section:

```markdown
## Web Unlocker Async Mode

Async mode also works for Web Unlocker:

```python
# Sync mode (default)
result = await client.scrape_url("https://example.com")

# Async mode
result = await client.scrape_url(
    "https://example.com",
    mode="async",
    poll_interval=2,
    poll_timeout=30
)
```

### Basic Usage

```python
from brightdata import BrightDataClient

async with BrightDataClient() as client:
    # Sync mode (default)
    result = await client.scrape_url("https://example.com")

    # Async mode
    result = await client.scrape_url(
        "https://example.com",
        mode="async",
        poll_interval=2,
        poll_timeout=30
    )
```

### With Response Format

```python
# Get structured JSON instead of HTML
result = await client.scrape_url(
    "https://api.example.com/data",
    response_format="json",
    mode="async"
)
```
