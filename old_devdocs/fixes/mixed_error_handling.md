# Mixed Error Handling Strategy Analysis

A deep dive into the inconsistent error handling patterns across the codebase, their implications, and potential solutions.

---

## Executive Summary

The codebase uses **two fundamentally different approaches** to communicate errors:

1. **Result Objects** (`success=False`) - Error information embedded in return value
2. **Exceptions** (`raise XxxError`) - Python's standard error propagation

These approaches are mixed inconsistently, making it difficult for users to write correct error handling code.

---

## The Two Error Philosophies

### Philosophy A: Result Objects (Fail-Safe)

```python
# Error returned in result object
result = await client.scrape.amazon.products(url)
if not result.success:
    print(f"Error: {result.error}")
    # Handle gracefully
```

**Characteristics**:
- Never throws (except for programmer errors)
- Caller must check `result.success`
- Errors are data, not exceptions
- Used in: Go, Rust, functional programming

**Pros**:
- Explicit error handling
- Easy to collect partial results
- No try/except noise
- Good for batch operations

**Cons**:
- Easy to forget checking `success`
- More verbose caller code
- Can't use with `await` chains easily

### Philosophy B: Exceptions (Fail-Fast)

```python
# Error raised as exception
try:
    result = await client.scrape.amazon.products(url)
except BrightDataError as e:
    print(f"Error: {e}")
    # Handle or propagate
```

**Characteristics**:
- Errors propagate automatically
- Must be caught or program crashes
- Pythonic approach
- Used in: Python, Java, most OOP languages

**Pros**:
- Can't be ignored
- Clean happy path code
- Works with async/await naturally
- Stack traces for debugging

**Cons**:
- Must wrap everything in try/except
- One failure aborts batch operations
- Performance overhead for exceptions

---

## Current State Analysis

### Layer-by-Layer Error Handling

| Layer | Strategy | Rationale |
|-------|----------|-----------|
| AsyncEngine | **Exceptions** | Network/auth errors are exceptional |
| DatasetAPIClient.trigger() | **Exceptions** | API failures are exceptional |
| DatasetAPIClient.get_status() | **Return value** | "error" is a valid status |
| DatasetAPIClient.fetch_result() | **Exceptions** | Fetch failures are exceptional |
| WorkflowExecutor | **Result objects** | Converts exceptions to results |
| poll_until_ready() | **Result objects** | Timeout/error are expected outcomes |
| ScrapeJob.wait() | **Exceptions** | Timeout/failure are exceptional |
| ScrapeJob.to_result() | **Result objects** | Catches exceptions, returns result |
| SERP Services | **Result objects** | HTTP errors become result.error |
| Web Unlocker | **Mixed** | Some raise, some return |
| Validation | **Exceptions** | Invalid input is exceptional |

### The Conversion Layer Problem

```
User calls scraper.products(url)
         │
         ▼
    ┌─────────────────────────────────────────────┐
    │  WorkflowExecutor.execute()                 │
    │  ┌─────────────────────────────────────┐    │
    │  │ try:                                │    │
    │  │   api_client.trigger()  ◄── raises  │    │
    │  │ except APIError:                    │    │
    │  │   return ScrapeResult(success=False)│◄── converts to result
    │  └─────────────────────────────────────┘    │
    └─────────────────────────────────────────────┘
         │
         ▼
    Returns ScrapeResult (never raises)
```

This conversion layer exists because:
- Lower layers (engine, API client) are reused by multiple callers
- Higher layers want a uniform result interface
- But it creates inconsistency

---

## Detailed Code Examples

### Example 1: DatasetAPIClient (Mixed)

```python
# api_client.py

async def trigger(...) -> Optional[str]:
    """
    Returns:
        snapshot_id if successful, None otherwise  # ← Return value for None
    Raises:
        APIError: If trigger request fails          # ← Exception for HTTP error
    """
    if response.status == HTTP_OK:
        return data.get("snapshot_id")  # Could return None!
    else:
        raise APIError(...)  # HTTP error → exception

async def get_status(self, snapshot_id: str) -> str:
    """
    Returns:
        Status string ("ready", "in_progress", "error", etc.)
        # Note: Returns "error" string, doesn't raise!
    """
    if response.status == HTTP_OK:
        return data.get("status", "unknown")
    else:
        return "error"  # HTTP error → return value

async def fetch_result(...) -> Any:
    """
    Raises:
        APIError: If fetch request fails  # ← Exception for HTTP error
    """
    if response.status == HTTP_OK:
        return await response.json()
    else:
        raise APIError(...)  # HTTP error → exception
```

**Inconsistency**: `trigger()` and `fetch_result()` raise on HTTP errors, but `get_status()` returns "error" string.

### Example 2: ScrapeJob (Mixed)

```python
# job.py

async def wait(self, timeout: int = 300, ...) -> str:
    """
    Returns:
        Final status ("ready" or "error")
    Raises:
        TimeoutError: If timeout is reached   # ← Exception
        APIError: If job fails                # ← Exception
    """
    if elapsed > timeout:
        raise TimeoutError(...)  # Timeout → exception

    if status == "error" or status == "failed":
        raise APIError(...)  # Job failure → exception

    return status  # Success → return value

async def to_result(self, ...) -> ScrapeResult:
    """
    Returns:
        ScrapeResult object  # Never raises!
    """
    try:
        await self.wait(...)  # wait() raises
        data = await self.fetch()
        return ScrapeResult(success=True, ...)
    except Exception as e:
        return ScrapeResult(success=False, error=str(e))  # Convert to result
```

**Inconsistency**: `wait()` raises exceptions, but `to_result()` catches them and returns result objects.

### Example 3: Web Unlocker (Mixed)

```python
# web_unlocker.py

async def _scrape_single_async(self, url: str, ...) -> ScrapeResult:
    try:
        # ... make request ...
        if response.status == HTTP_OK:
            return ScrapeResult(success=True, ...)
        else:
            return ScrapeResult(success=False, ...)  # HTTP error → result

    except Exception as e:
        if isinstance(e, (ValidationError, APIError)):
            raise  # ← Re-raise ValidationError and APIError!

        return ScrapeResult(success=False, ...)  # Other errors → result
```

**Inconsistency**: ValidationError and APIError propagate, but other errors become result objects.

### Example 4: SERP Base (Result-only)

```python
# serp/base.py

async def _search_single_async(self, query: str, ...) -> SearchResult:
    # ...
    if response.status == HTTP_OK:
        return SearchResult(success=True, ...)
    else:
        return SearchResult(success=False, error=...)  # HTTP error → result

    # Outer try/except:
    try:
        result = await retry_with_backoff(_make_request, ...)
        return result
    except Exception as e:
        return SearchResult(success=False, error=str(e))  # All errors → result
```

**Consistency** (within SERP): All errors become result objects. But:

```python
def _validate_queries(self, queries: List[str]) -> None:
    if not queries:
        raise ValidationError("Query list cannot be empty")  # ← Exception!
```

**Inconsistency**: Validation raises, but runtime errors return results.

---

## The Problem for Users

### Scenario 1: User Thinks Everything Returns Results

```python
# User assumes scrape always returns a result
result = await client.scrape.amazon.products(url)
if result.success:
    process(result.data)
else:
    log_error(result.error)
```

**Reality**: This mostly works, but:

```python
# This WILL raise, not return result:
result = await client.scrape.amazon.products(None)
# ValidationError: URL must be a non-empty string

# And this might raise:
job = await client.scrape.amazon.products_trigger(url)
await job.wait()  # Raises TimeoutError or APIError!
```

### Scenario 2: User Thinks Everything Raises

```python
# User wraps everything in try/except
try:
    result = await client.scrape.amazon.products(url)
    process(result.data)
except BrightDataError as e:
    log_error(e)
```

**Reality**: This catches validation errors, but:

```python
# Scrape errors are in result, not raised!
result = await client.scrape.amazon.products(invalid_url)
# No exception! But result.success = False, result.error = "..."

process(result.data)  # Oops! result.data is None
```

### Scenario 3: Batch Operations

```python
# User expects partial results
urls = ["url1", "url2", "url3"]
results = await client.scrape.amazon.products(urls)

for result in results:
    if result.success:
        process(result.data)
    else:
        log(f"Failed: {result.error}")
```

**Reality**: This works correctly because batch operations use `asyncio.gather(..., return_exceptions=True)` and convert exceptions to results.

But single operations behave differently:

```python
# Single operation might raise
result = await client.scrape.amazon.products("single_url")
# Might return result with success=False
# Or might raise ValidationError
```

---

## Classification of Errors

### Errors That Always Raise

| Error Type | Where | Why |
|------------|-------|-----|
| `ValidationError` | payloads.py, validation.py | Invalid input is programmer error |
| `AuthenticationError` | engine.py | No point continuing without auth |
| `TypeError`, `ValueError` | payloads.py | Malformed input |

### Errors That Sometimes Raise, Sometimes Return

| Error Condition | Raises | Returns |
|----------------|--------|---------|
| HTTP 4xx/5xx from trigger | ✅ APIError | |
| HTTP 4xx/5xx from status | | ✅ "error" string |
| HTTP 4xx/5xx from fetch | ✅ APIError | |
| HTTP 4xx/5xx from SERP | | ✅ SearchResult(success=False) |
| HTTP 4xx/5xx from Unlocker | | ✅ ScrapeResult(success=False) |
| Timeout in wait() | ✅ TimeoutError | |
| Timeout in poll_until_ready() | | ✅ ScrapeResult(status="timeout") |
| Network error | Depends on layer | |

### Errors That Always Return Results

| Error Type | Where |
|------------|-------|
| Polling timeout | WorkflowExecutor, poll_until_ready |
| Job status "error" | poll_until_ready |
| Any error in batch operation | Converted by asyncio.gather handler |

---

## Proposed Solutions

### Option A: All Exceptions (Pythonic)

Convert everything to exceptions. Result objects only contain data, never errors.

```python
# Proposed API
async def products(self, url: str) -> ScrapeResult:
    """
    Raises:
        ValidationError: If URL is invalid
        APIError: If API request fails
        TimeoutError: If operation times out
        NetworkError: If network issue occurs
    """
    # All errors raise, never return success=False
```

**User code**:
```python
try:
    result = await client.scrape.amazon.products(url)
    process(result.data)  # Safe - if we got here, it succeeded
except ValidationError:
    # Bad input
except TimeoutError:
    # Took too long
except APIError as e:
    # API failed
    log(f"Status: {e.status_code}, Message: {e.message}")
```

**Pros**:
- Pythonic
- Can't forget to check errors
- Clean happy path

**Cons**:
- Breaking change
- Batch operations need special handling
- More verbose for "expected" failures

### Option B: All Result Objects (Go-style)

Convert everything to result objects. Never raise from public API.

```python
# Proposed API
async def products(self, url: str) -> ScrapeResult:
    """
    Never raises. Check result.success for status.
    """
    if not url:
        return ScrapeResult(success=False, error="URL required")
    # All errors become result.success=False
```

**User code**:
```python
result = await client.scrape.amazon.products(url)
if not result.success:
    match result.error_type:  # New field
        case "validation":
            handle_bad_input()
        case "timeout":
            retry_later()
        case "api":
            log_api_error(result.error)
else:
    process(result.data)
```

**Pros**:
- Consistent
- Works well for batch
- No try/except needed

**Cons**:
- Not Pythonic
- Easy to forget checking success
- Loses stack traces
- Need error classification system

### Option C: Hybrid with Clear Boundaries (Recommended)

Define clear rules for when to raise vs return:

| Condition | Strategy | Rationale |
|-----------|----------|-----------|
| Invalid input (programmer error) | **Raise ValidationError** | Fail fast, fix the code |
| Auth failure | **Raise AuthenticationError** | No point continuing |
| Network unreachable | **Raise NetworkError** | Transient, retry at higher level |
| API returns error | **Return result.success=False** | Expected outcome, handle gracefully |
| Timeout | **Return result.status="timeout"** | Expected outcome, handle gracefully |
| Job failed | **Return result.success=False** | Expected outcome, handle gracefully |

**Key Principle**:
- **Exceptions** for things the programmer should fix or can't recover from locally
- **Result objects** for things the caller should handle as normal control flow

**User code**:
```python
try:
    result = await client.scrape.amazon.products(url)
    # If we get here, request was valid and sent successfully

    if result.success:
        process(result.data)
    elif result.status == "timeout":
        schedule_retry()
    else:
        log_failure(result.error)

except ValidationError as e:
    # Programmer error - fix the code
    raise
except AuthenticationError:
    # Get new token
    refresh_token()
except NetworkError:
    # Transient - retry
    await asyncio.sleep(5)
    retry()
```

---

## Migration Path

### Phase 1: Document Current Behavior

Add explicit docstrings stating what raises vs returns:

```python
async def products(self, url: str) -> ScrapeResult:
    """
    Scrape Amazon product URL.

    Args:
        url: Amazon product URL

    Returns:
        ScrapeResult with success=True and data, or
        ScrapeResult with success=False and error message

    Raises:
        ValidationError: If url is None, empty, or malformed

    Note:
        API errors, timeouts, and job failures are returned
        in the result object, not raised as exceptions.
    """
```

### Phase 2: Add Error Classification

Add `error_type` field to result objects:

```python
@dataclass
class ScrapeResult(BaseResult):
    # Existing fields...
    error_type: Optional[Literal[
        "validation",
        "authentication",
        "api",
        "timeout",
        "network",
        "unknown"
    ]] = None
```

### Phase 3: Standardize Lower Layers

Make DatasetAPIClient consistent:

```python
async def get_status(self, snapshot_id: str) -> str:
    """
    Get snapshot status.

    Returns:
        Status string ("ready", "in_progress", "error", etc.)

    Raises:
        APIError: If HTTP request fails (not if status is "error")
    """
    async with self.engine.get_from_url(url) as response:
        if response.status == HTTP_OK:
            return data.get("status", "unknown")
        else:
            # NOW raises instead of returning "error"
            raise APIError(f"Status check failed: HTTP {response.status}")
```

### Phase 4: Unify ScrapeJob

Make ScrapeJob consistent with WorkflowExecutor:

```python
async def wait(self, timeout: int = 300, ...) -> str:
    """
    Wait for job to complete.

    Returns:
        Final status ("ready", "error", "timeout")

    Note:
        Unlike previous version, does NOT raise TimeoutError.
        Check return value or use to_result() for full details.
    """
    # Never raises, returns status string
```

Or alternatively, make to_result() match wait():

```python
async def to_result(self, ...) -> ScrapeResult:
    """
    Wait for completion and return as ScrapeResult.

    Raises:
        TimeoutError: If timeout is reached
        APIError: If job fails

    Note:
        Unlike previous version, DOES raise on failure.
        Use wait() + fetch() manually if you want result objects.
    """
```

---

## Summary

The current mixed error handling creates cognitive load and potential bugs. The recommended approach:

1. **Exceptions** for:
   - Invalid input (ValidationError)
   - Auth failures (AuthenticationError)
   - Network issues (NetworkError)
   - Programmer errors (TypeError, ValueError)

2. **Result objects** for:
   - API errors (success=False, error_type="api")
   - Timeouts (success=False, error_type="timeout")
   - Job failures (success=False, error_type="job_failed")
   - Any "expected" failure mode

3. **Document everything** explicitly in docstrings

4. **Add error_type** field for programmatic error handling

This gives users predictable behavior:
- Catch exceptions for "fix your code" errors
- Check result.success for "handle this case" situations
