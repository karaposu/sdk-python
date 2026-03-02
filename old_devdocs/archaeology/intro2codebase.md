# Codebase Architecture Introduction

A guide for engineers joining the project.

---

## The 30-Second Mental Model

This SDK is essentially a **well-organized HTTP client** that talks to Bright Data's APIs. The complexity comes from:

1. Supporting many platforms (Amazon, LinkedIn, Instagram, etc.)
2. Handling async operations (some scrapes take minutes)
3. Providing both sync and async interfaces
4. Managing Bright Data "zones" (account configuration)

```
User Code
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  BrightDataClient                                       │
│  (or SyncBrightDataClient)                              │
│                                                         │
│  ┌─────────────┐  ┌──────────────┐  ┌───────────────┐   │
│  │ ScrapeService│  │SearchService │  │CrawlerService │   │
│  └──────┬──────┘  └──────┬───────┘  └───────────────┘   │
│         │                │                              │
│  ┌──────┴──────────────────┴──────┐                     │
│  │     Platform Scrapers          │                     │
│  │  (Amazon, LinkedIn, etc.)      │                     │
│  └──────────────┬─────────────────┘                     │
│                 │                                       │
│  ┌──────────────┴─────────────────┐                     │
│  │      WorkflowExecutor          │                     │
│  │   (trigger → poll → fetch)     │                     │
│  └──────────────┬─────────────────┘                     │
│                 │                                       │
│  ┌──────────────┴─────────────────┐                     │
│  │         AsyncEngine            │                     │
│  │  (HTTP, rate limits, retries)  │                     │
│  └──────────────┬─────────────────┘                     │
└─────────────────┼───────────────────────────────────────┘
                  │
                  ▼
          Bright Data API
```

---

## Data Flow Paths

There are **two main data flows** in this codebase:

### Flow 1: Synchronous (Simple Path)

For quick operations like SERP searches or Web Unlocker requests:

```
User calls method
    │
    ▼
AsyncEngine.post_to_url()  ──────►  Bright Data API
    │                                     │
    ◄─────────────────────────────────────┘
    │                               (immediate response)
    ▼
Return ScrapeResult/SearchResult
```

**Example**: `client.search.google("python tutorial")` - Google returns results immediately.

### Flow 2: Asynchronous Workflow (Dataset Path)

For platform scrapes (Amazon, LinkedIn, etc.) that take time:

```
User calls method
    │
    ▼
WorkflowExecutor.execute()
    │
    ├──► 1. TRIGGER: Send scrape request ──────►  Bright Data API
    │         │                                        │
    │         ◄────────────────────────────────────────┘
    │         │                              (returns snapshot_id)
    │         ▼
    ├──► 2. POLL: Check status repeatedly ─────►  Bright Data API
    │         │        (every N seconds)               │
    │         ◄────────────────────────────────────────┘
    │         │                              (returns "ready" or "in_progress")
    │         ▼
    └──► 3. FETCH: Download results ───────────►  Bright Data API
              │                                        │
              ◄────────────────────────────────────────┘
              │                                  (returns data)
              ▼
         Return ScrapeResult
```

**Example**: `client.scrape.amazon.products(url)` - Amazon scrapes can take 30+ seconds.

### Flow 3: Manual Job Control

Users can also manage the workflow themselves:

```python
job = await client.scrape.amazon.products_trigger(url)  # Returns immediately
# ... do other things ...
status = await job.status()      # Check progress
if status == "ready":
    data = await job.fetch()     # Get results
```

---

## Main Abstractions

### Layer 1: Entry Points

| Class | Role | File |
|-------|------|------|
| `BrightDataClient` | Main async client, owns all services | `client.py` |
| `SyncBrightDataClient` | Sync wrapper using persistent event loop | `sync_client.py` |

**Key insight**: `SyncBrightDataClient` doesn't duplicate logic—it wraps the async client and runs coroutines in a managed event loop.

### Layer 2: Service Namespaces

| Class | Role | Access Pattern |
|-------|------|----------------|
| `ScrapeService` | Groups platform scrapers | `client.scrape.amazon`, `client.scrape.linkedin` |
| `SearchService` | Groups search engines + platform searches | `client.search.google`, `client.search.amazon` |
| `CrawlerService` | Web crawling operations | `client.crawler.crawl()` |

**Key insight**: Services use **lazy initialization**—scrapers are only created when first accessed.

### Layer 3: Platform Scrapers

| Base Class | Role |
|------------|------|
| `BaseWebScraper` | Common scraping logic, trigger/poll/fetch |
| `BaseSERPService` | Common search engine logic |

Platform implementations:
- `AmazonScraper`, `LinkedInScraper`, `InstagramScraper`, `FacebookScraper`, `ChatGPTScraper`
- `GoogleSERPService`, `BingSERPService`, `YandexSERPService`

**Key insight**: Each scraper has a `DATASET_ID` constant that identifies which Bright Data dataset to use.

### Layer 4: Workflow Components

| Class | Role | File |
|-------|------|------|
| `WorkflowExecutor` | Orchestrates trigger→poll→fetch cycle | `scrapers/workflow.py` |
| `DatasetAPIClient` | Low-level Dataset API calls | `scrapers/api_client.py` |
| `ScrapeJob` | Represents an in-flight scraping job | `scrapers/job.py` |

### Layer 5: HTTP Foundation

| Class | Role | File |
|-------|------|------|
| `AsyncEngine` | HTTP client, auth headers, rate limiting | `core/engine.py` |
| `ZoneManager` | Creates/lists/deletes Bright Data zones | `core/zone_manager.py` |

**Key insight**: `AsyncEngine` is a **context manager**. All HTTP operations require `async with engine:` to ensure proper connection cleanup.

### Data Types

| Category | Classes |
|----------|---------|
| **Results** (outputs) | `ScrapeResult`, `SearchResult`, `CrawlResult` |
| **Payloads** (inputs) | `AmazonProductPayload`, `LinkedInProfilePayload`, etc. |
| **Errors** | `BrightDataError`, `ValidationError`, `APIError`, `AuthenticationError`, `ZoneError` |

---

## Top-Level Design Patterns

### 1. Fluent Namespace Pattern

Access is hierarchical: `client.scrape.amazon.products()`

```python
# Instead of:
client.scrape_amazon_products(url)

# We have:
client.scrape.amazon.products(url)
```

**Why**: Discoverable API. Users can type `client.scrape.` and see all platforms, then `client.scrape.amazon.` and see all Amazon operations.

### 2. Async-First with Sync Adapter

Core logic is async. Sync support wraps it:

```python
# Async (native)
async with BrightDataClient() as client:
    result = await client.scrape.amazon.products(url)

# Sync (adapter)
with SyncBrightDataClient() as client:
    result = client.scrape.amazon.products(url)
```

**Why**: Modern Python code is often async. But many users want simple sync code. The adapter pattern lets us support both without duplicating business logic.

**Implementation detail**: `SyncBrightDataClient` creates a **persistent event loop** and runs all async calls through `loop.run_until_complete()`.

### 3. Context Manager Protocol

All resources that need cleanup use context managers:

```python
async with BrightDataClient() as client:    # Opens HTTP session
    async with AmazonScraper() as scraper:  # If used standalone
        ...
# Sessions automatically closed
```

**Why**: Prevents resource leaks (unclosed connections, sockets).

### 4. Template Method in Base Scrapers

`BaseWebScraper` defines the skeleton; subclasses customize:

```python
class BaseWebScraper:
    async def scrape_async(self, urls, ...):
        payload = self._build_scrape_payload(urls)  # Hook: subclass can override
        result = await self.workflow_executor.execute(...)
        return self.normalize_result(result)        # Hook: subclass can override

class AmazonScraper(BaseWebScraper):
    DATASET_ID = "gd_l7q7dkf244hwjntr0"  # Just set the dataset
    # Can override _build_scrape_payload() or normalize_result() if needed
```

**Why**: New platforms can be added with minimal code—just define the dataset ID and any platform-specific parameters.

### 5. Registry Pattern for Scrapers

Scrapers register themselves:

```python
@register("amazon")
class AmazonScraper(BaseWebScraper):
    ...
```

**Why**: Enables future features like auto-detection of URLs and dynamic scraper loading.

### 6. Workflow Pattern (Saga-like)

Long operations are broken into steps with intermediate state:

```
TRIGGER ──► snapshot_id ──► POLL ──► status ──► FETCH ──► data
```

The `ScrapeJob` class holds the `snapshot_id` and provides methods to continue the workflow:

```python
job = await scraper.products_trigger(url)
# job.snapshot_id is set
await job.wait()    # Polls until ready
data = await job.fetch()
```

**Why**: Lets users fire-and-forget, do other work, then collect results. Also enables parallel scrapes.

### 7. Automatic Zone Provisioning

When the client starts, it checks if required "zones" exist and creates them:

```python
async def __aenter__(self):
    await self.engine.__aenter__()
    await self._ensure_zones()  # Auto-creates sdk_unlocker, sdk_serp zones
    return self
```

**Why**: Zero-configuration experience for new users.

---

## Key File Locations

```
src/brightdata/
├── __init__.py          # Public exports
├── client.py            # BrightDataClient (main entry point)
├── sync_client.py       # SyncBrightDataClient (sync wrapper)
├── models.py            # Result dataclasses
├── payloads.py          # Input validation dataclasses
├── exceptions/          # Error types
│
├── core/
│   ├── engine.py        # AsyncEngine (HTTP layer)
│   └── zone_manager.py  # Zone CRUD operations
│
├── api/
│   ├── scrape_service.py   # ScrapeService namespace
│   ├── search_service.py   # SearchService namespace
│   ├── web_unlocker.py     # Direct URL scraping
│   └── serp/               # Search engine services
│       ├── google.py
│       ├── bing.py
│       └── yandex.py
│
└── scrapers/
    ├── base.py          # BaseWebScraper
    ├── workflow.py      # WorkflowExecutor (trigger/poll/fetch)
    ├── api_client.py    # DatasetAPIClient
    ├── job.py           # ScrapeJob
    ├── amazon/          # AmazonScraper, AmazonSearchScraper
    ├── linkedin/        # LinkedInScraper, LinkedInSearchScraper
    ├── instagram/       # InstagramScraper, InstagramSearchScraper
    ├── facebook/        # FacebookScraper
    └── chatgpt/         # ChatGPTScraper
```

---

## Adding a New Platform (Quick Guide)

1. **Create scraper directory**: `src/brightdata/scrapers/newplatform/`

2. **Implement scraper class**:
   ```python
   @register("newplatform")
   class NewPlatformScraper(BaseWebScraper):
       DATASET_ID = "gd_xxxxx"  # From Bright Data dashboard
       PLATFORM_NAME = "newplatform"

       async def some_method(self, url, **kwargs):
           return await self._scrape_urls(url=url, dataset_id=self.DATASET_ID, ...)
   ```

3. **Add to ScrapeService**: In `api/scrape_service.py`, add property:
   ```python
   @property
   def newplatform(self):
       if self._newplatform is None:
           from ..scrapers.newplatform import NewPlatformScraper
           self._newplatform = NewPlatformScraper(...)
       return self._newplatform
   ```

4. **Add sync wrapper**: In `sync_client.py`, add `SyncNewPlatformScraper` class

5. **Export**: Add to `__init__.py` if users need direct access

---

## Common Gotchas

1. **Context managers are required**: Never use `BrightDataClient()` without `async with`—the HTTP session won't be initialized.

2. **Sync client can't run in async context**: `SyncBrightDataClient` detects if there's already an event loop and raises an error.

3. **Consistent async/sync method naming**: All scrapers now use the same pattern:
   - `method()` = async (primary)
   - `method_sync()` = sync wrapper

4. **Dataset IDs are magic strings**: Each platform operation maps to a specific Bright Data dataset. These IDs come from Bright Data's dashboard.

5. **Rate limiting is automatic**: `AsyncEngine` uses `aiolimiter` to prevent hitting API limits. Default is 10 requests/second.

---

## Questions You Might Have

**Q: Why async-first?**
A: Modern Python web applications are async. Scraping often involves waiting for network I/O, which async handles efficiently.

**Q: Why not just use `requests`?**
A: The sync client does use an event loop internally. Using `aiohttp` directly enables concurrent scrapes without threading complexity.

**Q: What are "zones"?**
A: Bright Data configuration containers. Different zones for different proxy types (web unlocker, SERP, browser). The SDK auto-creates `sdk_unlocker` and `sdk_serp` zones.

**Q: Why the trigger/poll/fetch pattern?**
A: Platform scrapes aren't instant. Bright Data queues the work, processes it, then stores results. This pattern matches their API design.
