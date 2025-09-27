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
            website_name = "batdongsan.com.vn"
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
        "https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-duong-dai-lo-vong-cung-phuong-an-khanh-prj-the-galleria-residence/cho-duplex-day-du-noi-that-view-quan-1-dep-lung-linh-tai-galleria-pr43970779",
        # "https://batdongsan.com.vn/cho-thue-nha-rieng-duong-huynh-van-banh-phuong-13-9/cho-5x20m-4tang-5pn-san-thuong-40-trieu-thang-pr43826765",
        # "https://batdongsan.com.vn/cho-thue-can-ho-chung-cu-duong-n1-phuong-son-ky-prj-diamond-alnata/cho-2pn-2wc-khu-celadon-city-16-trieu-thang-bao-phi-quan-ly-pr43970713"
    ]
    asyncio.run(test_detail(urls))