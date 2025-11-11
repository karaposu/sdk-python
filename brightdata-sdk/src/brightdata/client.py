"""Main Bright Data SDK client."""

import os
from typing import Optional, Union, List
from datetime import datetime, timezone

from .core.engine import AsyncEngine
from .api.web_unlocker import WebUnlockerService
from .models import ScrapeResult
from .exceptions import ValidationError


class BrightData:
    """
    Modern async-first Bright Data SDK client.
    
    Provides high-level interface for all Bright Data APIs with async-first
    design and sync wrappers for compatibility.
    
    Example:
        >>> # Simple usage
        >>> client = BrightData(api_token="your_token")
        >>> result = client.scrape("https://example.com")
        >>> 
        >>> # Async usage
        >>> async with BrightData(api_token="your_token") as client:
        ...     result = await client.scrape_async("https://example.com")
    """
    
    DEFAULT_TIMEOUT = 30
    
    def __init__(
        self,
        api_token: Optional[str] = None,
        web_unlocker_zone: str = "sdk_unlocker",
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize Bright Data client.
        
        Args:
            api_token: Your Bright Data API token (or set BRIGHTDATA_API_TOKEN env var).
            web_unlocker_zone: Zone name for web unlocker (default: "sdk_unlocker").
            timeout: Default timeout in seconds (default: 30).
        
        Raises:
            ValidationError: If API token is not provided.
        """
        self.api_token = api_token or os.getenv("BRIGHTDATA_API_TOKEN")
        if not self.api_token:
            raise ValidationError(
                "API token required. Provide api_token parameter or set BRIGHTDATA_API_TOKEN environment variable."
            )
        
        self.web_unlocker_zone = web_unlocker_zone
        self.timeout = timeout
        self.engine = AsyncEngine(self.api_token, timeout=timeout)
        self._web_unlocker_service: Optional[WebUnlockerService] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.engine.__aenter__()
        self._web_unlocker_service = WebUnlockerService(self.engine)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.engine.__aexit__(exc_type, exc_val, exc_tb)
        self._web_unlocker_service = None
    
    def _ensure_service(self) -> WebUnlockerService:
        """Ensure WebUnlockerService is initialized."""
        if self._web_unlocker_service is None:
            raise RuntimeError(
                "Client must be used as async context manager for async methods. "
                "For sync methods, use client.scrape() directly."
            )
        return self._web_unlocker_service
    
    async def scrape_async(
        self,
        url: Union[str, List[str]],
        zone: Optional[str] = None,
        country: str = "",
        response_format: str = "raw",
        method: str = "GET",
        timeout: Optional[int] = None,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """
        Scrape URL(s) asynchronously using Web Unlocker API.
        
        This is the fastest, most cost-effective option for basic HTML extraction
        without JavaScript rendering. Uses Bright Data's Web Unlocker proxy service
        with anti-bot capabilities.
        
        Args:
            url: Single URL string or list of URLs to scrape.
            zone: Bright Data zone identifier (defaults to web_unlocker_zone from init).
            country: Two-letter ISO country code for proxy location (optional).
            response_format: Response format - "json" for structured data, "raw" for HTML string.
            method: HTTP method for the request (default: "GET").
            timeout: Request timeout in seconds (uses client default if not provided).
        
        Returns:
            ScrapeResult for single URL, or List[ScrapeResult] for multiple URLs.
        
        Example:
            >>> async with BrightData(api_token="token") as client:
            ...     result = await client.scrape_async("https://example.com")
            ...     print(result.data)
        """
        service = self._ensure_service()
        zone = zone or self.web_unlocker_zone
        return await service.scrape_async(
            url=url,
            zone=zone,
            country=country,
            response_format=response_format,
            method=method,
            timeout=timeout,
        )
    
    def scrape(
        self,
        url: Union[str, List[str]],
        zone: Optional[str] = None,
        country: str = "",
        response_format: str = "raw",
        method: str = "GET",
        timeout: Optional[int] = None,
    ) -> Union[ScrapeResult, List[ScrapeResult]]:
        """
        Scrape URL(s) synchronously using Web Unlocker API.
        
        This is the fastest, most cost-effective option for basic HTML extraction
        without JavaScript rendering. Uses Bright Data's Web Unlocker proxy service
        with anti-bot capabilities.
        
        Args:
            url: Single URL string or list of URLs to scrape.
            zone: Bright Data zone identifier (defaults to web_unlocker_zone from init).
            country: Two-letter ISO country code for proxy location (optional).
            response_format: Response format - "json" for structured data, "raw" for HTML string.
            method: HTTP method for the request (default: "GET").
            timeout: Request timeout in seconds (uses client default if not provided).
        
        Returns:
            ScrapeResult for single URL, or List[ScrapeResult] for multiple URLs.
        
        Example:
            >>> client = BrightData(api_token="token")
            >>> result = client.scrape("https://example.com")
            >>> print(result.data)
        """
        import asyncio
        
        effective_zone = zone or self.web_unlocker_zone
        
        async def _scrape():
            async with self.engine:
                service = WebUnlockerService(self.engine)
                return await service.scrape_async(
                    url=url,
                    zone=effective_zone,
                    country=country,
                    response_format=response_format,
                    method=method,
                    timeout=timeout,
                )
        
        try:
            loop = asyncio.get_running_loop()
            raise RuntimeError(
                "Cannot call sync method from async context. Use scrape_async() instead."
            )
        except RuntimeError:
            return asyncio.run(_scrape())
