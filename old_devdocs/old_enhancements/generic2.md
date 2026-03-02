# Enhancement: Document Concurrent Operations Limitations

## Issue
When running multiple SDK operations concurrently (e.g., `list_zones()`, `get_account_info()`), users may encounter "Network error: Connector is closed" errors due to engine context conflicts.

## Current Behavior
- Sequential operations work fine
- Concurrent operations may fail with connector closed errors
- Each operation tries to manage its own engine context
- Context management is not thread-safe for concurrent operations

## Root Cause
The SDK's operations like `list_zones()` and `get_account_info()` internally manage their own engine contexts. When run concurrently:

1. Operation A starts, creates/enters engine context
2. Operation B starts, tries to use same engine
3. Operation A completes, closes its context
4. Operation B tries to use the now-closed connector
5. Result: "Connector is closed" error

## Affected Methods
- `client.list_zones()`
- `client.get_account_info()`
- `client.test_connection()`
- Any method that internally manages engine context

## Workarounds

### 1. Use Shared Engine Context (Recommended)
```python
async with client.engine:
    # All operations share the same context
    results = await asyncio.gather(
        client.list_zones(),
        client.get_account_info(),
        client.list_zones()
    )
```

### 2. Sequential Async Operations
```python
zones1 = await client.list_zones()
info = await client.get_account_info()
zones2 = await client.list_zones()
```

### 3. Separate Client Instances
```python
client1 = BrightDataClient()
client2 = BrightDataClient()

results = await asyncio.gather(
    client1.list_zones(),
    client2.get_account_info()
)
```

## Proposed Fix

### Option 1: Update Methods to Check for Active Context
Modify methods to detect if engine is already active and reuse it:

```python
async def list_zones(self):
    if self.engine._session is not None:
        # Engine is active, use existing context
        return await self._zone_manager.list_zones()
    else:
        # Create new context
        async with self.engine:
            return await self._zone_manager.list_zones()
```

### Option 2: Add Concurrent-Safe Methods
Add new methods designed for concurrent use:

```python
async def list_zones_concurrent(self):
    """Version safe for concurrent execution within shared engine context."""
    # Assumes engine context is already active
    return await self._zone_manager.list_zones()
```

### Option 3: Document the Limitation
Update docstrings to warn about concurrent usage:

```python
async def list_zones(self):
    """
    List all zones in the account.

    Warning: Not safe for concurrent execution with other operations.
    For concurrent use, wrap operations in a shared engine context:

        async with client.engine:
            results = await asyncio.gather(
                client.list_zones(),
                client.get_account_info()
            )
    """
```

## Testing Evidence

From `probe_tests/test_03_auto_zone_creation_async.py`:

Sequential execution: All operations succeed
```
Seq-1: 0.524s - 2 zones
Seq-2: 0.526s - 2 zones
Seq-3: 0.504s - 2 zones
Sequential total: 1.555s
```

Concurrent execution: One operation fails
```
Async-1: Error: Connector is closed
Async-2: 0.000s - 2 zones
Async-3: 0.517s - 2 zones
Concurrent total: 0.692s
```

## Priority
**High** - This affects anyone trying to use the SDK with async/await for performance optimization.

## Recommendation
1. **Short term**: Document the limitation in all affected methods
2. **Medium term**: Implement context detection to reuse active contexts
3. **Long term**: Redesign engine management for true concurrent safety
