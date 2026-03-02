# Implementation Approaches

## Approach 1: Concurrent Pagination (User's Patch)

Fetch page 1 first, then calculate all remaining page offsets and fire requests in parallel.

### Flow

```
1. Request page 1 (start=0)
2. Parse response, extract pagination.next_page_start to get step size
3. Calculate offsets: [step, step*2, step*3, ...] until num_results
4. Fire all remaining requests concurrently via asyncio.gather()
5. Aggregate all organic results
```

### Code Pattern

```python
async def _search_with_concurrent_pagination(self, query, num_results, ...):
    # Page 1 - must be sequential to get step size
    page1 = await self._fetch_page(query, start=0)
    step = page1.pagination.next_page_start or 10

    # Calculate remaining pages
    offsets = list(range(step, num_results, step))

    # Fire all in parallel
    tasks = [self._fetch_page(query, start=offset) for offset in offsets]
    pages = await asyncio.gather(*tasks, return_exceptions=True)

    # Aggregate
    return self._merge_results([page1] + pages)
```

### Pros

- **Fast**: All pages fetched in parallel, total time ~ single page time
- **Efficient**: Minimizes total wait time for large result sets
- **Predictable**: Known number of requests upfront

### Cons

- **Rate limiting risk**: Many concurrent requests may trigger rate limits or blocks
- **Wasted requests**: If Google has fewer results than requested, some requests return empty
- **Step size assumption**: Assumes consistent page size across all pages (usually true, but not guaranteed)
- **Memory spike**: All results held in memory simultaneously
- **Complexity**: More complex error handling (partial failures)

---

## Approach 2: Sequential Pagination (Follow Next Link)

Follow the `next_page_link` from each response until reaching desired count.

### Flow

```
1. Request page 1
2. Check: have enough results? -> done
3. Extract next_page_link from response
4. Request next page
5. Repeat steps 2-4
```

### Code Pattern

```python
async def _search_with_sequential_pagination(self, query, num_results, ...):
    results = []
    next_url = self._build_initial_url(query)

    while len(results) < num_results and next_url:
        page = await self._fetch_page(next_url)
        results.extend(page.organic)
        next_url = page.pagination.next_page_link

    return results[:num_results]
```

### Pros

- **Safe**: One request at a time, low rate limit risk
- **Accurate**: Stops immediately when no more results available
- **Simple**: Linear flow, easy to understand and debug
- **Memory efficient**: Can process/stream results page by page

### Cons

- **Slow**: Total time = N * single_page_time (sequential)
- **Latency accumulation**: Each request adds network latency
- **Timeout risk**: Long total time increases chance of timeout/failure

---

## Approach 3: Batched Concurrent (Hybrid)

Fetch pages in small batches (e.g., 3 at a time) to balance speed and safety.

### Flow

```
1. Request page 1, get step size
2. Calculate next 3 page offsets
3. Fire 3 requests concurrently
4. Wait for batch, check if more needed
5. Repeat with next batch
```

### Code Pattern

```python
BATCH_SIZE = 3

async def _search_with_batched_pagination(self, query, num_results, ...):
    results = []
    current_offset = 0
    step = 10

    while len(results) < num_results:
        # Build batch of offsets
        batch_offsets = [current_offset + i * step for i in range(BATCH_SIZE)]
        batch_offsets = [o for o in batch_offsets if o < num_results]

        if not batch_offsets:
            break

        # Fetch batch concurrently
        tasks = [self._fetch_page(query, start=o) for o in batch_offsets]
        pages = await asyncio.gather(*tasks)

        for page in pages:
            results.extend(page.organic)
            if not page.organic:  # No more results
                return results

        current_offset = batch_offsets[-1] + step

    return results[:num_results]
```

### Pros

- **Balanced**: Faster than sequential, safer than full concurrent
- **Adaptive**: Can stop early if results exhausted
- **Configurable**: Batch size can be tuned per use case
- **Moderate memory**: Only batch_size pages in memory at once

### Cons

- **Still some rate limit risk**: 3 concurrent requests might still trigger limits
- **Complexity**: More complex than either pure approach
- **Suboptimal in both directions**: Not as fast as full concurrent, not as safe as sequential

---

## Approach 4: Automatic Mode Selection

Let the SDK choose the best strategy based on `num_results`.

### Logic

```python
def _choose_pagination_strategy(num_results: int) -> str:
    if num_results <= 10:
        return "none"        # Single page
    elif num_results <= 30:
        return "sequential"  # 3 pages, sequential is fine
    elif num_results <= 100:
        return "batched"     # Medium range, use batches
    else:
        return "concurrent"  # Large requests, go parallel
```

### Pros

- **User-friendly**: No extra parameters needed
- **Optimized**: Best strategy for each use case
- **Backwards compatible**: Existing code works unchanged

### Cons

- **Magic behavior**: Users may not understand why behavior differs
- **Hard to debug**: Different code paths for different inputs
- **Thresholds are arbitrary**: 30 vs 100 cutoffs are guesses

---

## Comparison Table

| Approach | Speed | Safety | Complexity | Memory | Best For |
|----------|-------|--------|------------|--------|----------|
| Concurrent | Fast | Low | High | High | Large batches, low rate limit concern |
| Sequential | Slow | High | Low | Low | Small requests, strict rate limits |
| Batched | Medium | Medium | Medium | Medium | General use |
| Auto | Varies | Varies | High | Varies | Default behavior |

---

## Recommendation

**Primary**: Implement **Approach 1 (Concurrent)** with an opt-in flag (`pagination="concurrent"`).

**Default**: Keep **Approach 2 (Sequential)** as the default for backwards compatibility and safety.

**Rationale**:
1. Sequential is safer and sufficient for most use cases (10-30 results)
2. Power users who need 100+ results can opt into concurrent mode
3. Explicit flag makes behavior predictable and documented
4. Avoids magic/automatic selection that's hard to debug

### Suggested API

```python
# Default: sequential pagination (safe)
result = await client.search.google(query="test", num_results=50)

# Opt-in: concurrent pagination (fast)
result = await client.search.google(query="test", num_results=100, pagination="concurrent")

# Explicit sequential
result = await client.search.google(query="test", num_results=50, pagination="sequential")
```
