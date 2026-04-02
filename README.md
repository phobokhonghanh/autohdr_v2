# AutoHDR v4

Hệ thống xử lý ảnh HDR tự động với Dashboard theo dõi thời gian thực.

## 🚀 Deployment Guide

Hệ thống được thiết kế để deploy hoàn toàn miễn phí trên **Vercel** (Frontend) và **Railway** (Backend).

### 1. Backend (Railway)

Railway được chọn vì hỗ trợ SSE (Server-Sent Events) ổn định nhờ cơ chế heartbeat :keepalive.

> [!IMPORTANT]
> **BẮT BUỘC**: Bạn phải chỉnh **Root Directory** thành `/autohdr_backend` trong cài đặt của Railway, nếu không build sẽ lỗi.

1.  **Connect**: Truy cập [Railway.app](https://railway.app), tạo project mới và kết nối với repository GitHub của bạn (`phobokhonghanh/autohdr_v2`).
2.  **Cấu hình Root Directory (Làm ngay sau khi connect)**: 
    *   Vào service vừa tạo -> **Settings** -> **General**.
    *   Tìm mục **Root Directory** và điền: `/autohdr_backend`.
    *   Nhấn **Save**. Railway sẽ tự động trigger lại một bản build mới đúng chuẩn.
3.  **Environment Variables**: Thêm các biến sau vào tab **Variables**:
    *   `PORT`: `8000`
    *   `AUTOHDR_RESOURCES_DIR`: `/app/resources`
    *   Copy toàn bộ các biến từ file `.env` cục bộ.
4.  **Volumes (Quan trọng)**: 
    *   Vào tab **Settings** -> **Volumes** -> **Add Volume**.
    *   Mount Path: `/app/resources`.
5.  **Networking**: Railway sẽ cấp domain public trong mục **Public Networking**.

#### 💡 Khắc phục lỗi "Railpack could not determine how to build the app"
Nếu bạn gặp lỗi này, nghĩa là Railway đang cố build từ thư mục gốc (root) của repo. Hãy thực hiện Bước 2 ở trên để chỉ định Railway build trong thư mục `/autohdr_backend`.

### 2. Frontend (Vercel)

1. **Connect**: Kết nối project Vercel với repository GitHub.
2. **Root Directory**: Chọn thư mục `/autohdr_frontend`.
3. **Framework Preset**: Chọn `Vite` (hoặc `Other` nếu không tự nhận diện).
4. **Environment Variables**:
   - `VITE_API_BASE`: Link public từ Railway (ví dụ: `https://autohdr-backend.up.railway.app`).
5. **GitHub Secrets**: Để CI/CD hoạt động, thêm các biến sau vào GitHub repo Settings -> Secrets and variables -> Actions:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

---

## 📊 Google Analytics

Hệ thống đã tích hợp sẵn GA4. Để kích hoạt:
1. Mở file `autohdr_frontend/index.html`.
2. Thay thế `G-XXXXXXXXXX` bằng **Measurement ID** thực tế của bạn.

## 🛠️ Phát triển cục bộ

### Backend
```bash
cd autohdr_backend
pip install -r requirements.txt
python app.py
```

### Frontend
```bash
cd autohdr_frontend
npm install
npm run dev
```
