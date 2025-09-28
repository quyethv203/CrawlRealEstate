import re
from typing import List, Dict, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bson import ObjectId

from src.crawlers.base.base_crawler import BaseCrawler
from src.utils.text_processing import extract_rooms, clean_text, extract_area, extract_price, extract_bathrooms, \
    extract_frontage, parse_date, extract_city_from_address


class BDS123Crawler(BaseCrawler):
    """Crawler for bds_123.vn"""

    def build_pagination_url(self, base_url: str, page: int) -> str:
        """Build pagination url for bds123
.vn"""
        if page == 1:
            return base_url

        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}p={page}"

    def extract_links_from_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract links from bds123.vn"""

        links = []

        # Find property items - these are common selectors for BDS
        property_items = soup.find_all('li', class_=re.compile(r'(vip|normal|free)', re.I))

        for item in property_items:
            try:
                # Extract link
                a_tag = item.find('h3').find('a', href=True)
                if not a_tag:
                    continue

                url = a_tag['href']
                if not url.startswith('http'):
                    url = urljoin(self.base_url, url)

                # Extract title
                title = a_tag.get('title', '').strip() or a_tag.get_text(strip=True)

                links.append({'url': url, 'title': title})
            except Exception as e:
                self.logger.warning(f"Error extracting link from item: {e}")
                continue

        return links

    def extract_property_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract details from bds123.vn"""
        data = {}

        schema = {
            "title": {
                "selectors": [
                    'header h1',
                ],
                "postprocess": clean_text
            },
            "address": {
                "selectors": [
                    "td:has(div:-soup-contains('Địa chỉ')) + td"
                ],
                "postprocess": clean_text
            },
            "seller": {
                "selectors": [
                    ".agent-name a",
                    ".agent-name",
                    ".author-name",
                    ".contact-name",
                    ".mt-3.text-center > span.fs-5.fw-medium"
                ],
                "postprocess": clean_text
            },
            "description": {
                "selectors": [
                    '.post__main__content',
                    '.info-content-body',
                    '.description'
                ],
                "postprocess": clean_text
            },
            "price": {
                "selectors": [
                    'header .d-flex > div.fs-6.fw-semibold.text-pink'
                ],
                "postprocess": extract_price
            },
            "area": {
                "selectors": [
                    'header .d-flex > div.fs-6.d-flex.ms-5'
                ],
                "postprocess": extract_area
            },
            "bedroom": {
                "custom": lambda soup: (
                    extract_rooms(
                        soup.select_one('i.icon.bed').parent.get_text(strip=True)
                    ) if soup.select_one('i.icon.bed') and soup.select_one('i.icon.bed').parent else None
                )
            },
            "bathroom": {
                "custom": lambda soup: (
                    extract_bathrooms(
                        soup.select_one('i.icon.bath').parent.get_text(strip=True)
                    ) if soup.select_one('i.icon.bath') and soup.select_one('i.icon.bath').parent else None
                )
            },
            "frontage": {
                "selectors": [
                    '.re__pr-specs-content-item:has(.re__pr-specs-content-item-title:-soup-contains("Mặt tiền")) .re__pr-specs-content-item-value'
                ],
                "postprocess": extract_frontage
            },
            "legal": {
                "selectors": [
                    '.info-attr:nth-child(2) span:nth-child(2)',
                    'span:has(> span:-soup-contains("Pháp lý")) + span',
                ],
                "postprocess": clean_text
            },
            "datepost": {
                "selectors": [
                    "tr:has(div:contains('Ngày đăng')) time",
                    "tr td time"
                ],
                "postprocess": lambda v: parse_date(v).replace(hour=0, minute=0, second=0, microsecond=0) if parse_date(v) else None
            },
            "city": {
                "custom": lambda soup, data: extract_city_from_address(data.get('address', ''))
            },
            "numberphone": {
                "custom": lambda soup: __import__('src.utils.text_processing',
                                                  fromlist=['extract_phone']).extract_phone(soup.get_text())
            },
            "link": {
                "value": url,
                "postprocess": clean_text
            }
        }

        # Extract theo schema
        for field, conf in schema.items():
            value = None
            if "custom" in conf:
                # custom có thể cần truyền soup hoặc data
                try:
                    if "data" in conf["custom"].__code__.co_varnames:
                        value = conf["custom"](soup, data)
                    else:
                        value = conf["custom"](soup)
                except Exception as e:
                    value = None
            elif "selectors" in conf:
                value = self._extract_text_by_selector(soup, conf["selectors"])
                if value and "postprocess" in conf:
                    value = conf["postprocess"](value)
            elif "value" in conf:
                value = conf["value"]
                if value and "postprocess" in conf:
                    value = conf["postprocess"](value)
            data[field] = value if value else None

        # Unit price
        price_value = data.get('price')
        area_value = data.get('area')
        if price_value and area_value and price_value > 0 and area_value > 0:
            data['unit_price'] = round(price_value / area_value, 2)
        else:
            data['unit_price'] = None

        if "id" not in data or not data["id"]:
            data["id"] = str(ObjectId())
        return data

    @staticmethod
    def _extract_text_by_selector(soup: BeautifulSoup, selectors: List[str]):
        """Extract text using multiple CSS selectors"""
        for selector in selectors:
            try:
                if ':contains(' in selector:
                    # Handle pseudo-selector contains
                    base_selector, contains_text = selector.split(':contains(')
                    contains_text = contains_text.rstrip(')')
                    elements = soup.select(base_selector)
                    for elem in elements:
                        if contains_text.lower() in elem.get_text().lower():
                            return elem.get_text(strip=True)
                else:
                    element = soup.select_one(selector)
                    if element:
                        return element.get_text(strip=True)
            except Exception as e:
                continue
        return ""
