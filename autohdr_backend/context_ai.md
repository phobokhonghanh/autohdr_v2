# Context AI - AutoHDR v2 Backend

## Mục đích

Đây là file context giúp AI hiểu được dự án này đang làm gì dựa trên thông tin từ file `v2.md` và `v2.1.md` gốc.

## Tổng quan dự án

AutoHDR v2 Backend là một pipeline tự động hóa quy trình upload, xử lý HDR, và tải ảnh đã xử lý từ AutoHDR API (https://www.autohdr.com). Pipeline gồm 8 bước (Step 0-7), mỗi bước phụ thuộc output của bước trước.

## Flow Pipeline

```
Step 7: Download ảnh → check quota → lưu file → update quota JSON

## v3 Dashboard & API

Phiên bản v3 bổ sung lớp giao diện và API để dễ dàng sử dụng hơn:
- **Backend API (app.py)**: Sử dụng FastAPI để đóng gói pipeline.
    - `POST /api/process`: Nhận files + info, chạy pipeline trong background (BackgroundTasks).
    - `GET /api/status/{job_id}`: Trả về trạng thái, logs, và kết quả (urls) của job.
- **Frontend (autohdr_frontend/)**: Dashboard Vanilla JS với 3 tab:
    1. **Setup**: Form nhập liệu và kéo thả ảnh để upload.
    2. **Logs**: Theo dõi log xử lý thời gian thực từ backend qua polling.
    3. **Results**: Hiển thị danh sách ảnh đã xử lý và cho phép tải xuống.

## Kiến trúc
```

## Kiến trúc

- **config/settings.py**: Load cấu hình từ `.env`, không hardcode
- **core/http_client.py**: Shared HTTP session với headers, cookie, proxy
- **core/logger.py**: Custom format `<LEVEL: STEP: MSG>`
- **core/retry.py**: Retry chung với backoff (dùng ở step5, step7)
- **models/schemas.py**: PipelineContext, QuotaRecord, SessionRecord
- **steps/step0_session.py**: Cookie/session management, quota init, dir pre-creation
- **steps/step1-7_*.py**: 7 file, mỗi file 1 step, có hàm `execute()` là entry point
- **main.py**: Orchestrator chạy Step 0 → Step 7, dừng nếu bất kỳ step fail

## Data & Storage Structure (v3.3)

| Phân loại | Đường dẫn | Mô tả |
|-----------|-----------|-------|
| **System** | `resources/system/` | Chứa files hệ thống dùng chung |
| Sessions | `resources/system/sessions.json` | Lưu cookie + user info |
| Quota | `resources/system/quota.json` | Track download quota theo email |
| **Users** | `resources/users/{email}/` | Thư mục riêng cho mỗi user |
| Input | `resources/users/{email}/input/{uuid}/{address}/` | Ảnh gốc được move vào đây từ temp |
| Logs | `resources/users/{email}/logs/{date}.log` | Log chi tiết (append) cho mỗi lần chạy |
| Temp | `resources/users/{email}/temp/{job_id}/` | Nơi lưu ảnh upload tạm thời từ API |

## Nguồn tham khảo

- File `v2.md` trong thư mục cha: mô tả chi tiết logic từng step 1-7
- File `v2.1.md` trong thư mục cha: mô tả Step 0 cookie management
- Files `step0.py` - `step7.py` trong thư mục cha: request/response mẫu từ API thực

## Lưu ý quan trọng

1. **Không sửa file gốc**: Các file `step0-7.py`, `v2.md`, `v2.1.md` chỉ là reference
2. **Không hardcode**: Mọi giá trị config đều từ `.env`
3. **Session flow**: Cookie → API auth → save session → dùng email cho lần sau
4. **Quota tracking**: Auto-init khi có email mới (count=0, limit_count=0, limit_file=0)
5. **Retry logic**: Step5 (poll status) và Step7 (download) dùng chung module `core/retry.py`
6. **Log format**: Luôn tuân theo `<LEVEL: STEP_NUMBER: MESSAGE>`
7. **Headers**: API calls dùng headers chung, S3 upload (step2) dùng headers riêng
8. **Directories**: Tự động tạo trước khi chạy pipeline (Step 0)
