#!/usr/bin/env python3
"""
Real Estate Crawler - Main Application
Crawl real estate data from multiple Vietnamese websites
"""

import sys
import os
import asyncio
import argparse
from datetime import datetime
from src.crawlers.base.observer import DataSaveObserver, LLMProcessingObserver
from src.data.repositories.RealEstateRepository import RealEstateRepository
from src.data.repositories.WebsiteStateRepository import WebsiteStateRepository

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Setup logging
from src.services.llm_service import LLMService
from src.utils.logging import setup_logging

setup_logging()


def get_enabled_websites_from_db(config):
    """
    Trả về dict {name: config} cho các website đang enabled,
    lấy trạng thái từ DB, còn config chi tiết lấy từ config.
    """
    enabled_names = WebsiteStateRepository.get_enabled_websites()  # trả về list tên web đang enabled
    return {name: config.WEBSITES[name] for name in enabled_names if name in config.WEBSITES}


async def run_full_crawl():
    """Run full crawl across all enabled websites"""
    print("🏠 Real Estate Crawler - Starting Full Crawl")
    print("=" * 60)

    try:
        # Import components
        from src.config.settings import config
        from src.crawlers.base.factory import CrawlerFactory
        from src.crawlers.base.observer import (
            DataSaveObserver, LoggingObserver,
            ProgressObserver, LLMProcessingObserver
        )

        from src.services.llm_service import LLMService
        from src.utils.logging import get_logger

        print("✅ All components imported successfully")

        # Initialize services
        repository = RealEstateRepository()
        llm_service = LLMService()
        logger = get_logger("crawler_main")

        # Get enabled websites from DB
        enabled_websites = get_enabled_websites_from_db(config)
        print(f"🌐 Found {len(enabled_websites)} enabled websites:")
        for name in enabled_websites.keys():
            print(f"   - {name}")

        # Initialize observers
        data_save_observer = DataSaveObserver(repository)
        llm_observer = LLMProcessingObserver(llm_service, downstream_observers=[data_save_observer])
        observers = [
            LoggingObserver(logger),
            ProgressObserver(),
            llm_observer,
            data_save_observer
        ]

        total_properties = 0

        # Crawl each website
        async def crawl_one_site(website_name, website_config):
            print(f"\n🚀 Starting crawl for: {website_name}")
            print("-" * 40)
            try:
                crawler = CrawlerFactory.create_crawler(website_name, website_config)
                for observer in observers:
                    crawler.add_observer(observer)
                properties = await crawler.crawl_all()
                print(f"✅ {website_name}: Found {len(properties)} properties")
                return len(properties)
            except Exception as e:
                print(f"❌ Error crawling {website_name}: {e}")
                return 0

        # Tạo task cho từng website
        tasks = [
            crawl_one_site(website_name, website_config)
            for website_name, website_config in enabled_websites.items()
        ]
        # Chạy song song
        results = await asyncio.gather(*tasks)
        total_properties = sum(results)
        if llm_observer.tasks:
            print(">>> [MAIN] Waiting for all LLM tasks to finish...")
            await asyncio.gather(*llm_observer.tasks)

        print(f"\n🎉 Crawl completed!")
        print(f"   Total properties found: {total_properties}")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        return total_properties

    except Exception as e:
        print(f"❌ Crawl failed: {e}")
        import traceback
        traceback.print_exc()
        return 0


async def test_single_website(website_name):
    """Test crawling a single website"""
    print(f"🧪 Testing Single Website: {website_name}")
    print("=" * 50)

    try:
        from src.config.settings import config
        from src.crawlers.base.factory import CrawlerFactory
        from src.crawlers.base.observer import LoggingObserver, ProgressObserver
        from src.utils.logging import get_logger

        repository = RealEstateRepository()
        llm_service = LLMService()
        # Get enabled websites from DB
        enabled_websites = get_enabled_websites_from_db(config)
        if website_name not in enabled_websites:
            print(f"❌ Website '{website_name}' not found in enabled websites")
            print(f"Available websites: {list(enabled_websites.keys())}")
            return False

        website_config = enabled_websites[website_name]
        print(f"✅ Website config loaded")
        print(f"   - Base URL: {website_config['base_url']}")
        print(f"   - Search URLs: {len(website_config['search_urls'])}")

        # Create logger
        logger = get_logger(f"test_{website_name}")

        # Create crawler
        crawler = CrawlerFactory.create_crawler(website_name, website_config)
        print(f"✅ Crawler created: {type(crawler).__name__}")

        # Add basic observers  
        data_save_observer = DataSaveObserver(repository)
        llm_observer = LLMProcessingObserver(llm_service, downstream_observers=[data_save_observer])
        observers = [
            LoggingObserver(logger),
            ProgressObserver(),
            llm_observer,
            data_save_observer
        ]
        for observer in observers:
            crawler.add_observer(observer)

        # Test crawl (will use default settings from config)
        print(f"\n🚀 Starting crawl test...")
        print(f"   This may take a few minutes depending on the website...")

        properties = await crawler.crawl_all()

        if llm_observer.tasks:
            print(">>> [MAIN] Waiting for all LLM tasks to finish...")
            await asyncio.gather(*llm_observer.tasks)

        print(f"✅ Test successful!")
        print(f"   - Properties found: {len(properties)}")

        if properties:
            sample = properties[0]
            print(sample)
        return True

    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def list_websites():
    """List all available websites (enabled in DB)"""
    print("🌐 Available Websites")
    print("=" * 30)

    try:
        from src.config.settings import config
        enabled_websites = get_enabled_websites_from_db(config)
        print(f"Found {len(enabled_websites)} websites:")
        for i, (name, conf) in enumerate(enabled_websites.items(), 1):
            print(f"{i}. {name}")
            print(f"   - Base URL: {conf['base_url']}")
            print(f"   - Search URLs: {len(conf['search_urls'])}")
            print()
        return True

    except Exception as e:
        print(f"❌ Failed to list websites: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description='Real Estate Crawler')
    parser.add_argument('--action', choices=['crawl', 'test', 'list'],
                        default='crawl', help='Action to perform')
    parser.add_argument('--website', help='Website to test (for test action)')

    args = parser.parse_args()

    try:
        if args.action == 'list':
            asyncio.run(list_websites())
        elif args.action == 'test':
            if not args.website:
                print("❌ Please specify --website for test action")
                print("Use --action list to see available websites")
                return
            asyncio.run(test_single_website(args.website))
        elif args.action == 'crawl':
            total = asyncio.run(run_full_crawl())
            if total > 0:
                print(f"\n💾 Database status:")
                print(f"   - Properties saved: {total}")
                print(f"   - Ready for analysis!")

    except KeyboardInterrupt:
        print("\n⚠️ Crawl interrupted by user")
    except Exception as e:
        print(f"💥 Fatal error: {e}")


if __name__ == "__main__":
    main()