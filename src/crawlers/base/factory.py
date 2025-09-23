from typing import Dict, Any
from src.crawlers.base.base_crawler import BaseCrawler
from src.crawlers.sites.batdongsan_crawler import BatDongSanCrawler
from src.crawlers.sites.nhatot_crawler import NhaTotCrawler
from src.crawlers.sites.muaban_crawler import MuaBanCrawler
from src.crawlers.sites.bds123_crawler import BDS123Crawler
from src.crawlers.sites.sosanhnha_crawler import SoSanhNhaCrawler
from src.crawlers.sites.mogi_crawler import MogiCrawler


class CrawlerFactory:
    """Factory for creating website-specific crawlers"""

    _crawler_classes = {
        'batdongsan.com.vn': BatDongSanCrawler,
        'nhatot.com': NhaTotCrawler,
        'muaban.net': MuaBanCrawler,
        'bds123.vn': BDS123Crawler,
        'sosanhnha.com': SoSanhNhaCrawler,
        'mogi.vn': MogiCrawler
    }

    @classmethod
    def create_crawler(cls, website_name: str, website_config: Dict[str, Any]) -> BaseCrawler:
        """Factory method to create appropriate crawler"""

        crawler_class = cls._crawler_classes.get(website_name)

        if not crawler_class:
            raise ValueError(f"No crawler implementation found for website: {website_name}")

        return crawler_class(website_name, website_config)

    @classmethod
    def get_supported_websites(cls) -> list:
        """Get list of supported websites"""
        return list(cls._crawler_classes.keys())

    @classmethod
    def register_crawler(cls, website_name: str, crawler_class: type):
        """Register new crawler class for a website"""
        if not issubclass(crawler_class, BaseCrawler):
            raise ValueError("Crawler class must inherit from BaseCrawler")

        cls._crawler_classes[website_name] = crawler_class
