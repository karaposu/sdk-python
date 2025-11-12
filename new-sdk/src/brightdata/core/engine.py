"""Async HTTP engine for Bright Data API operations."""

import asyncio
import aiohttp
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from ..exceptions import APIError, AuthenticationError, NetworkError, TimeoutError


class AsyncEngine:
    """
    Async HTTP engine for all API operations.
    
    Manages aiohttp sessions and provides async HTTP methods for
    communicating with Bright Data APIs.
    """
    
    BASE_URL = "https://api.brightdata.com"
    
    def __init__(self, bearer_token: str, timeout: int = 30):
        """
        Initialize async engine.
        
        Args:
            bearer_token: Bright Data API bearer token.
            timeout: Request timeout in seconds.
        """
        self.bearer_token = bearer_token
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Context manager entry."""
        self._session = aiohttp.ClientSession(
            timeout=self.timeout,
            headers={
                "Authorization": f"Bearer {self.bearer_token}",
                "Content-Type": "application/json",
                "User-Agent": "brightdata-sdk/2.0.0",
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self._session:
            await self._session.close()
            self._session = None
    
    async def request(
        self,
        method: str,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> aiohttp.ClientResponse:
        """
        Make an async HTTP request.
        
        Args:
            method: HTTP method (GET, POST, etc.).
            endpoint: API endpoint (relative to BASE_URL).
            json_data: Optional JSON payload.
            params: Optional query parameters.
            headers: Optional additional headers.
        
        Returns:
            aiohttp ClientResponse object.
        
        Raises:
            AuthenticationError: If authentication fails.
            APIError: If API request fails.
            NetworkError: If network error occurs.
            TimeoutError: If request times out.
        """
        if not self._session:
            raise RuntimeError("Engine must be used as async context manager")
        
        url = f"{self.BASE_URL}{endpoint}"
        request_headers = dict(self._session.headers)
        if headers:
            request_headers.update(headers)
        
        try:
            async with self._session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                headers=request_headers,
            ) as response:
                if response.status == 401:
                    text = await response.text()
                    raise AuthenticationError(f"Unauthorized (401): {text}")
                elif response.status == 403:
                    text = await response.text()
                    raise AuthenticationError(f"Forbidden (403): {text}")
                
                return response
                
        except aiohttp.ClientError as e:
            raise NetworkError(f"Network error: {str(e)}") from e
        except asyncio.TimeoutError as e:
            raise TimeoutError(f"Request timeout after {self.timeout.total} seconds") from e
    
    async def post(
        self,
        endpoint: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> aiohttp.ClientResponse:
        """Make POST request."""
        return await self.request("POST", endpoint, json_data=json_data, params=params, headers=headers)
    
    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
    ) -> aiohttp.ClientResponse:
        """Make GET request."""
        return await self.request("GET", endpoint, params=params, headers=headers)
