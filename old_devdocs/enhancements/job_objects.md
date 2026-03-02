# Job Objects: A Design Pattern for Async Operations

## Overview

Job Objects are a design pattern for representing asynchronous operations that have been triggered but not yet completed. Instead of returning a simple identifier (`response_id` or `snapshot_id`), we return a rich object that encapsulates the entire job context.

## The Problem Space

### Current SDK Architecture

The SDK currently has two types of operations:

1. **Synchronous (blocking)**
   ```python
   result = await client.scrape.amazon.products(url="...")
   # Returns: ScrapeResult (complete data)
   ```

2. **Asynchronous (manual control)**
   ```python
   snapshot_id = await client.scrape.amazon.products_trigger(url="...")
   # Returns: str (just an ID)

   # Later...
   status = await client.scrape.amazon.products_status(snapshot_id)
   result = await client.scrape.amazon.products_fetch(snapshot_id)
   ```

### The Lost Context Problem

When users trigger an async operation, they lose the context of what they asked for:

```python
# Trigger multiple operations
id1 = await client.search.google_trigger(query="python")
id2 = await client.search.google_trigger(query="javascript")
id3 = await client.search.google_trigger(query="rust")

# Later... which ID corresponds to which query?
# User must maintain their own mapping!
mapping = {
    id1: "python",
    id2: "javascript",
    id3: "rust"
}
```

## Job Objects as a Solution

### What is a Job Object?

A Job Object is a stateful object that represents an in-flight operation:

```python
job = await client.search.google_trigger(query="python", zone="z")

# Job contains:
# - job.response_id: The identifier from Bright Data
# - job.query: The original search query
# - job.zone: The zone used
# - job.status: Current status (pending/ready/error)
# - job.triggered_at: When it was triggered
# - job.fetch(): Method to get results
# - job.check_status(): Method to check status
```

### Why This Pattern Fits the SDK

#### 1. **Aligns with Existing Patterns**

The SDK already has similar patterns:

- `ScrapeResult`: Encapsulates completed operations
- `SearchResult`: Encapsulates search results
- `CrawlResult`: Encapsulates crawl results

Job Objects are simply the "pending" version of these result objects.

#### 2. **Maintains Context Automatically**

Users don't need to track what they asked for:

```python
# Without Job Objects
id1 = await trigger("python")
# User must remember: id1 = "python"

# With Job Objects
job1 = await trigger("python")
# Job remembers everything
print(job1.query)  # {"q": "python"}
```

#### 3. **Enables Natural Workflows**

Job Objects support intuitive async patterns:

```python
# Trigger multiple searches
jobs = []
for query in ["python", "javascript", "rust"]:
    job = await client.search.google_trigger(query=query, zone="z")
    jobs.append(job)

# Do other work...
await process_other_tasks()

# Collect results
for job in jobs:
    result = await job.fetch()
    print(f"Query '{job.query}' returned {len(result.data)} results")
```

#### 4. **Self-Contained State Management**

Each job manages its own state:

```python
job = await client.search.google_trigger(query="python", zone="z")

# Check status
if await job.is_ready():
    result = await job.fetch()
else:
    print(f"Job triggered at {job.triggered_at}, still pending...")
```

No global state store needed in the SDK.

## Benefits for Users

### 1. **Simplified Mental Model**

**Without Job Objects:**
```python
# User thinks: "I have 3 IDs, what do they mean?"
id1, id2, id3 = ...
```

**With Job Objects:**
```python
# User thinks: "I have 3 jobs, each knows what it's doing"
job1, job2, job3 = ...
```

### 2. **Self-Documenting Code**

```python
# Without Job Objects - unclear
response_id = await client.search.google_trigger(query="python", zone="z")
await asyncio.sleep(30)
result = await client.search.google_fetch(zone="z", response_id=response_id)

# With Job Objects - clear intent
job = await client.search.google_trigger(query="python", zone="z")
await asyncio.sleep(30)
result = await job.fetch()
```

### 3. **Easy Batch Operations**

```python
# Trigger batch
jobs = [
    await client.search.google_trigger(query=q, zone="z")
    for q in ["python", "javascript", "rust", "golang"]
]

# Wait for all
results = await asyncio.gather(*[job.fetch() for job in jobs])

# Results are automatically matched to queries
for job, result in zip(jobs, results):
    print(f"{job.query} → {result.data}")
```

### 4. **Natural Error Handling**

```python
job = await client.search.google_trigger(query="python", zone="z")

try:
    result = await job.fetch(timeout=60)
except TimeoutError:
    print(f"Job {job.response_id} timed out")
    print(f"Original query: {job.query}")  # Context preserved!
```

## Benefits for SDK Design

### 1. **Encapsulation**

Job Objects hide implementation details:

```python
# User doesn't need to know:
# - How polling works
# - How status is checked
# - What endpoints are called
# - How errors are handled

# They just do:
job = await trigger(...)
result = await job.fetch()
```

### 2. **Extensibility**

Easy to add new features without breaking API:

```python
class SERPSearchJob:
    # Current
    async def fetch(self) -> SearchResult:
        ...

    # Future additions (non-breaking)
    async def cancel(self) -> bool:
        ...

    async def stream_results(self) -> AsyncIterator[Dict]:
        ...

    def to_json(self) -> str:
        ...
```

### 3. **Consistent Interface**

All async operations can use the same pattern:

```python
# SERP
job = await client.search.google_trigger(...)
result = await job.fetch()

# Scraper
job = await client.scrape.linkedin.profiles_trigger(...)
result = await job.fetch()

# Crawler
job = await client.crawl.discover_trigger(...)
result = await job.fetch()

# Same pattern everywhere!
```

### 4. **Type Safety**

Job Objects provide strong typing:

```python
# Without Job Objects
response_id: str = await trigger(...)  # Just a string, could be anything

# With Job Objects
job: SERPSearchJob = await trigger(...)  # IDE knows the type
# IDE can autocomplete: job.fetch(), job.query, job.status, etc.
```

## Comparison with Alternatives

### Alternative 1: Return Just ID (Current Approach)

```python
response_id = await trigger(...)
result = await fetch(response_id)
```

**Pros:**
- Simple return value
- Minimal memory footprint

**Cons:**
- Lost context
- User must track metadata
- No type information
- Inconsistent with SDK's result objects

### Alternative 2: Internal State Store

```python
response_id = await trigger(...)
# SDK stores: _jobs[response_id] = {"query": ..., "zone": ...}

result = await fetch(response_id)
# SDK retrieves context from _jobs
```

**Pros:**
- User gets context back

**Cons:**
- Hidden global state
- Memory leaks if jobs not cleaned up
- Thread-safety concerns
- Hard to debug ("where is this state stored?")
- Doesn't work across SDK instances

### Alternative 3: Job Objects (Recommended)

```python
job = await trigger(...)
result = await job.fetch()
```

**Pros:**
- Explicit state (no hidden storage)
- Self-contained (no global state)
- Type-safe
- Extensible
- Consistent with SDK patterns

**Cons:**
- Slightly more complex return type
- User needs to hold reference to job

## Real-World Use Cases

### Use Case 1: Batch Processing

```python
async def process_search_batch(queries: List[str]) -> Dict[str, SearchResult]:
    """Process multiple searches and return results mapped by query."""

    # Trigger all
    jobs = [
        await client.search.google_trigger(query=q, zone="z")
        for q in queries
    ]

    # Wait for all
    results = await asyncio.gather(*[job.fetch() for job in jobs])

    # Return mapped results
    return {job.query["q"]: result for job, result in zip(jobs, results)}
```

### Use Case 2: Background Job Queue

```python
class JobQueue:
    def __init__(self):
        self.jobs = []

    async def add_search(self, query: str):
        """Add search to queue."""
        job = await client.search.google_trigger(query=query, zone="z")
        self.jobs.append(job)

    async def collect_ready(self) -> List[SearchResult]:
        """Collect all ready jobs."""
        results = []
        for job in self.jobs[:]:
            if await job.is_ready():
                results.append(await job.fetch())
                self.jobs.remove(job)
        return results
```

### Use Case 3: Progress Tracking UI

```python
async def search_with_progress(query: str):
    """Show progress of search operation."""

    job = await client.search.google_trigger(query=query, zone="z")

    print(f"Job {job.response_id} started at {job.triggered_at}")

    while True:
        status = await job.check_status()

        if status == "ready":
            result = await job.fetch()
            print(f"✓ Completed: {len(result.data)} results")
            return result
        elif status == "error":
            print(f"✗ Failed: {job.response_id}")
            return None
        else:
            elapsed = (datetime.now() - job.triggered_at).seconds
            print(f"⏳ Pending... ({elapsed}s elapsed)")
            await asyncio.sleep(2)
```

### Use Case 4: Retry Logic

```python
async def search_with_retry(query: str, max_retries: int = 3):
    """Search with automatic retry on failure."""

    for attempt in range(max_retries):
        job = await client.search.google_trigger(query=query, zone="z")

        try:
            result = await job.fetch(timeout=60)
            return result
        except TimeoutError:
            print(f"Attempt {attempt + 1} timed out")
            print(f"Job ID: {job.response_id}")
            print(f"Query: {job.query}")
            if attempt < max_retries - 1:
                print("Retrying...")
                await asyncio.sleep(5)

    raise Exception(f"Failed after {max_retries} attempts")
```

## Implementation Sketch

### Basic Job Object Structure

```python
@dataclass
class SERPSearchJob:
    """Represents an in-flight SERP search operation."""

    # Identity
    response_id: str

    # Context (preserved from trigger)
    query: Dict[str, Any]
    zone: str
    search_engine: str

    # Timing
    triggered_at: datetime

    # Internal (SDK maintains)
    _client: "BaseSERPService"
    _customer_id: str

    async def check_status(self) -> str:
        """Check current job status."""
        return await self._client._async_client.get_status(
            zone=self.zone,
            response_id=self.response_id
        )

    async def is_ready(self) -> bool:
        """Check if job is ready."""
        status = await self.check_status()
        return status == "ready"

    async def fetch(self, timeout: int = 60) -> SearchResult:
        """Fetch results (blocks until ready or timeout)."""
        start = datetime.now()

        while True:
            status = await self.check_status()

            if status == "ready":
                data = await self._client._async_client.fetch_result(
                    zone=self.zone,
                    response_id=self.response_id
                )

                # Context is preserved!
                return SearchResult(
                    success=True,
                    query=self.query,  # ← Available!
                    data=data,
                    search_engine=self.search_engine,
                    trigger_sent_at=self.triggered_at,
                    data_fetched_at=datetime.now(),
                )

            elif status == "error":
                return SearchResult(
                    success=False,
                    query=self.query,  # ← Available!
                    error="Job failed",
                    search_engine=self.search_engine,
                    trigger_sent_at=self.triggered_at,
                    data_fetched_at=datetime.now(),
                )

            # Check timeout
            if (datetime.now() - start).seconds > timeout:
                raise TimeoutError(f"Job {self.response_id} timed out")

            await asyncio.sleep(2)

    def __repr__(self) -> str:
        return f"<SERPSearchJob {self.response_id[:8]}... query={self.query}>"
```

## Migration Path

### Phase 1: Add Job Objects (Non-Breaking)

```python
# Old API still works
response_id = await client.search.google_trigger(query="python", zone="z")
result = await client.search.google_fetch(zone="z", response_id=response_id)

# New API available
job = await client.search.google_trigger(query="python", zone="z")  # Returns job now
result = await job.fetch()  # New method
```

### Phase 2: Deprecate Old API

```python
# Warn users
@deprecated("Use job.fetch() instead")
async def google_fetch(self, zone: str, response_id: str):
    ...
```

### Phase 3: Remove Old API (Major Version)

```python
# Only Job Objects remain
job = await client.search.google_trigger(query="python", zone="z")
result = await job.fetch()
```

## Conclusion

Job Objects provide a **clean, intuitive, and extensible** way to handle asynchronous operations in the SDK. They:

1. **Preserve context** automatically (no user tracking needed)
2. **Align with existing patterns** (ScrapeResult, SearchResult, etc.)
3. **Simplify user code** (self-documenting, type-safe)
4. **Enable advanced patterns** (batch processing, queues, progress tracking)
5. **Avoid global state** (each job is self-contained)
6. **Support future growth** (easy to add features without breaking changes)

The pattern is **proven** in other SDKs (AWS Boto3, Google Cloud SDK, Stripe SDK) and fits naturally with Python's async/await model. For a modern SDK handling asynchronous operations, Job Objects are a **best practice** that improves both the developer experience and the SDK's maintainability.

## Appendix: Similar Patterns in Other SDKs

### AWS Boto3
```python
# Similar pattern with "Waiter" objects
waiter = client.get_waiter('instance_running')
waiter.wait(InstanceIds=['i-12345'])
```

### Google Cloud Tasks
```python
# Task objects represent async operations
task = tasks_client.create_task(parent, task)
# task.name, task.schedule_time, task.status_time
```

### Stripe SDK
```python
# PaymentIntent object represents async payment
intent = stripe.PaymentIntent.create(amount=1000, currency="usd")
# intent.id, intent.status, intent.amount
intent.confirm()  # Method on the object
```

### Celery (Task Queue)
```python
# AsyncResult object represents background task
result = add.delay(4, 4)
# result.id, result.state, result.ready()
result.get()  # Fetch result
```

All these successful SDKs use similar patterns to Job Objects for managing asynchronous operations.
