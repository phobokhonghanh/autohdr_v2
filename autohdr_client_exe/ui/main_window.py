import customtkinter as ctk
from tkinterdnd2 import TkinterDnD
from .tab_home import TabHome
from .tab_active import TabActive
from .tab_result import TabResult
from .widget_logger import LoggerWidget

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize Drag and Drop extension
        self.TkdndVersion = TkinterDnD._require(self)

        self.title("AutoHDR - Desktop Client (v5)")
        self.geometry("900x600")
        
        # Grid layout (2 columns)
        self.grid_columnconfigure(0, weight=1) # Left side (Tabs)
        self.grid_columnconfigure(1, weight=1) # Right side (Logs)
        self.grid_rowconfigure(0, weight=1)
        
        # Logger side
        self.logger_widget = LoggerWidget(self)
        self.logger_widget.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        
        # Tabs side
        self.tab_container = ctk.CTkTabview(self)
        self.tab_container.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        self.tab_container.add("Home")
        self.tab_container.add("Active")
        self.tab_container.add("Result")
        
        # Initialize tabs content
        self.tab_home = TabHome(self.tab_container.tab("Home"), self.logger_widget)
        self.tab_home.pack(expand=True, fill="both")
        
        self.tab_active = TabActive(self.tab_container.tab("Active"), self.logger_widget)
        self.tab_active.pack(expand=True, fill="both")
        
        self.tab_result = TabResult(self.tab_container.tab("Result"), self.logger_widget)
        self.tab_result.pack(expand=True, fill="both")
        
        # Default start log
        self.logger_widget.write_log("INFO", 0, "Application started...")
