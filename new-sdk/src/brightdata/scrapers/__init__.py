"""Specialized platform scrapers."""

from .base import BaseWebScraper
from .registry import register, get_scraper_for, get_registered_platforms, is_platform_supported

# Import scrapers to trigger registration
try:
    from .amazon.scraper import AmazonScraper
except ImportError:
    AmazonScraper = None

try:
    from .linkedin.scraper import LinkedInScraper
except ImportError:
    LinkedInScraper = None

try:
    from .chatgpt.scraper import ChatGPTScraper
except ImportError:
    ChatGPTScraper = None


__all__ = [
    "BaseWebScraper",
    "register",
    "get_scraper_for",
    "get_registered_platforms",
    "is_platform_supported",
    "AmazonScraper",
    "LinkedInScraper",
    "ChatGPTScraper",
]
