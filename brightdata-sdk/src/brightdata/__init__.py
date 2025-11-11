"""Bright Data Python SDK - Modern async-first SDK for Bright Data APIs."""

__version__ = "2.0.0"

# Export main client
from .client import BrightData

# Export result models
from .models import (
    BaseResult,
    ScrapeResult,
    SearchResult,
    CrawlResult,
    Result,
)

# Export exceptions
from .exceptions import (
    BrightDataError,
    ValidationError,
    AuthenticationError,
    APIError,
    TimeoutError,
    ZoneError,
    NetworkError,
)

# Export WebUnlockerService for advanced usage
from .api.web_unlocker import WebUnlockerService

__all__ = [
    "__version__",
    # Main client
    "BrightData",
    # Result models
    "BaseResult",
    "ScrapeResult",
    "SearchResult",
    "CrawlResult",
    "Result",
    # Exceptions
    "BrightDataError",
    "ValidationError",
    "AuthenticationError",
    "APIError",
    "TimeoutError",
    "ZoneError",
    "NetworkError",
    # Services
    "WebUnlockerService",
]
