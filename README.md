# AutoHDR v4

Hệ thống xử lý ảnh HDR tự động với Dashboard theo dõi thời gian thực.

## 🚀 Deployment Guide

Hệ thống được thiết kế để deploy hoàn toàn miễn phí trên **Vercel** (Frontend) và **Railway** (Backend).

### 1. Backend (Railway)

Railway được chọn vì hỗ trợ SSE (Server-Sent Events) ổn định với cơ chế keepalive.

1. **Connect**: Kết nối dịch vụ Railway với repository GitHub của bạn.
2. **Root Directory**: Chọn thư mục `/autohdr_backend`.
3. **Environment**: Copy các biến từ file `.env` cục bộ vào Railway Dashboard.
4. **Auto-deploy**: Mỗi khi push lên nhánh `main`, Railway sẽ tự động build và deploy dựa trên `railway.toml`.

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
