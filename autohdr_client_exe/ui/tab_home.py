import os
import json
import threading
import customtkinter as ctk
from tkinter import filedialog
from core.api_client import ApiClient
from core.cache import cache
import sseclient
from tkinterdnd2 import DND_FILES

class TabHome(ctk.CTkFrame):
    def __init__(self, master, logger_widget, **kwargs):
        super().__init__(master, **kwargs)
        self.logger = logger_widget
        self.api = ApiClient()
        self.selected_files = []
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        
        # --- Section: Init Session ---
        self.session_frame = ctk.CTkFrame(self)
        self.session_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(self.session_frame, text="1. Init Session", font=("Arial", 14, "bold")).pack(anchor="w", pady=5, padx=5)
        
        self.cookie_entry = ctk.CTkEntry(self.session_frame, placeholder_text="Nhập nội dung cookie.txt")
        self.cookie_entry.pack(fill="x", padx=5, pady=5)
        
        btn_frame = ctk.CTkFrame(self.session_frame, fg_color="transparent")
        btn_frame.pack(fill="x", padx=5, pady=5)
        
        ctk.CTkButton(btn_frame, text="Chọn file cookie JSON/TXT", command=self.load_cookie_file).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Khởi tạo (Init)", command=self.init_session).pack(side="left", padx=5)
        
        self.email_label = ctk.CTkLabel(self.session_frame, text="Email: Chưa có", text_color="gray")
        self.email_label.pack(anchor="w", padx=10)
        
        cached_email = cache.get("email", "")
        if cached_email:
            self.email_label.configure(text=f"Email (Cached): {cached_email}", text_color="green")

        # --- Section: Input Mảng & Run ---
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(self.input_frame, text="2. Input Ảnh & Xử Lý", font=("Arial", 14, "bold")).pack(anchor="w", pady=5, padx=5)
        
        # --- DROP ZONE ---
        self.drop_frame = ctk.CTkFrame(self.input_frame, border_width=2, border_color="gray", fg_color=("gray95", "gray15"))
        self.drop_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Make frame clickable to open dialog
        self.drop_frame.bind("<Button-1>", lambda e: self.select_images())
        
        self.drop_label = ctk.CTkLabel(self.drop_frame, text="Kéo thả Ảnh hoặc Thư mục vào đây\n(Hoặc click để chọn tệp)", font=("Arial", 13))
        self.drop_label.pack(expand=True, pady=20)
        self.drop_label.bind("<Button-1>", lambda e: self.select_images()) # Ensure label is also clickable
        
        # Register for Drag and Drop
        self.drop_frame.drop_target_register(DND_FILES)
        self.drop_frame.dnd_bind('<<Drop>>', self.on_drop)
        
        self.img_count_label = ctk.CTkLabel(self.input_frame, text="0 files selected", font=("Arial", 12, "bold"))
        self.img_count_label.pack(anchor="w", padx=15)
        
        # Settings area below drop zone
        settings_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        settings_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(settings_frame, text="Thư mục lưu file:").pack(anchor="w", padx=5)
        
        dir_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        dir_frame.pack(fill="x", padx=5, pady=2)
        
        self.dir_entry = ctk.CTkEntry(dir_frame)
        self.dir_entry.pack(side="left", fill="x", expand=True, padx=(0,5))
        
        cached_dir = cache.get("download_dir", os.path.expanduser("~/Downloads"))
        self.dir_entry.insert(0, cached_dir)
        
        ctk.CTkButton(dir_frame, text="Chọn thư mục", width=100, command=self.select_dir).pack(side="left")
        
        self.address_entry = ctk.CTkEntry(settings_frame, placeholder_text="Nhập địa chỉ (Address)")
        self.address_entry.pack(fill="x", padx=5, pady=5)
        self.address_entry.insert(0, cache.get("address", "Demo Address"))
        
        # --- Action Buttons ---
        actions_frame = ctk.CTkFrame(self.input_frame, fg_color="transparent")
        actions_frame.pack(fill="x", pady=10)
        
        self.btn_process = ctk.CTkButton(actions_frame, text="Bắt đầu xử lý (PROCESS)", command=self.start_process, fg_color="green", height=40)
        self.btn_process.pack(side="left", fill="x", expand=True, padx=5)
        
        self.btn_stop = ctk.CTkButton(actions_frame, text="Dừng tiến trình (STOP)", command=self.stop_process, fg_color="#c0392b", hover_color="#a93226", height=40, state="disabled")
        self.btn_stop.pack(side="left", fill="x", expand=True, padx=5)
        
        self.current_job_id = None
        
    def on_drop(self, event):
        """Handle Drag and Drop event."""
        # Standard way to parse dnd2 data which might contain paths with spaces in curly braces
        import re
        data = event.data
        # Replace curly braced paths with double quoted ones for easier splitting if needed
        # but ctk.CTk.tk.splitlist is usually better
        paths = self.master.tk.splitlist(data)
        
        added_count = 0
        self.selected_files = [] # Optional: Reset current selection or append? 
        # Requirement says "import", usually implies reset or additive. Let's do reset for clarity.
        
        for path in paths:
            added_count += self._process_path(path)
            
        self.img_count_label.configure(text=f"{len(self.selected_files)} files selected")
        self.logger.write_log("INFO", 0, f"Đã nhận {added_count} ảnh qua kéo thả.")

    def _process_path(self, path):
        """Recursively process file or folder path."""
        count = 0
        if os.path.isfile(path):
            ext = os.path.splitext(path)[1].lower()
            if ext in self.allowed_extensions:
                if path not in self.selected_files:
                    self.selected_files.append(path)
                    count += 1
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                for f in files:
                    f_path = os.path.join(root, f)
                    ext = os.path.splitext(f_path)[1].lower()
                    if ext in self.allowed_extensions:
                        if f_path not in self.selected_files:
                            self.selected_files.append(f_path)
                            count += 1
        return count

    def select_images(self):
        """Open file dialog to select multiple images."""
        file_types = [("Image files", "*.jpg *.jpeg *.png *.webp"), ("All files", "*.*")]
        files = filedialog.askopenfilenames(title="Chọn hình ảnh", filetypes=file_types)
        if files:
            self.selected_files = list(files)
            self.img_count_label.configure(text=f"{len(self.selected_files)} files selected")
            self.logger.write_log("INFO", 0, f"Đã chọn {len(files)} files.")

    def load_cookie_file(self):
        file_path = filedialog.askopenfilename(title="Chọn file Session", filetypes=[("JSON/TEXT files", "*.json *.txt"), ("All files", "*.*")])
        if file_path:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read().strip()
                try:
                    data = json.loads(content)
                    
                    # Case 1: JSON has a "cookie" key containing the full string
                    if isinstance(data, dict) and "cookie" in data:
                        content = data["cookie"]
                    
                    # Case 2: JSON is a list of cookie objects [{name:..., value:...}, ...]
                    elif isinstance(data, list):
                        content = "; ".join([f"{c['name']}={c['value']}" for c in data if 'name' in c and 'value' in c])
                    
                    # Case 3: JSON is a dict with a "cookies" key (e.g. site export)
                    elif isinstance(data, dict) and "cookies" in data and isinstance(data["cookies"], list):
                        content = "; ".join([f"{c['name']}={c['value']}" for c in data["cookies"] if 'name' in c and 'value' in c])
                        
                except:
                    # Not a JSON or error, treat as raw text cookie string
                    pass
                
                self.cookie_entry.delete(0, "end")
                self.cookie_entry.insert(0, content)
                self.logger.write_log("INFO", 0, f"Đã tải và chuẩn hóa cookie từ file: {os.path.basename(file_path)}")

    def init_session(self):
        cookie = self.cookie_entry.get().strip()
        email = cache.get("email")
        if not cookie and not email:
            self.logger.write_log("ERROR", 0, "Cần nhập cookie hoặc phải có session cũ (Email).")
            return
            
        self.logger.write_log("INFO", 0, "Đang khởi tạo session...")
        try:
            res = self.api.init_session(cookie=cookie if cookie else None, email=email if not cookie else None)
            new_email = res.get("email")
            self.email_label.configure(text=f"Email: {new_email}", text_color="green")
            cache.set("email", new_email)
            self.logger.write_log("INFO", 0, f"Session OK: {new_email}")
        except Exception as e:
            self.logger.write_log("ERROR", 0, f"Lỗi Init Session: {e}")
            
    def select_dir(self):
        dir_path = filedialog.askdirectory(title="Chọn thư mục tải về")
        if dir_path:
            self.dir_entry.delete(0, "end")
            self.dir_entry.insert(0, dir_path)
            cache.set("download_dir", dir_path)

    def stop_process(self):
        if not self.current_job_id:
            return
        
        self.logger.write_log("WARNING", 0, f"Đang yêu cầu dừng tiến trình {self.current_job_id}...")
        success = self.api.stop_job(self.current_job_id)
        if success:
            self.logger.write_log("INFO", 0, "Lệnh dừng đã được gửi.")
        else:
            self.logger.write_log("ERROR", 0, "Không thể gửi lệnh dừng.")

    def start_process(self):
        if not self.selected_files:
            self.logger.write_log("ERROR", 0, "Chưa chọn ảnh nào!")
            return
            
        key = cache.get("active_key")
        if not key:
            self.logger.write_log("ERROR", 0, "Trống Key kích hoạt! Sang tab Active để kích hoạt trước.")
            return
            
        email = cache.get("email")
        if not email:
            self.logger.write_log("ERROR", 0, "Trống Session/Email! Hãy Init Session trước.")
            return
            
        address = self.address_entry.get().strip()
        if not address:
            self.logger.write_log("ERROR", 0, "Chưa nhập địa chỉ (Address).")
            return
            
        cache.set("address", address)
        download_dir = self.dir_entry.get().strip()
        
        self.btn_process.configure(state="disabled", text="Đang gửi request...")
        self.btn_stop.configure(state="normal")
        self.logger.write_log("INFO", 0, f"Bắt đầu upload {len(self.selected_files)} files...")
        
        threading.Thread(target=self._process_thread, args=(address, key, email, download_dir), daemon=True).start()

    def _process_thread(self, address, key, email, download_dir):
        try:
            job_id = self.api.process_photos(address, self.selected_files, key, email)
            self.current_job_id = job_id
            self.logger.write_log("INFO", 0, f"Job bắt đầu: {job_id}. Đang theo dõi tiến trình...")
            self._stream_logs(job_id, download_dir)
        except Exception as e:
            self.logger.write_log("ERROR", 0, f"Lỗi Process: {e}")
            if hasattr(self, 'master'):
                self.master.after(0, lambda: self._reset_ui())
            
    def _stream_logs(self, job_id, download_dir):
        url = f"{self.api.base_url}/api/stream/{job_id}"
        response = None
        try:
            import requests
            response = requests.get(url, stream=True, headers={'Cache-Control': 'no-cache'})
            client = sseclient.SSEClient(response)
            
            for event in client.events():
                if event.event == 'log':
                    data = json.loads(event.data)
                    line = data.get('line', '')
                    if self.logger:
                        self.master.after(0, lambda l=line: self._append_raw_log(l))
                elif event.event == 'status':
                    data = json.loads(event.data)
                    status = data.get('status')
                    if status == 'completed':
                        results = data.get('results', [])
                        unique_str = data.get('unique_str', 'recent')
                        self.logger.write_log("INFO", 0, f"Xử lý hoàn tất. Download file: {results}")
                        self._download_files(results, download_dir, unique_str)
                        break
                    elif status == 'failed':
                        self.logger.write_log("ERROR", 0, f"Tiến trình dừng: {data.get('error')}")
                        break
        except Exception as e:
            self.logger.write_log("ERROR", 0, f"Mất kết nối SSE stream: {e}")
        finally:
            if response:
                response.close()
            self.master.after(0, lambda: self._reset_ui())

    def _reset_ui(self):
        self.btn_process.configure(state="normal", text="Bắt đầu xử lý (PROCESS)")
        self.btn_stop.configure(state="disabled")
        self.current_job_id = None
            
    def _append_raw_log(self, text):
        self.logger.textbox.configure(state="normal")
        self.logger.textbox.insert("end", text + "\n")
        self.logger.textbox.see("end")
        self.logger.textbox.configure(state="disabled")

    def _download_files(self, results, download_dir, unique_str=""):
        if not results:
            self.logger.write_log("WARNING", 0, "Không có file nào để tải về.")
            return
            
        import urllib.parse
        import datetime
        
        email = cache.get("email", "unknown_email")
        date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        
        target_dir = os.path.join(download_dir, email, date_str, unique_str)
        os.makedirs(target_dir, exist_ok=True)
        
        self.logger.write_log("INFO", 0, f"Bắt đầu tải {len(results)} file trực tiếp về {target_dir}...")
        
        success_count = 0
        for i, url in enumerate(results):
            parsed = urllib.parse.urlparse(url)
            filename = os.path.basename(parsed.path)
            if not filename:
                filename = f"photo_{i:03d}.jpg"
                
            local_path = os.path.join(target_dir, filename)
            self.logger.write_log("INFO", 0, f"Đang tải {filename}...")
            
            success = self.api.download_file_with_retry(url, local_path, max_retries=5)
            if success:
                success_count += 1
            else:
                self.logger.write_log("ERROR", 0, f"Không thể tải file: {url}")
                
        self.logger.write_log("INFO", 0, f"Hoàn tất tải {success_count}/{len(results)} file.")


