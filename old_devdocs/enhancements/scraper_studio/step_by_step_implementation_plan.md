# Scraper Studio - Step-by-Step Implementation Plan

> Reference: [interface_docs.md](./interface_docs.md) | [api_reference.md](./api_reference.md)

---

## Step 1: Create Models (`src/brightdata/scraper_studio/models.py`)

Define the data models used across the service.

### 1a. `JobStatus` dataclass

Returned by `status()`. Maps the response from `GET /dca/log/{job_id}`.

```python
@dataclass
class JobStatus:
    id: str
    status: str           # "queued", "running", "done", "failed", "cancelled"
    collector: str
    inputs: int
    lines: int
    fails: int
    success_rate: float
    created: str
    started: Optional[str]
    finished: Optional[str]
    job_time: Optional[int]
    queue_time: Optional[int]
```

Note: API returns mixed-case field names (`Id`, `Status`, `Collector`, `Job_time`, etc.). The `from_api_response(data)` classmethod should handle case-insensitive mapping.

> **Existing similar models:** `SnapshotStatus` (datasets) and `ScrapeJob` (web scraper) serve
> similar purposes but for different APIs. `JobStatus` has richer fields (success_rate, lines,
> fails, job_time, etc.) that are specific to Scraper Studio's `/dca/log` response.

### 1b. `ScraperStudioJob` class

Returned by `trigger()`. Same shape as `ScrapeJob` (status/wait/fetch/wait_and_fetch) but
wired to Scraper Studio endpoints and status values. **Own standalone class — no shared base
class with `ScrapeJob` for now.** Extracting a common `BaseJob` is a future refactor concern.

Key differences from `ScrapeJob`:

| | `ScrapeJob` | `ScraperStudioJob` |
|---|---|---|
| ID field | `snapshot_id` | `response_id` |
| API client | `DatasetAPIClient` (Web Scraper endpoints) | `ScraperStudioAPIClient` (DCA endpoints) |
| Poll mechanism | `get_status()` → check status string | `fetch()` → try to get data (200 vs 202) |
| `to_result()` | Returns `ScrapeResult` | Not needed (returns raw `List[Dict]`) |
| Extra fields | `platform_name`, `cost_per_record` | — |

```python
class ScraperStudioJob:
    def __init__(self, response_id, api_client):
        self.response_id = response_id
        self._api_client = api_client  # ScraperStudioAPIClient
        self._cached_data = None

    async def fetch(self) -> List[Dict[str, Any]]:
        """Fetch results via GET /dca/get_result?response_id=..."""

    async def wait_and_fetch(self, timeout=300, poll_interval=10) -> List[Dict[str, Any]]:
        """Poll fetch() until data arrives or timeout."""
```

> **Note:** Since `trigger_immediate` returns a `response_id` (not a `job_id`), the job object
> polls `fetch_immediate_result()` — not `get_status()`. Status checking via `/dca/log/{job_id}`
> is a separate concern (for jobs you already know the ID of). When batch support is added later,
> `ScraperStudioJob` will gain `job_id` and `status()`/`wait()` methods.

### 1c. `__init__.py`

Export both models.

### Files to create:
- `src/brightdata/scraper_studio/__init__.py`
- `src/brightdata/scraper_studio/models.py`

---

## Step 2: Create API Client (`src/brightdata/scraper_studio/client.py`)

Low-level HTTP client for Scraper Studio endpoints. Uses `AsyncEngine` for HTTP calls (same pattern as `DatasetAPIClient` and `AsyncUnblockerClient`).

Naming follows existing SDK convention: action-based names (`trigger`, `get_status`, `fetch_result`), no HTTP verb prefixes.

### Methods (implement now):

| Method | HTTP | Endpoint | Purpose |
|--------|------|----------|---------|
| `trigger_immediate(collector, input)` | `POST` | `/dca/trigger_immediate` | Trigger single-input scrape, returns `response_id` |
| `fetch_immediate_result(response_id)` | `GET` | `/dca/get_result?response_id=...` | Fetch real-time result data |
| `get_status(job_id)` | `GET` | `/dca/log/{job_id}` | Job status |

### Deferred (future — batch support):

| Method | HTTP | Endpoint | Purpose |
|--------|------|----------|---------|
| `trigger(collector, input)` | `POST` | `/dca/trigger` | Batch trigger, returns `collection_id` |
| `fetch_result(job_id)` | `GET` | `/dca/dataset?id={job_id}` | Fetch batch results |

### Skipped (redundant):

| Endpoint | Why skip |
|----------|----------|
| `POST /dca/crawl` | Blocking variant of `trigger_immediate` — falls back to same `response_id` + polling flow. SDK's `run()` handles the trigger+poll experience. |

All methods use `self.engine.post_to_url()` / `self.engine.get_from_url()` with absolute URLs (same pattern as `DatasetAPIClient`).

### Key behaviors:
- `trigger_immediate` → returns `response_id` string on 200
- `fetch_immediate_result` → returns `List[Dict]` on 200, raises `DataNotReadyError` on 202
- `get_status` → returns raw dict, parsed into `JobStatus` by the service layer

### Files to create:
- `src/brightdata/scraper_studio/client.py`

---

## Step 3: Create Service (`src/brightdata/api/scraper_studio_service.py`)

The main service class that users interact with via `client.scraper_studio`. Takes the `BrightDataClient` instance (same as `ScrapeService`, `SearchService`).

### Constructor:

```python
class ScraperStudioService:
    def __init__(self, client: "BrightDataClient"):
        self._client = client
        self._api = ScraperStudioAPIClient(client.engine)
```

### Methods to implement:

#### `run(collector, input, timeout=180, poll_interval=10)` → `List[Dict]`

High-level method. Logic:
1. Call `trigger_immediate(collector, input)` → get `response_id`
2. Poll `fetch_immediate_result(response_id)` until data arrives or timeout
3. Return `List[Dict[str, Any]]`

#### `trigger(collector, input)` → `ScraperStudioJob`

Calls `POST /dca/trigger_immediate`. Wraps response in `ScraperStudioJob(response_id=..., ...)`.

#### `status(job_id)` → `JobStatus`

Calls `GET /dca/log/{job_id}`. Parses response into `JobStatus` dataclass.

#### `fetch(response_id)` → `List[Dict]`

Calls `GET /dca/get_result?response_id=...`. Returns data on 200, raises `DataNotReadyError` on 202.

> **Deferred (future — batch support):** When batch is added, `trigger()` will also support
> `POST /dca/trigger` and `fetch()` will also support `GET /dca/dataset`.

### Files to create:
- `src/brightdata/api/scraper_studio_service.py`

---

## Step 4: Wire into `BrightDataClient` (`src/brightdata/client.py`)

Follow the exact same pattern as `scrape`, `search`, `crawler`, `datasets`.

### Changes:

1. **Import** (at top of file):
   ```python
   from .api.scraper_studio_service import ScraperStudioService
   ```

2. **`__init__`** — add private slot:
   ```python
   self._scraper_studio_service: Optional[ScraperStudioService] = None
   ```

3. **`@property`** — add lazy accessor:
   ```python
   @property
   def scraper_studio(self) -> ScraperStudioService:
       if self._scraper_studio_service is None:
           self._scraper_studio_service = ScraperStudioService(self)
       return self._scraper_studio_service
   ```

### Files to modify:
- `src/brightdata/client.py`

---

## Step 5: Wire into `SyncBrightDataClient` (`src/brightdata/sync_client.py`)

Add a sync wrapper class and wire it into the sync client.

### 5a. Create `SyncScraperStudioService` class

Follows the same pattern as `SyncAmazonScraper`, `SyncLinkedInScraper`, etc:

```python
class SyncScraperStudioService:
    def __init__(self, async_service: ScraperStudioService, loop: asyncio.AbstractEventLoop):
        self._async = async_service
        self._loop = loop

    def run(self, collector, input, timeout=180, poll_interval=10):
        return self._loop.run_until_complete(
            self._async.run(collector, input, timeout, poll_interval)
        )

    def trigger(self, collector, input):
        return self._loop.run_until_complete(
            self._async.trigger(collector, input)
        )

    def status(self, job_id):
        return self._loop.run_until_complete(
            self._async.status(job_id)
        )

    def fetch(self, response_id):
        return self._loop.run_until_complete(
            self._async.fetch(response_id)
        )
```

### 5b. Wire into `SyncBrightDataClient`

1. Add `self._scraper_studio = None` in `__init__`
2. Add `@property` with lazy init:
   ```python
   @property
   def scraper_studio(self) -> SyncScraperStudioService:
       if self._scraper_studio is None:
           self._scraper_studio = SyncScraperStudioService(
               self._async_client.scraper_studio, self._loop
           )
       return self._scraper_studio
   ```

### Files to modify:
- `src/brightdata/sync_client.py`

---

## Step 6: Update Exports (`src/brightdata/__init__.py`)

Add to public API:

```python
from .scraper_studio.models import ScraperStudioJob, JobStatus
from .api.scraper_studio_service import ScraperStudioService
```

Add to `__all__` (if used).

### Files to modify:
- `src/brightdata/__init__.py`

---

## Step 7: Add Constants (`src/brightdata/constants.py`)

Add Scraper Studio-specific defaults:

```python
# Scraper Studio
SCRAPER_STUDIO_DEFAULT_TIMEOUT = 180
SCRAPER_STUDIO_POLL_INTERVAL = 10
```

### Files to modify:
- `src/brightdata/constants.py`

---

## Step 8: Write Unit Tests (`tests/unit/test_scraper_studio.py`)

Follow the same testing pattern as `test_amazon.py` / `test_scrapers.py`.

### Test classes:

#### `TestScraperStudioModels`
- `test_job_status_from_api_response` — parse API JSON → `JobStatus` with correct fields
- `test_job_status_handles_mixed_case` — API returns `Id`, `Status`, `Collector` etc.
- `test_scraper_studio_job_attributes` — `job_id`, `start_eta` set correctly

#### `TestScraperStudioService`
- `test_service_has_run_method`
- `test_service_has_trigger_method`
- `test_service_has_status_method`
- `test_service_has_fetch_method`
- `test_run_method_signature` — params: `collector`, `input`, `timeout`, `poll_interval`
- `test_trigger_method_signature` — params: `collector`, `input`
- `test_status_method_signature` — params: `job_id`
- `test_fetch_method_signature` — params: `response_id`

#### `TestScraperStudioClientIntegration`
- `test_client_has_scraper_studio_property`
- `test_scraper_studio_returns_service_instance`
- `test_scraper_studio_lazy_loaded` — second access returns same instance

#### `TestSyncScraperStudioService`
- `test_sync_client_has_scraper_studio_property`
- `test_sync_service_has_all_methods` — `run`, `trigger`, `status`, `fetch`

### Files to create:
- `tests/unit/test_scraper_studio.py`

---

## Step 9: Verify — Run All Tests

```bash
cd /Users/ns/Desktop/projects/sdk-python
python -m pytest tests/unit/test_scraper_studio.py -v
python -m pytest tests/ -v   # ensure nothing else broke
```

---

## File Summary

### New files (5):
| File | Purpose |
|------|---------|
| `src/brightdata/scraper_studio/__init__.py` | Package init, export models |
| `src/brightdata/scraper_studio/models.py` | `ScraperStudioJob`, `JobStatus` |
| `src/brightdata/scraper_studio/client.py` | Low-level HTTP API client |
| `src/brightdata/api/scraper_studio_service.py` | High-level service (`run`, `trigger`, `status`, `fetch`) |
| `tests/unit/test_scraper_studio.py` | Unit tests |

### Modified files (4):
| File | Change |
|------|--------|
| `src/brightdata/client.py` | Add `scraper_studio` property + import |
| `src/brightdata/sync_client.py` | Add `SyncScraperStudioService` + property |
| `src/brightdata/__init__.py` | Export new classes |
| `src/brightdata/constants.py` | Add scraper studio constants |

### Total: 9 files (5 new + 4 modified)

---

## Implementation Order

```
Step 1  →  models.py          (no dependencies)
Step 2  →  client.py          (depends on: engine)
Step 3  →  service.py         (depends on: Step 1 + Step 2)
Step 4  →  client.py wiring   (depends on: Step 3)
Step 5  →  sync_client.py     (depends on: Step 3 + Step 4)
Step 6  →  __init__.py        (depends on: Step 1 + Step 3)
Step 7  →  constants.py       (no dependencies, can be done anytime)
Step 8  →  tests              (depends on: all above)
Step 9  →  verify             (depends on: Step 8)
```
