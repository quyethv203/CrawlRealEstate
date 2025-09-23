import re
from datetime import datetime, timedelta
from typing import Optional


def clean_text(text: str) -> str:
    """Làm sạch text"""
    if not text:
        return None

    # Loại bỏ khoảng trắng thừa
    text = re.sub(r'\s+', ' ', text.strip())

    # Loại bỏ ký tự đặc biệt
    text = re.sub(
        r'[^\w\s\-.,:;()\[\]{}!?@#$%^&*+=<>/\\|`~"\'àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]',
        '', text)

    return text.strip()


def extract_price(text: str) -> Optional[float]:
    """Trích xuất giá từ text (VND), hỗ trợ cả dạng '12 tỷ 500 triệu'."""
    if not text:
        return None

    text = text.lower().replace(',', '.').replace('  ', ' ')
    total = 0

    # Xử lý dạng "x tỷ y triệu"
    ty_match = re.search(r'(\d+(?:[.,]\d+)?)\s*t[ỷy]', text)
    trieu_match = re.search(r'(\d+(?:[.,]\d+)?)\s*triệu', text)
    nghin_match = re.search(r'(\d+(?:[.,]\d+)?)\s*(nghìn|ngàn|k)', text)

    if ty_match:
        ty = float(ty_match.group(1).replace(',', '.'))
        total += ty * 1_000_000_000
    if trieu_match:
        trieu = float(trieu_match.group(1).replace(',', '.'))
        total += trieu * 1_000_000
    if nghin_match:
        nghin = float(nghin_match.group(1).replace(',', '.'))
        total += nghin * 1_000

    # Nếu có dạng "x tỷ y triệu" thì trả về luôn
    if total > 0:
        return total

    # Nếu không, fallback về các pattern cũ
    patterns = [
        (r'(\d+)[,\.](\d+)\s*tỷ', 1_000_000_000),
        (r'(\d+)[,\.](\d+)\s*ty', 1_000_000_000),
        (r'(\d+)\s*tỷ', 1_000_000_000),
        (r'(\d+)\s*ty', 1_000_000_000),
        (r'(\d+)[,\.](\d+)\s*triệu', 1_000_000),
        (r'(\d+)[,\.](\d+)\s*tr(?![aăâ])', 1_000_000),
        (r'(\d+)\s*triệu', 1_000_000),
        (r'(\d+)\s*tr(?![aăâ])', 1_000_000),
        (r'(\d+)[,\.](\d+)\s*nghìn', 1_000),
        (r'(\d+)[,\.](\d+)\s*ngàn', 1_000),
        (r'(\d+)[,\.](\d+)\s*k', 1_000),
        (r'(\d+)\s*nghìn', 1_000),
        (r'(\d+)\s*ngàn', 1_000),
        (r'(\d+)\s*k', 1_000),
        (r'(\d+(?:\d{3})*)', 1),
    ]

    for pattern, multiplier in patterns:
        match = re.search(pattern, text)
        if match:
            try:
                if len(match.groups()) == 2:
                    integer_part = int(match.group(1))
                    decimal_part = int(match.group(2))
                    if decimal_part < 10:
                        value = integer_part + decimal_part / 10.0
                    else:
                        value = integer_part + decimal_part / 100.0
                else:
                    value = float(match.group(1))
                return value * multiplier
            except (ValueError, IndexError):
                continue

    return None


def extract_area(text: str) -> Optional[float]:
    """Trích xuất diện tích từ text (m²)"""
    if not text:
        return None

    text = text.lower().replace(',', '.')

    patterns = [
        r'(\d+(?:\.\d+)?)\s*m[²2]',
        r'(\d+(?:\.\d+)?)\s*m\s*2',
        r'(\d+(?:\.\d+)?)\s*mét\s*vuông',
        r'(\d+(?:\.\d+)?)\s*met\s*vuong'
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return float(match.group(1))

    return None


def extract_phone(text: str) -> Optional[str]:
    """Trích xuất số điện thoại từ text"""
    if not text:
        return None

    # Loại bỏ khoảng trắng và dấu
    text = re.sub(r'[\s\-.]', '', text)

    # Pattern cho số điện thoại VN
    patterns = [
        r'(0\d{9,10})',  # 0xxxxxxxxx
        r'(\+84\d{9,10})',  # +84xxxxxxxxx
        r'(84\d{9,10})',  # 84xxxxxxxxx
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            phone = match.group(1)
            # Chuẩn hóa về định dạng 0xxxxxxxxx
            if phone.startswith('+84'):
                phone = '0' + phone[3:]
            elif phone.startswith('84'):
                phone = '0' + phone[2:]
            return phone

    return None


def extract_rooms(text: str) -> Optional[int]:
    """Trích xuất số phòng ngủ từ text (hỗ trợ cả dạng viết tắt như 2PN, 3bed...)"""
    if not text:
        return None

    text = text.lower()

    patterns = [
        r'(\d+)\s*phòng\s*ngủ',
        r'(\d+)\s*pn\b',
        r'(\d+)\s*bed(room)?\b',
        r'(\d+)\s*bed\b',
        r'(\d+)\s* ngủ\b',
        r'(\d+)\s*pn',  # 2pn, 3pn không dấu cách
        r'(\d+)\s*phòng',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    # Nếu chỉ là số, ví dụ "2", "3"
    if text.strip().isdigit():
        return int(text.strip())

    return None


def extract_bathrooms(text: str) -> Optional[int]:
    """Trích xuất số phòng tắm/vệ sinh từ text (hỗ trợ cả dạng viết tắt như 2WC, 1bath...)"""
    if not text:
        return None

    text = text.lower()

    patterns = [
        r'(\d+)\s*phòng',
        r'(\d+)\s*phòng\s*tắm',
        r'(\d+)\s*phòng\s*vệ\s*sinh',
        r'(\d+)\s*wc\b',
        r'(\d+)\s*toilet\b',
        r'(\d+)\s*bath(room)?\b',
        r'(\d+)\s*tắm\b',
        r'(\d+)\s*vệ\s*sinh\b',
        r'(\d+)\s*wc',  # 2wc, 3wc không dấu cách
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))

    # Nếu chỉ là số, ví dụ "1", "2"
    if text.strip().isdigit():
        return int(text.strip())

    return None


def parse_date(date_str: str) -> Optional[datetime]:
    """Parse ngày tháng từ string"""
    if not date_str:
        return None

    date_str = clean_text(date_str.lower())

    # Các pattern ngày tháng thường gặp
    patterns = [
        r'(\d{1,2})/(\d{1,2})/(\d{4})',  # dd/mm/yyyy
        r'(\d{1,2})-(\d{1,2})-(\d{4})',  # dd-mm-yyyy
        r'(\d{4})/(\d{1,2})/(\d{1,2})',  # yyyy/mm/dd
        r'(\d{4})-(\d{1,2})-(\d{1,2})',  # yyyy-mm-dd
    ]

    for pattern in patterns:
        match = re.search(pattern, date_str)
        if match:
            try:
                if len(match.group(3)) == 4:  # dd/mm/yyyy format
                    day, month, year = int(match.group(1)), int(match.group(2)), int(match.group(3))
                else:  # yyyy/mm/dd format
                    year, month, day = int(match.group(1)), int(match.group(2)), int(match.group(3))

                return datetime(year, month, day)
            except (ValueError, IndexError):
                continue

    # Xử lý "hôm nay", "hôm qua", "x ngày trước", "x giờ trước", "x phút trước"
    now = datetime.now()
    if 'hôm nay' in date_str or 'today' in date_str:
        return now
    elif 'hôm qua' in date_str or 'yesterday' in date_str:
        return now - timedelta(days=1)
    elif 'tuần' in date_str and 'trước' in date_str:
        return now - timedelta(days=7)
    else:
        # x ngày trước
        match = re.search(r'(\d+)\s*ngày\s*trước', date_str)
        if match:
            days = int(match.group(1))
            return now - timedelta(days=days)
        # x giờ trước
        match = re.search(r'(\d+)\s*giờ\s*trước', date_str)
        if match:
            hours = int(match.group(1))
            return now - timedelta(hours=hours)
        # x phút trước
        match = re.search(r'(\d+)\s*phút\s*trước', date_str)
        if match:
            minutes = int(match.group(1))
            return now - timedelta(minutes=minutes)

    return None


def extract_frontage(text: str) -> Optional[float]:
    """Trích xuất mặt tiền từ text (hỗ trợ cả số, '7', '7.0', '7m', 'mặt tiền 7m', ...)"""
    if text is None:
        return None

    # Nếu là số (int, float), trả về luôn
    if isinstance(text, (int, float)):
        return float(text)

    text = str(text).strip().lower().replace(',', '.')

    # Nếu chỉ là số hoặc số thực dạng chuỗi
    try:
        return float(text)
    except ValueError:
        pass

    # Pattern cho các trường hợp có chữ 'm'
    pattern = r'(\d+(?:\.\d+)?)\s*m(?![²2])'
    match = re.search(pattern, text)
    if match:
        return float(match.group(1))

    return None


def extract_city_from_address(text: str) -> str:
    """Extract city name from address (after last comma, clean format)"""
    if not text:
        return None

    # Split by comma and get the last part
    parts = text.split(',')
    if len(parts) >= 2:
        city_part = parts[-1].strip()
    else:
        city_part = text.strip()

    # Clean city name - remove prefixes like TP, Thành phố, Tỉnh, etc.
    city_part = re.sub(r'^(TP\.?\s*|Thành phố\s*|Tỉnh\s*|Huyện\s*)', '', city_part, flags=re.IGNORECASE)

    # Specific handling for common Vietnamese cities
    city_mapping = {
        'Hồ Chí Minh': 'Hồ Chí Minh',
        'HCM': 'Hồ Chí Minh',
        'TPHCM': 'Hồ Chí Minh',
        'Ho Chi Minh': 'Hồ Chí Minh',
        'Sai Gon': 'Hồ Chí Minh',
        'Sài Gòn': 'Hồ Chí Minh',
        'Hà Nội': 'Hà Nội',
        'Ha Noi': 'Hà Nội',
        'Hanoi': 'Hà Nội',
        'Đà Nẵng': 'Đà Nẵng',
        'Da Nang': 'Đà Nẵng',
        'Danang': 'Đà Nẵng',
        'Hải Phòng': 'Hải Phòng',
        'Hai Phong': 'Hải Phòng',
        'Cần Thơ': 'Cần Thơ',
        'Can Tho': 'Cần Thơ',
        'Biên Hòa': 'Biên Hòa',
        'Bien Hoa': 'Biên Hòa',
        'Nha Trang': 'Nha Trang',
        'Vũng Tàu': 'Vũng Tàu',
        'Vung Tau': 'Vũng Tàu',
        'Huế': 'Huế',
        'Hue': 'Huế'
    }

    # Check exact matches first
    for key, value in city_mapping.items():
        if key.lower() in city_part.lower():
            return value

    # If no exact match, clean and return the city part
    city_part = city_part.strip()

    # Remove any remaining prefixes/suffixes
    city_part = re.sub(r'(việt nam|vietnam|vn)$', '', city_part, flags=re.IGNORECASE).strip()

    return city_part if city_part else None


def is_valid_url(url: str) -> bool:
    """Kiểm tra URL hợp lệ"""
    if not url:
        return False

    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    return url_pattern.match(url) is not None
