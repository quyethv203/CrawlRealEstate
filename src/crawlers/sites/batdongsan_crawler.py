import re
from typing import List, Dict, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bson import ObjectId

from src.crawlers.base.base_crawler import BaseCrawler
from src.utils.text_processing import extract_price, extract_area, clean_text, extract_rooms, extract_bathrooms, \
    parse_date, extract_frontage, extract_city_from_address


class BatDongSanCrawler(BaseCrawler):
    """Crawler for batdongsan.com.vn"""

    def build_pagination_url(self, base_url: str, page: int) -> str:
        """Build pagination url for batdongsan.com.vn"""
        if page == 1:
            return base_url

        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}p={page}"

    def extract_links_from_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract links from batdongsan.com.vn"""

        links = []

        # Find property items - these are common selectors for BDS
        property_items = soup.find_all('a', class_='js__product-link-for-product-id')

        for item in property_items:
            try:
                # Extract link
                url = item.get('href', '')
                if not url:
                    continue

                if not url.startswith('http'):
                    url = urljoin(self.base_url, url)

                # Lấy title từ attribute title hoặc từ span bên trong
                title = item.get('title', '')

                # Nếu không có title trong attribute, tìm trong span.pr-title
                if not title:
                    title_element = item.select_one('span.pr-title.js__card-title')
                    if title_element:
                        title = title_element.get_text(strip=True)

                # Fallback: tìm trong h3
                if not title:
                    h3_element = item.select_one('h3.re__card-title span')
                    if h3_element:
                        title = h3_element.get_text(strip=True)

                if url and title:
                    links.append({
                        'url': url,
                        'title': title
                    })
                    self.logger.debug(f"Extracted: {title[:50]}... -> {url}")
            except Exception as e:
                self.logger.warning(f"Error extracting link from item: {e}")
                continue

        return links

    def extract_property_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        data = {}

        # SCHEMA cho các trường lấy trực tiếp bằng selector
        schema = {
            "title": {
                "selectors": [
                    'h1.pr-title',
                    'h1.title',
                    '.detail-title h1',
                    'h1',
                    '.product-title'
                ],
                "postprocess": clean_text
            },
            "address": {
                "selectors": [
                    '.re__pr-short-description',
                ],
                "postprocess": clean_text
            },
            "seller": {
                "selectors": [
                    '.re__contact-name',
                    '.seller-name',
                    '.contact-name',
                    '.agent-name'
                ],
                "postprocess": clean_text
            },
            "description": {
                "selectors": [
                    '.re__section-body.js__pr-description',
                    '.re__pr-description .re__section-body',
                    '.re__pr-des-content',
                    '.description',
                    '.content',
                    '.detail-content'
                ],
                "postprocess": clean_text
            },
            "link": {
                "value": url,
                "postprocess": clean_text
            }
        }

        # Extract các trường cơ bản theo schema
        for field, conf in schema.items():
            if "selectors" in conf:
                value = self._extract_text_by_selector(soup, conf["selectors"])
            else:
                value = conf.get("value")
            if value and "postprocess" in conf:
                value = conf["postprocess"](value)
            data[field] = value if value else None

        # Extract các trường đặc biệt từ block specs
        specs = soup.select('.re__pr-specs-content-item')
        specs_map = {}
        for item in specs:
            label = item.select_one('.re__pr-specs-content-item-title')
            value = item.select_one('.re__pr-specs-content-item-value')
            if label and value:
                specs_map[label.get_text(strip=True)] = value.get_text(strip=True)

        # Price
        price_text = specs_map.get('Mức giá')
        data['price'] = extract_price(price_text) if price_text else None

        # Area
        area_text = specs_map.get('Diện tích')
        data['area'] = extract_area(area_text) if area_text else None

        # Unit price
        price_value = data['price']
        area_value = data['area']
        if price_value and area_value and price_value > 0 and area_value > 0:
            data['unit_price'] = round(price_value / area_value, 2)
        else:
            data['unit_price'] = None

        # Bedroom
        bedroom_text = specs_map.get('Số phòng ngủ') or specs_map.get('Phòng ngủ')
        data['bedroom'] = extract_rooms(bedroom_text) if bedroom_text else None

        # Bathroom
        bathroom_text = specs_map.get('Số phòng tắm, vệ sinh') or specs_map.get('Phòng tắm')
        data['bathroom'] = extract_bathrooms(bathroom_text) if bathroom_text else None

        # Frontage
        frontage_text = None
        for k in specs_map:
            if "Mặt tiền" in k:
                frontage_text = specs_map[k]
                break
        data['frontage'] = extract_frontage(frontage_text) if frontage_text else None

        # Legal
        legal_text = None
        for k in specs_map:
            if "Pháp lý" in k:
                legal_text = specs_map[k]
                break
        data['legal'] = clean_text(legal_text) if legal_text else None

        # Date posted
        datepost = None
        for item in soup.select('.re__pr-short-info-item'):
            label = item.select_one('.title')
            value = item.select_one('.value')
            if label and value and "ngày đăng" in label.get_text(strip=True).lower():
                datepost = value.get_text(strip=True)
                break
        date_obj = parse_date(datepost)
        if date_obj:
        # Đặt giờ phút giây về 0 để chỉ lưu ngày/tháng/năm
            date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
        data['datepost'] = date_obj if date_obj else None

        # City
        data['city'] = extract_city_from_address(data['address']) if data.get('address') else None

        # NumberPhone (số điện thoại)
        from src.utils.text_processing import extract_phone
        data['numberphone'] = extract_phone(soup.get_text())
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
            except Exception:
                continue
        return ""
