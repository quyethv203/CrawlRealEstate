import re
from typing import List, Dict, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bson import ObjectId

from src.crawlers.base.base_crawler import BaseCrawler
from src.utils.text_processing import extract_rooms, clean_text, extract_area, extract_price, extract_bathrooms, \
    extract_frontage, parse_date, extract_city_from_address


class MogiCrawler(BaseCrawler):
    """Crawler for mogi.vn"""

    def build_pagination_url(self, base_url: str, page: int) -> str:
        """Build pagination url for mogi.vn"""
        if page == 1:
            return base_url

        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}p={page}"

    def extract_links_from_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract links from mogi.vn"""

        links = []

        # Find property items - these are common selectors for BDS
        property_items = soup.find_all(['div'], class_=re.compile(r'prop-info', re.I))

        for item in property_items:
            try:
                # Extract link
                link_element = item.find('a', href=True)
                if not link_element:
                    continue

                url = link_element['href']
                if not url.startswith('http'):
                    url = urljoin(self.base_url, url)

                # Extract title
                title_element = item.find(['h1', 'a'], class_=re.compile(r'prop-title', re.I))
                title = title_element.get_text(strip=True) if title_element else ''

                links.append({'url': url, 'title': title})
            except Exception as e:
                self.logger.warning(f"Error extracting link from item: {e}")
                continue

        return links

    def extract_property_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract details from mogi.vn"""
        data = {}

        try:
            # 1. Title
            title_selectors = [
                '.main-info .title h1'
            ]
            title = self._extract_text_by_selector(soup, title_selectors)
            data['title'] = clean_text(title)

            # 2. Address
            address_selectors = [
                'div.address',
                '.main-info .address'
            ]
            address = self._extract_text_by_selector(soup, address_selectors)
            data['address'] = clean_text(address)

            # 14. City
            if address:
                city = extract_city_from_address(address)
            else:
                city = ""

            data['city'] = clean_text(city)

            # 3. Price
            price_selectors = [
                '.main-info .price'
            ]
            price_text = self._extract_text_by_selector(soup, price_selectors)
            data['price'] = extract_price(price_text) if price_text else None

            info_attrs = soup.select('.info-attrs .info-attr')
            info_map = {}
            for attr in info_attrs:
                spans = attr.find_all('span')
                if len(spans) >= 2:
                    key = spans[0].get_text(strip=True)
                    value = spans[1].get_text(strip=True)
                    info_map[key] = value
            # 4. Area
            data['area'] = extract_area(info_map.get('Diện tích đất', None))


            # 5. Unit price
            price_value = data['price']
            area_value = data['area']
            if price_value and area_value and price_value > 0 and area_value > 0:
                data['unit_price'] = round(price_value / area_value, 2)
            else:
                data['unit_price'] = None

            # 6. Seller
            seller_selectors = [
                ".agent-name a"
            ]
            seller = self._extract_text_by_selector(soup, seller_selectors)
            data['seller'] = clean_text(seller)

            # 7. Bedroom
            data['bedroom'] = extract_rooms(info_map.get('Phòng ngủ', None))

            # 8. Bathroom
            data['bathroom'] = extract_bathrooms(info_map.get('Nhà tắm', None))

            # 9. Frontage
            data['frontage'] = extract_frontage(info_map.get('Mặt tiền', None))

            # 10. Legal
            data['legal'] = clean_text(info_map.get('Pháp lý', None))

            # 11. Dateposted
            date_obj = parse_date(info_map.get('Ngày đăng', None))
            if date_obj:
    # Đặt giờ phút giây về 0 để chỉ lưu ngày/tháng/năm
                date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            data['datepost'] = date_obj if date_obj else None

            # 12. Description
            description_selectors = [
                '.info-content-body'
            ]
            description = self._extract_text_by_selector(soup, description_selectors)
            data['description'] = clean_text(description)

            # 13. Link
            data['link'] = clean_text(url)


            # 15. NumberPhone

        except Exception as e:
            self.logger.error(f"Error extracting property details: {e}")

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
