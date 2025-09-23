import json
import os
from datetime import datetime, timedelta

from crawl4ai import AsyncWebCrawler

from src.crawlers.authentication.batdongsan_strategy import BatDongSanAuthStrategy
from src.utils.logging import get_logger


class AuthenticationService:
    """Service to manage authentication using Strategy pattern"""

    def __init__(self):
        self.logger = get_logger(__name__)
        self.sessions_dir = "sessions"
        os.makedirs(self.sessions_dir, exist_ok=True)

        # Register authentication strategies
        self.strategies = {
            "batdongsan.com.vn": BatDongSanAuthStrategy("batdongsan.com.vn"),
            # Add more strategies later:
            # "nhatot.com": NhatotAuthStrategy("nhatot.com"),
            # "muaban.net": MuaBanAuthStrategy("muaban.net")
        }

        # Credentials from environment
        self.credentials = {
            "batdongsan.com.vn": {
                "username": os.getenv("username"),
                "password": os.getenv("password")
            }
        }

    async def ensure_authenticated(self, crawler: AsyncWebCrawler, website_name: str) -> bool:
        """Ensure authentication using appropriate strategy"""

        # Get strategy for this website
        strategy = self.strategies.get(website_name)
        if not strategy:
            self.logger.info(f"No auth strategy for {website_name} - continuing without login")
            return True  # No auth required

        # Get credentials
        creds = self.credentials.get(website_name, {})
        username = creds.get("username")
        password = creds.get("password")

        if not username or not password:
            self.logger.warning(f"No credentials configured for {website_name}")
            return False

        try:
            # Try existing session first
            if await self._load_session(crawler, website_name):
                if await strategy.verify_login(crawler):
                    self.logger.info(f"Using existing session for {website_name}")
                    return True
                else:
                    self.logger.info(f"Existing session invalid for {website_name}")

            # Perform fresh login using strategy
            self.logger.info(f"Performing fresh login for {website_name}")
            success = await strategy.login(crawler, username, password)

            if success:
                await self._save_session(crawler, website_name)
                self.logger.info(f"Successfully authenticated to {website_name}")
                return True
            else:
                self.logger.error(f"Authentication failed for {website_name}")
                return False

        except Exception as e:
            self.logger.error(f"Authentication error for {website_name}: {e}")
            return False

    def get_phone_selectors(self, website_name: str) -> list:
        """Get phone selectors for authenticated website"""
        strategy = self.strategies.get(website_name)
        if strategy:
            return strategy.get_phone_selectors()
        return []

    def requires_auth(self, website_name: str) -> bool:
        """Check if website requires authentication"""
        return website_name in self.strategies

    def add_strategy(self, website_name: str, strategy, username: str = None, password: str = None):
        """Add new authentication strategy"""
        self.strategies[website_name] = strategy

        if username and password:
            self.credentials[website_name] = {
                "username": username,
                "password": password
            }

        self.logger.info(f"Added auth strategy for {website_name}")

    async def _save_session(self, crawler: AsyncWebCrawler, website_name: str):
        """Save session cookies for later use"""
        try:
            session_file = os.path.join(self.sessions_dir, f"{website_name.replace('.', '_')}_session.json")

            # Get current cookies
            cookies = await crawler.get_cookies()

            session_data = {
                "website": website_name,
                "cookies": cookies,
                "saved_at": datetime.now().isoformat(),
                "expires_at": (datetime.now() + timedelta(days=7)).isoformat()  # 7 days validity
            }

            with open(session_file, 'w') as f:
                json.dump(session_data, f, indent=2)

            self.logger.debug(f"Session saved for {website_name}")

        except Exception as e:
            self.logger.warning(f"Failed to save session for {website_name}: {e}")

    async def _load_session(self, crawler: AsyncWebCrawler, website_name: str) -> bool:
        """Load existing session cookies"""
        try:
            session_file = os.path.join(self.sessions_dir, f"{website_name.replace('.', '_')}_session.json")

            if not os.path.exists(session_file):
                return False

            with open(session_file, 'r') as f:
                session_data = json.load(f)

            # Check if session is expired
            expires_at = datetime.fromisoformat(session_data.get("expires_at", ""))
            if datetime.now() > expires_at:
                self.logger.info(f"Session expired for {website_name}")
                os.remove(session_file)
                return False

            # Set cookies
            for cookie in session_data.get("cookies", []):
                await crawler.set_cookie(cookie)

            self.logger.debug(f"Session loaded for {website_name}")
            return True

        except Exception as e:
            self.logger.warning(f"Failed to load session for {website_name}: {e}")
            return False

    async def logout(self, crawler: AsyncWebCrawler, website_name: str) -> bool:
        """Logout from website and clear session"""
        try:
            # Clear session file
            session_file = os.path.join(self.sessions_dir, f"{website_name.replace('.', '_')}_session.json")
            if os.path.exists(session_file):
                os.remove(session_file)

            # Clear cookies
            await crawler.clear_cookies()

            self.logger.info(f"Logged out from {website_name}")
            return True

        except Exception as e:
            self.logger.error(f"Logout failed for {website_name}: {e}")
            return False