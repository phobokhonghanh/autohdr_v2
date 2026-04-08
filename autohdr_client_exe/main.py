import customtkinter as ctk
import sys
import os
from dotenv import load_dotenv

# 1. Load bundled .env (if running as PyInstaller EXE)
if getattr(sys, 'frozen', False):
    bundled_env = os.path.join(sys._MEIPASS, '.env')
    if os.path.exists(bundled_env):
        load_dotenv(bundled_env)

# 2. Load external .env (next to EXE or in CWD) - allows user overrides
external_env = os.path.join(os.getcwd(), '.env')
load_dotenv(external_env, override=True)

# Add parent directory to path so it can be run standalone easily if needed
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from ui.main_window import MainWindow

def main():
    ctk.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
    ctk.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"
    
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
