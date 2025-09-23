import asyncio
from bs4 import BeautifulSoup

from src.config.settings import Config
from crawl4ai import AsyncWebCrawler
from src.crawlers.base.factory import CrawlerFactory
from src.crawlers.crawlconfig.crawl_config import browserConfig, crawlerRunConfig, dispatcherConfig, strategyConfig
from src.data.models.RealEstateModel import RealEstateProperty
from src.services.llm_service import LLMService

async def test_detail(urls):
    print(f"🔎 Test crawl detail: {urls}")
    browser_cfg = browserConfig()
    async with AsyncWebCrawler(verbose=True, headless=False, config=browser_cfg, crawler_strategy=strategyConfig()) as crawler:
        results = await crawler.arun_many(
            urls=urls,
            config=crawlerRunConfig(),
            dispatcher=dispatcherConfig()
        )

        for idx, result in enumerate(results):
            if not result.success:
                print(f"❌ Failed to fetch page: {urls[idx]} | {result.error_message}")
                continue

            soup = BeautifulSoup(result.html, "html.parser")
            website_name = "sosanhnha.com"
            website_config = Config.WEBSITES[website_name]
            llm_service = LLMService()
            crawler_instance = CrawlerFactory.create_crawler(website_name, website_config)
            raw_data = crawler_instance.extract_property_details(soup, urls[idx])

            raw_data.setdefault("source", website_name)
            raw_data.setdefault("link", urls[idx])  # Đảm bảo luôn có trường link

            try:
                property_obj = RealEstateProperty(**raw_data)
            except Exception as e:
                print(f"❌ Error creating RealEstateProperty for {urls[idx]}: {e}")
                continue

            data_list = await llm_service.process_batch([property_obj])
            data = data_list[0] if data_list else {}
            print("\n--- Extracted Data ---")
            for k, v in data.__dict__.items():
                print(f"{k}: {v}")

if __name__ == "__main__":
    urls = [
        "https://sosanhnha.com/cho-thue-nha-xuong-11-300-m-kcn-chau-duc-brvt-clawD8bo2",
        "https://sosanhnha.com/chuyen-nhuong-lo-dat-dep-kinh-doanh-buon-ban-tot-gia-mem-mat-duong-351-cla6A9Bdo",
        "https://sosanhnha.com/biet-thu-400m2-sd-quan-2-compound-luong-dinh-cua-tran-nao-5pn-6wc-moi-1ham-4l-31t500-dep-cla4xEwyN"
    ]
    asyncio.run(test_detail(urls))