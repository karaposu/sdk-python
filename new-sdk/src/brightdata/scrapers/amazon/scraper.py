"""
Amazon scraper - URL-based and keyword-based product extraction.

Supports:
- Scrape: Direct product URLs
- Search: Keyword-based product discovery
"""

import asyncio
from typing import List, Dict, Any, Optional, Union

from ..base import BaseWebScraper
from ..registry import register
from ...models import ScrapeResult
from ...utils.validation import validate_url


@register("amazon")
class AmazonScraper(BaseWebScraper):
    """
    Amazon product scraper.
    
    Provides both URL-based scraping and keyword-based search for Amazon products.
    
    Methods:
        scrape(): URL-based product extraction
        products(): Keyword-based product search
    
    Example:
        >>> # URL-based scraping
        >>> scraper = AmazonScraper(bearer_token="token")
        >>> result = scraper.scrape("https://amazon.com/dp/B0CRMZHDG8")
        >>> 
        >>> # Keyword-based search
        >>> result = scraper.products(keyword="laptop", max_results=10)
    """
    
    DATASET_ID = "gd_l7q7dkf244hwxbl93"  # Amazon Products dataset
    PLATFORM_NAME = "amazon"
    MIN_POLL_TIMEOUT = 240  # Amazon scrapes can take longer
    COST_PER_RECORD = 0.001
    
    # ============================================================================
    # SEARCH METHODS (Parameter-based discovery)
    # ============================================================================
    
    async def products_async(
        self,
        keyword: str,
        category: Optional[str] = None,
        max_results: int = 10,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        poll_interval: int = 10,
        poll_timeout: Optional[int] = None,
    ) -> ScrapeResult:
        """
        Search Amazon products by keyword (async).
        
        This is a parameter-based search operation - discovers products
        by keyword rather than scraping specific URLs.
        
        Args:
            keyword: Search keyword (e.g., "laptop", "wireless headphones")
            category: Amazon category filter (optional)
            max_results: Maximum number of products to return (default: 10)
            min_price: Minimum price filter (optional)
            max_price: Maximum price filter (optional)
            min_rating: Minimum rating filter (1.0-5.0, optional)
            poll_interval: Seconds between status checks
            poll_timeout: Maximum seconds to wait
        
        Returns:
            ScrapeResult with list of product data
        
        Example:
            >>> result = await scraper.products_async(
            ...     keyword="laptop",
            ...     category="electronics",
            ...     max_results=20,
            ...     min_rating=4.0
            ... )
            >>> for product in result.data:
            ...     print(product['title'], product['price'])
        """
        # Build search payload
        payload = [{
            "keyword": keyword,
            "max_results": max_results,
        }]
        
        if category:
            payload[0]["category"] = category
        if min_price is not None:
            payload[0]["min_price"] = min_price
        if max_price is not None:
            payload[0]["max_price"] = max_price
        if min_rating is not None:
            payload[0]["min_rating"] = min_rating
        
        # Execute workflow
        timeout = poll_timeout or self.MIN_POLL_TIMEOUT
        result = await self._execute_workflow_async(
            payload=payload,
            include_errors=True,
            poll_interval=poll_interval,
            poll_timeout=timeout,
        )
        
        return result
    
    def products(
        self,
        keyword: str,
        **kwargs
    ) -> ScrapeResult:
        """
        Search Amazon products by keyword (sync).
        
        See products_async() for full documentation.
        
        Example:
            >>> result = scraper.products(keyword="laptop", max_results=10)
        """
        return asyncio.run(self.products_async(keyword, **kwargs))
    
    async def reviews_async(
        self,
        product_url: str,
        max_reviews: int = 100,
        poll_interval: int = 10,
        poll_timeout: Optional[int] = None,
    ) -> ScrapeResult:
        """
        Get product reviews (async).
        
        Args:
            product_url: Amazon product URL
            max_reviews: Maximum number of reviews to fetch
            poll_interval: Seconds between status checks
            poll_timeout: Maximum seconds to wait
        
        Returns:
            ScrapeResult with list of reviews
        
        Example:
            >>> result = await scraper.reviews_async(
            ...     product_url="https://amazon.com/dp/B123",
            ...     max_reviews=50
            ... )
        """
        validate_url(product_url)
        
        payload = [{
            "url": product_url,
            "reviews_count": max_reviews,
        }]
        
        timeout = poll_timeout or self.MIN_POLL_TIMEOUT
        result = await self._execute_workflow_async(
            payload=payload,
            include_errors=True,
            poll_interval=poll_interval,
            poll_timeout=timeout,
        )
        
        return result
    
    def reviews(
        self,
        product_url: str,
        **kwargs
    ) -> ScrapeResult:
        """
        Get product reviews (sync).
        
        See reviews_async() for full documentation.
        """
        return asyncio.run(self.reviews_async(product_url, **kwargs))
    
    # ============================================================================
    # DATA NORMALIZATION
    # ============================================================================
    
    def normalize_result(self, data: Any) -> Any:
        """
        Normalize Amazon API response.
        
        Ensures consistent field naming and structure across
        different Amazon dataset responses.
        
        Args:
            data: Raw Amazon API response
        
        Returns:
            Normalized product data
        """
        if not isinstance(data, list):
            return data
        
        # Data is already normalized by Bright Data's Amazon dataset
        # Just pass through for now - can add transformations if needed
        return data
    
    def _build_scrape_payload(
        self,
        urls: List[str],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Build payload for Amazon product scraping.
        
        Adds Amazon-specific parameters if provided.
        """
        payload = []
        for url in urls:
            item = {"url": url}
            
            # Add optional parameters
            if "reviews_count" in kwargs:
                item["reviews_count"] = kwargs["reviews_count"]
            if "images_count" in kwargs:
                item["images_count"] = kwargs["images_count"]
            
            payload.append(item)
        
        return payload
