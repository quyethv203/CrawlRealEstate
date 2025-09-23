# CrawlRealEstate

# Real Estate Crawler

## 🏠 Mô Tả
Hệ thống crawler bất động sản Việt Nam sử dụng Crawl4AI và LLM để trích xuất dữ liệu từ các website:
- BatDongSan.com.vn
- NhaTot.com  
- Mogi.vn
- BDS123.com
- MuaBanNhadat.com
- SoSanhNha.com

## 🚀 Tính Năng
- **Crawl4AI Integration**: Sử dụng công nghệ Crawl4AI thay vì BeautifulSoup
- **LLM Extraction**: AI hiểu ngữ cảnh để extract dữ liệu phức tạp
- **Authentication**: Tự động đăng nhập các website cần thiết
- **MongoDB Storage**: Lưu trữ dữ liệu vào MongoDB
- **Async Processing**: Xử lý bất đồng bộ cho performance tốt

## 📋 Yêu Cầu
- Python 3.8+
- MongoDB
- Crawl4AI
- PyMongo
- Pydantic

## ⚡ Cài Đặt
```bash
# Clone repository
git clone <repository_url>
cd RealEstateCrawler_Test

# Cài đặt dependencies
pip install -r requirements.txt

# Cấu hình
cp .env.example .env
# Sửa .env với thông tin MongoDB và authentication
```

## 🔧 Cấu Hình
Sửa file `src/config/settings.py`:
```python
MONGODB_URL = "mongodb://localhost:27017"
DATABASE_NAME = "real_estate_db"

# Thêm authentication cho websites cần thiết
WEBSITES = {
    'batdongsan.com.vn': {
        'authentication': {
            'required': True,
            'credentials': {
                'email': 'your_email@example.com',
                'password': 'your_password'
            }
        }
    }
}
```

## 🏃 Chạy Crawler
```bash
# Chạy crawler cho tất cả websites
python main.py

# Chạy crawler cho website cụ thể
python run.py --site batdongsan.com.vn
```

## 📊 Dữ Liệu
Dữ liệu được lưu vào MongoDB collections:
- `real_estate_properties`: Thông tin bất động sản
- `crawl_statistics`: Thống kê crawl

## 🔍 Monitoring
- Logs được ghi trong terminal
- Statistics được lưu trong database
- Error handling với graceful degradation

## 📈 Performance
- Single crawl với CSS + LLM extraction
- Session reuse cho authenticated websites
- Async processing với rate limiting

## 🤝 Đóng Góp
1. Fork repository
2. Tạo feature branch
3. Commit changes
4. Push và tạo Pull Request

## 📄 License
MIT License
