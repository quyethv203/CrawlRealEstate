# Real Estate Crawler

## Giới thiệu

**Real Estate Crawler** là hệ thống tự động thu thập dữ liệu bất động sản đa nguồn, hỗ trợ lưu trữ, quản lý, giám sát và phân tích dữ liệu. Dự án phù hợp cho các tổ chức, doanh nghiệp hoặc cá nhân cần xây dựng kho dữ liệu bất động sản phục vụ phân tích, báo cáo, hoặc phát triển sản phẩm số.

---

## Tính năng nổi bật

- **Crawl đa nguồn:** Tự động thu thập dữ liệu từ các website bất động sản lớn tại Việt Nam.
- **Lưu trữ tập trung:** Dữ liệu được chuẩn hóa và lưu vào MongoDB.
- **API quản lý:** RESTful API cho quản lý trạng thái website, lên lịch crawl, thống kê, và truy vấn dữ liệu.
- **Lên lịch thông minh:** Tích hợp APScheduler, hỗ trợ crawl theo mốc giờ cố định hoặc tuỳ chỉnh.
- **Quản lý tiến trình:** Sử dụng subprocess để chạy crawler riêng biệt, đảm bảo tính ổn định và mở rộng.
- **Logging chuyên nghiệp:** Tích hợp Loguru, ghi log chi tiết ra file `crawler.log` (xoay vòng, nén, retention).
- **Giám sát & Monitoring:**  
  - Log hệ thống chi tiết giúp theo dõi tiến trình crawl, lỗi, cảnh báo.
  - Có thể tích hợp với các công cụ giám sát như Grafana, Prometheus, hoặc ELK Stack thông qua log file hoặc custom exporter.
  - Endpoint API cung cấp thông tin trạng thái, lịch sử crawl, thống kê nguồn dữ liệu.
- **Hiệu năng & Khả năng mở rộng:**  
  - Thiết kế module hóa, dễ dàng mở rộng crawler cho website mới.
  - Hỗ trợ chạy song song nhiều tiến trình crawl.
  - Có thể triển khai trên server vật lý, cloud hoặc container.

---

## Yêu cầu hệ thống

- Python >= 3.9
- MongoDB server
- Các package Python: loguru, fastapi, apscheduler, pymongo, uvicorn, v.v.

---

## Hướng dẫn cài đặt

### 1. Clone mã nguồn

```bash
git clone https://github.com/yourusername/real_estate_crawler.git
cd real_estate_crawler
```

### 2. Cài đặt package

```bash
pip install -r requirements.txt
```

### 3. Cấu hình hệ thống

- Sửa file `src/config/settings.py` để cấu hình thông tin MongoDB, đường dẫn file log, các thông số crawl, v.v.
- Đảm bảo biến môi trường hoặc file cấu hình phù hợp với môi trường triển khai.

### 4. Khởi tạo logging

- Đảm bảo gọi `setup_logging()` ở đầu chương trình (thường trong `main.py`):

```python
from src.utils.logging import setup_logging
setup_logging()
```

---

## Hướng dẫn sử dụng

### Chạy hệ thống

```bash
python main.py
```

### Sử dụng API

- Truy cập các endpoint qua FastAPI (mặc định chạy trên `localhost:8000`):

  - `POST /schedule_crawl`: Lên lịch crawl tự động.
  - `GET /websites`: Xem danh sách website và trạng thái crawl.
  - `GET /current_schedule`: Kiểm tra lịch crawl hiện tại.
  - `GET /stats`: Thống kê dữ liệu theo nguồn.

- Ví dụ lên lịch crawl:
  ```bash
  curl -X POST "http://localhost:8000/schedule_crawl?interval_hours=12"
  ```

### Theo dõi & Giám sát hệ thống

- **Log hệ thống:**  
  - Kiểm tra file `crawler.log` để theo dõi tiến trình crawl, lỗi, cảnh báo.
  - Có thể tích hợp log vào các hệ thống giám sát như ELK Stack, Grafana Loki, hoặc gửi alert qua email/Slack.
- **API monitoring:**  
  - Sử dụng các endpoint API để kiểm tra trạng thái hệ thống, lịch sử crawl, thống kê nguồn dữ liệu.
- **Performance:**  
  - Theo dõi số lượng bản ghi, thời gian crawl, trạng thái tiến trình qua log và API.
  - Có thể mở rộng thêm exporter Prometheus hoặc custom metrics nếu cần.

---

## Cấu trúc thư mục

```
src/
  api/                # API quản lý, lên lịch, thống kê
  crawlers/           # Các crawler cho từng website
    base/             # Base class, observer, interface
  data/
    database/         # Kết nối, thao tác MongoDB
    models/           # Định nghĩa model dữ liệu
  services/           # Xử lý dữ liệu, tích hợp LLM
  utils/              # Logging, cấu hình, tiện ích
main.py               # Điểm khởi động hệ thống
requirements.txt      # Danh sách package cần thiết
README.md             # Tài liệu dự án
```

---

## Mở rộng & đóng góp

- Dễ dàng thêm crawler mới bằng cách kế thừa `BaseCrawler`.
- Đóng góp code, báo lỗi hoặc đề xuất tính năng qua [GitHub Issues](https://github.com/yourusername/real_estate_crawler/issues).
- Pull request luôn được chào đón!

---

## License

MIT License.  
Vui lòng tham khảo file `LICENSE` để biết chi tiết.

---

## Liên hệ

- Email: your.email@example.com
- Github: [yourusername](https://github.com/yourusername)

---

**Real Estate Crawler** – Giải pháp tự động hóa thu thập, quản lý và giám sát dữ liệu bất động sản!
