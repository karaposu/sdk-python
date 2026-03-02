# Low-Level Implementation Plan: Async + Sync Adapter

> **REVISED**: Updated based on plan critique findings (2025-12-11)

This document provides specific code changes required to implement Approach 2.

---

## Table of Contents

1. [Phase 1: Create SyncBrightDataClient](#phase-1-create-syncbrightdataclient)
2. [Phase 2: Add Context Manager to BaseWebScraper](#phase-2-add-context-manager-to-basewebscraper)
3. [Phase 3: Fix SERP Base Class](#phase-3-fix-serp-base-class)
4. [Phase 4: BrightDataClient - Remove Nested Contexts](#phase-4-brightdataclient---remove-nested-contexts)
5. [Phase 5: BrightDataClient - Remove Sync Wrappers](#phase-5-brightdataclient---remove-sync-wrappers)
6. [Phase 6: Services - Remove Sync Methods](#phase-6-services---remove-sync-methods)
7. [Phase 7: Scrapers - Remove Sync Wrappers](#phase-7-scrapers---remove-sync-wrappers)
8. [Phase 8: Fix ScrapeJob Engine Lifecycle](#phase-8-fix-scrapejob-engine-lifecycle)
9. [Phase 9: Update Exports and Tests](#phase-9-update-exports-and-tests)

---

## Phase 1: Create SyncBrightDataClient

### New File: `src/brightdata/sync_client.py`

This is the complete sync adapter with all fixes from the plan critique.

```python
"""
Synchronous client adapter for Bright Data SDK.

Provides sync interface using persistent event loop for optimal performance.
"""

import asyncio
from typing import Optional, List, Dict, Any, Union

from .client import BrightDataClient
from .models import ScrapeResult, SearchResult
from .types import AccountInfo


class SyncBrightDataClient:
    """
    Synchronous adapter for BrightDataClient.

    Uses a persistent event loop for all operations, providing better
    performance than repeated asyncio.run() calls.

    WARNING: This client is NOT thread-safe. For multi-threaded usage,
    create a separate SyncBrightDataClient per thread.

    Example:
        >>> with SyncBrightDataClient(token="...") as client:
        ...     zones = client.list_zones()
        ...     result = client.scrape.amazon.products(url)
    """

    def __init__(
        self,
        token: Optional[str] = None,
        customer_id: Optional[str] = None,
        timeout: int = 30,
        web_unlocker_zone: Optional[str] = None,
        serp_zone: Optional[str] = None,
        browser_zone: Optional[str] = None,
        auto_create_zones: bool = True,
        validate_token: bool = False,
        rate_limit: Optional[float] = None,
        rate_period: float = 1.0,
    ):
        """
        Initialize sync client.

        Args:
            Same as BrightDataClient
        """
        # Check if we're inside an async context - FIXED logic
        try:
            asyncio.get_running_loop()
            # If we get here, there IS a running loop - this is an error
            raise RuntimeError(
                "SyncBrightDataClient cannot be used inside async context. "
                "Use BrightDataClient with async/await instead."
            )
        except RuntimeError as e:
            # Only pass if it's the "no running event loop" error
            if "no running event loop" not in str(e).lower():
                raise  # Re-raise our custom error or other RuntimeErrors
            # No running loop - correct for sync usage, continue

        self._async_client = BrightDataClient(
            token=token,
            customer_id=customer_id,
            timeout=timeout,
            web_unlocker_zone=web_unlocker_zone,
            serp_zone=serp_zone,
            browser_zone=browser_zone,
            auto_create_zones=auto_create_zones,
            validate_token=False,  # Will validate during __enter__
            rate_limit=rate_limit,
            rate_period=rate_period,
        )
        self._validate_token = validate_token
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._scrape: Optional["SyncScrapeService"] = None
        self._search: Optional["SyncSearchService"] = None
        self._crawler: Optional["SyncCrawlerService"] = None

    def __enter__(self):
        """Initialize persistent event loop and async client."""
        # Create persistent loop
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)

        # Initialize async client
        self._loop.run_until_complete(self._async_client.__aenter__())

        # Validate token if requested
        if self._validate_token:
            is_valid = self._loop.run_until_complete(
                self._async_client.test_connection()
            )
            if not is_valid:
                self.__exit__(None, None, None)
                from .exceptions import AuthenticationError
                raise AuthenticationError(
                    "Token validation failed. Token appears to be invalid."
                )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Cleanup async client and event loop."""
        if self._loop is None:
            return

        try:
            # Cleanup async client
            self._loop.run_until_complete(
                self._async_client.__aexit__(exc_type, exc_val, exc_tb)
            )
        finally:
            # Close the loop
            self._loop.close()
            self._loop = None

    def _run(self, coro):
        """Run coroutine in persistent loop."""
        if self._loop is None:
            raise RuntimeError(
                "SyncBrightDataClient not initialized. "
                "Use: with SyncBrightDataClient() as client: ..."
            )
        return self._loop.run_until_complete(coro)

    # ========================================
    # Utility Methods
    # ========================================

    def list_zones(self) -> List[Dict[str, Any]]:
        """List all active zones."""
        return self._run(self._async_client.list_zones())

    def delete_zone(self, zone_name: str) -> None:
        """Delete a zone."""
        return self._run(self._async_client.delete_zone(zone_name))

    def get_account_info(self, refresh: bool = False) -> AccountInfo:
        """Get account information."""
        return self._run(self._async_client.get_account_info(refresh=refresh))

    def test_connection(self) -> bool:
        """Test API connection."""
        return self._run(self._async_client.test_connection())

    def scrape_url(self, url, **kwargs):
        """Scrape URL using Web Unlocker."""
        return self._run(self._async_client.scrape_url(url, **kwargs))

    # ========================================
    # Service Properties
    # ========================================

    @property
    def scrape(self) -> "SyncScrapeService":
        """Access scraping services (sync)."""
        if self._scrape is None:
            self._scrape = SyncScrapeService(self._async_client.scrape, self._loop)
        return self._scrape

    @property
    def search(self) -> "SyncSearchService":
        """Access search services (sync)."""
        if self._search is None:
            self._search = SyncSearchService(self._async_client.search, self._loop)
        return self._search

    @property
    def crawler(self) -> "SyncCrawlerService":
        """Access crawler services (sync)."""
        if self._crawler is None:
            self._crawler = SyncCrawlerService(self._async_client.crawler, self._loop)
        return self._crawler

    @property
    def token(self) -> str:
        """Get API token."""
        return self._async_client.token

    def __repr__(self) -> str:
        """String representation."""
        token_preview = f"{self.token[:10]}...{self.token[-5:]}" if self.token else "None"
        status = "Initialized" if self._loop else "Not initialized"
        return f"<SyncBrightDataClient token={token_preview} status='{status}'>"


# ============================================================================
# SYNC SCRAPE SERVICE
# ============================================================================

class SyncScrapeService:
    """Sync wrapper for ScrapeService."""

    def __init__(self, async_service, loop):
        self._async = async_service
        self._loop = loop
        self._amazon = None
        self._linkedin = None
        self._instagram = None
        self._facebook = None
        self._chatgpt = None
        self._generic = None

    @property
    def amazon(self) -> "SyncAmazonScraper":
        if self._amazon is None:
            self._amazon = SyncAmazonScraper(self._async.amazon, self._loop)
        return self._amazon

    @property
    def linkedin(self) -> "SyncLinkedInScraper":
        if self._linkedin is None:
            self._linkedin = SyncLinkedInScraper(self._async.linkedin, self._loop)
        return self._linkedin

    @property
    def instagram(self) -> "SyncInstagramScraper":
        if self._instagram is None:
            self._instagram = SyncInstagramScraper(self._async.instagram, self._loop)
        return self._instagram

    @property
    def facebook(self) -> "SyncFacebookScraper":
        if self._facebook is None:
            self._facebook = SyncFacebookScraper(self._async.facebook, self._loop)
        return self._facebook

    @property
    def chatgpt(self) -> "SyncChatGPTScraper":
        if self._chatgpt is None:
            self._chatgpt = SyncChatGPTScraper(self._async.chatgpt, self._loop)
        return self._chatgpt

    @property
    def generic(self) -> "SyncGenericScraper":
        """Access generic web scraper (Web Unlocker)."""
        if self._generic is None:
            self._generic = SyncGenericScraper(self._async.generic, self._loop)
        return self._generic


class SyncGenericScraper:
    """Sync wrapper for GenericScraper (Web Unlocker)."""

    def __init__(self, async_scraper, loop):
        self._async = async_scraper
        self._loop = loop

    def url(self, url, **kwargs):
        """Scrape URL using Web Unlocker."""
        return self._loop.run_until_complete(self._async.url(url, **kwargs))


class SyncAmazonScraper:
    """Sync wrapper for AmazonScraper - COMPLETE with all methods."""

    def __init__(self, async_scraper, loop):
        self._async = async_scraper
        self._loop = loop

    # Products
    def products(self, url, **kwargs) -> ScrapeResult:
        """Scrape Amazon product details."""
        return self._loop.run_until_complete(self._async.products(url, **kwargs))

    def products_trigger(self, url, **kwargs):
        """Trigger Amazon products scrape."""
        return self._loop.run_until_complete(self._async.products_trigger(url, **kwargs))

    def products_status(self, snapshot_id):
        """Check Amazon products scrape status."""
        return self._loop.run_until_complete(self._async.products_status(snapshot_id))

    def products_fetch(self, snapshot_id):
        """Fetch Amazon products scrape results."""
        return self._loop.run_until_complete(self._async.products_fetch(snapshot_id))

    # Reviews
    def reviews(self, url, **kwargs) -> ScrapeResult:
        """Scrape Amazon reviews."""
        return self._loop.run_until_complete(self._async.reviews(url, **kwargs))

    def reviews_trigger(self, url, **kwargs):
        """Trigger Amazon reviews scrape."""
        return self._loop.run_until_complete(self._async.reviews_trigger(url, **kwargs))

    def reviews_status(self, snapshot_id):
        """Check Amazon reviews scrape status."""
        return self._loop.run_until_complete(self._async.reviews_status(snapshot_id))

    def reviews_fetch(self, snapshot_id):
        """Fetch Amazon reviews scrape results."""
        return self._loop.run_until_complete(self._async.reviews_fetch(snapshot_id))

    # Sellers
    def sellers(self, url, **kwargs) -> ScrapeResult:
        """Scrape Amazon sellers."""
        return self._loop.run_until_complete(self._async.sellers(url, **kwargs))

    def sellers_trigger(self, url, **kwargs):
        """Trigger Amazon sellers scrape."""
        return self._loop.run_until_complete(self._async.sellers_trigger(url, **kwargs))

    def sellers_status(self, snapshot_id):
        """Check Amazon sellers scrape status."""
        return self._loop.run_until_complete(self._async.sellers_status(snapshot_id))

    def sellers_fetch(self, snapshot_id):
        """Fetch Amazon sellers scrape results."""
        return self._loop.run_until_complete(self._async.sellers_fetch(snapshot_id))


class SyncLinkedInScraper:
    """Sync wrapper for LinkedInScraper - COMPLETE with all methods."""

    def __init__(self, async_scraper, loop):
        self._async = async_scraper
        self._loop = loop

    # Posts
    def posts(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts(url, **kwargs))

    def posts_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts_trigger(url, **kwargs))

    def posts_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_status(snapshot_id))

    def posts_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_fetch(snapshot_id))

    # Jobs
    def jobs(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.jobs(url, **kwargs))

    def jobs_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.jobs_trigger(url, **kwargs))

    def jobs_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.jobs_status(snapshot_id))

    def jobs_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.jobs_fetch(snapshot_id))

    # Profiles
    def profiles(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.profiles(url, **kwargs))

    def profiles_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.profiles_trigger(url, **kwargs))

    def profiles_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.profiles_status(snapshot_id))

    def profiles_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.profiles_fetch(snapshot_id))

    # Companies
    def companies(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.companies(url, **kwargs))

    def companies_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.companies_trigger(url, **kwargs))

    def companies_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.companies_status(snapshot_id))

    def companies_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.companies_fetch(snapshot_id))


class SyncInstagramScraper:
    """Sync wrapper for InstagramScraper - COMPLETE with all methods."""

    def __init__(self, async_scraper, loop):
        self._async = async_scraper
        self._loop = loop

    # Profiles
    def profiles(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.profiles(url, **kwargs))

    def profiles_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.profiles_trigger(url, **kwargs))

    def profiles_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.profiles_status(snapshot_id))

    def profiles_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.profiles_fetch(snapshot_id))

    # Posts
    def posts(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts(url, **kwargs))

    def posts_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts_trigger(url, **kwargs))

    def posts_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_status(snapshot_id))

    def posts_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_fetch(snapshot_id))

    # Comments
    def comments(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.comments(url, **kwargs))

    def comments_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.comments_trigger(url, **kwargs))

    def comments_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.comments_status(snapshot_id))

    def comments_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.comments_fetch(snapshot_id))

    # Reels
    def reels(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.reels(url, **kwargs))

    def reels_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.reels_trigger(url, **kwargs))

    def reels_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.reels_status(snapshot_id))

    def reels_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.reels_fetch(snapshot_id))


class SyncFacebookScraper:
    """Sync wrapper for FacebookScraper - COMPLETE with all methods."""

    def __init__(self, async_scraper, loop):
        self._async = async_scraper
        self._loop = loop

    # Posts by profile
    def posts_by_profile(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts_by_profile(url, **kwargs))

    def posts_by_profile_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts_by_profile_trigger(url, **kwargs))

    def posts_by_profile_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_by_profile_status(snapshot_id))

    def posts_by_profile_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_by_profile_fetch(snapshot_id))

    # Posts by group
    def posts_by_group(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts_by_group(url, **kwargs))

    def posts_by_group_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts_by_group_trigger(url, **kwargs))

    def posts_by_group_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_by_group_status(snapshot_id))

    def posts_by_group_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_by_group_fetch(snapshot_id))

    # Posts by URL
    def posts_by_url(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts_by_url(url, **kwargs))

    def posts_by_url_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts_by_url_trigger(url, **kwargs))

    def posts_by_url_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_by_url_status(snapshot_id))

    def posts_by_url_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.posts_by_url_fetch(snapshot_id))

    # Comments
    def comments(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.comments(url, **kwargs))

    def comments_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.comments_trigger(url, **kwargs))

    def comments_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.comments_status(snapshot_id))

    def comments_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.comments_fetch(snapshot_id))

    # Reels
    def reels(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.reels(url, **kwargs))

    def reels_trigger(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.reels_trigger(url, **kwargs))

    def reels_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.reels_status(snapshot_id))

    def reels_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.reels_fetch(snapshot_id))


class SyncChatGPTScraper:
    """Sync wrapper for ChatGPTScraper - COMPLETE with all methods."""

    def __init__(self, async_scraper, loop):
        self._async = async_scraper
        self._loop = loop

    # Prompt
    def prompt(self, prompt_text, **kwargs):
        return self._loop.run_until_complete(self._async.prompt(prompt_text, **kwargs))

    def prompt_trigger(self, prompt_text, **kwargs):
        return self._loop.run_until_complete(self._async.prompt_trigger(prompt_text, **kwargs))

    def prompt_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.prompt_status(snapshot_id))

    def prompt_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.prompt_fetch(snapshot_id))

    # Prompts (batch)
    def prompts(self, prompts, **kwargs):
        return self._loop.run_until_complete(self._async.prompts(prompts, **kwargs))

    def prompts_trigger(self, prompts, **kwargs):
        return self._loop.run_until_complete(self._async.prompts_trigger(prompts, **kwargs))

    def prompts_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.prompts_status(snapshot_id))

    def prompts_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.prompts_fetch(snapshot_id))


# ============================================================================
# SYNC SEARCH SERVICE
# ============================================================================

class SyncSearchService:
    """Sync wrapper for SearchService - COMPLETE."""

    def __init__(self, async_service, loop):
        self._async = async_service
        self._loop = loop
        self._amazon = None
        self._linkedin = None
        self._instagram = None

    def google(self, query, **kwargs) -> SearchResult:
        """Search Google."""
        return self._loop.run_until_complete(self._async.google(query, **kwargs))

    def bing(self, query, **kwargs) -> SearchResult:
        """Search Bing."""
        return self._loop.run_until_complete(self._async.bing(query, **kwargs))

    def yandex(self, query, **kwargs) -> SearchResult:
        """Search Yandex."""
        return self._loop.run_until_complete(self._async.yandex(query, **kwargs))

    @property
    def amazon(self) -> "SyncAmazonSearchScraper":
        """Amazon search service."""
        if self._amazon is None:
            self._amazon = SyncAmazonSearchScraper(self._async.amazon, self._loop)
        return self._amazon

    @property
    def linkedin(self) -> "SyncLinkedInSearchScraper":
        """LinkedIn search service."""
        if self._linkedin is None:
            self._linkedin = SyncLinkedInSearchScraper(self._async.linkedin, self._loop)
        return self._linkedin

    @property
    def instagram(self) -> "SyncInstagramSearchScraper":
        """Instagram search service."""
        if self._instagram is None:
            self._instagram = SyncInstagramSearchScraper(self._async.instagram, self._loop)
        return self._instagram

    @property
    def chatGPT(self) -> "SyncChatGPTScraper":
        """ChatGPT search service."""
        return SyncChatGPTScraper(self._async.chatGPT, self._loop)


class SyncAmazonSearchScraper:
    """Sync wrapper for AmazonSearchScraper."""

    def __init__(self, async_scraper, loop):
        self._async = async_scraper
        self._loop = loop

    def products(self, keyword, **kwargs):
        return self._loop.run_until_complete(self._async.products(keyword, **kwargs))

    def products_trigger(self, keyword, **kwargs):
        return self._loop.run_until_complete(self._async.products_trigger(keyword, **kwargs))

    def products_status(self, snapshot_id):
        return self._loop.run_until_complete(self._async.products_status(snapshot_id))

    def products_fetch(self, snapshot_id):
        return self._loop.run_until_complete(self._async.products_fetch(snapshot_id))


class SyncLinkedInSearchScraper:
    """Sync wrapper for LinkedInSearchScraper."""

    def __init__(self, async_scraper, loop):
        self._async = async_scraper
        self._loop = loop

    def posts(self, profile_url, **kwargs):
        return self._loop.run_until_complete(self._async.posts(profile_url, **kwargs))

    def profiles(self, **kwargs):
        return self._loop.run_until_complete(self._async.profiles(**kwargs))

    def jobs(self, **kwargs):
        return self._loop.run_until_complete(self._async.jobs(**kwargs))


class SyncInstagramSearchScraper:
    """Sync wrapper for InstagramSearchScraper."""

    def __init__(self, async_scraper, loop):
        self._async = async_scraper
        self._loop = loop

    def posts(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.posts(url, **kwargs))

    def reels(self, url, **kwargs):
        return self._loop.run_until_complete(self._async.reels(url, **kwargs))


# ============================================================================
# SYNC CRAWLER SERVICE
# ============================================================================

class SyncCrawlerService:
    """Sync wrapper for CrawlerService."""

    def __init__(self, async_service, loop):
        self._async = async_service
        self._loop = loop

    def crawl(self, url, **kwargs):
        """Crawl a URL."""
        return self._loop.run_until_complete(self._async.crawl(url, **kwargs))

    def scrape(self, url, **kwargs):
        """Scrape a URL."""
        return self._loop.run_until_complete(self._async.scrape(url, **kwargs))
```

**Why This Implementation**:
1. Fixed `__init__` check for running loop (Issue #4)
2. Added `SyncGenericScraper` class (Issue #5)
3. Complete trigger/status/fetch methods for all scrapers (Issue #6)
4. Added `SyncCrawlerService` (Issue #9)

---

## Phase 2: Add Context Manager to BaseWebScraper

### File: `src/brightdata/scrapers/base.py`

**Add** (after existing methods, before class end):
```python
async def __aenter__(self):
    """
    Async context manager entry for standalone scraper usage.

    Example:
        >>> async with AmazonScraper(token="...") as scraper:
        ...     result = await scraper.products(url)
    """
    await self.engine.__aenter__()
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Async context manager exit - cleanup engine."""
    await self.engine.__aexit__(exc_type, exc_val, exc_tb)
```

**Why**: Enables standalone scraper usage pattern (Issue #3)

---

## Phase 3: Fix SERP Base Class

### File: `src/brightdata/api/serp/base.py`

**Delete** (lines 109-111):
```python
def search(self, *args, **kwargs):
    """Synchronous search wrapper."""
    return asyncio.run(self.search_async(*args, **kwargs))
```

**Rename** `search_async` to `search` (line 56):
```python
# Change from:
async def search_async(self, query, ...):

# Change to:
async def search(self, query, ...):
```

**Add backward compatibility alias** (after the method):
```python
# Backward compatibility alias
search_async = search
```

**Why**: The sync method was broken - no engine context (Issue #2). Sync access handled by `SyncSearchService`.

---

## Phase 4: BrightDataClient - Remove Nested Contexts

### File: `src/brightdata/client.py`

**Problem**: Client methods wrap operations in `async with self.engine:` causing race conditions.

#### Change 4.1: Add `_ensure_initialized()` helper method

**Add** (after `__init__`):
```python
def _ensure_initialized(self) -> None:
    """
    Ensure client is properly initialized (used as context manager).

    Raises:
        RuntimeError: If client not initialized via context manager
    """
    if self.engine._session is None:
        raise RuntimeError(
            "BrightDataClient not initialized. "
            "Use: async with BrightDataClient() as client: ..."
        )
```

#### Change 4.2: `test_connection()` - Remove nested context

**Current Code**:
```python
async def test_connection(self) -> bool:
    try:
        async with self.engine:  # ❌ REMOVE THIS
            async with self.engine.get_from_url(...) as response:
                ...
```

**New Code**:
```python
async def test_connection(self) -> bool:
    """Test API connection and token validity."""
    self._ensure_initialized()
    try:
        async with self.engine.get_from_url(
            f"{self.engine.BASE_URL}/zone/get_active_zones"
        ) as response:
            if response.status == HTTP_OK:
                self._is_connected = True
                return True
            else:
                self._is_connected = False
                return False
    except (asyncio.TimeoutError, OSError, Exception):
        self._is_connected = False
        return False
```

#### Change 4.3: `get_account_info()` - Remove nested context

Same pattern: Remove `async with self.engine:`, add `self._ensure_initialized()`.

#### Change 4.4: `list_zones()` - Remove nested context

```python
async def list_zones(self) -> List[Dict[str, Any]]:
    """List all active zones."""
    self._ensure_initialized()
    if self._zone_manager is None:
        self._zone_manager = ZoneManager(self.engine)
    return await self._zone_manager.list_zones()
```

#### Change 4.5: `delete_zone()` - Remove nested context

```python
async def delete_zone(self, zone_name: str) -> None:
    """Delete a zone."""
    self._ensure_initialized()
    if self._zone_manager is None:
        self._zone_manager = ZoneManager(self.engine)
    await self._zone_manager.delete_zone(zone_name)
```

#### Change 4.6: `scrape_url_async()` - Remove nested context

```python
async def scrape_url_async(self, url, ...):
    """Scrape URL(s) asynchronously."""
    self._ensure_initialized()
    if self._web_unlocker_service is None:
        self._web_unlocker_service = WebUnlockerService(self.engine)
    # ... rest unchanged
```

---

## Phase 5: BrightDataClient - Remove Sync Wrappers

### File: `src/brightdata/client.py`

**Delete these methods entirely**:
- `_run_async_with_cleanup()` method
- `get_account_info_sync()` method
- `test_connection_sync()` method
- `list_zones_sync()` method
- `delete_zone_sync()` method
- `scrape_url()` sync method
- `_validate_token_sync()` method

**Change** `validate_token` handling in `__init__`:
```python
# Change from:
if validate_token:
    self._validate_token_sync()

# Change to:
self._validate_token_on_enter = validate_token
```

**Update** `__aenter__`:
```python
async def __aenter__(self):
    """Async context manager entry - initializes engine session."""
    await self.engine.__aenter__()

    # Validate token if requested
    if self._validate_token_on_enter:
        is_valid = await self.test_connection()
        if not is_valid:
            await self.engine.__aexit__(None, None, None)
            raise AuthenticationError(
                "Token validation failed. Token appears to be invalid.\n"
                "Check your token at: https://brightdata.com/cp/api_keys"
            )

    await self._ensure_zones()
    return self
```

**Rename** `scrape_url_async` to `scrape_url` and add alias:
```python
async def scrape_url(self, url, ...):
    """Scrape URL(s)."""
    ...

# Backward compatibility alias
scrape_url_async = scrape_url
```

---

## Phase 6: Services - Remove Sync Methods

### File: `src/brightdata/api/search_service.py`

**Delete** sync methods:
- `google()` sync method
- `bing()` sync method
- `yandex()` sync method

**Rename** async methods and add aliases:
```python
async def google(self, query, ...):
    """Search Google."""
    ...

# Backward compatibility alias
google_async = google

async def bing(self, query, ...):
    """Search Bing."""
    ...

bing_async = bing

async def yandex(self, query, ...):
    """Search Yandex."""
    ...

yandex_async = yandex
```

### File: `src/brightdata/api/scrape_service.py`

**Delete** `GenericScraper.url()` sync method.

**Rename** `url_async` to `url` and add alias:
```python
async def url(self, *args, **kwargs):
    """Scrape URL using Web Unlocker."""
    ...

url_async = url
```

---

## Phase 7: Scrapers - Remove Sync Wrappers

> **IMPORTANT**: The async methods (`products_async`, `reviews_async`, etc.) are **already correctly implemented** without nested contexts. Only remove the sync wrappers!

### File: `src/brightdata/scrapers/amazon/scraper.py`

**Delete ALL sync wrapper methods**:
- `products()` (the sync one that calls `asyncio.run`)
- `products_trigger()`
- `products_status()`
- `products_fetch()`
- `reviews()`
- `reviews_trigger()`
- `reviews_status()`
- `reviews_fetch()`
- `sellers()`
- `sellers_trigger()`
- `sellers_status()`
- `sellers_fetch()`

**Rename** async methods and add aliases:
```python
async def products(self, url, ...):
    """Scrape Amazon products."""
    ...

# Backward compatibility alias
products_async = products

async def products_trigger(self, url, ...):
    """Trigger Amazon products scrape."""
    ...

products_trigger_async = products_trigger

# ... same pattern for all methods
```

### Same pattern for ALL other scrapers:

- `src/brightdata/scrapers/amazon/search.py`
- `src/brightdata/scrapers/linkedin/scraper.py`
- `src/brightdata/scrapers/linkedin/search.py`
- `src/brightdata/scrapers/instagram/scraper.py`
- `src/brightdata/scrapers/instagram/search.py`
- `src/brightdata/scrapers/facebook/scraper.py`
- `src/brightdata/scrapers/chatgpt/scraper.py`

### File: `src/brightdata/scrapers/base.py`

**Delete**:
- `scrape()` sync method
- `_run_blocking()` helper

**Rename** `scrape_async` to `scrape` and add alias:
```python
async def scrape(self, urls, **kwargs):
    """Scrape URLs."""
    ...

scrape_async = scrape
```

---

## Phase 8: Fix ScrapeJob Engine Lifecycle

### File: `src/brightdata/scrapers/job.py`

**Delete** sync wrappers:
- `status()` sync method
- `wait()` sync method
- `fetch()` sync method
- `to_result()` sync method

**Add engine check** to async methods:
```python
def _ensure_engine_active(self) -> None:
    """Check if engine session is still active."""
    if self._api_client.engine._session is None:
        raise RuntimeError(
            f"Cannot perform operation: client session closed.\n"
            f"Use snapshot_id '{self.snapshot_id}' with a new client:\n"
            f"  async with BrightDataClient() as client:\n"
            f"      result = await client._api_client.fetch_result('{self.snapshot_id}')"
        )

async def status(self, refresh: bool = True) -> str:
    """Check job status."""
    self._ensure_engine_active()
    # ... rest unchanged

async def fetch(self, format: str = "json") -> Any:
    """Fetch job results."""
    self._ensure_engine_active()
    # ... rest unchanged

async def wait(self, timeout, poll_interval, verbose) -> str:
    """Wait for job completion."""
    self._ensure_engine_active()
    # ... rest unchanged

async def to_result(self, timeout, poll_interval) -> ScrapeResult:
    """Convert to ScrapeResult."""
    self._ensure_engine_active()
    # ... rest unchanged
```

**Rename** and add aliases:
```python
# Backward compatibility aliases
status_async = status
fetch_async = fetch
wait_async = wait
to_result_async = to_result
```

---

## Phase 9: Update Exports and Tests

### File: `src/brightdata/__init__.py`

```python
from .client import BrightDataClient, BrightData
from .sync_client import SyncBrightDataClient

__all__ = [
    "BrightDataClient",
    "BrightData",
    "SyncBrightDataClient",
    # ... other exports
]
```

### Tests to Update/Add

**File: `tests/test_sync_client.py`** (NEW):
```python
import pytest
from brightdata import SyncBrightDataClient

def test_sync_client_requires_context_manager():
    """Test that sync client requires context manager."""
    client = SyncBrightDataClient()
    with pytest.raises(RuntimeError, match="not initialized"):
        client.list_zones()

def test_sync_client_in_async_context():
    """Test that sync client rejects async context."""
    import asyncio

    async def try_sync_client():
        with pytest.raises(RuntimeError, match="cannot be used inside async"):
            SyncBrightDataClient()

    asyncio.run(try_sync_client())

def test_sync_client_basic_usage():
    """Test basic sync client usage."""
    with SyncBrightDataClient() as client:
        zones = client.list_zones()
        assert isinstance(zones, list)

def test_sync_client_multiple_calls():
    """Test that multiple calls reuse same loop."""
    with SyncBrightDataClient() as client:
        zones1 = client.list_zones()
        zones2 = client.list_zones()
        info = client.get_account_info()
        assert zones1 == zones2
```

**File: `tests/test_async_client.py`** (NEW):
```python
import pytest
import asyncio
from brightdata import BrightDataClient

@pytest.mark.asyncio
async def test_async_client_requires_context_manager():
    """Test that async client requires context manager."""
    client = BrightDataClient()
    with pytest.raises(RuntimeError, match="not initialized"):
        await client.list_zones()

@pytest.mark.asyncio
async def test_async_client_concurrent_calls():
    """Test that concurrent calls work correctly."""
    async with BrightDataClient() as client:
        # All concurrent calls should work
        results = await asyncio.gather(
            client.list_zones(),
            client.get_account_info(),
            client.test_connection(),
        )
        assert len(results) == 3

@pytest.mark.asyncio
async def test_backward_compat_aliases():
    """Test that *_async aliases work."""
    async with BrightDataClient() as client:
        # Old name should still work
        result = await client.scrape_url_async("https://example.com")
        assert result is not None
```

---

## Summary of Changes by File

| File | Changes |
|------|---------|
| `sync_client.py` | **NEW FILE** - Complete sync adapter with all fixes |
| `client.py` | Remove nested contexts, remove sync wrappers, add `_ensure_initialized()` |
| `base.py` (scrapers) | Add `__aenter__`/`__aexit__`, remove sync methods |
| `serp/base.py` | Remove broken `search()` sync method |
| `search_service.py` | Remove sync methods, add backward compat aliases |
| `scrape_service.py` | Remove sync method from GenericScraper |
| `amazon/scraper.py` | Remove sync methods (NOT async!), add aliases |
| `linkedin/scraper.py` | Remove sync methods, add aliases |
| `instagram/scraper.py` | Remove sync methods, add aliases |
| `facebook/scraper.py` | Remove sync methods, add aliases |
| `chatgpt/scraper.py` | Remove sync methods, add aliases |
| `amazon/search.py` | Remove sync method, add alias |
| `linkedin/search.py` | Remove sync methods, add aliases |
| `instagram/search.py` | Remove sync methods, add aliases |
| `job.py` | Remove sync wrappers, add engine check, add aliases |
| `__init__.py` | Add `SyncBrightDataClient` export |

---

## Implementation Order

1. **Phase 1**: Create `sync_client.py` (new file, no conflicts)
2. **Phase 2**: Add context manager to `BaseWebScraper`
3. **Phase 3**: Fix SERP base class
4. **Phase 9**: Update `__init__.py` exports (allows testing sync client)
5. **Phase 4**: Fix `client.py` nested contexts
6. **Phase 5**: Remove `client.py` sync wrappers
7. **Phase 6**: Fix services
8. **Phase 7**: Fix scrapers (largest change)
9. **Phase 8**: Fix ScrapeJob
10. **Tests**: Update throughout

This order:
- Minimizes breaking changes during development
- Allows testing each phase independently
- Creates sync client first so it can be used to test async changes
