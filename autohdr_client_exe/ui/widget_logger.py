import customtkinter as ctk
import datetime

class LoggerWidget(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.label = ctk.CTkLabel(self, text="Logs Hệ Thống", font=("Arial", 14, "bold"))
        self.label.pack(pady=5, padx=10, anchor="w")
        
        self.textbox = ctk.CTkTextbox(self, font=("Consolas", 12))
        self.textbox.pack(expand=True, fill="both", padx=10, pady=(0, 10))
        self.textbox.configure(state="disabled")
        
    def write_log(self, level: str, step: int, msg: str):
        now = datetime.datetime.now().strftime("%H:%M:%S")
        log_line = f"[{now}] <{level}: {step}: {msg}>\n"
        
        self.textbox.configure(state="normal")
        self.textbox.insert("end", log_line)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")
