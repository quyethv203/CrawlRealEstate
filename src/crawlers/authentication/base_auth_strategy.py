from abc import ABC, abstractmethod

from crawl4ai import AsyncWebCrawler

from src.utils.logging import get_logger


class BaseAuthStrategy(ABC):
    """Abstract base class for website-specific authentication strategies"""

    def __init__(self, site_name: str):
        self.site_name  = site_name
        self.logger = get_logger(__name__)

    @abstractmethod
    async def login(self, crawler: AsyncWebCrawler, username: str, password: str) -> bool:
        """Perform login specific to this website"""
        pass

    @abstractmethod
    async def verify_login(self, crawler: AsyncWebCrawler) -> bool:
        """Verify if currently logged in"""
        pass

    @abstractmethod
    def get_phone_selectors(self) -> list:
        """Get CSS selectors for phone extraction after login"""
        pass

    def requires_credentials(self) -> bool:
        """Check if this strategy requires username/password"""
        return True