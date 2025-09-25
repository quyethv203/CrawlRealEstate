from crawl4ai import RateLimiter, BrowserConfig, UndetectedAdapter, CrawlerRunConfig, CacheMode
from crawl4ai.async_crawler_strategy import AsyncPlaywrightCrawlerStrategy
from crawl4ai.async_dispatcher import MemoryAdaptiveDispatcher

rate_limiter = RateLimiter(
    base_delay=(2.0, 4.0),  # Random delay between 2-4 seconds
    max_delay=30.0,  # Cap delay at 30 seconds
    max_retries=5,  # Retry up to 5 times on rate-limiting errors
    rate_limit_codes=[429, 503]  # Handle these HTTP status codes
)

def dispatcherConfig(): # arun.many()
    return MemoryAdaptiveDispatcher(
        memory_threshold_percent=85,
        check_interval=3,
        max_session_permit=50,
        rate_limiter= rate_limiter
    )

def browserConfig(): # asyncwebcrawler
    return BrowserConfig(
        browser_type='chromium',
        user_agent='random',
        headless=True,
        enable_stealth=True,
        extra_args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-blink-features=AutomationControlled",
            "--disable-extensions",
            "--disable-plugins",
            "--disable-images",  # Skip images for speed
            "--disable-javascript",  # Skip JS if not needed
            "--disable-css",  # Skip CSS for speed
            "--disable-web-security",
            "--disable-features=VizDisplayCompositor",
            "--disable-background-timer-throttling",
            "--disable-renderer-backgrounding",
            "--disable-backgrounding-occluded-windows",
            "--disable-component-extensions-with-background-pages",
            "--disable-ipc-flooding-protection",
            "--no-first-run",
            "--no-default-browser-check",
            "--memory-pressure-off",
            "--max_old_space_size=4096"
        ],
        headers={
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "vi-VN,vi;q=0.9,en;q=0.8,fr;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Cache-Control": "max-age=0"
        }
    )

def crawlerRunConfig(): #arun
    return CrawlerRunConfig(
        page_timeout=60000,
        delay_before_return_html=3.0,
        simulate_user=True,
        cache_mode=CacheMode.BYPASS
    )

def strategyConfig(): # asyncWebcrawler
    adapter = UndetectedAdapter()
    config = browserConfig()
    return AsyncPlaywrightCrawlerStrategy(
        browser_config=config,
        browser_adapter=adapter
    )