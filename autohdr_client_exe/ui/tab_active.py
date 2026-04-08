import customtkinter as ctk
from core.api_client import ApiClient
from core.cache import cache
from core.utils import get_hwid

class TabActive(ctk.CTkFrame):
    def __init__(self, master, logger_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.logger = logger_widget
        self.api = ApiClient()
        self.hwid = get_hwid()
        
        self.label = ctk.CTkLabel(self, text="Kích hoạt Key", font=("Arial", 16, "bold"))
        self.label.pack(pady=10)
        
        # Display Machine ID (HWID)
        hwid_frame = ctk.CTkFrame(self, fg_color="transparent")
        hwid_frame.pack(pady=5)
        ctk.CTkLabel(hwid_frame, text="Mã máy (Machine ID):", font=("Arial", 12)).pack(side="left", padx=5)
        self.hwid_display = ctk.CTkEntry(hwid_frame, width=150, font=("Arial", 11))
        self.hwid_display.insert(0, self.hwid)
        self.hwid_display.configure(state="readonly")
        self.hwid_display.pack(side="left", padx=5)
        
        self.key_entry = ctk.CTkEntry(self, placeholder_text="Nhập API Key của bạn", width=300)
        self.key_entry.pack(pady=10)
        
        # Load cached key
        cached_key = cache.get("active_key", "")
        if cached_key:
            self.key_entry.insert(0, cached_key)
            
        self.check_btn = ctk.CTkButton(self, text="Kích hoạt (Check & Active)", command=self.check_key, fg_color="blue", height=35)
        self.check_btn.pack(pady=10)
        
        self.status_label = ctk.CTkLabel(self, text="", text_color="gray")
        self.status_label.pack(pady=5)
        
    def check_key(self):
        key = self.key_entry.get().strip()
        if not key:
            self.status_label.configure(text="Vui lòng nhập Key", text_color="red")
            return
            
        self.logger.write_log("INFO", 0, f"Đang kiểm tra Key: {key[:4]}*** trên máy {self.hwid}")
        self.status_label.configure(text="Đang kết nối server...", text_color="blue")
        self.update()
        
        try:
            # Pass hwid for machine locking
            is_valid = self.api.check_key(key, self.hwid)
            if is_valid:
                self.status_label.configure(text="Kích hoạt thành công!", text_color="green")
                self.logger.write_log("INFO", 0, "Key hợp lệ và đã khóa vào máy này.")
                cache.set("active_key", key)
            else:
                self.status_label.configure(text="Key không hợp lệ, hết hạn hoặc đã dùng trên máy khác", text_color="red")
                self.logger.write_log("ERROR", 0, "Kích hoạt thất bại: Key không hợp lệ hoặc sai mã máy.")
        except Exception as e:
            self.status_label.configure(text=f"Lỗi: {str(e)}", text_color="red")
            self.logger.write_log("ERROR", 0, f"Lỗi gọi API: {e}")
