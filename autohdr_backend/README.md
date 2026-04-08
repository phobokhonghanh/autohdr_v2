# AutoHDR v2 Backend

Automated pipeline for uploading, processing, and downloading HDR images via the AutoHDR API.

## Tổng quan

Tool tự động hóa quy trình 8 bước:

| Step | Mô tả | API Endpoint |
|------|--------|-------------|
| 0 | Quản lý cookie/session (xác thực) | `GET /api/auth/session` |
| 1 | Tạo presigned URLs để upload ảnh lên S3 | `POST /api/proxy/generate_presigned_urls` |
| 2 | Upload binary files lên S3 | `PUT <presigned_url>` |
| 3 | Thông báo hoàn tất upload | `POST /api/proxy/finalize_upload` |
| 4 | Liên kết và chạy xử lý HDR | `POST /api/inference/associate-and-run` |
| 5 | Theo dõi trạng thái xử lý | `GET /api/users/{id}/photoshoots` |
| 6 | Lấy danh sách ảnh đã xử lý | `GET /api/proxy/photoshoots/{id}/processed_photos` |
| 7 | Tải ảnh đã xử lý về máy | Download từ S3 URLs |

## Cài đặt

### 1. Tạo môi trường ảo (venv)

```bash
cd autohdr_backend

# Tạo venv
python3 -m venv venv

# Kích hoạt venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows
```

### 2. Cài đặt dependencies

```bash
pip install -r requirements.txt
```

### 3. Cấu hình môi trường

```bash
# Copy file cấu hình mẫu
cp .env.example .env

# Chỉnh sửa .env với thông tin thực
nano .env
```

**Các biến cần cấu hình (fallback nếu không dùng --cookie):**

| Biến | Mô tả |
|------|--------|
| `AUTOHDR_COOKIE` | Cookie từ browser (fallback nếu không dùng `--cookie`) |
| `AUTOHDR_USER_ID` | User ID trên AutoHDR (auto-detect khi dùng `--cookie`) |
| `AUTOHDR_EMAIL` | Email đăng ký (auto-detect khi dùng `--cookie`) |
| `AUTOHDR_FIRSTNAME` | Tên (auto-detect khi dùng `--cookie`) |
| `AUTOHDR_LASTNAME` | Họ (auto-detect khi dùng `--cookie`) |

## v3 Dashboad (Frontend & API)

Dự án hiện đã có giao diện web để sử dụng dễ dàng hơn.

### 1. Chạy Backend API
```bash
cd autohdr_backend
python app.py
```
API sẽ chạy tại `http://localhost:8000`.

### 2. Chạy Frontend
Bạn có thể mở trực tiếp file `autohdr_frontend/index.html` trong trình duyệt hoặc dùng một web server đơn giản:
```bash
cd autohdr_frontend
# Nếu có cài npm
npx serve .
```

### Các tính năng của Dashboard:
- **Tab 1: Setup**: Nhập Cookie/Email, Địa chỉ và Kéo thả ảnh để upload.
- **Tab 2: Logs**: Theo dõi log xử lý thời gian thực từ backend.
- **Tab 3: Results**: Xem và tải ảnh đã xử lý sau khi hoàn tất.

---

## Sử dụng CLI (v2)
### Chạy pipeline

```bash
# Lần đầu tiên: cung cấp cookie
python main.py --files photo1.jpg photo2.png --address "123 Main St" --cookie "your_cookie_string"

# Các lần sau: chỉ cần email
python main.py --files photo1.jpg photo2.png --address "123 Main St" --email "user@email.com"

# Sử dụng .env (không cần --cookie/--email)
python main.py --files photo1.jpg --address "Test Address" --env .env.prod
```

### Tham số CLI

| Tham số | Bắt buộc | Mô tả |
|---------|----------|--------|
| `--files` | ✅ | Danh sách file ảnh cần upload |
| `--address` | ✅ | Địa chỉ cho photoshoot |
| `--cookie` | ❌ | Cookie xác thực (cần cho lần đầu hoặc khi hết hạn) |
| `--email` | ❌ | Email để tìm session đã lưu |
| `--env` | ❌ | Đường dẫn file .env (mặc định: `.env`) |

## Chạy Tests

```bash
# Chạy tất cả tests
python -m pytest tests/ -v

# Chạy test cho 1 step cụ thể
python -m pytest tests/test_step1.py -v

# Chạy với coverage
python -m pytest tests/ -v --cov=. --cov-report=term-missing
```

## Cấu trúc thư mục

```
autohdr_backend/
├── config/
│   ├── __init__.py
│   └── settings.py          # Cấu hình từ .env
├── core/
│   ├── __init__.py
│   ├── http_client.py       # HTTP session (headers, cookie, proxy)
│   ├── logger.py            # Custom logger <LEVEL: STEP: MSG>
│   └── retry.py             # Retry logic với exponential backoff
├── models/
│   ├── __init__.py
│   └── schemas.py           # Dataclasses (PipelineContext, QuotaRecord, SessionRecord)
├── steps/
│   ├── __init__.py
│   ├── step0_session.py     # Cookie/session management
│   ├── step1_presigned_urls.py
│   ├── step2_upload_files.py
│   ├── step3_finalize_upload.py
│   ├── step4_associate_and_run.py
│   ├── step5_poll_status.py
│   ├── step6_get_processed_urls.py
│   └── step7_download_photos.py
├── tests/
│   ├── conftest.py
│   ├── test_step0.py - test_step7.py
│   ├── test_http_client.py
│   ├── test_logger.py
│   └── test_retry.py
├── .env.example
├── main.py                  # Pipeline orchestrator (CLI)
├── app.py                   # FastAPI backend service (v3)
├── context_ai.md            # AI context document
├── README.md
└── requirements.txt

autohdr_frontend/            # Dashboard files (v3)
├── index.html
├── style.css
└── main.js
```

## Proxy

Nếu cần sử dụng proxy, cấu hình trong `.env`:

```env
AUTOHDR_PROXY_HTTP=http://proxy:8080
AUTOHDR_PROXY_HTTPS=https://proxy:8080
```

## Quota

Download quota được track trong file `quota.json`:

```json
[
  {
    "email": "user@example.com",
    "unique_str": ["uuid-1", "uuid-2"],
    "count": 25,
    "limit_count": 1000,
    "limit_file": 50
  }
]
```

## Quản lý Key (License)

Hệ thống hỗ trợ quản lý Key để giới hạn quyền truy cập cho Desktop Client (EXE). Key được lưu trữ trong file `keys.json`.

### Các câu lệnh quản lý:

Sử dụng script `scripts/manage_keys.py` để quản lý:

```bash
# 1. Tạo Key mới cho một người dùng (mặc định 30 ngày)
python scripts/manage_keys.py add --name "nguyen_vancouver" --days 30

# 2. Tạo Key vĩnh viễn
python scripts/manage_keys.py add --name "admin_pro" --forever

# 3. Liệt kê danh sách các Key hiện có
python scripts/manage_keys.py list
```

### Cách thức hoạt động:
- Khi một Key được sử dụng lần đầu tiên trên một máy tính, nó sẽ tự động bị **khóa (locked)** vào máy đó thông qua `machine_id`.
- Những yêu cầu từ máy tính khác sử dụng cùng một Key sẽ bị từ chối (403 Forbidden).
- File `keys.json` được cấu hình qua biến `AUTOHDR_KEYS_FILE` trong `.env`.

## Log Format

```
<LEVEL: STEP_NUMBER: MESSAGE>
```

- **INFO**: Thông tin từng bước
- **ERROR**: Báo lỗi
- **DEBUG**: Thông tin debug
