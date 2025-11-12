"""
LinkedIn scraper - Profiles, companies, and jobs extraction.

Supports:
- Scrape: Direct profile/company/job URLs
- Search: Keyword-based discovery of profiles, companies, jobs
"""

import asyncio
from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone

from ..base import BaseWebScraper
from ..registry import register
from ...models import ScrapeResult
from ...utils.validation import validate_url
from ...exceptions import ValidationError, APIError


@register("linkedin")
class LinkedInScraper(BaseWebScraper):
    """
    LinkedIn scraper with support for profiles, companies, and jobs.
    
    Provides both URL-based scraping and keyword-based search across
    LinkedIn's different data types (profiles, companies, jobs).
    
    Methods:
        scrape(): URL-based extraction (any LinkedIn URL)
        profiles(): Search for people profiles
        companies(): Search for companies
        jobs(): Search for job postings
    
    Example:
        >>> # URL-based scraping
        >>> scraper = LinkedInScraper(bearer_token="token")
        >>> result = scraper.scrape("https://linkedin.com/in/johndoe")
        >>> 
        >>> # Search for jobs
        >>> result = scraper.jobs(keyword="python developer", location="NYC")
        >>> 
        >>> # Search for profiles
        >>> result = scraper.profiles(keyword="data scientist", location="San Francisco")
    """
    
    # LinkedIn has multiple dataset IDs for different types
    DATASET_ID = "gd_l1oojb10z2jye29kh"  # LinkedIn People Profiles (default)
    DATASET_ID_COMPANIES = "gd_lhkq90okie75oj8mo"  # LinkedIn Companies
    DATASET_ID_JOBS = "gd_lj4v2v5oqpp3qb79j"  # LinkedIn Jobs
    
    PLATFORM_NAME = "linkedin"
    MIN_POLL_TIMEOUT = 300  # LinkedIn scrapes can be slow
    COST_PER_RECORD = 0.002  # LinkedIn data is more expensive
    
    # ============================================================================
    # PROFILE SEARCH (Parameter-based discovery)
    # ============================================================================
    
    async def profiles_async(
        self,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
        company: Optional[str] = None,
        title: Optional[str] = None,
        max_results: int = 10,
        poll_interval: int = 10,
        poll_timeout: Optional[int] = None,
    ) -> ScrapeResult:
        """
        Search LinkedIn profiles by keyword/filters (async).
        
        This is a parameter-based search operation for discovering profiles.
        
        Args:
            keyword: General search keyword (optional if other filters provided)
            location: Location filter (e.g., "New York", "San Francisco")
            company: Company name filter
            title: Job title filter
            max_results: Maximum number of profiles to return (default: 10)
            poll_interval: Seconds between status checks
            poll_timeout: Maximum seconds to wait
        
        Returns:
            ScrapeResult with list of profile data
        
        Example:
            >>> result = await scraper.profiles_async(
            ...     keyword="data scientist",
            ...     location="San Francisco",
            ...     max_results=20
            ... )
            >>> for profile in result.data:
            ...     print(profile['name'], profile['headline'])
        """
        if not any([keyword, location, company, title]):
            raise ValidationError(
                "At least one search parameter required (keyword, location, company, or title)"
            )
        
        # Build search payload
        payload: List[Dict[str, Any]] = [{}]
        
        if keyword:
            payload[0]["keyword"] = keyword
        if location:
            payload[0]["location"] = location
        if company:
            payload[0]["company"] = company
        if title:
            payload[0]["title"] = title
        if max_results:
            payload[0]["max_results"] = max_results
        
        # Execute with profiles dataset
        timeout = poll_timeout or self.MIN_POLL_TIMEOUT
        
        async with self.engine:
            # Override dataset_id for profiles
            snapshot_id = await self._trigger_async_with_dataset(
                payload=payload,
                dataset_id=self.DATASET_ID,  # People Profiles dataset
                include_errors=True
            )
            
            if not snapshot_id:
                return ScrapeResult(
                    success=False,
                    url="",
                    status="error",
                    error="Failed to trigger profile search",
                    platform=self.PLATFORM_NAME,
                )
            
            snapshot_id_received_at = datetime.now(timezone.utc)
            request_sent_at = datetime.now(timezone.utc)
            
            result = await self._poll_and_fetch_async(
                snapshot_id=snapshot_id,
                poll_interval=poll_interval,
                poll_timeout=timeout,
                request_sent_at=request_sent_at,
                snapshot_id_received_at=snapshot_id_received_at,
            )
            
            return result
    
    def profiles(
        self,
        keyword: Optional[str] = None,
        **kwargs
    ) -> ScrapeResult:
        """
        Search LinkedIn profiles (sync).
        
        See profiles_async() for full documentation.
        """
        return asyncio.run(self.profiles_async(keyword=keyword, **kwargs))
    
    # ============================================================================
    # COMPANY SEARCH
    # ============================================================================
    
    async def companies_async(
        self,
        keyword: Optional[str] = None,
        location: Optional[str] = None,
        industry: Optional[str] = None,
        max_results: int = 10,
        poll_interval: int = 10,
        poll_timeout: Optional[int] = None,
    ) -> ScrapeResult:
        """
        Search LinkedIn companies by keyword/filters (async).
        
        Args:
            keyword: Company search keyword
            location: Location filter
            industry: Industry filter
            max_results: Maximum number of companies
            poll_interval: Seconds between status checks
            poll_timeout: Maximum seconds to wait
        
        Returns:
            ScrapeResult with list of company data
        
        Example:
            >>> result = await scraper.companies_async(
            ...     keyword="tech startup",
            ...     location="Silicon Valley",
            ...     max_results=50
            ... )
        """
        if not any([keyword, location, industry]):
            raise ValidationError(
                "At least one search parameter required (keyword, location, or industry)"
            )
        
        payload: List[Dict[str, Any]] = [{}]
        
        if keyword:
            payload[0]["keyword"] = keyword
        if location:
            payload[0]["location"] = location
        if industry:
            payload[0]["industry"] = industry
        if max_results:
            payload[0]["max_results"] = max_results
        
        timeout = poll_timeout or self.MIN_POLL_TIMEOUT
        
        async with self.engine:
            snapshot_id = await self._trigger_async_with_dataset(
                payload=payload,
                dataset_id=self.DATASET_ID_COMPANIES,
                include_errors=True
            )
            
            if not snapshot_id:
                return ScrapeResult(
                    success=False,
                    url="",
                    status="error",
                    error="Failed to trigger company search",
                    platform=self.PLATFORM_NAME,
                )
            
            snapshot_id_received_at = datetime.now(timezone.utc)
            request_sent_at = datetime.now(timezone.utc)
            
            result = await self._poll_and_fetch_async(
                snapshot_id=snapshot_id,
                poll_interval=poll_interval,
                poll_timeout=timeout,
                request_sent_at=request_sent_at,
                snapshot_id_received_at=snapshot_id_received_at,
            )
            
            return result
    
    def companies(self, keyword: Optional[str] = None, **kwargs) -> ScrapeResult:
        """Search LinkedIn companies (sync)."""
        return asyncio.run(self.companies_async(keyword=keyword, **kwargs))
    
    # ============================================================================
    # JOB SEARCH
    # ============================================================================
    
    async def jobs_async(
        self,
        keyword: str,
        location: Optional[str] = None,
        experience_level: Optional[str] = None,
        job_type: Optional[str] = None,
        max_results: int = 10,
        poll_interval: int = 10,
        poll_timeout: Optional[int] = None,
    ) -> ScrapeResult:
        """
        Search LinkedIn jobs by keyword/filters (async).
        
        Args:
            keyword: Job search keyword (required)
            location: Location filter (e.g., "New York, NY")
            experience_level: Experience level (e.g., "entry", "mid", "senior")
            job_type: Job type (e.g., "full-time", "contract", "remote")
            max_results: Maximum number of jobs
            poll_interval: Seconds between status checks
            poll_timeout: Maximum seconds to wait
        
        Returns:
            ScrapeResult with list of job postings
        
        Example:
            >>> result = await scraper.jobs_async(
            ...     keyword="python developer",
            ...     location="NYC",
            ...     job_type="remote",
            ...     max_results=50
            ... )
            >>> for job in result.data:
            ...     print(job['title'], job['company'])
        """
        if not keyword:
            raise ValidationError("Keyword required for job search")
        
        payload: List[Dict[str, Any]] = [{
            "keyword": keyword,
            "max_results": max_results,
        }]
        
        if location:
            payload[0]["location"] = location
        if experience_level:
            payload[0]["experience_level"] = experience_level
        if job_type:
            payload[0]["job_type"] = job_type
        
        timeout = poll_timeout or self.MIN_POLL_TIMEOUT
        
        async with self.engine:
            snapshot_id = await self._trigger_async_with_dataset(
                payload=payload,
                dataset_id=self.DATASET_ID_JOBS,
                include_errors=True
            )
            
            if not snapshot_id:
                return ScrapeResult(
                    success=False,
                    url="",
                    status="error",
                    error="Failed to trigger job search",
                    platform=self.PLATFORM_NAME,
                )
            
            snapshot_id_received_at = datetime.now(timezone.utc)
            request_sent_at = datetime.now(timezone.utc)
            
            result = await self._poll_and_fetch_async(
                snapshot_id=snapshot_id,
                poll_interval=poll_interval,
                poll_timeout=timeout,
                request_sent_at=request_sent_at,
                snapshot_id_received_at=snapshot_id_received_at,
            )
            
            return result
    
    def jobs(self, keyword: str, **kwargs) -> ScrapeResult:
        """
        Search LinkedIn jobs (sync).
        
        See jobs_async() for full documentation.
        
        Example:
            >>> result = scraper.jobs(
            ...     keyword="python developer",
            ...     location="NYC"
            ... )
        """
        return asyncio.run(self.jobs_async(keyword, **kwargs))
    
    # ============================================================================
    # HELPER METHOD (supports multiple dataset IDs)
    # ============================================================================
    
    async def _trigger_async_with_dataset(
        self,
        payload: List[Dict[str, Any]],
        dataset_id: str,
        include_errors: bool,
    ) -> Optional[str]:
        """
        Trigger with specific dataset ID.
        
        LinkedIn has multiple datasets (profiles, companies, jobs),
        so we need to override dataset_id per method.
        """
        params = {
            "dataset_id": dataset_id,
            "include_errors": str(include_errors).lower(),
        }
        
        async with self.engine._session.post(
            self.TRIGGER_URL,
            json=payload,
            params=params,
            headers=self.engine._session.headers
        ) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("snapshot_id")
            else:
                error_text = await response.text()
                raise APIError(
                    f"Trigger failed (HTTP {response.status}): {error_text}",
                    status_code=response.status
                )
