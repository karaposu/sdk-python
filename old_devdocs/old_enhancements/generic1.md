# Enhancement: Document test_connection() Async Behavior

## Issue
The `test_connection()` method in `src/brightdata/client.py` has undocumented behavior when used in concurrent async contexts.

## Current Behavior
- `test_connection()` works asynchronously in most scenarios
- It's only incompatible when mixed with other operations in a shared engine context
- For 99% of use cases, it works fine
- Just use it as a pre-flight check or standalone health check, not mixed with other concurrent operations

## Problem
The current docstring doesn't mention this limitation, which can cause confusion when developers encounter `False` returns in concurrent execution scenarios.

## Proposed Enhancement

### Update the docstring in `src/brightdata/client.py` (line 297-320)

Current docstring doesn't mention the concurrent execution limitation. Should be updated to include:

```python
async def test_connection(self) -> bool:
    """
    Test API connection and token validity.

    Makes a lightweight API call to verify:
    - Token is valid
    - API is reachable
    - Account is active

    Returns:
        True if connection successful, False otherwise (never raises exceptions)

    Note:
        This method never raises exceptions - it returns False for any errors
        (invalid token, network issues, etc.). This makes it safe for testing
        connectivity without exception handling.

        **Async Usage Note:**
        This method works perfectly in async contexts with one limitation:
        It may return False when called concurrently with other operations
        inside a shared `async with client.engine:` context. This is because
        test_connection() creates its own engine context internally.

        Best practices:
        - Use as a pre-flight check BEFORE other operations
        - Call it standalone for health checks
        - Avoid calling inside `async with client.engine:` blocks
        - If needed with other ops, call sequentially not concurrently

    Example:
        >>> # Good: Pre-flight check
        >>> if await client.test_connection():
        >>>     async with client.engine:
        >>>         zones = await client.list_zones()
        >>>
        >>> # Avoid: Concurrent inside shared context
        >>> async with client.engine:
        >>>     # This may return False due to context conflict
        >>>     results = await asyncio.gather(
        >>>         client.list_zones(),
        >>>         client.test_connection()  # May fail
        >>>     )
    """
```

## Implementation Details

The issue occurs because `test_connection()` at line 322 creates its own engine context:
```python
async with self.engine:  # Creates new context
```

When this is called while the engine is already in use by other concurrent operations, it causes a conflict and returns `False`.

## Testing Evidence

See `probe_tests/test_connection_async_demo.py` which demonstrates:
- ✅ Works: Standalone calls, sequential calls, concurrent test_connection() calls
- ✅ Works: As pre-flight check before other operations
- ❌ Fails: When called concurrently with other ops in shared engine context
- ❌ Fails: Inside existing `async with client.engine:` when other ops use that context

## Priority
**Medium** - This is a documentation issue that affects developer experience but doesn't break functionality. The method works correctly in most use cases.

## Alternative Solutions

1. **Code Change Option**: Modify `test_connection()` to detect if engine is already active and reuse it
2. **Documentation Only**: Just update the docstring (recommended as simpler and maintains backward compatibility)

## Recommendation
Update the docstring as proposed above. This is a documentation-only change that:
- Maintains backward compatibility
- Clearly explains the limitation
- Provides best practices
- Shows good and bad usage patterns
- Requires no code changes
