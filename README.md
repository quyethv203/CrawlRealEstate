# Real Estate Crawler

## Giới thiệu

**Real Estate Crawler** là hệ thống thu thập dữ liệu bất động sản tự động, đa nguồn, được thiết kế để phục vụ các nhu cầu phân tích, tổng hợp, và quản lý dữ liệu bất động sản tại Việt Nam. Dự án hỗ trợ crawl dữ liệu từ nhiều website lớn, lưu trữ tập trung vào MongoDB, cung cấp API quản lý, thống kê, và lên lịch crawl linh hoạt. Hệ thống được xây dựng với kiến trúc mở rộng, dễ bảo trì, và tích hợp logging chuyên nghiệp.

---

## Tính năng nổi bật

- **Crawl đa nguồn:** Tự động thu thập dữ liệu từ các website bất động sản phổ biến như batdongsan.com.vn, nhatot.com, muaban.net, bds123.vn, mogi.vn, sosanhnha.com,...
- **Lưu trữ tập trung:** Dữ liệu được lưu vào MongoDB với các model chuẩn hóa, hỗ trợ truy vấn và thống kê hiệu quả.
- **API quản lý:** Cung cấp các endpoint RESTful để quản lý trạng thái website, lên lịch crawl, kiểm tra tiến trình, và thống kê dữ liệu.
- **Lên lịch thông minh:** Hỗ trợ lên lịch crawl theo mốc giờ cố định (2h, 14h hoặc chỉ 2h sáng), sử dụng APScheduler, đảm bảo crawl đều đặn và tối ưu tài nguyên.
- **Quản lý tiến trình:** Sử dụng subprocess để chạy các crawler riêng biệt, đảm bảo tính độc lập và khả năng mở rộng.
- **Logging chuyên nghiệp:** Tích hợp Loguru, ghi log chi tiết ra file `crawler.log` (xoay vòng, nén, giữ lịch sử), hỗ trợ debug và giám sát hệ thống.
- **Kiến trúc mở rộng:** Dễ dàng thêm mới crawler cho website khác, mở rộng API hoặc tích hợp các service xử lý dữ liệu nâng cao.

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

### Theo dõi log

- Log hệ thống được ghi vào file `crawler.log` (xoay vòng, nén tự động).
- Có thể theo dõi log để kiểm tra tiến trình crawl, lỗi, và các cảnh báo.

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

**Real Estate Crawler** – Giải pháp tự động hóa thu thập dữ liệu bất động sản, phục vụ phân tích và phát triển sản phẩm số!
