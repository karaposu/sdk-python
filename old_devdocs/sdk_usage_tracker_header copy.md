# SDK Usage Tracking

## Purpose

The Bright Data SDK includes usage tracking mechanisms that allow Bright Data to:

1. **Identify SDK requests** - Distinguish SDK requests from direct API calls
2. **Track SDK version adoption** - Know which versions are in use
3. **Monitor SDK function usage** - Understand which SDK methods are most used
4. **Debug and support** - Help troubleshoot issues by knowing the SDK version and function

This data helps Bright Data:
- Prioritize SDK development
- Identify deprecated version usage
- Understand usage patterns
- Provide better support

---

## Design Overview

The SDK uses **two tracking mechanisms**:

### 1. User-Agent Header (Global)
- Set once when the HTTP session is created
- Sent with **every** HTTP request
- Format: `brightdata-sdk/{version}`

### 2. sdk_function Query Parameter (Per-Operation)
- Passed as a query parameter to specific API endpoints
- Tracks which SDK method initiated the request
- Only used for Dataset API operations

---

## Implementation Details

### 1. User-Agent Header

**Location:** `src/brightdata/core/engine.py`

The User-Agent is set when creating the `aiohttp.ClientSession`:

```python
# src/brightdata/core/engine.py:89-97
self._session = aiohttp.ClientSession(
    connector=connector,
    timeout=self.timeout,
    headers={
        "Authorization": f"Bearer {self.bearer_token}",
        "Content-Type": "application/json",
        "User-Agent": "brightdata-sdk/2.0.0",  # <-- Tracking header
    },
)
```

**When it's added:** Once, when `AsyncEngine.__aenter__()` is called (entering async context).

**Scope:** All HTTP requests through the engine (GET, POST, DELETE, etc.)

**Request flow:**
```
BrightDataClient
    └── AsyncEngine (creates session with User-Agent)
        └── All HTTP methods inherit the header
            ├── post_to_url()
            ├── get_from_url()
            └── delete_from_url()
```

---

### 2. sdk_function Query Parameter

**Location:** `src/brightdata/utils/function_detection.py`

The SDK detects the calling function name using Python's `inspect` module:

```python
# src/brightdata/utils/function_detection.py:12-55
def get_caller_function_name(skip_frames: int = 1) -> Optional[str]:
    """
    Get the name of the calling function.

    Uses inspect.currentframe() to walk up the call stack and find
    the function name. This is useful for SDK monitoring where we need
    to track which SDK function is being called.
    """
    frame = inspect.currentframe()
    try:
        for _ in range(skip_frames + 1):
            if frame is None:
                return None
            frame = frame.f_back

        if frame is None:
            return None

        return frame.f_code.co_name
    finally:
        del frame  # Prevent reference cycles
```

**How it's used in scrapers:**

```python
# src/brightdata/scrapers/base.py:144-153
sdk_function = get_caller_function_name()

result = await self.workflow_executor.execute(
    payload=payload,
    dataset_id=self.DATASET_ID,
    poll_interval=poll_interval,
    poll_timeout=timeout,
    include_errors=include_errors,
    normalize_func=self.normalize_result,
    sdk_function=sdk_function,  # <-- Passed along
)
```

**How it's sent to the API:**

```python
# src/brightdata/scrapers/api_client.py:64-73
params = {
    "dataset_id": dataset_id,
    "include_errors": str(include_errors).lower(),
}

if sdk_function:
    params["sdk_function"] = sdk_function  # <-- Added to query params

async with self.engine.post_to_url(
    self.TRIGGER_URL, json_data=payload, params=params
) as response:
```

**Resulting API call:**
```
POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=xxx&include_errors=true&sdk_function=products
```

---

## What Gets Tracked

### User-Agent Header
| Aspect | Tracked? | Details |
|--------|----------|---------|
| SDK name | Yes | Always "brightdata-sdk" |
| SDK version | Yes | e.g., "2.1.0" |
| Operation type | No | Same for all requests |
| Python version | No | Not included |
| OS info | No | Not included |

### sdk_function Parameter
| Aspect | Tracked? | Details |
|--------|----------|---------|
| Function name | Yes | e.g., "products", "reviews", "profiles" |
| Used for | Dataset API only | Not for SERP or Web Unlocker |

---

## Coverage by API Type

| API | User-Agent | sdk_function |
|-----|------------|--------------|
| Dataset API (scrapers) | Yes | Yes |
| SERP API | Yes | Yes (in some methods) |
| Web Unlocker API | Yes | Yes (in scrape method) |
| Zone Management API | Yes | No |
| Account Info API | Yes | No |

---

## Analysis: Is This Design Good?

### What Works Well

1. **Low overhead** - User-Agent is set once, not per-request
2. **Non-intrusive** - Tracking doesn't affect request payloads
3. **Standard approach** - User-Agent is the industry standard for client identification
4. **Function detection is clever** - Using `inspect` to auto-detect function names means no manual tracking code needed in each method

### What Could Be Improved

1. **Inconsistent sdk_function coverage**
   - Only used for Dataset API, partially for SERP/Web Unlocker
   - Zone management and account APIs don't track function names
   - Creates incomplete picture of SDK usage

2. **User-Agent lacks context**
   - No Python version (useful for debugging compatibility issues)
   - No OS info (could help identify platform-specific issues)
   - Example of better format: `brightdata-sdk/2.1.0 (Python/3.11; Linux)`

3. **Version is hardcoded**
   ```python
   "User-Agent": "brightdata-sdk/2.0.0",  # Hardcoded string
   ```
   Should import from `_version.py`:
   ```python
   from .._version import __version__
   "User-Agent": f"brightdata-sdk/{__version__}",
   ```

4. **No request ID correlation**
   - Can't trace a specific request through logs
   - Adding a unique request ID header would help debugging

5. **sdk_function only captures immediate caller**
   - If user wraps SDK calls, tracking shows wrapper name, not user's intent
   - Could capture full call stack (with limits) for better context

### Recommendations

1. **Fix version hardcoding** - Import from `_version.py`
2. **Enhance User-Agent** - Add Python version and OS
3. **Standardize sdk_function** - Use it consistently across all API types
4. **Add request ID** - Generate UUID for each request for correlation
5. **Consider opt-out** - Some enterprise users may want to disable tracking

### Example Improved Implementation

```python
# Improved User-Agent
import platform
from .._version import __version__

user_agent = (
    f"brightdata-sdk/{__version__} "
    f"(Python/{platform.python_version()}; {platform.system()})"
)
# Result: "brightdata-sdk/2.1.0 (Python/3.11.0; Darwin)"

# With request ID
import uuid

headers = {
    "Authorization": f"Bearer {self.bearer_token}",
    "Content-Type": "application/json",
    "User-Agent": user_agent,
    "X-Request-ID": str(uuid.uuid4()),  # For correlation
}
```

---

## Summary

The current tracking design is **functional but incomplete**:

| Aspect | Rating | Notes |
|--------|--------|-------|
| User-Agent approach | Good | Industry standard |
| sdk_function idea | Good | Clever auto-detection |
| Implementation consistency | Needs work | Inconsistent coverage |
| Version management | Needs work | Hardcoded values |
| Debug-friendliness | Needs work | Missing request IDs |

The core concepts are sound, but the implementation has gaps that could be improved for better analytics and debugging capabilities.
