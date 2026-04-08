# Hướng dẫn Build EXE cho AutoHDR Client

Tài liệu này hướng dẫn cách đóng gói ứng dụng AutoHDR Desktop Client thành một tệp thực thi duy nhất (.exe trên Windows, hoặc binary trên Linux/macOS) sử dụng **PyInstaller**.

## 1. Yêu cầu hệ thống

- Python 3.10 trở lên.
- Đã cài đặt các phụ thuộc trong `requirements.txt`.

## 2. Chuẩn bị môi trường

Khuyến khích sử dụng môi trường ảo (venv) để tránh xung đột thư viện.

```bash
# Di chuyển vào thư mục client
cd autohdr_client_exe

# Tạo venv (nếu chưa có)
python -m venv venv

# Kích hoạt venv
source venv/bin/activate      # Linux/macOS
# venv\Scripts\activate       # Windows
```

Cài đặt các thư viện cần thiết:

```bash
pip install -r requirements.txt
pip install pyinstaller
```

## 3. Build ứng dụng

Dự án đã có sẵn tệp cấu hình `main.spec` để xử lý các thư viện đặc biệt như `tkinterdnd2`. Bạn chỉ cần chạy lệnh sau:

```bash
pyinstaller main.spec --clean
```

### Các tham số quan trọng:
- `--clean`: Xóa các thư mục tạm từ lần build trước.
- Tệp `main.spec` đã được cấu hình để:
    - Chạy ở chế độ **Windowed** (không hiện cửa sổ console đen).
    - Tự động thu thập thư viện `tkinterdnd2`.
    - Đóng gói thành **một tệp duy nhất** (One File).

## 4. Kết quả build

Sau khi lệnh chạy xong, bạn sẽ thấy các thư mục mới:
- `dist/`: Chứa tệp thực thi cuối cùng (`main.exe` trên Windows, hoặc `main` trên Linux).
- `build/`: Các tệp tạm của quá trình build (có thể xóa sau khi hoàn tất).

**Lưu ý cho Linux:** Nếu bạn build trên Linux, bạn cần cấp quyền thực thi cho file binary trước khi chạy:
```bash
chmod +x dist/main
./dist/main
```

## 5. Trình tự ưu tiên của Biến môi trường (.env)

Ứng dụng được cấu hình để tìm file `.env` theo thứ tự sau:

1.  **Mặc định (Bundled)**: Tệp `.env` hiện tại đã được đóng gói trực tiếp vào trong file `.exe`. Khi bạn gửi file `.exe` cho người khác, họ sẽ tự động sử dụng cấu hình này (ví dụ: trỏ về server Railway) mà không cần file đi kèm.
2.  **Ghi đè (External Override)**: Nếu bạn muốn thay đổi cấu hình mà không muốn build lại code, bạn chỉ cần tạo một file `.env` mới và đặt nó **nằm cùng thư mục** với file `.exe`. Ứng dụng sẽ ưu tiên đọc file bên ngoài này để ghi đè lên cấu hình mặc định bên trong.

Điều này giúp ứng dụng vừa có tính "mì ăn liền" khi gửi cho người dùng cuối, vừa giữ được tính linh hoạt cho người quản trị.

---
**Lưu ý:** Để có file `.exe` cho Windows, bạn phải thực hiện quá trình build này trên máy chạy Windows. Tương tự cho Linux và macOS.
