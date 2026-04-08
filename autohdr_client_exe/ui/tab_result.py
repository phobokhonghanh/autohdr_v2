import customtkinter as ctk
import os
from core.cache import cache

class TabResult(ctk.CTkFrame):
    def __init__(self, master, logger_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.logger = logger_widget
        
        self.label = ctk.CTkLabel(self, text="Kết Quả", font=("Arial", 16, "bold"))
        self.label.pack(pady=10)
        
        info = "Kết quả đã được tự động xử lý và lưu tại thư mục mà bạn đã chọn ở Tab Home."
        ctk.CTkLabel(self, text=info, wraplength=400).pack(pady=10, padx=20)
        
        self.btn_open = ctk.CTkButton(self, text="Mở thư mục lưu trữ", command=self.open_dir)
        self.btn_open.pack(pady=20)
        
    def open_dir(self):
        download_dir = cache.get("download_dir")
        if download_dir and os.path.exists(download_dir):
            try:
                # Works on windows/mac/linux
                os.startfile(download_dir) if hasattr(os, 'startfile') else os.system(f"xdg-open '{download_dir}'" if os.name == 'posix' else f"open '{download_dir}'")
            except Exception as e:
                self.logger.write_log("ERROR", 0, f"Lỗi mở thư mục: {e}")
        else:
            self.logger.write_log("WARNING", 0, "Chưa chọn thư mục lưu trữ hoặc thư mục không tồn tại.")
