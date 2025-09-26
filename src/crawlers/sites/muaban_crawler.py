from typing import List, Dict, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from bson import ObjectId

from src.crawlers.base.base_crawler import BaseCrawler
from src.utils.text_processing import clean_text, extract_price, extract_area, extract_rooms, extract_bathrooms, \
    extract_frontage, parse_date, extract_city_from_address


class MuaBanCrawler(BaseCrawler):
    """Crawler for muaban.net"""

    def build_pagination_url(self, base_url: str, page: int) -> str:
        """Build pagination url for muaban.net"""
        if page == 1:
            return base_url

        separator = "&" if "?" in base_url else "?"
        return f"{base_url}{separator}p={page}"

    def extract_links_from_page(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract links from muaban.net"""

        links = []

        # Find property items - these are common selectors for BDS
        property_items = soup.select('div.sc-c7upxc-3.cBJHnx')

        for item in property_items:
            try:
                # Extract link
                link_element = item.find('a', href=True)
                if not link_element:
                    continue

                url = link_element['href']
                if not url.startswith('http'):
                    url = (
                        urljoin(self.base_url, url))

                # Extract title
                title_element = link_element.select_one('h3')
                title = title_element.get_text(strip=True) if title_element else ''

                links.append({'url': url, 'title': title})
            except Exception as e:
                self.logger.warning(f"Error extracting link from item: {e}")
                continue

        return links

    def extract_property_details(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract details from muaban.net"""
        data = {}

        try:
            # 1. Title
            title_selectors = [
                'h1.sc-6orc5o-8',
                'h1.title',
                'h1',

            ]
            title = self._extract_text_by_selector(soup, title_selectors)
            data['title'] = (
                clean_text(title))

            # 2. Address
            address_selectors = [
                'div.address',
                '.address'
            ]
            address = self._extract_text_by_selector(soup, address_selectors)
            data['address'] = clean_text(address)

            # 3. Price
            price_selectors = [
                'div.price',
                '.price'
            ]
            price_text = self._extract_text_by_selector(soup, price_selectors)
            data['price'] = extract_price(price_text) if price_text else None

            # 4. Area
            area_selectors = [
                'li:has(.label:-soup-contains("Diện tích đất")) span:not(.label)'
            ]
            area_text = self._extract_text_by_selector(soup, area_selectors)
            data['area'] = extract_area(area_text) if area_text else None

            # 5. Unit price
            price_value = data['price']
            area_value = data['area']
            if price_value and area_value and price_value > 0 and area_value > 0:
                data['unit_price'] = round(price_value / area_value, 2)
            else:
                data['unit_price'] = None

            # 6. Seller
            seller_selectors = [
                '.sc-lohvv8-4 .title',
                '.seller-name',
                '.author .title'
            ]
            seller = self._extract_text_by_selector(soup, seller_selectors)
            data['seller'] = clean_text(seller)

            # 7. Bedroom
            bedroom_selectors = [
                'li:has(.label:-soup-contains("Số phòng ngủ")) span:not(.label)'
            ]
            bedroom = self._extract_text_by_selector(soup, bedroom_selectors)
            data['bedroom'] = (
                extract_rooms(bedroom))

            # 8. Bathroom
            bathroom_selectors = [
                'li:has(.label:-soup-contains("Số phòng vệ sinh")) span:not(.label)'
            ]
            bathroom = self._extract_text_by_selector(soup, bathroom_selectors)
            data['bathroom'] = (
                extract_bathrooms(bathroom))

            # 9. Frontage
            frontage_selectors = [
                '.re__pr-specs-content-item:has(.re__pr-specs-content-item-title:-soup-contains("Mặt tiền")) .re__pr-specs-content-item-value'
            ]
            frontage = self._extract_text_by_selector(soup, frontage_selectors)
            data['frontage'] = (
                extract_frontage(frontage))

            # 10. Legal
            legal_selectors = [
                'li:has(.label:-soup-contains("Giấy tờ pháp lý")) span:not(.label)'
            ]
            legal = self._extract_text_by_selector(soup, legal_selectors)
            data['legal'] = clean_text(legal)

            # 11. Dateposted
            datepost_selectors = [
                'div.sc-6orc5o-21.ebxmhG div:has(span.label:-soup-contains("Ngày bắt đầu")) span.value'
            ]
            datepost = self._extract_text_by_selector(soup, datepost_selectors)
            date_obj = parse_date(datepost)
            if date_obj:
                # Đặt giờ phút giây về 0 để chỉ lưu ngày/tháng/năm
                date_obj = date_obj.replace(hour=0, minute=0, second=0, microsecond=0)
            data['datepost'] = date_obj if date_obj else None

            # 12. Description
            description_selectors = [
                '.sc-6orc5o-10.eRboKF'
            ]
            description = self._extract_text_by_selector(soup, description_selectors)
            data['description'] = clean_text(description)

            # 13. Link
            data['link'] = clean_text(url)

            # 14. City
            city = (
                extract_city_from_address(address))
            data['city'] = clean_text(city)

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