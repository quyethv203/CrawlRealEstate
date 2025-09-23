import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup
from crawl4ai import AsyncWebCrawler

from src.config.settings import config
from src.crawlers.crawlconfig.crawl_config import dispatcherConfig, browserConfig, crawlerRunConfig, strategyConfig
from src.data.models.CrawlStatsModel import CrawlStats
from src.data.models.RealEstateModel import RealEstateProperty
from src.data.repositories.RealEstateRepository import RealEstateRepository
from src.utils.logging import get_logger


class BaseCrawler(ABC):
    def __init__(self, website_name: str, website_config: Dict[str, Any]):
        self.website_name = website_name
        self.website_config = website_config
        self.base_url = website_config['base_url']
        self.search_urls = website_config['search_urls']
        self.delay = website_config.get('delay', 2)
        self.logger = get_logger(f"crawler.{website_name}")
        self.observers = []
        self.crawl_stats = None
        self.repository = RealEstateRepository()
        self.dispatcher = dispatcherConfig()
        self.browser = browserConfig()
        self.crawler = crawlerRunConfig()
        self.strategy = strategyConfig()


    def add_observer(self, observer):
        self.observers.append(observer)

    def notify_observers(self, event_type: str, data: Any):
        for observer in self.observers:
            observer.notify(event_type, data, self.website_name)

    async def crawl_all(self) -> List[RealEstateProperty]:
        self.logger.info(f"Starting crawl for {self.website_name}")
        self.crawl_stats = CrawlStats(
            source=self.website_name,
            start_time=datetime.now(),
            status="running"
        )
        self.notify_observers("crawl_started", self.crawl_stats)
        all_properties = []
        try:
            async with AsyncWebCrawler(verbose=True, config=self.browser, crawler_strategy=self.strategy) as crawler:
                for search_url in self.search_urls:
                    self.logger.info(f"Crawling search URL: {search_url}")
                    property_links = await self.extract_property_links(crawler, search_url)
                    self.logger.info(f"Found {len(property_links)} property links")
                    properties = await self.crawl_property_details_batch(crawler, property_links)
                    all_properties.extend(properties)
                    await asyncio.sleep(self.delay)
            self.crawl_stats.end_time = datetime.now()
            self.crawl_stats.total_items = len(all_properties)
            self.crawl_stats.successful_items = len([p for p in all_properties if p])
            self.crawl_stats.status = "completed"
            self.notify_observers("crawl_completed", self.crawl_stats)
            self.logger.info(f"Completed crawl for {self.website_name}: {len(all_properties)} properties")
            return all_properties
        except Exception as e:
            self.crawl_stats.status = "failed"
            self.crawl_stats.error_message = str(e)
            self.crawl_stats.end_time = datetime.now()
            self.notify_observers("crawl_failed", {"error": str(e), "stats": self.crawl_stats})
            self.logger.error(f"Crawl failed for {self.website_name}: {e}")
            return []

    async def extract_property_links(self, crawler: AsyncWebCrawler, search_url: str) -> List[Dict[str, Any]]:
        all_links = []
        page = 1
        batch_size = config.LINK_PER_BATCH
        while True:
            batch_urls = []
            page_numbers = []
            for i in range(batch_size):
                current_page = page + i
                if current_page > config.PAGES_SITE:
                    break
                paginated_url = self.build_pagination_url(search_url, current_page)
                batch_urls.append(paginated_url)
                page_numbers.append(current_page)
            if not batch_urls:
                break
            self.logger.info(f"Crawling pages {page_numbers[0]}-{page_numbers[-1]} in batch")
            try:
                results = await crawler.arun_many(
                    urls=batch_urls,
                    config=self.crawler,
                    dispatcher=self.dispatcher,
                )
                for i, result in enumerate(results):
                    if result.success:
                        soup = BeautifulSoup(result.html, 'html.parser')
                        page_links = self.extract_links_from_page(soup)
                        all_links.extend(page_links)
                        # if len(all_links) >= config.LINK_PER_BATCH:
                        #     return all_links[:config.LINK_PER_BATCH]
            except Exception as e:
                self.logger.error(f"Error in batch crawling: {e}")
                break
            page += len(batch_urls)
            await asyncio.sleep(self.delay)
        self.logger.info(f"Finished crawling, found {len(all_links)} property links")
        return all_links

    async def crawl_property_details_batch(self, crawler: AsyncWebCrawler, property_links: List[Dict[str, Any]]) -> List[RealEstateProperty]:
        properties = []
        batch_size = config.ITEM_PER_BATCH
        duplicate_count = 0
        failed_count = 0

        unique_links = []
        for prop in property_links:
            if not self.repository.exists_by_link(prop['url']):
                unique_links.append(prop)
            else:
                duplicate_count += 1

        for i in range(0, len(unique_links), batch_size):
            batch = unique_links[i:i + batch_size]
            tasks = [self.crawl_single_property(crawler, prop_link) for prop_link in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in batch_results:
                if isinstance(result, Exception):
                    self.logger.error(f"Property crawl failed: {result}")
                    failed_count += 1
                elif result:
                    properties.append(result)
                    self.notify_observers("property_extracted", result)
            await asyncio.sleep(self.delay)

        # Cập nhật thống kê vào crawl_stats nếu có
        if self.crawl_stats:
            self.crawl_stats.duplicate_items = duplicate_count
            self.crawl_stats.failed_items = failed_count
            self.crawl_stats.successful_items = len(properties)
            self.crawl_stats.total_items = len(property_links)

        return properties

    async def crawl_single_property(self, crawler: AsyncWebCrawler, property_link: Dict[str, Any]) -> Optional[RealEstateProperty]:
        try:
            url = property_link['url']
            result = await crawler.arun(url=url)
            if result.success:
                soup = BeautifulSoup(result.html, 'html.parser')
                property_data = self.extract_property_details(soup, url)
                if property_data:
                    property_data['source'] = self.website_name
                    property_data['crawled_at'] = datetime.now()
                    property_data['link'] = url
                    return RealEstateProperty(**property_data)
            else:
                self.logger.warning(f"Failed to crawl property: {url}")
        except Exception as e:
            self.logger.error(f"Error crawling property {property_link.get('url', '')}: {e}")
        return None

    # Abstract methods to be implemented by each website crawler
    @abstractmethod
    def build_pagination_url(self, base_url: str, page: int) -> str:
        pass

    @abstractmethod
    def extract_links_from_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def extract_property_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        pass