# Module Discovery Analysis

Analysis of natural module boundaries, coupling, cohesion, and dependencies.

---

## 1. Natural Module Boundaries

### Current Directory Structure

```
src/brightdata/
├── Core Layer
│   ├── client.py              # Main async client
│   ├── sync_client.py         # Sync wrapper
│   ├── models.py              # Result dataclasses
│   ├── constants.py           # Shared constants
│   ├── payloads.py            # Input validation
│   ├── types.py               # TypedDict (deprecated)
│   └── exceptions/            # Error types
│
├── Infrastructure Layer
│   └── core/
│       ├── engine.py          # HTTP client
│       ├── zone_manager.py    # Zone CRUD
│       ├── auth.py            # Authentication
│       ├── hooks.py           # Lifecycle hooks
│       └── logging.py         # Logging setup
│
├── Service Layer
│   └── api/
│       ├── scrape_service.py  # Scraper namespace
│       ├── search_service.py  # Search namespace
│       ├── crawler_service.py # Crawler namespace
│       ├── web_unlocker.py    # Generic scraping
│       ├── serp/              # Search engine services
│       └── browser/           # Browser automation (unused)
│
├── Domain Layer
│   └── scrapers/
│       ├── base.py            # Base scraper class
│       ├── workflow.py        # Trigger/poll/fetch
│       ├── api_client.py      # Dataset API
│       ├── job.py             # ScrapeJob
│       ├── registry.py        # Auto-discovery
│       ├── amazon/            # Amazon scraper
│       ├── linkedin/          # LinkedIn scraper
│       ├── instagram/         # Instagram scraper
│       ├── facebook/          # Facebook scraper
│       └── chatgpt/           # ChatGPT scraper
│
├── Utilities Layer
│   └── utils/
│       ├── validation.py      # Input validation
│       ├── polling.py         # Async polling
│       ├── retry.py           # Retry logic
│       ├── ssl_helpers.py     # SSL error handling
│       ├── url.py             # URL utilities
│       ├── timing.py          # Timing utilities
│       ├── location.py        # Geo location
│       ├── parsing.py         # Data parsing
│       └── function_detection.py  # Caller detection
│
└── CLI Layer
    └── cli/
        ├── main.py            # Entry point
        ├── banner.py          # ASCII art
        ├── utils.py           # CLI utilities
        └── commands/          # Subcommands
```

### Recommended Logical Boundaries

```
┌─────────────────────────────────────────────────────────────┐
│                      Public API                             │
│  ┌─────────────┐  ┌──────────────────┐  ┌───────────────┐   │
│  │BrightData   │  │SyncBrightData    │  │CLI Interface  │   │
│  │Client       │  │Client            │  │               │   │
│  └──────┬──────┘  └────────┬─────────┘  └───────────────┘   │
└─────────┼──────────────────┼────────────────────────────────┘
          │                  │
┌─────────┼──────────────────┼────────────────────────────────┐
│         │    Service Layer │                                │
│  ┌──────▼──────┐  ┌────────▼───────┐  ┌─────────────────┐   │
│  │ScrapeService│  │SearchService   │  │CrawlerService   │   │
│  └──────┬──────┘  └────────┬───────┘  └─────────────────┘   │
└─────────┼──────────────────┼────────────────────────────────┘
          │                  │
┌─────────┼──────────────────┼────────────────────────────────┐
│         │    Domain Layer  │                                │
│  ┌──────▼──────────────────▼──────┐  ┌──────────────────┐   │
│  │Platform Scrapers               │  │SERP Services     │   │
│  │(amazon, linkedin, instagram...)│  │(google,bing...)  │   │
│  └──────┬─────────────────────────┘  └──────────────────┘   │
└─────────┼───────────────────────────────────────────────────┘
          │
┌─────────┼───────────────────────────────────────────────────┐
│         │    Infrastructure Layer                           │
│  ┌──────▼──────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │Workflow     │  │DatasetAPI   │  │WebUnlocker          │  │
│  │Executor     │  │Client       │  │Service              │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────────┘  │
└─────────┼────────────────┼──────────────────────────────────┘
          │                │
┌─────────┼────────────────┼──────────────────────────────────┐
│         │    Core Layer  │                                  │
│  ┌──────▼────────────────▼──────┐  ┌─────────────────────┐  │
│  │AsyncEngine                   │  │ZoneManager          │  │
│  │(HTTP, rate limiting, auth)   │  │                     │  │
│  └──────────────────────────────┘  └─────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 2. Coupling Analysis

### High Coupling (Problematic)

#### 1. sync_client.py ↔ Everything

The sync client creates wrappers for every single async class:

```python
# sync_client.py - 751 lines wrapping:
class SyncBrightDataClient    # wraps BrightDataClient
class SyncScrapeService       # wraps ScrapeService
class SyncSearchService       # wraps SearchService
class SyncAmazonScraper       # wraps AmazonScraper
class SyncLinkedInScraper     # wraps LinkedInScraper
class SyncInstagramScraper    # wraps InstagramScraper
class SyncFacebookScraper     # wraps FacebookScraper
class SyncChatGPTScraper      # wraps ChatGPTScraper
# ... 12+ more wrapper classes
```

**Problem**: Every new method requires updating sync_client.py
**Impact**: ~80% of sync_client.py is boilerplate

#### 2. Scrapers ↔ Multiple Core Modules

Each scraper imports from 5-7 different modules:

```python
# Typical scraper imports:
from ..base import BaseWebScraper           # Parent class
from ..registry import register             # Registration
from ..job import ScrapeJob                 # Job handling
from ...models import ScrapeResult          # Result type
from ...utils.validation import ...         # Validation
from ...utils.function_detection import ... # Caller detection
from ...constants import ...                # Constants
```

**Impact**: Changes to any imported module can break scrapers

#### 3. Service Layer ↔ Client

Services hold reference to client and access multiple client properties:

```python
class ScrapeService:
    def __init__(self, client: "BrightDataClient"):
        self._client = client

    @property
    def amazon(self):
        return AmazonScraper(
            bearer_token=self._client.token,  # Access 1
            engine=self._client.engine         # Access 2
        )
```

**Impact**: Client interface changes break all services

### Low Coupling (Good)

#### 1. AsyncEngine (Self-contained)

```python
# engine.py only imports:
import aiohttp
from ..exceptions import ...  # Own exceptions
from ..constants import ...   # HTTP codes only
```

**Benefit**: Can be tested and used independently

#### 2. DatasetAPIClient (Clean interface)

```python
# api_client.py
class DatasetAPIClient:
    def __init__(self, engine: AsyncEngine):
        self.engine = engine

    # Only 3 methods:
    async def trigger(...) -> Optional[str]
    async def get_status(...) -> str
    async def fetch_result(...) -> Any
```

**Benefit**: Clear contract, easy to mock

#### 3. Models (No dependencies)

```python
# models.py only imports:
from dataclasses import dataclass
from typing import ...
import json
from pathlib import Path
```

**Benefit**: Pure data structures, no coupling

---

## 3. Cohesion Analysis

### High Cohesion (Good)

#### 1. core/engine.py

Single responsibility: HTTP communication

| Method | Purpose |
|--------|---------|
| `__aenter__` | Open session |
| `__aexit__` | Close session |
| `request()` | Make request |
| `post()` | POST wrapper |
| `get()` | GET wrapper |
| `post_to_url()` | External POST |
| `get_from_url()` | External GET |

All methods relate to HTTP operations. **Cohesion: HIGH**

#### 2. scrapers/workflow.py

Single responsibility: Trigger/poll/fetch orchestration

| Method | Purpose |
|--------|---------|
| `execute()` | Full workflow |
| `_poll_and_fetch()` | Polling loop |

All methods relate to workflow execution. **Cohesion: HIGH**

#### 3. utils/polling.py

Single responsibility: Async polling

| Function | Purpose |
|----------|---------|
| `poll_until_ready()` | Generic polling |

Single focused function. **Cohesion: HIGH**

### Low Cohesion (Problematic)

#### 1. client.py

Multiple responsibilities mixed:

```python
class BrightDataClient:
    # Responsibility 1: Service management
    @property
    def scrape(self): ...
    @property
    def search(self): ...
    @property
    def crawler(self): ...

    # Responsibility 2: Zone management
    async def _ensure_zones(self): ...

    # Responsibility 3: Direct scraping
    async def scrape_url(self, url, ...): ...

    # Responsibility 4: Lifecycle
    async def __aenter__(self): ...
    async def __aexit__(self): ...
```

**Suggestion**: Extract zone management, move `scrape_url` to WebUnlockerService

#### 2. sync_client.py

Massive file (751 lines) with 15+ wrapper classes. Each class is cohesive internally, but the file as a whole is a "grab bag" of sync wrappers.

**Suggestion**: Split into sync/ directory with separate files per wrapper

#### 3. payloads.py (911 lines)

Contains ALL payload definitions for ALL platforms:

```python
# Base payloads
class BasePayload
class URLPayload

# Amazon payloads (5 classes)
class AmazonProductPayload
class AmazonReviewPayload
class AmazonSellerPayload
class AmazonProductsSearchPayload
class AmazonQuestionsPayload

# LinkedIn payloads (7 classes)
class LinkedInProfilePayload
class LinkedInJobPayload
# ...

# Instagram payloads (6 classes)
# Facebook payloads (5 classes)
# ChatGPT payloads (1 class)
```

**Suggestion**: Move payloads to respective scraper directories:
- `scrapers/amazon/payloads.py`
- `scrapers/linkedin/payloads.py`
- etc.

---

## 4. Dependency Relationships

### Import Heat Map

Modules sorted by number of internal imports:

| Module | Internal Imports | Depends On |
|--------|-----------------|------------|
| `sync_client.py` | 15+ | Everything |
| `client.py` | 10 | core, api, scrapers, models |
| `scrapers/base.py` | 8 | core, models, utils, constants |
| `scrapers/*/scraper.py` | 7-8 | base, models, utils, constants |
| `api/search_service.py` | 6 | models, serp, scrapers |
| `api/scrape_service.py` | 5 | models, scrapers |
| `core/engine.py` | 4 | exceptions, constants |
| `models.py` | 0 | (external only) |

### Dependency Direction

```
                    External (user code)
                           ↓
┌──────────────────────────┴─────────────────────────┐
│                    Public API                       │
│         client.py, sync_client.py, __init__.py     │
└──────────────────────────┬─────────────────────────┘
                           ↓ depends on
┌──────────────────────────┴─────────────────────────┐
│                   Service Layer                     │
│    scrape_service.py, search_service.py, etc.      │
└──────────────────────────┬─────────────────────────┘
                           ↓ depends on
┌──────────────────────────┴─────────────────────────┐
│                   Domain Layer                      │
│    scrapers/*, api/serp/*, api/web_unlocker.py     │
└──────────────────────────┬─────────────────────────┘
                           ↓ depends on
┌──────────────────────────┴─────────────────────────┐
│                Infrastructure Layer                 │
│    workflow.py, api_client.py, polling.py          │
└──────────────────────────┬─────────────────────────┘
                           ↓ depends on
┌──────────────────────────┴─────────────────────────┐
│                    Core Layer                       │
│    engine.py, zone_manager.py, auth.py             │
└──────────────────────────┬─────────────────────────┘
                           ↓ depends on
┌──────────────────────────┴─────────────────────────┐
│                Foundation Layer                     │
│    models.py, constants.py, exceptions/            │
└────────────────────────────────────────────────────┘
```

**Observation**: Dependencies flow downward (good). No circular dependencies at module level.

### Circular Import Prevention

The codebase uses `TYPE_CHECKING` pattern to prevent circular imports:

```python
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import BrightDataClient

class ScrapeService:
    def __init__(self, client: "BrightDataClient"):  # String annotation
        self._client = client
```

**Occurrences**: 5 files use this pattern

---

## 5. Shared Utilities Analysis

### utils/ Module Contents

| File | Functions | Used By |
|------|-----------|---------|
| `validation.py` | 10 functions | scrapers, services |
| `polling.py` | 1 function | workflow.py |
| `retry.py` | 1 decorator | serp services |
| `ssl_helpers.py` | 2 functions | engine.py |
| `url.py` | 3 functions | web_unlocker, scrapers |
| `timing.py` | 2 functions | (unused?) |
| `location.py` | 1 class | serp services |
| `parsing.py` | 4 functions | scrapers |
| `function_detection.py` | 1 function | ALL scrapers |

### Function Detection Utility

Every scraper uses this to identify the calling function for monitoring:

```python
# function_detection.py
def get_caller_function_name() -> Optional[str]:
    """Get the name of the function that called this function."""
    frame = inspect.currentframe()
    # Walk up the stack to find caller
    ...
```

**Usage**: Passed to API as `sdk_function` parameter for analytics

### Validation Functions

```python
# validation.py - Used across codebase
validate_url(url)           # Single URL validation
validate_url_list(urls)     # URL list validation
validate_bearer_token(...)  # Token format check
validate_zone_name(...)     # Zone name format
validate_timeout(...)       # Timeout range check
validate_poll_interval(...) # Interval range check
```

**Observation**: Good abstraction, prevents duplicate validation logic

---

## 6. Module Boundaries Recommendations

### Current Issues

1. **sync_client.py is monolithic**: 751 lines, 15+ classes
2. **payloads.py is monolithic**: 911 lines, all platforms mixed
3. **types.py duplicates payloads.py**: Both define same structures
4. **Browser module unused**: Dead code in api/browser/

### Recommended Refactoring

#### 1. Split sync_client.py

```
sync/
├── __init__.py          # Re-export all
├── client.py            # SyncBrightDataClient
├── services.py          # SyncScrapeService, SyncSearchService
├── amazon.py            # SyncAmazonScraper
├── linkedin.py          # SyncLinkedInScraper
├── instagram.py         # SyncInstagramScraper
├── facebook.py          # SyncFacebookScraper
└── chatgpt.py           # SyncChatGPTScraper
```

#### 2. Colocate Payloads with Scrapers

```
scrapers/amazon/
├── __init__.py
├── scraper.py
├── search.py
└── payloads.py          # Amazon-specific payloads

scrapers/linkedin/
├── __init__.py
├── scraper.py
├── search.py
└── payloads.py          # LinkedIn-specific payloads
```

#### 3. Delete Dead Code

- Remove `types.py` (deprecated, duplicates payloads.py)
- Remove `api/browser/` (unused)
- Remove `timing.py` if truly unused

#### 4. Clean Up Constants

Fix the confusing timeout naming:
```python
# Before (confusing)
DEFAULT_TIMEOUT_SHORT: int = 180   # 3 min
DEFAULT_TIMEOUT_MEDIUM: int = 240  # 4 min
DEFAULT_TIMEOUT_LONG: int = 120    # 2 min (?!)

# After (logical)
DEFAULT_TIMEOUT_FAST: int = 120    # 2 min (SERP)
DEFAULT_TIMEOUT_NORMAL: int = 180  # 3 min (most scrapers)
DEFAULT_TIMEOUT_SLOW: int = 240    # 4 min (Facebook, batch)
```

---

## 7. Metrics Summary

### Code Distribution

| Layer | Files | Lines | % of Total |
|-------|-------|-------|------------|
| Scrapers | 15 | ~3,500 | 28% |
| API/Services | 12 | ~1,800 | 14% |
| Core | 6 | ~1,200 | 9% |
| Utils | 10 | ~800 | 6% |
| Models/Types | 3 | ~1,600 | 13% |
| Sync Client | 1 | 751 | 6% |
| Payloads | 1 | 911 | 7% |
| CLI | 5 | ~1,200 | 9% |
| Other | 10 | ~1,000 | 8% |
| **Total** | **63** | **~12,700** | **100%** |

### Complexity Hotspots

Files with highest complexity (lines + imports + responsibilities):

1. **sync_client.py** - 751 lines, 15+ classes
2. **payloads.py** - 911 lines, 28 classes
3. **scrapers/facebook/scraper.py** - 791 lines
4. **scrapers/amazon/scraper.py** - 537 lines
5. **client.py** - 524 lines

### Test Coverage Gaps (Inferred)

Based on file structure, these areas likely need more tests:

1. Sync client wrappers (many classes, lots of boilerplate)
2. CLI commands (interactive, hard to test)
3. Error handling paths (exception cases)
4. Browser module (if kept, currently unused)

---

## 8. Module Health Checklist

| Module | Single Responsibility | Low Coupling | High Cohesion | No Dead Code |
|--------|----------------------|--------------|---------------|--------------|
| core/engine.py | ✅ | ✅ | ✅ | ✅ |
| core/zone_manager.py | ✅ | ✅ | ✅ | ✅ |
| scrapers/workflow.py | ✅ | ✅ | ✅ | ✅ |
| scrapers/api_client.py | ✅ | ✅ | ✅ | ✅ |
| scrapers/base.py | ⚠️ | ⚠️ | ✅ | ✅ |
| models.py | ✅ | ✅ | ✅ | ✅ |
| client.py | ❌ | ⚠️ | ⚠️ | ✅ |
| sync_client.py | ❌ | ❌ | ❌ | ✅ |
| payloads.py | ❌ | ✅ | ❌ | ✅ |
| types.py | ❌ | ✅ | ❌ | ❌ |
| api/browser/* | ❓ | ❓ | ❓ | ❌ |

**Legend**: ✅ Good | ⚠️ Needs attention | ❌ Problematic | ❓ Unknown (unused)
