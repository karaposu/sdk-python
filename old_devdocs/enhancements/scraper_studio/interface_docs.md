# Scraper Studio SDK Interface Design

## Summary

Add `client.scraper_studio` namespace to support triggering and fetching results from user-created custom scrapers (built via Bright Data's AI Agent, IDE, or templates).

---

## Naming Convention Alignment

Follows the same pattern as existing SDK services:

| Pattern | Existing (e.g. LinkedIn) | Scraper Studio |
|---------|-------------------------|----------------|
| High-level (trigger+poll+return) | `posts(url=...)` | `run(collector=..., input=...)` |
| Trigger only | `posts_trigger(url=...)` | `trigger(collector=..., input=...)` |
| Check status | `posts_status(snapshot_id)` | `status(job_id)` |
| Fetch results | `posts_fetch(snapshot_id)` | `fetch(job_id)` |

Also consistent with `ScrapeJob` which has: `status()`, `wait()`, `fetch()`, `to_result()`.

---

## Access Pattern

```python
client.scraper_studio              # ScraperStudioService instance
client.scraper_studio.run(...)     # High-level: trigger + poll + return data
client.scraper_studio.trigger(...) # Trigger a scrape job, returns job object
client.scraper_studio.status(...)  # Check job status
client.scraper_studio.fetch(...)   # Fetch completed job results
```

---

## Client Integration

Follows the same lazy-loaded `@property` pattern as `scrape`, `search`, `datasets`:

```python
# client.py
from .api.scraper_studio_service import ScraperStudioService

class BrightDataClient:
    ...
    @property
    def scraper_studio(self) -> ScraperStudioService:
        if self._scraper_studio is None:
            self._scraper_studio = ScraperStudioService(self)
        return self._scraper_studio
```

Also wired in `SyncBrightDataClient` for sync usage.

---

## Methods

### `run()` - High-Level (trigger + poll + return)

Single method that handles the full workflow. Mirrors how `client.scrape.linkedin.posts(url=...)` works — trigger, poll, return data.

```python
# Single input
data = await client.scraper_studio.run(
    collector="c_mly0sa6x10hshxi8jb",
    input={"url": "https://www.sahibinden.com/ilan/.../detay"},
    timeout=180,
)

# Multiple inputs
data = await client.scraper_studio.run(
    collector="c_mly0sa6x10hshxi8jb",
    input=[
        {"url": "https://www.sahibinden.com/ilan/1"},
        {"url": "https://www.sahibinden.com/ilan/2"},
    ],
    timeout=300,
)

# Custom input fields (non-URL scrapers)
data = await client.scraper_studio.run(
    collector="c_abc123",
    input={"keyword": "laptop", "location": "US"},
)
```

**Behavior:**
- Internally uses `POST /dca/crawl` for single input, falls back to polling `GET /dca/get_result` if 202
- Internally uses `POST /dca/trigger` + polls `GET /dca/dataset` for multiple inputs
- Returns `List[Dict[str, Any]]` — the scraped records

**Signature:**

```python
async def run(
    self,
    collector: str,
    input: Union[Dict[str, Any], List[Dict[str, Any]]],
    timeout: int = 180,
    poll_interval: int = 10,
) -> List[Dict[str, Any]]:
```

---

### `trigger()` - Trigger Only

Starts a scrape job and returns a job object. Does not wait for results.

Mirrors: `posts_trigger()` in LinkedIn scraper.

```python
job = await client.scraper_studio.trigger(
    collector="c_mly0sa6x10hshxi8jb",
    input=[{"url": "https://example.com/1"}, {"url": "https://example.com/2"}],
)
print(job.job_id)      # "j_abc123"
print(job.start_eta)   # "2026-02-22T..."
```

**Signature:**

```python
async def trigger(
    self,
    collector: str,
    input: Union[Dict[str, Any], List[Dict[str, Any]]],
) -> ScraperStudioJob:
```

Maps to: `POST /dca/trigger`

---

### `status()` - Check Job Status

Check the status of a triggered job.

Mirrors: `posts_status()` in LinkedIn scraper, `job.status()` in ScrapeJob.

```python
info = await client.scraper_studio.status(job_id="j_abc123")
print(info.status)        # "done"
print(info.success_rate)  # 1.0
print(info.inputs)        # 1
print(info.lines)         # 60
print(info.job_time)      # 71459 (ms)
```

**Signature:**

```python
async def status(
    self,
    job_id: str,
) -> JobStatus:
```

Maps to: `GET /dca/log/{job_id}`

---

### `fetch()` - Fetch Results

Fetch the results of a completed job.

Mirrors: `posts_fetch()` in LinkedIn scraper, `job.fetch()` in ScrapeJob.

```python
data = await client.scraper_studio.fetch(job_id="j_abc123")
for record in data:
    print(record["title"], record["price"])
```

**Signature:**

```python
async def fetch(
    self,
    job_id: str,
) -> List[Dict[str, Any]]:
```

Maps to: `GET /dca/dataset?id={job_id}`

---

## ScraperStudioJob

Returned by `trigger()`. Wraps the job ID and provides convenience methods (same pattern as `ScrapeJob`).

```python
class ScraperStudioJob:
    """A triggered Scraper Studio job."""

    job_id: str
    start_eta: Optional[str] = None

    # Convenience methods (use the service internally)
    async def status(self) -> JobStatus:
        """Check job status."""

    async def wait(self, timeout: int = 300, poll_interval: int = 10) -> None:
        """Wait for job completion."""

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch results (call after wait)."""

    async def wait_and_fetch(self, timeout=300, poll_interval=10) -> List[Dict[str, Any]]:
        """Wait + fetch in one call."""
```

### JobStatus

Returned by `status()`.

```python
@dataclass
class JobStatus:
    id: str
    status: str           # "queued", "running", "done", "failed", "cancelled"
    collector: str
    inputs: int
    lines: int            # Records collected
    fails: int
    success_rate: float
    created: str
    started: Optional[str]
    finished: Optional[str]
    job_time: Optional[int]    # milliseconds
    queue_time: Optional[int]  # milliseconds
```

---

## API-to-SDK Endpoint Mapping

| SDK Method | HTTP | Endpoint | Returns |
|-----------|------|----------|---------|
| `run()` (single) | `POST` | `/dca/crawl` → `/dca/get_result` | `List[Dict]` |
| `run()` (batch) | `POST` | `/dca/trigger` → `/dca/dataset` | `List[Dict]` |
| `trigger()` | `POST` | `/dca/trigger` | `ScraperStudioJob` |
| `status()` | `GET` | `/dca/log/{job_id}` | `JobStatus` |
| `fetch()` | `GET` | `/dca/dataset?id={job_id}` | `List[Dict]` |

---

## File Structure

```
src/brightdata/
├── api/
│   └── scraper_studio_service.py    # ScraperStudioService class
├── scraper_studio/
│   ├── __init__.py
│   ├── models.py                    # ScraperStudioJob, JobStatus
│   └── client.py                    # Low-level HTTP calls
├── client.py                        # Add scraper_studio @property
└── sync_client.py                   # Add sync wrapper
```

---

## Sync Client Usage

```python
from brightdata import SyncBrightDataClient

with SyncBrightDataClient() as client:
    # High-level
    data = client.scraper_studio.run(
        collector="c_abc123",
        input={"url": "https://example.com/1"},
    )

    # Manual control
    job = client.scraper_studio.trigger(
        collector="c_abc123",
        input=[{"url": "https://example.com/1"}],
    )
    status = client.scraper_studio.status(job_id=job.job_id)
    data = client.scraper_studio.fetch(job_id=job.job_id)
```

---

## Error Handling

| Scenario | Behavior |
|----------|----------|
| Invalid collector ID | `APIError` with message from API |
| Job fails | `APIError("Job failed with status: failed")` |
| Timeout waiting for data | `TimeoutError` |
| Auth failure | `AuthenticationError` |
| Rate limit exceeded (>1000 batch) | `APIError` with rate limit message |

---

## Usage Examples

### Basic: Scrape a Single URL

```python
async with BrightDataClient() as client:
    data = await client.scraper_studio.run(
        collector="c_mly0sa6x10hshxi8jb",
        input={"url": "https://www.sahibinden.com/ilan/.../detay"},
    )
    print(data[0]["title"])
    print(data[0]["price"])
```

### Batch: Scrape Multiple URLs

```python
async with BrightDataClient() as client:
    urls = [
        {"url": "https://www.sahibinden.com/ilan/1/detay"},
        {"url": "https://www.sahibinden.com/ilan/2/detay"},
        {"url": "https://www.sahibinden.com/ilan/3/detay"},
    ]
    data = await client.scraper_studio.run(
        collector="c_mly0sa6x10hshxi8jb",
        input=urls,
        timeout=300,
    )
    for record in data:
        print(f"{record['title']}: {record['price']}")
```

### Manual Control: Trigger + Status + Fetch

```python
async with BrightDataClient() as client:
    # Trigger
    job = await client.scraper_studio.trigger(
        collector="c_mly0sa6x10hshxi8jb",
        input=[{"url": "https://example.com/1"}],
    )
    print(f"Job started: {job.job_id}")

    # Check status
    info = await client.scraper_studio.status(job_id=job.job_id)
    print(f"Status: {info.status}")

    # Or use job convenience methods
    data = await job.wait_and_fetch(timeout=300)

    # Or fetch directly when you know it's done
    data = await client.scraper_studio.fetch(job_id=job.job_id)
```
