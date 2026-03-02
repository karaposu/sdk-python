# Instagram Scraper - Implementation Plan

## Overview

Based on analysis of Amazon and LinkedIn scraper implementations and the Instagram API documentation, this document outlines what needs to be created for the Instagram scraper.

> **Note:** See `initial_critic.md` for critical analysis and issue resolutions. All blocking issues have been resolved.

---

## Files to Create

```
src/brightdata/scrapers/instagram/
├── __init__.py          # Export InstagramScraper, InstagramSearchScraper
├── scraper.py           # URL-based extraction (InstagramScraper)
└── search.py            # Parameter-based discovery (InstagramSearchScraper)
```

---

## Dataset IDs (from documentation)

| Content Type | Dataset ID | Purpose |
|--------------|------------|---------|
| Profiles | `gd_l1vikfch901nx3by4` | Profile data extraction |
| Posts | `gd_lk5ns7kz21pck8jpis` | Post data extraction |
| Reels | `gd_lyclm20il4r5helnj` | Reel/video extraction |
| Comments | `gd_ltppn085pokosxh13` | Comment extraction |

---

## Part 1: InstagramScraper (scraper.py)

URL-based extraction class. Similar to `AmazonScraper` and `LinkedInScraper`.

### Class Structure

```python
from ..constants import COST_PER_RECORD_INSTAGRAM, DEFAULT_TIMEOUT_SHORT

@register("instagram")
class InstagramScraper(BaseWebScraper):
    DATASET_ID = "gd_l1vikfch901nx3by4"  # Profiles (default)
    DATASET_ID_POSTS = "gd_lk5ns7kz21pck8jpis"
    DATASET_ID_REELS = "gd_lyclm20il4r5helnj"
    DATASET_ID_COMMENTS = "gd_ltppn085pokosxh13"

    PLATFORM_NAME = "instagram"
    MIN_POLL_TIMEOUT = DEFAULT_TIMEOUT_SHORT  # 180s like LinkedIn
    COST_PER_RECORD = COST_PER_RECORD_INSTAGRAM  # 0.002 (same as LinkedIn)
```

> **Implementation Note:** Use `_trigger_scrape_async(urls, dataset_id=self.DATASET_ID_POSTS)` to pass different dataset IDs for different content types. The `dataset_id` parameter was added to `base.py` for this purpose.

### Methods to Implement

#### 1. Profiles (URL-based)

```python
# Async
async def profiles(self, url: Union[str, List[str]], timeout: int = 180) -> Union[ScrapeResult, List[ScrapeResult]]
# Sync
def profiles_sync(self, url: Union[str, List[str]], timeout: int = 180) -> Union[ScrapeResult, List[ScrapeResult]]
# Manual control
async def profiles_trigger(self, url: Union[str, List[str]]) -> ScrapeJob
def profiles_trigger_sync(self, url: Union[str, List[str]]) -> ScrapeJob
async def profiles_status(self, snapshot_id: str) -> str
def profiles_status_sync(self, snapshot_id: str) -> str
async def profiles_fetch(self, snapshot_id: str) -> Any
def profiles_fetch_sync(self, snapshot_id: str) -> Any
```

**Input:** `{"url": "https://www.instagram.com/username/"}`

**API Endpoint:**
```
POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_l1vikfch901nx3by4
```

---

#### 2. Posts (URL-based)

```python
# Async
async def posts(self, url: Union[str, List[str]], timeout: int = 180) -> Union[ScrapeResult, List[ScrapeResult]]
# Sync
def posts_sync(self, url: Union[str, List[str]], timeout: int = 180) -> Union[ScrapeResult, List[ScrapeResult]]
# Manual control
async def posts_trigger(self, url: Union[str, List[str]]) -> ScrapeJob
def posts_trigger_sync(self, url: Union[str, List[str]]) -> ScrapeJob
async def posts_status(self, snapshot_id: str) -> str
def posts_status_sync(self, snapshot_id: str) -> str
async def posts_fetch(self, snapshot_id: str) -> Any
def posts_fetch_sync(self, snapshot_id: str) -> Any
```

**Input:** `{"url": "https://www.instagram.com/p/Cuf4s0MNqNr"}`

**API Endpoint:**
```
POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_lk5ns7kz21pck8jpis
```

---

#### 3. Reels (URL-based)

```python
# Async
async def reels(self, url: Union[str, List[str]], timeout: int = 180) -> Union[ScrapeResult, List[ScrapeResult]]
# Sync
def reels_sync(self, url: Union[str, List[str]], timeout: int = 180) -> Union[ScrapeResult, List[ScrapeResult]]
# Manual control
async def reels_trigger(self, url: Union[str, List[str]]) -> ScrapeJob
def reels_trigger_sync(self, url: Union[str, List[str]]) -> ScrapeJob
async def reels_status(self, snapshot_id: str) -> str
def reels_status_sync(self, snapshot_id: str) -> str
async def reels_fetch(self, snapshot_id: str) -> Any
def reels_fetch_sync(self, snapshot_id: str) -> Any
```

**Input:** `{"url": "https://www.instagram.com/reel/C5Rdyj_q7YN/"}`

**API Endpoint:**
```
POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_lyclm20il4r5helnj
```

---

#### 4. Comments (URL-based)

```python
# Async
async def comments(self, url: Union[str, List[str]], timeout: int = 180) -> Union[ScrapeResult, List[ScrapeResult]]
# Sync
def comments_sync(self, url: Union[str, List[str]], timeout: int = 180) -> Union[ScrapeResult, List[ScrapeResult]]
# Manual control
async def comments_trigger(self, url: Union[str, List[str]]) -> ScrapeJob
def comments_trigger_sync(self, url: Union[str, List[str]]) -> ScrapeJob
async def comments_status(self, snapshot_id: str) -> str
def comments_status_sync(self, snapshot_id: str) -> str
async def comments_fetch(self, snapshot_id: str) -> Any
def comments_fetch_sync(self, snapshot_id: str) -> Any
```

**Input:** `{"url": "https://www.instagram.com/p/CesFC7JLyFl/"}`

**API Endpoint:**
```
POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_ltppn085pokosxh13
```

---

## Part 2: InstagramSearchScraper (search.py)

Parameter-based discovery class. Similar to `AmazonSearchScraper` and `LinkedInSearchScraper`.

### Class Structure

```python
from ..constants import COST_PER_RECORD_INSTAGRAM, DEFAULT_TIMEOUT_SHORT

class InstagramSearchScraper:
    DATASET_ID_PROFILES = "gd_l1vikfch901nx3by4"
    DATASET_ID_POSTS = "gd_lk5ns7kz21pck8jpis"
    DATASET_ID_REELS = "gd_lyclm20il4r5helnj"

    PLATFORM_NAME = "instagram"
    MIN_POLL_TIMEOUT = DEFAULT_TIMEOUT_SHORT
    COST_PER_RECORD = COST_PER_RECORD_INSTAGRAM
```

> **Implementation Note:** Discovery methods require `extra_params` in API calls. Use `api_client.trigger(..., extra_params={"type": "discover_new", "discover_by": "user_name"})`. The `extra_params` parameter was added to `DatasetAPIClient.trigger()` for this purpose.

### Methods to Implement

#### 1. Profiles Discovery (by username)

```python
# Async
async def profiles(
    self,
    user_name: Union[str, List[str]],
    timeout: int = 180,
) -> ScrapeResult
# Sync
def profiles_sync(
    self,
    user_name: Union[str, List[str]],
    timeout: int = 180,
) -> ScrapeResult
```

**Input:** `{"user_name": "zoobarcelona"}`

> **Important:** The field is `user_name` (with underscore), NOT `username`. This must be exact in payload construction.

**API Endpoint:**
```
POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_l1vikfch901nx3by4&type=discover_new&discover_by=user_name
```

---

#### 2. Posts Discovery (by profile URL)

```python
# Async
async def posts(
    self,
    url: Union[str, List[str]],
    num_of_posts: Optional[int] = None,
    start_date: Optional[str] = None,  # Format: "MM-DD-YYYY"
    end_date: Optional[str] = None,    # Format: "MM-DD-YYYY"
    post_type: Optional[str] = None,   # "Post", "Reel", etc.
    posts_to_not_include: Optional[List[str]] = None,
    timeout: int = 180,
) -> ScrapeResult
# Sync
def posts_sync(...) -> ScrapeResult
```

**Input:**
```json
{
    "url": "https://www.instagram.com/meta/",
    "num_of_posts": 10,
    "start_date": "01-01-2025",
    "end_date": "03-01-2025",
    "post_type": "Post"
}
```

> **Implementation Note:** Omit optional parameters when None (don't send empty strings). Use `validate_instagram_date()` from `utils/validation.py` to validate date format (MM-DD-YYYY).

**API Endpoint:**
```
POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_lk5ns7kz21pck8jpis&type=discover_new&discover_by=url
```

---

#### 3. Reels Discovery (by profile URL)

```python
# Async
async def reels(
    self,
    url: Union[str, List[str]],
    num_of_posts: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    timeout: int = 180,
) -> ScrapeResult
# Sync
def reels_sync(...) -> ScrapeResult
```

**Input:**
```json
{
    "url": "https://www.instagram.com/espn"
}
```

> **Note:** Omit `start_date` and `end_date` when not provided (don't send empty strings).

**API Endpoint:**
```
POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_lyclm20il4r5helnj&type=discover_new&discover_by=url
```

---

#### 4. Reels Discovery - All Reels (by profile URL)

```python
# Async
async def reels_all(
    self,
    url: Union[str, List[str]],
    num_of_posts: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    timeout: int = 180,
) -> ScrapeResult
# Sync
def reels_all_sync(...) -> ScrapeResult
```

**Input:**
```json
{
    "url": "https://www.instagram.com/billieeilish",
    "num_of_posts": 20
}
```

> **Note:** The difference between `reels()` and `reels_all()` is the `discover_by` parameter (`url` vs `url_all_reels`). The exact behavioral difference is unclear - implement both and test.

**API Endpoint:**
```
POST https://api.brightdata.com/datasets/v3/trigger?dataset_id=gd_lyclm20il4r5helnj&type=discover_new&discover_by=url_all_reels
```

---

## Part 3: __init__.py

```python
"""Instagram scrapers for URL-based and parameter-based extraction."""

from .scraper import InstagramScraper
from .search import InstagramSearchScraper

__all__ = ["InstagramScraper", "InstagramSearchScraper"]
```

---

## Part 4: Integration with BrightDataClient

After creating the scraper files, register them in the client:

### File: `src/brightdata/scrapers/registry.py`

The `@register("instagram")` decorator should handle this automatically.

### File: `src/brightdata/client.py`

Verify Instagram scraper is accessible via:
- `client.scrape.instagram.profiles(url)`
- `client.scrape.instagram.posts(url)`
- `client.scrape.instagram.reels(url)`
- `client.scrape.instagram.comments(url)`
- `client.search.instagram.profiles(user_name)`
- `client.search.instagram.posts(url, ...)`
- `client.search.instagram.reels(url, ...)`
- `client.search.instagram.reels_all(url, ...)`

---

## API Summary

### InstagramScraper (URL-based - scraper.py)

| Method | Input | Dataset ID |
|--------|-------|------------|
| `profiles(url)` | Profile URL | `gd_l1vikfch901nx3by4` |
| `posts(url)` | Post URL | `gd_lk5ns7kz21pck8jpis` |
| `reels(url)` | Reel URL | `gd_lyclm20il4r5helnj` |
| `comments(url)` | Post/Reel URL | `gd_ltppn085pokosxh13` |

### InstagramSearchScraper (Parameter-based - search.py)

| Method | Input | Query Params | Dataset ID |
|--------|-------|--------------|------------|
| `profiles(user_name)` | username | `type=discover_new&discover_by=user_name` | `gd_l1vikfch901nx3by4` |
| `posts(url, ...)` | profile URL + filters | `type=discover_new&discover_by=url` | `gd_lk5ns7kz21pck8jpis` |
| `reels(url, ...)` | profile URL + filters | `type=discover_new&discover_by=url` | `gd_lyclm20il4r5helnj` |
| `reels_all(url, ...)` | profile URL + filters | `type=discover_new&discover_by=url_all_reels` | `gd_lyclm20il4r5helnj` |

---

## Implementation Order

> **Prerequisites completed:**
> - ✅ `DatasetAPIClient.trigger()` supports `extra_params` for discovery
> - ✅ `base.py._trigger_scrape_async()` supports optional `dataset_id`
> - ✅ `validate_instagram_date()` added to `utils/validation.py`
> - ✅ `COST_PER_RECORD_INSTAGRAM` exists in `constants.py`

1. **Create `__init__.py`** - Export classes
2. **Create `scraper.py`** - InstagramScraper with profiles, posts, reels, comments
3. **Create `search.py`** - InstagramSearchScraper with discovery methods
4. **Test URL-based methods** - Verify profiles, posts, reels, comments work
5. **Test discovery methods** - Verify search/discovery methods work
6. **Integration test** - Test via BrightDataClient

---

## Notes

### Discovery Query Parameters ✅ RESOLVED

The discovery endpoints require special query parameters:
- `type=discover_new` - Indicates discovery mode
- `discover_by=user_name` - For profile discovery by username
- `discover_by=url` - For posts/reels discovery from profile
- `discover_by=url_all_reels` - For all reels from profile

**Resolution:** `DatasetAPIClient.trigger()` now accepts `extra_params: Optional[Dict[str, str]]` parameter. Pass discovery params as:
```python
extra_params={"type": "discover_new", "discover_by": "user_name"}
```

### Date Format ✅ RESOLVED

Instagram API uses `MM-DD-YYYY` format (e.g., "01-01-2025"), not ISO format.

**Resolution:** Use `validate_instagram_date()` from `src/brightdata/utils/validation.py` to validate date inputs:
```python
from ..utils.validation import validate_instagram_date

if start_date:
    validate_instagram_date(start_date)  # Raises ValidationError if invalid
```

### Post Types

For posts discovery, valid `post_type` values:
- `"Post"` - Regular posts
- `"Reel"` - Reels/videos

### Optional Parameters ✅ RESOLVED

When optional parameters (like `start_date`, `end_date`, `num_of_posts`) are None, **omit them from the payload** rather than sending empty strings. This follows SDK convention and was verified via probe testing.

```python
# Correct - omit None values
payload = {"url": url}
if num_of_posts is not None:
    payload["num_of_posts"] = num_of_posts
if start_date:
    validate_instagram_date(start_date)
    payload["start_date"] = start_date
```

---

## Method Count Summary

| Class | Async Methods | Sync Methods | Total |
|-------|---------------|--------------|-------|
| InstagramScraper | 16 (4 resources × 4 methods each) | 16 | 32 |
| InstagramSearchScraper | 4 | 4 | 8 |
| **Total** | **20** | **20** | **40** |
