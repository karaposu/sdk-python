# Instagram Scraper - Step-by-Step Implementation Plan

## Overview

This document provides a detailed, step-by-step implementation plan for the Instagram scraper, based on thorough analysis of Amazon and LinkedIn scraper implementations.

**Key Principle:** Separate implementation into two distinct phases:
- **Phase 1: InstagramScraper (scraper.py)** - URL-based extraction
- **Phase 2: InstagramSearchScraper (search.py)** - Parameter-based discovery

---

## Prerequisites (Already Completed)

Before starting implementation, these infrastructure changes were made:

| Prerequisite | File | Status |
|--------------|------|--------|
| `extra_params` support for discovery | `api_client.py` | ✅ Done |
| `dataset_id` parameter in base | `base.py` | ✅ Done |
| Instagram date validation | `validation.py` | ✅ Done |
| Cost constant | `constants.py` | ✅ Exists |

---

## Phase 0: Setup

### Step 0.1: Create Directory Structure

```bash
mkdir -p src/brightdata/scrapers/instagram
touch src/brightdata/scrapers/instagram/__init__.py
touch src/brightdata/scrapers/instagram/scraper.py
touch src/brightdata/scrapers/instagram/search.py
```

### Step 0.2: Create `__init__.py`

**File:** `src/brightdata/scrapers/instagram/__init__.py`

```python
"""Instagram scrapers for URL-based and parameter-based extraction."""

from .scraper import InstagramScraper
from .search import InstagramSearchScraper

__all__ = ["InstagramScraper", "InstagramSearchScraper"]
```

**Why this pattern:**
- Matches Amazon and LinkedIn structure
- Clean public API surface
- Two classes for two distinct use cases

---

## Phase 1: InstagramScraper (URL-Based Extraction)

This phase implements `scraper.py` - the URL-based extraction class.

### Step 1.1: Class Skeleton

**File:** `src/brightdata/scrapers/instagram/scraper.py`

Create the basic class structure with imports and constants:

```python
"""
Instagram URL-based scraper for extracting data from Instagram URLs.

Supports:
- Profile extraction from profile URLs
- Post extraction from post URLs
- Reel extraction from reel URLs
- Comment extraction from post/reel URLs
"""

import asyncio
from typing import List, Any, Optional, Union

from ..base import BaseWebScraper
from ..registry import register
from ..job import ScrapeJob
from ...models import ScrapeResult
from ...constants import (
    COST_PER_RECORD_INSTAGRAM,
    DEFAULT_TIMEOUT_SHORT,
    DEFAULT_POLL_INTERVAL,
)
from ...utils.validation import validate_url, validate_url_list
from ...utils.function_detection import get_caller_function_name


@register("instagram")
class InstagramScraper(BaseWebScraper):
    """
    Instagram scraper for URL-based data extraction.

    Extracts structured data from Instagram URLs including profiles,
    posts, reels, and comments.

    Example:
        >>> async with InstagramScraper(bearer_token="...") as scraper:
        ...     result = await scraper.profiles("https://instagram.com/nasa")
        ...     print(result.data)
    """

    # Dataset IDs for different content types
    DATASET_ID = "gd_l1vikfch901nx3by4"  # Profiles (default)
    DATASET_ID_POSTS = "gd_lk5ns7kz21pck8jpis"
    DATASET_ID_REELS = "gd_lyclm20il4r5helnj"
    DATASET_ID_COMMENTS = "gd_ltppn085pokosxh13"

    # Platform configuration
    PLATFORM_NAME = "instagram"
    MIN_POLL_TIMEOUT = DEFAULT_TIMEOUT_SHORT  # 180s
    COST_PER_RECORD = COST_PER_RECORD_INSTAGRAM  # 0.002
```

**Key Points:**
- Inherits from `BaseWebScraper` (like LinkedIn)
- Uses `@register("instagram")` for registry (like Amazon/LinkedIn)
- Defines 4 dataset IDs for 4 content types
- Uses same timeout as LinkedIn (180s)

### Step 1.2: Implement `_scrape_urls()` Helper

This is the **core pattern** used by both Amazon and LinkedIn. Add this private method:

```python
    # ============================================================================
    # INTERNAL HELPERS
    # ============================================================================

    async def _scrape_urls(
        self,
        url: Union[str, List[str]],
        dataset_id: str,
        timeout: int,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """
        Internal method to scrape URLs with specified dataset.

        Args:
            url: Single URL or list of URLs to scrape
            dataset_id: Bright Data dataset identifier for this content type
            timeout: Maximum seconds to wait for results

        Returns:
            ScrapeResult for single URL, List[ScrapeResult] for multiple URLs
        """
        # Normalize input
        is_single = isinstance(url, str)
        url_list = [url] if is_single else url

        # Validate
        if is_single:
            validate_url(url)
        else:
            validate_url_list(url_list)

        # Build simple payload
        payload = [{"url": u} for u in url_list]

        # Get SDK function name for tracking
        sdk_function = get_caller_function_name()

        # Execute workflow
        result = await self.workflow_executor.execute(
            payload=payload,
            dataset_id=dataset_id,
            poll_interval=DEFAULT_POLL_INTERVAL,
            poll_timeout=timeout,
            include_errors=True,
            sdk_function=sdk_function,
            normalize_func=self.normalize_result,
        )

        # Transform result based on input type
        if is_single and isinstance(result.data, list) and len(result.data) == 1:
            # Single URL: unwrap single item
            result.url = url if isinstance(url, str) else url[0]
            result.data = result.data[0]
            return result
        elif not is_single and isinstance(result.data, list):
            # Multiple URLs: create individual ScrapeResult for each
            results = []
            for url_item, data_item in zip(url_list, result.data):
                individual_result = ScrapeResult(
                    success=True,
                    data=data_item,
                    url=url_item,
                    error=None,
                    platform=result.platform,
                    method=result.method,
                    trigger_sent_at=result.trigger_sent_at,
                    snapshot_id_received_at=result.snapshot_id_received_at,
                    snapshot_polled_at=result.snapshot_polled_at,
                    data_fetched_at=result.data_fetched_at,
                    snapshot_id=result.snapshot_id,
                    cost=result.cost / len(result.data) if result.cost else None,
                )
                results.append(individual_result)
            return results

        return result
```

**Why this pattern:**
- Copied from LinkedIn's `_scrape_urls()` (lines 399-462 in linkedin/scraper.py)
- Handles single/multiple URL input gracefully
- Divides cost across multiple results
- Preserves timing metadata

### Step 1.3: Implement Profiles Methods

Add profiles extraction methods:

```python
    # ============================================================================
    # PROFILES (URL-based extraction)
    # ============================================================================

    async def profiles(
        self,
        url: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """
        Extract profile data from Instagram profile URLs.

        Args:
            url: Profile URL or list of profile URLs
                 Example: "https://www.instagram.com/nasa/"
            timeout: Maximum seconds to wait (default: 180)

        Returns:
            ScrapeResult for single URL, List[ScrapeResult] for multiple URLs

        Example:
            >>> result = await scraper.profiles("https://instagram.com/nasa")
            >>> print(result.data["followers"])
        """
        return await self._scrape_urls(
            url=url,
            dataset_id=self.DATASET_ID,
            timeout=timeout,
        )

    def profiles_sync(
        self,
        url: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """Synchronous version of profiles(). See profiles() for documentation."""
        async def _run():
            async with self.engine:
                return await self.profiles(url, timeout)
        return asyncio.run(_run())

    async def profiles_trigger(
        self, url: Union[str, List[str]]
    ) -> ScrapeJob:
        """
        Trigger profile extraction job without waiting for results.

        Args:
            url: Profile URL or list of profile URLs

        Returns:
            ScrapeJob for status checking and result fetching

        Example:
            >>> job = await scraper.profiles_trigger("https://instagram.com/nasa")
            >>> status = await job.status()
            >>> if status == "ready":
            ...     data = await job.fetch()
        """
        sdk_function = get_caller_function_name()
        return await self._trigger_scrape_async(
            urls=url,
            dataset_id=self.DATASET_ID,
            sdk_function=sdk_function,
        )

    def profiles_trigger_sync(self, url: Union[str, List[str]]) -> ScrapeJob:
        """Synchronous version of profiles_trigger()."""
        async def _run():
            async with self.engine:
                return await self.profiles_trigger(url)
        return asyncio.run(_run())

    async def profiles_status(self, snapshot_id: str) -> str:
        """Check status of a profiles extraction job."""
        return await self._check_status_async(snapshot_id)

    def profiles_status_sync(self, snapshot_id: str) -> str:
        """Synchronous version of profiles_status()."""
        async def _run():
            async with self.engine:
                return await self.profiles_status(snapshot_id)
        return asyncio.run(_run())

    async def profiles_fetch(self, snapshot_id: str) -> Any:
        """Fetch results of a completed profiles extraction job."""
        return await self._fetch_results_async(snapshot_id)

    def profiles_fetch_sync(self, snapshot_id: str) -> Any:
        """Synchronous version of profiles_fetch()."""
        async def _run():
            async with self.engine:
                return await self.profiles_fetch(snapshot_id)
        return asyncio.run(_run())
```

**Pattern Notes:**
- 8 methods per content type: async main, sync main, trigger, trigger_sync, status, status_sync, fetch, fetch_sync
- Uses `_scrape_urls()` for main methods
- Uses inherited `_trigger_scrape_async()`, `_check_status_async()`, `_fetch_results_async()` from BaseWebScraper
- Passes `dataset_id=self.DATASET_ID` explicitly

### Step 1.4: Implement Posts Methods

Repeat the pattern for posts (use `DATASET_ID_POSTS`):

```python
    # ============================================================================
    # POSTS (URL-based extraction)
    # ============================================================================

    async def posts(
        self,
        url: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """
        Extract post data from Instagram post URLs.

        Args:
            url: Post URL or list of post URLs
                 Example: "https://www.instagram.com/p/Cuf4s0MNqNr"
            timeout: Maximum seconds to wait (default: 180)

        Returns:
            ScrapeResult for single URL, List[ScrapeResult] for multiple URLs
        """
        return await self._scrape_urls(
            url=url,
            dataset_id=self.DATASET_ID_POSTS,
            timeout=timeout,
        )

    def posts_sync(
        self,
        url: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """Synchronous version of posts()."""
        async def _run():
            async with self.engine:
                return await self.posts(url, timeout)
        return asyncio.run(_run())

    async def posts_trigger(self, url: Union[str, List[str]]) -> ScrapeJob:
        """Trigger post extraction job without waiting for results."""
        sdk_function = get_caller_function_name()
        return await self._trigger_scrape_async(
            urls=url,
            dataset_id=self.DATASET_ID_POSTS,
            sdk_function=sdk_function,
        )

    def posts_trigger_sync(self, url: Union[str, List[str]]) -> ScrapeJob:
        """Synchronous version of posts_trigger()."""
        async def _run():
            async with self.engine:
                return await self.posts_trigger(url)
        return asyncio.run(_run())

    async def posts_status(self, snapshot_id: str) -> str:
        """Check status of a posts extraction job."""
        return await self._check_status_async(snapshot_id)

    def posts_status_sync(self, snapshot_id: str) -> str:
        """Synchronous version of posts_status()."""
        async def _run():
            async with self.engine:
                return await self.posts_status(snapshot_id)
        return asyncio.run(_run())

    async def posts_fetch(self, snapshot_id: str) -> Any:
        """Fetch results of a completed posts extraction job."""
        return await self._fetch_results_async(snapshot_id)

    def posts_fetch_sync(self, snapshot_id: str) -> Any:
        """Synchronous version of posts_fetch()."""
        async def _run():
            async with self.engine:
                return await self.posts_fetch(snapshot_id)
        return asyncio.run(_run())
```

### Step 1.5: Implement Reels Methods

Repeat the pattern for reels (use `DATASET_ID_REELS`):

```python
    # ============================================================================
    # REELS (URL-based extraction)
    # ============================================================================

    async def reels(
        self,
        url: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """
        Extract reel data from Instagram reel URLs.

        Args:
            url: Reel URL or list of reel URLs
                 Example: "https://www.instagram.com/reel/C5Rdyj_q7YN/"
            timeout: Maximum seconds to wait (default: 180)

        Returns:
            ScrapeResult for single URL, List[ScrapeResult] for multiple URLs
        """
        return await self._scrape_urls(
            url=url,
            dataset_id=self.DATASET_ID_REELS,
            timeout=timeout,
        )

    def reels_sync(
        self,
        url: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """Synchronous version of reels()."""
        async def _run():
            async with self.engine:
                return await self.reels(url, timeout)
        return asyncio.run(_run())

    async def reels_trigger(self, url: Union[str, List[str]]) -> ScrapeJob:
        """Trigger reel extraction job without waiting for results."""
        sdk_function = get_caller_function_name()
        return await self._trigger_scrape_async(
            urls=url,
            dataset_id=self.DATASET_ID_REELS,
            sdk_function=sdk_function,
        )

    def reels_trigger_sync(self, url: Union[str, List[str]]) -> ScrapeJob:
        """Synchronous version of reels_trigger()."""
        async def _run():
            async with self.engine:
                return await self.reels_trigger(url)
        return asyncio.run(_run())

    async def reels_status(self, snapshot_id: str) -> str:
        """Check status of a reels extraction job."""
        return await self._check_status_async(snapshot_id)

    def reels_status_sync(self, snapshot_id: str) -> str:
        """Synchronous version of reels_status()."""
        async def _run():
            async with self.engine:
                return await self.reels_status(snapshot_id)
        return asyncio.run(_run())

    async def reels_fetch(self, snapshot_id: str) -> Any:
        """Fetch results of a completed reels extraction job."""
        return await self._fetch_results_async(snapshot_id)

    def reels_fetch_sync(self, snapshot_id: str) -> Any:
        """Synchronous version of reels_fetch()."""
        async def _run():
            async with self.engine:
                return await self.reels_fetch(snapshot_id)
        return asyncio.run(_run())
```

### Step 1.6: Implement Comments Methods

Repeat the pattern for comments (use `DATASET_ID_COMMENTS`):

```python
    # ============================================================================
    # COMMENTS (URL-based extraction)
    # ============================================================================

    async def comments(
        self,
        url: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """
        Extract comments from Instagram post or reel URLs.

        Args:
            url: Post/reel URL or list of URLs
                 Example: "https://www.instagram.com/p/CesFC7JLyFl/"
            timeout: Maximum seconds to wait (default: 180)

        Returns:
            ScrapeResult for single URL, List[ScrapeResult] for multiple URLs
        """
        return await self._scrape_urls(
            url=url,
            dataset_id=self.DATASET_ID_COMMENTS,
            timeout=timeout,
        )

    def comments_sync(
        self,
        url: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """Synchronous version of comments()."""
        async def _run():
            async with self.engine:
                return await self.comments(url, timeout)
        return asyncio.run(_run())

    async def comments_trigger(self, url: Union[str, List[str]]) -> ScrapeJob:
        """Trigger comment extraction job without waiting for results."""
        sdk_function = get_caller_function_name()
        return await self._trigger_scrape_async(
            urls=url,
            dataset_id=self.DATASET_ID_COMMENTS,
            sdk_function=sdk_function,
        )

    def comments_trigger_sync(self, url: Union[str, List[str]]) -> ScrapeJob:
        """Synchronous version of comments_trigger()."""
        async def _run():
            async with self.engine:
                return await self.comments_trigger(url)
        return asyncio.run(_run())

    async def comments_status(self, snapshot_id: str) -> str:
        """Check status of a comments extraction job."""
        return await self._check_status_async(snapshot_id)

    def comments_status_sync(self, snapshot_id: str) -> str:
        """Synchronous version of comments_status()."""
        async def _run():
            async with self.engine:
                return await self.comments_status(snapshot_id)
        return asyncio.run(_run())

    async def comments_fetch(self, snapshot_id: str) -> Any:
        """Fetch results of a completed comments extraction job."""
        return await self._fetch_results_async(snapshot_id)

    def comments_fetch_sync(self, snapshot_id: str) -> Any:
        """Synchronous version of comments_fetch()."""
        async def _run():
            async with self.engine:
                return await self.comments_fetch(snapshot_id)
        return asyncio.run(_run())
```

### Step 1.7: Verify Phase 1

After completing Phase 1, verify:

```bash
# Run unit tests
pytest tests/unit/ -v

# Import test
python -c "from brightdata.scrapers.instagram import InstagramScraper; print('OK')"
```

**Phase 1 Complete Checklist:**
- [ ] `__init__.py` created
- [ ] `scraper.py` created with InstagramScraper class
- [ ] 4 content types implemented (profiles, posts, reels, comments)
- [ ] 8 methods per content type (32 methods total)
- [ ] Unit tests pass
- [ ] Import works

---

## Phase 2: InstagramSearchScraper (Parameter-Based Discovery)

This phase implements `search.py` - the parameter-based discovery class.

### Step 2.1: Class Skeleton

**File:** `src/brightdata/scrapers/instagram/search.py`

```python
"""
Instagram parameter-based discovery scraper.

Supports:
- Profile discovery by username
- Posts discovery from profile with filters
- Reels discovery from profile with filters
"""

import asyncio
import os
from typing import List, Dict, Any, Optional, Union

from ..api_client import DatasetAPIClient
from ..workflow import WorkflowExecutor
from ...core.engine import AsyncEngine
from ...models import ScrapeResult
from ...exceptions import ValidationError
from ...constants import (
    COST_PER_RECORD_INSTAGRAM,
    DEFAULT_TIMEOUT_SHORT,
    DEFAULT_POLL_INTERVAL,
)
from ...utils.validation import validate_url, validate_url_list, validate_instagram_date
from ...utils.function_detection import get_caller_function_name


class InstagramSearchScraper:
    """
    Instagram scraper for parameter-based content discovery.

    Unlike InstagramScraper (URL-based), this class discovers content
    using parameters like username, date ranges, and filters.

    Example:
        >>> scraper = InstagramSearchScraper(bearer_token="...")
        >>> result = await scraper.profiles("nasa")  # Find by username
        >>> result = await scraper.posts(
        ...     url="https://instagram.com/nasa",
        ...     num_of_posts=10,
        ...     start_date="01-01-2025"
        ... )
    """

    # Dataset IDs
    DATASET_ID_PROFILES = "gd_l1vikfch901nx3by4"
    DATASET_ID_POSTS = "gd_lk5ns7kz21pck8jpis"
    DATASET_ID_REELS = "gd_lyclm20il4r5helnj"

    # Platform configuration
    PLATFORM_NAME = "instagram"
    MIN_POLL_TIMEOUT = DEFAULT_TIMEOUT_SHORT
    COST_PER_RECORD = COST_PER_RECORD_INSTAGRAM

    def __init__(
        self,
        bearer_token: Optional[str] = None,
        engine: Optional[AsyncEngine] = None,
    ):
        """
        Initialize Instagram search scraper.

        Args:
            bearer_token: Bright Data API token. If None, loads from environment.
            engine: Optional AsyncEngine instance for connection reuse.
        """
        self.bearer_token = bearer_token or os.getenv("BRIGHTDATA_API_TOKEN")
        if not self.bearer_token:
            raise ValidationError(
                "Bearer token required for Instagram search. "
                "Provide bearer_token parameter or set BRIGHTDATA_API_TOKEN environment variable."
            )

        # Reuse engine if provided, otherwise create new
        self.engine = engine if engine is not None else AsyncEngine(self.bearer_token)
        self.api_client = DatasetAPIClient(self.engine)
        self.workflow_executor = WorkflowExecutor(
            api_client=self.api_client,
            platform_name=self.PLATFORM_NAME,
            cost_per_record=self.COST_PER_RECORD,
        )
```

**Key Differences from InstagramScraper:**
- Does NOT inherit from `BaseWebScraper` (like LinkedInSearchScraper)
- Creates own `AsyncEngine`, `DatasetAPIClient`, `WorkflowExecutor`
- No `@register()` decorator (search scrapers aren't registered)

### Step 2.2: Implement `_execute_discovery()` Helper

This is the core method for discovery operations. Unlike `_scrape_urls()`, it needs to pass `extra_params`:

```python
    # ============================================================================
    # INTERNAL HELPERS
    # ============================================================================

    async def _execute_discovery(
        self,
        payload: List[Dict[str, Any]],
        dataset_id: str,
        discover_by: str,
        timeout: int,
    ) -> ScrapeResult:
        """
        Execute discovery operation with extra query parameters.

        Args:
            payload: Request payload
            dataset_id: Bright Data dataset identifier
            discover_by: Discovery type (user_name, url, url_all_reels)
            timeout: Maximum seconds to wait

        Returns:
            ScrapeResult with discovered data
        """
        sdk_function = get_caller_function_name()

        # Build extra params for discovery endpoints
        extra_params = {
            "type": "discover_new",
            "discover_by": discover_by,
        }

        # Use workflow_executor.execute() with extra_params support
        # (extra_params was added to WorkflowExecutor for Instagram discovery)
        result = await self.workflow_executor.execute(
            payload=payload,
            dataset_id=dataset_id,
            poll_interval=DEFAULT_POLL_INTERVAL,
            poll_timeout=timeout,
            include_errors=True,
            sdk_function=sdk_function,
            extra_params=extra_params,
        )

        return result
```

### Step 2.3: Implement Profiles Discovery

Discovery by username (NOT URL):

```python
    # ============================================================================
    # PROFILES DISCOVERY (by username)
    # ============================================================================

    async def profiles(
        self,
        user_name: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> ScrapeResult:
        """
        Discover Instagram profiles by username.

        Args:
            user_name: Username or list of usernames (without @)
                       Example: "nasa" or ["nasa", "spacex"]
            timeout: Maximum seconds to wait (default: 180)

        Returns:
            ScrapeResult with profile data

        Example:
            >>> result = await scraper.profiles("nasa")
            >>> print(result.data)
        """
        # Normalize to list
        user_names = [user_name] if isinstance(user_name, str) else user_name

        # Build payload - IMPORTANT: field is "user_name" with underscore
        payload = [{"user_name": name} for name in user_names]

        return await self._execute_discovery(
            payload=payload,
            dataset_id=self.DATASET_ID_PROFILES,
            discover_by="user_name",
            timeout=timeout,
        )

    def profiles_sync(
        self,
        user_name: Union[str, List[str]],
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> ScrapeResult:
        """Synchronous version of profiles()."""
        async def _run():
            async with self.engine:
                return await self.profiles(user_name, timeout)
        return asyncio.run(_run())
```

**Critical Note:** The field is `user_name` (with underscore), NOT `username`.

### Step 2.4: Implement Posts Discovery

Discovery by profile URL with optional filters:

```python
    # ============================================================================
    # POSTS DISCOVERY (by profile URL + filters)
    # ============================================================================

    async def posts(
        self,
        url: Union[str, List[str]],
        num_of_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        post_type: Optional[str] = None,
        posts_to_not_include: Optional[List[str]] = None,
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> ScrapeResult:
        """
        Discover posts from Instagram profile with optional filters.

        Args:
            url: Profile URL or list of profile URLs
                 Example: "https://www.instagram.com/nasa/"
            num_of_posts: Maximum number of posts to return
            start_date: Filter posts after this date (format: MM-DD-YYYY)
            end_date: Filter posts before this date (format: MM-DD-YYYY)
            post_type: Filter by type - "Post" or "Reel"
            posts_to_not_include: List of post IDs to exclude
            timeout: Maximum seconds to wait (default: 180)

        Returns:
            ScrapeResult with discovered posts

        Example:
            >>> result = await scraper.posts(
            ...     url="https://instagram.com/nasa",
            ...     num_of_posts=10,
            ...     start_date="01-01-2025",
            ...     post_type="Post"
            ... )
        """
        # Normalize URL to list
        urls = [url] if isinstance(url, str) else url

        # Validate URLs
        validate_url_list(urls)

        # Validate dates if provided
        if start_date:
            validate_instagram_date(start_date)
        if end_date:
            validate_instagram_date(end_date)

        # Build payload - omit None values (don't send empty strings)
        payload = []
        for u in urls:
            item: Dict[str, Any] = {"url": u}

            if num_of_posts is not None:
                item["num_of_posts"] = num_of_posts
            if start_date:
                item["start_date"] = start_date
            if end_date:
                item["end_date"] = end_date
            if post_type:
                item["post_type"] = post_type
            if posts_to_not_include:
                item["posts_to_not_include"] = posts_to_not_include

            payload.append(item)

        return await self._execute_discovery(
            payload=payload,
            dataset_id=self.DATASET_ID_POSTS,
            discover_by="url",
            timeout=timeout,
        )

    def posts_sync(
        self,
        url: Union[str, List[str]],
        num_of_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        post_type: Optional[str] = None,
        posts_to_not_include: Optional[List[str]] = None,
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> ScrapeResult:
        """Synchronous version of posts()."""
        async def _run():
            async with self.engine:
                return await self.posts(
                    url, num_of_posts, start_date, end_date,
                    post_type, posts_to_not_include, timeout
                )
        return asyncio.run(_run())
```

### Step 2.5: Implement Reels Discovery

Discovery by profile URL:

```python
    # ============================================================================
    # REELS DISCOVERY (by profile URL)
    # ============================================================================

    async def reels(
        self,
        url: Union[str, List[str]],
        num_of_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> ScrapeResult:
        """
        Discover reels from Instagram profile.

        Args:
            url: Profile URL or list of profile URLs
            num_of_posts: Maximum number of reels to return
            start_date: Filter reels after this date (format: MM-DD-YYYY)
            end_date: Filter reels before this date (format: MM-DD-YYYY)
            timeout: Maximum seconds to wait (default: 180)

        Returns:
            ScrapeResult with discovered reels
        """
        # Normalize and validate
        urls = [url] if isinstance(url, str) else url
        validate_url_list(urls)

        if start_date:
            validate_instagram_date(start_date)
        if end_date:
            validate_instagram_date(end_date)

        # Build payload
        payload = []
        for u in urls:
            item: Dict[str, Any] = {"url": u}
            if num_of_posts is not None:
                item["num_of_posts"] = num_of_posts
            if start_date:
                item["start_date"] = start_date
            if end_date:
                item["end_date"] = end_date
            payload.append(item)

        return await self._execute_discovery(
            payload=payload,
            dataset_id=self.DATASET_ID_REELS,
            discover_by="url",
            timeout=timeout,
        )

    def reels_sync(
        self,
        url: Union[str, List[str]],
        num_of_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> ScrapeResult:
        """Synchronous version of reels()."""
        async def _run():
            async with self.engine:
                return await self.reels(url, num_of_posts, start_date, end_date, timeout)
        return asyncio.run(_run())
```

### Step 2.6: Implement Reels All Discovery

Same as reels but uses `discover_by=url_all_reels`:

```python
    # ============================================================================
    # REELS ALL DISCOVERY (by profile URL - all reels)
    # ============================================================================

    async def reels_all(
        self,
        url: Union[str, List[str]],
        num_of_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> ScrapeResult:
        """
        Discover ALL reels from Instagram profile.

        This differs from reels() by using discover_by=url_all_reels,
        which may return more comprehensive results including archived reels.

        Args:
            url: Profile URL or list of profile URLs
            num_of_posts: Maximum number of reels to return
            start_date: Filter reels after this date (format: MM-DD-YYYY)
            end_date: Filter reels before this date (format: MM-DD-YYYY)
            timeout: Maximum seconds to wait (default: 180)

        Returns:
            ScrapeResult with discovered reels
        """
        # Normalize and validate
        urls = [url] if isinstance(url, str) else url
        validate_url_list(urls)

        if start_date:
            validate_instagram_date(start_date)
        if end_date:
            validate_instagram_date(end_date)

        # Build payload
        payload = []
        for u in urls:
            item: Dict[str, Any] = {"url": u}
            if num_of_posts is not None:
                item["num_of_posts"] = num_of_posts
            if start_date:
                item["start_date"] = start_date
            if end_date:
                item["end_date"] = end_date
            payload.append(item)

        # Key difference: discover_by=url_all_reels
        return await self._execute_discovery(
            payload=payload,
            dataset_id=self.DATASET_ID_REELS,
            discover_by="url_all_reels",
            timeout=timeout,
        )

    def reels_all_sync(
        self,
        url: Union[str, List[str]],
        num_of_posts: Optional[int] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT_SHORT,
    ) -> ScrapeResult:
        """Synchronous version of reels_all()."""
        async def _run():
            async with self.engine:
                return await self.reels_all(url, num_of_posts, start_date, end_date, timeout)
        return asyncio.run(_run())
```

### Step 2.7: Add Context Manager Support

For standalone usage:

```python
    # ============================================================================
    # CONTEXT MANAGER SUPPORT
    # ============================================================================

    async def __aenter__(self):
        """Async context manager entry."""
        await self.engine.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.engine.__aexit__(exc_type, exc_val, exc_tb)
```

### Step 2.8: Verify Phase 2

After completing Phase 2, verify:

```bash
# Run unit tests
pytest tests/unit/ -v

# Import test
python -c "from brightdata.scrapers.instagram import InstagramSearchScraper; print('OK')"
```

**Phase 2 Complete Checklist:**
- [ ] `search.py` created with InstagramSearchScraper class
- [ ] 4 discovery methods (profiles, posts, reels, reels_all)
- [ ] 8 total methods (4 async + 4 sync)
- [ ] Extra params passed correctly for discovery
- [ ] Date validation working
- [ ] Unit tests pass
- [ ] Import works

---

## Phase 3: Integration Testing

### Step 3.1: Verify Client Integration

Test that Instagram scraper is accessible via BrightDataClient:

```python
# Test import via client
from brightdata import BrightDataClient

client = BrightDataClient(bearer_token="...")

# These should work (via @register decorator)
assert hasattr(client.scrape, 'instagram')
assert hasattr(client.scrape.instagram, 'profiles')
assert hasattr(client.scrape.instagram, 'posts')
assert hasattr(client.scrape.instagram, 'reels')
assert hasattr(client.scrape.instagram, 'comments')

# Search scraper needs separate setup
# (search scrapers are typically accessed differently)
```

### Step 3.2: Create Integration Test Script

Create `probe_tests/test_instagram_integration.py`:

```python
"""Integration test for Instagram scraper."""

import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

async def test_url_based():
    """Test URL-based extraction."""
    from brightdata.scrapers.instagram import InstagramScraper

    async with InstagramScraper() as scraper:
        # Test profiles
        result = await scraper.profiles("https://www.instagram.com/instagram/")
        print(f"Profiles: {result.success}")

        # Test posts (need valid post URL)
        # result = await scraper.posts("https://www.instagram.com/p/VALID_POST_ID/")

async def test_discovery():
    """Test parameter-based discovery."""
    from brightdata.scrapers.instagram import InstagramSearchScraper

    async with InstagramSearchScraper() as scraper:
        # Test profiles by username
        result = await scraper.profiles("instagram")
        print(f"Profiles discovery: {result.success}")

        # Test posts discovery
        result = await scraper.posts(
            url="https://www.instagram.com/instagram/",
            num_of_posts=5
        )
        print(f"Posts discovery: {result.success}")

if __name__ == "__main__":
    asyncio.run(test_url_based())
    asyncio.run(test_discovery())
```

---

## Summary

### Files Created

| File | Purpose | Methods |
|------|---------|---------|
| `__init__.py` | Exports | 2 classes |
| `scraper.py` | URL-based extraction | 32 methods |
| `search.py` | Parameter-based discovery | 8 methods |

### Method Count

| Class | Content Types | Methods per Type | Total |
|-------|---------------|------------------|-------|
| InstagramScraper | 4 | 8 | 32 |
| InstagramSearchScraper | 4 | 2 | 8 |
| **Total** | - | - | **40** |

### Key Implementation Patterns

1. **URL-based (scraper.py):**
   - Inherits from `BaseWebScraper`
   - Uses `_scrape_urls()` pattern like LinkedIn
   - Passes `dataset_id` to differentiate content types

2. **Discovery (search.py):**
   - Standalone class (no inheritance)
   - Creates own engine/api_client/workflow_executor
   - Uses `extra_params` for discovery query parameters
   - Validates Instagram date format (MM-DD-YYYY)
   - Omits None values from payload

### Important Notes

- Field is `user_name` (with underscore) for profile discovery
- Date format is MM-DD-YYYY (NOT ISO)
- Omit optional params when None (don't send empty strings)
- `reels()` uses `discover_by=url`, `reels_all()` uses `discover_by=url_all_reels`
