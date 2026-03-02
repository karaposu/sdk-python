# Architecture Analysis

A deep dive into the codebase architecture, data flows, patterns, and inconsistencies.

---

## 1. Main Entry Points

### Primary Entry Points

| Entry Point | File | Role |
|-------------|------|------|
| `BrightDataClient` | `client.py` | Main async client, owns all services |
| `SyncBrightDataClient` | `sync_client.py` | Sync wrapper around async client |
| `brightdata` CLI | `cli/main.py` | Command-line interface |

### Initialization Flow

```
User creates BrightDataClient(token)
    │
    ├─► AsyncEngine created (HTTP layer)
    │
    ├─► ZoneManager created (zone provisioning)
    │
    └─► Service namespaces (lazy-initialized):
        ├─► ScrapeService  → Platform scrapers
        ├─► SearchService  → SERP + platform search
        ├─► CrawlerService → Web crawling
        └─► WebUnlockerService → Generic URL scraping
```

### Context Manager Protocol

```python
# Required pattern - session lifecycle
async with BrightDataClient(token) as client:
    # __aenter__:
    #   1. Opens HTTP session (aiohttp.ClientSession)
    #   2. Creates rate limiter
    #   3. Ensures zones exist (sdk_unlocker, sdk_serp)

    result = await client.scrape.amazon.products(url)

# __aexit__:
#   1. Closes HTTP session
#   2. Cleans up connections
```

---

## 2. Data Flow Paths

### Flow A: SERP Search (Synchronous)

Fast path for search engine queries. No polling required.

```
client.search.google("query")
    │
    ▼
SearchService.google()
    │
    ▼
GoogleSERPService.search()
    │
    ├─► Build SERP URL (url_builder.py)
    │
    ├─► AsyncEngine.post_to_url() ──────► Bright Data SERP API
    │                                            │
    │   ◄────────────────────────────────────────┘
    │                               (immediate JSON response)
    │
    ├─► Normalize data (data_normalizer.py)
    │
    └─► Return SearchResult
```

**Timing**: ~1-5 seconds

### Flow B: Dataset Scrape (Asynchronous Workflow)

Long-running operations for platform scrapers.

```
client.scrape.amazon.products(url)
    │
    ▼
AmazonScraper.products()
    │
    ▼
BaseWebScraper._scrape_urls()
    │
    ▼
WorkflowExecutor.execute()
    │
    ├─► 1. TRIGGER ──────────────────────────► Dataset API /trigger
    │       │                                        │
    │       ◄────────────────────────────────────────┘
    │       (returns snapshot_id)
    │
    ├─► 2. POLL (loop) ──────────────────────► Dataset API /progress/{id}
    │       │        (every 10s)                     │
    │       ◄────────────────────────────────────────┘
    │       (returns "in_progress" | "ready" | "error")
    │
    └─► 3. FETCH ────────────────────────────► Dataset API /snapshot/{id}
            │                                        │
            ◄────────────────────────────────────────┘
            (returns data JSON)
            │
            ▼
        Return ScrapeResult
```

**Timing**: 30 seconds - 10 minutes

### Flow C: Manual Job Control

User manages the workflow lifecycle.

```python
# 1. Trigger only
job = await client.scrape.amazon.products_trigger(url)
# Returns ScrapeJob immediately with snapshot_id

# 2. Do other work...
await do_something_else()

# 3. Check status
status = await job.status()  # "in_progress" | "ready" | "error"

# 4. Wait for completion
await job.wait(timeout=120)

# 5. Fetch results
data = await job.fetch()
```

### Flow D: Web Unlocker (Direct URL)

Generic URL scraping without polling.

```
client.scrape_url("https://example.com")
    │
    ▼
WebUnlockerService.scrape()
    │
    ├─► Build request payload
    │
    ├─► AsyncEngine.post_to_url() ──────► Web Unlocker API
    │                                          │
    │   ◄──────────────────────────────────────┘
    │                          (immediate HTML/JSON response)
    │
    └─► Return ScrapeResult
```

---

## 3. Data Models and Schemas

### Result Hierarchy

```
BaseResult
├── success: bool
├── cost: Optional[float]
├── error: Optional[str]
├── trigger_sent_at: Optional[datetime]
└── data_fetched_at: Optional[datetime]
    │
    ├── ScrapeResult (extends BaseResult)
    │   ├── url: str
    │   ├── status: "ready" | "error" | "timeout" | "in_progress"
    │   ├── data: Any
    │   ├── snapshot_id: Optional[str]
    │   ├── platform: Optional["linkedin" | "amazon" | "chatgpt"]
    │   ├── method: Optional[str]
    │   ├── snapshot_id_received_at: Optional[datetime]
    │   ├── snapshot_polled_at: List[datetime]
    │   └── row_count, field_count, html_char_size
    │
    ├── SearchResult (extends BaseResult)
    │   ├── query: Dict[str, Any]
    │   ├── data: Optional[List[Dict]]
    │   ├── total_found: Optional[int]
    │   ├── search_engine: Optional["google" | "bing" | "yandex"]
    │   └── country, page, results_per_page
    │
    └── CrawlResult (extends BaseResult)
        ├── domain: Optional[str]
        ├── pages: List[Dict]
        ├── total_pages: Optional[int]
        └── depth, start_url, filter_pattern, etc.
```

### Payload Types (Input Validation)

Two parallel systems exist (see "What Doesn't Make Sense" section):

**payloads.py (Dataclasses)**:
```python
@dataclass
class AmazonProductPayload(URLPayload):
    url: str
    reviews_count: Optional[int] = None

    def __post_init__(self):
        # Validation logic
```

**types.py (TypedDict - deprecated)**:
```python
class AmazonProductPayload(TypedDict, total=False):
    url: str
    reviews_count: NotRequired[int]
```

### Internal Data Structures

**ScrapeJob** (in-flight operation):
```python
@dataclass
class ScrapeJob:
    snapshot_id: str
    _api_client: DatasetAPIClient
    platform_name: Optional[str]
    cost_per_record: float
    triggered_at: datetime
    _cached_status: Optional[str]
    _cached_data: Optional[Any]
```

---

## 4. API Endpoints and Contracts

### Bright Data Datasets API v3

| Operation | Method | URL | Purpose |
|-----------|--------|-----|---------|
| Trigger | POST | `/datasets/v3/trigger?dataset_id={id}` | Start collection |
| Status | GET | `/datasets/v3/progress/{snapshot_id}` | Check progress |
| Fetch | GET | `/datasets/v3/snapshot/{snapshot_id}` | Get results |

**Trigger Request**:
```json
POST /datasets/v3/trigger?dataset_id=gd_xxx&include_errors=true
[
  {"url": "https://amazon.com/dp/B123"},
  {"url": "https://amazon.com/dp/B456"}
]
```

**Trigger Response**:
```json
{"snapshot_id": "s_abc123xyz"}
```

**Status Response**:
```json
{"status": "ready"}  // or "in_progress", "error"
```

### Bright Data SERP API

| Operation | Method | URL | Purpose |
|-----------|--------|-----|---------|
| Search | POST | `https://{zone}.serp.brightdata.com/` | Execute search |

**SERP Request** (Google):
```
POST https://sdk_serp.serp.brightdata.com/
Content-Type: application/x-www-form-urlencoded

url=https://www.google.com/search?q=python+tutorial&num=10&hl=en
```

### Bright Data Web Unlocker API

| Operation | Method | URL | Purpose |
|-----------|--------|-----|---------|
| Scrape | POST | `https://{zone}.unblocker.brightdata.com/` | Fetch URL |

### Zone Management API

| Operation | Method | Endpoint | Purpose |
|-----------|--------|----------|---------|
| List | GET | `/zone` | Get all zones |
| Create | POST | `/zone` | Create zone |
| Delete | DELETE | `/zone?zone={name}` | Delete zone |

---

## 5. Architectural Patterns

### Pattern 1: Fluent Namespace (Builder-like)

Hierarchical, discoverable API.

```python
# Access pattern
client.scrape.amazon.products(url)
client.search.google(query)
client.search.linkedin.jobs(keyword)

# Implementation: Service classes with lazy-loaded properties
class ScrapeService:
    @property
    def amazon(self):
        if self._amazon is None:
            self._amazon = AmazonScraper(...)
        return self._amazon
```

**Benefits**: IDE autocomplete, clear API structure, lazy loading
**Drawbacks**: Deep nesting can be confusing

### Pattern 2: Async-First with Sync Adapter

Core logic is async. Sync wraps via event loop.

```python
# Async (native)
class AmazonScraper:
    async def products(self, url): ...

# Sync (adapter)
class SyncAmazonScraper:
    def products(self, url):
        return self._loop.run_until_complete(
            self._async.products(url)
        )
```

**Implementation**: `SyncBrightDataClient` creates a persistent event loop.

### Pattern 3: Workflow Pattern (Saga-like)

Long operations broken into trigger → poll → fetch steps.

```python
class WorkflowExecutor:
    async def execute(self, payload, dataset_id, ...):
        # Step 1: Trigger
        snapshot_id = await self.api_client.trigger(payload, dataset_id)

        # Step 2: Poll
        result = await poll_until_ready(snapshot_id, ...)

        # Step 3: Fetch (happens inside poll_until_ready)
        return result
```

### Pattern 4: Registry Pattern

Scrapers self-register for URL-based auto-discovery.

```python
# Registration
@register("amazon")
class AmazonScraper(BaseWebScraper):
    ...

# Discovery
scraper_class = get_scraper_for("https://amazon.com/dp/B123")
# Returns AmazonScraper
```

**Current Usage**: Registration exists but auto-routing not yet implemented.

### Pattern 5: Template Method

Base class defines skeleton; subclasses customize.

```python
class BaseWebScraper:
    DATASET_ID = None  # Must override
    PLATFORM_NAME = None  # Must override

    async def _scrape_urls(self, url, dataset_id, ...):
        # Template: validate → build payload → execute workflow
        ...
        result = await self.workflow_executor.execute(...)
        return self.normalize_result(result)  # Hook

class AmazonScraper(BaseWebScraper):
    DATASET_ID = "gd_l7q7dkf244hwjntr0"
    PLATFORM_NAME = "amazon"

    def normalize_result(self, result):
        # Custom normalization
        ...
```

### Pattern 6: Context Manager Protocol

Resources requiring cleanup use context managers.

```python
async with BrightDataClient() as client:
    async with client.engine:  # Nested contexts
        ...
# Automatic cleanup of HTTP sessions, connections
```

---

## 6. What Doesn't Make Sense

### Issue 1: Dual Type Systems (TypedDict + Dataclass)

**Location**: `types.py` (350 lines) and `payloads.py` (911 lines)

Both define the same payload structures:

```python
# types.py (marked deprecated)
class AmazonProductPayload(TypedDict, total=False):
    url: str
    reviews_count: NotRequired[int]

# payloads.py
@dataclass
class AmazonProductPayload(URLPayload):
    url: str
    reviews_count: Optional[int] = None
```

**Problem**: Maintenance burden, confusion about which to use
**Neither is used**: Scrapers build raw dicts directly:
```python
# instagram/scraper.py
payload = [{"url": u} for u in url_list]  # No Payload class
```

**Recommendation**: Delete `types.py`, actually use `payloads.py` for validation

---

### Issue 2: Inconsistent scraper vs search Split

Some platforms have separate "scraper" and "search" classes:

| Platform | scraper.py | search.py | Separation Logic |
|----------|------------|-----------|------------------|
| Amazon | URL-based | Keyword-based | Clear |
| LinkedIn | URL-based | Parameter-based | Clear |
| Instagram | URL-based | Discovery-based | Unclear |
| Facebook | URL-based | None | Why no search? |
| ChatGPT | Prompt-based | Prompt-based | Duplicate? |

**ChatGPT specifically**:
- `scrapers/chatgpt/scraper.py`: `prompt()`, `prompts()`
- `scrapers/chatgpt/search.py`: `chatGPT()` (similar API)

Both do essentially the same thing with different interfaces.

**Recommendation**: Clarify distinction or merge

---

### Issue 3: Constants Naming Confusion

```python
# constants.py
DEFAULT_TIMEOUT_SHORT: int = 180   # 3 minutes - called "short"
DEFAULT_TIMEOUT_MEDIUM: int = 240  # 4 minutes - called "medium"
DEFAULT_TIMEOUT_LONG: int = 120    # 2 minutes - called "LONG"?!
```

The "LONG" timeout is the shortest! This appears to be a bug or misnamed constant.

---

### Issue 4: Registry Pattern Incomplete

The `@register` decorator and `get_scraper_for()` exist but aren't used:

```python
# registry.py - Functions exist
get_scraper_for(url)  # Returns scraper class for URL
is_platform_supported(url)  # Checks if URL has scraper

# client.py - Not used
# client.scrape_url() doesn't auto-detect platform
```

The infrastructure for intelligent URL routing exists but isn't wired up.

---

### Issue 5: ScrapeJob.to_result() Uses Wrong Fields

```python
# job.py line 207-215
return ScrapeResult(
    success=True,
    data=data,
    platform=self.platform_name,
    cost=estimated_cost,
    timing_start=start_time,  # Not a valid ScrapeResult field
    timing_end=end_time,      # Not a valid ScrapeResult field
    metadata={"snapshot_id": self.snapshot_id},  # Not a valid field
)
```

`ScrapeResult` doesn't have `timing_start`, `timing_end`, or `metadata` fields. This would raise a TypeError if called.

---

### Issue 6: Browser API Module Unused

```
api/browser/
├── browser_api.py
├── browser_pool.py
├── config.py
└── session.py
```

This module exists but:
- Not exported in `__init__.py`
- Not accessible from client
- Not documented

Appears to be work-in-progress or abandoned code.

---

### Issue 7: Service Instantiation Inconsistency

**SERP services** - Created with `engine` and `timeout`:
```python
self._google_service = GoogleSERPService(
    engine=self._client.engine,
    timeout=self._client.timeout,
)
```

**Scrapers** - Created with `bearer_token` and `engine`:
```python
self._amazon = AmazonScraper(
    bearer_token=self._client.token,
    engine=self._client.engine
)
```

Why do scrapers need `bearer_token` when they already have `engine`?
The engine already contains the bearer token in its headers.

---

### Issue 8: Validation Module Inconsistently Used

```python
# validation.py has:
validate_url(url)
validate_url_list(urls)
validate_bearer_token(token)
validate_zone_name(zone)

# Some scrapers validate:
if isinstance(url, str):
    validate_url(url)
else:
    validate_url_list(url)

# Some scrapers don't validate at all:
# (just pass through to API)
```

No consistent validation strategy across scrapers.

---

### Issue 9: Circular Import Prevention via TYPE_CHECKING

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import BrightDataClient
```

This pattern appears frequently, suggesting module boundaries could be cleaner.

---

## 7. Dependency Graph Summary

```
                    ┌─────────────────┐
                    │  BrightDataClient│
                    └────────┬────────┘
                             │
           ┌─────────────────┼─────────────────┐
           │                 │                 │
           ▼                 ▼                 ▼
    ┌────────────┐    ┌────────────┐    ┌────────────┐
    │ScrapeService│    │SearchService│    │ AsyncEngine│
    └──────┬─────┘    └──────┬─────┘    └──────┬─────┘
           │                 │                  │
    ┌──────┴──────┐   ┌──────┴──────┐          │
    │  Scrapers   │   │SERP Services│          │
    │  (amazon,   │   │(google,bing)│          │
    │  linkedin)  │   └─────────────┘          │
    └──────┬──────┘                            │
           │                                    │
           ▼                                    │
    ┌─────────────┐                            │
    │WorkflowExec │                            │
    └──────┬──────┘                            │
           │                                    │
           ▼                                    │
    ┌─────────────┐                            │
    │DatasetAPI   │◄───────────────────────────┘
    │Client       │
    └─────────────┘
           │
           ▼
    ┌─────────────┐
    │ ScrapeResult│
    │ SearchResult│
    │ CrawlResult │
    └─────────────┘
```

---

## 8. Key Observations

1. **Well-structured core**: `AsyncEngine` → `DatasetAPIClient` → `WorkflowExecutor` is clean
2. **Consistent result types**: `BaseResult` hierarchy works well
3. **Lazy loading**: Services only instantiate scrapers when first accessed
4. **Rate limiting built-in**: `aiolimiter` integration in engine
5. **Context manager discipline**: Resources properly managed
6. **Registry for future**: Auto-routing infrastructure exists but unused

**Technical debt**:
- Dual type systems
- Unused browser module
- Inconsistent validation
- Confusing timeout constants
- Some dead code paths
