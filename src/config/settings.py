import os
from typing import Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    def __init__(self):
        self.MONGODB_URI = os.getenv('MONGODB_URI', '')
        self.MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'real_estate_db')
        self.CRAWL_DELAY = int(os.getenv('CRAWL_DELAY', '2'))
        self.LINK_PER_BATCH = int(os.getenv('LINK_PER_PATCH', '20'))
        self.ITEM_PER_BATCH = int(os.getenv('ITEM_PER_PATCH', '20'))
        self.PAGES_SITE = int(os.getenv('PAGES_SITE', '1'))
        self.LLM_BATCH_SIZE = int(os.getenv('LLM_BATCH_SIZE', '5'))
        self.LLM_ENABLED = os.getenv('LLM_ENABLED', 'True').lower() == 'true'
        self.LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'gemini/gemini-2.0-flash')
        self.LLM_API_TOKEN = os.getenv('LLM_API_TOKEN', '')
        self.LLM_API_BASE_URL = os.getenv('LLM_API_BASE_URL', 'https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent')
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        self.LOG_FILE = os.getenv('LOG_FILE', 'logs/crawler.log')

        # Website configurations
        self.WEBSITES: Dict[str, Dict[str, Any]] = {
            'batdongsan.com.vn': {
                'base_url': 'https://batdongsan.com.vn',
                'search_urls': [
                    'https://batdongsan.com.vn/nha-dat-ban',
                    'https://batdongsan.com.vn/nha-dat-cho-thue'
                ],
                'login': True,
                'login_url': 'https://batdongsan.com.vn/sellernet/trang-dang-nhap',
                'enabled': True,
                'delay': self.CRAWL_DELAY
            },
            'nhatot.com': {
                'base_url': 'https://www.nhatot.com/',
                'search_urls': [
                    'https://www.nhatot.com/mua-ban-bat-dong-san',
                    'https://www.nhatot.com/thue-bat-dong-san'
                ],
                'login': True,
                'login_url': 'https://id.chotot.com/?continue=https://www.nhatot.com/in-popup-authorize-callback&event_source=navigation',
                'enabled': True,
                'delay': self.CRAWL_DELAY
            },
            'muaban.net': {
                'base_url': 'https://muaban.net/',
                'search_urls': [
                    'https://muaban.net/bat-dong-san/ban-nha-dat-chung-cu',
                    'https://muaban.net/bat-dong-san/cho-thue-nha-dat'
                ],
                'login': True,
                'login_url': 'https://muaban.net/account/login?returnUrl=https%3A%2F%2Fmuaban.net%2Fbat-dong-san',
                'enabled': True,
                'delay': self.CRAWL_DELAY
            },
            'bds123.vn': {
                'base_url': 'https://bds123.vn/',
                'search_urls': [
                    'https://bds123.vn/ban-nha.html'
                ],
                'login': False,
                'login_url': '',
                'enabled': True,
                'delay': self.CRAWL_DELAY
            },
            'sosanhnha.com': {
                'base_url': 'https://sosanhnha.com/',
                'search_urls': [
                    'https://sosanhnha.com/nh%C3%A0-%C4%91%E1%BA%A5t-b%C3%A1n',
                    'https://sosanhnha.com/nh%C3%A0-%C4%91%E1%BA%A5t-cho-thu%C3%AA'
                ],
                'login': False,
                'login_url': '',
                'enabled': True,
                'delay': self.CRAWL_DELAY
            },
            'mogi.vn': {
                'base_url': 'https://mogi.vn/',
                'search_urls': [
                    'https://mogi.vn/mua-nha-dat',
                    'https://mogi.vn/thue-nha-dat'
                ],
                'login': False,
                'login_url': '',
                'enabled': True,
                'delay': self.CRAWL_DELAY
            },
        }


config = Config()
