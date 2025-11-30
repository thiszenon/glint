import customtkinter as ctk
from glint.core.database import create_db_and_tables
from glint.core.notifier import Notifier
from glint.gui.components.dashboard import Dashboard
from glint.gui.components.terminal import Terminal
from glint.gui.utils.scrolling import ScrollHandler
import os
from PIL import Image, ImageTk

class GlintApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize DB
        create_db_and_tables()
        
        # Window Setup
        self.title("Glint")
        self.geometry("400x600")
        self.minsize(400, 600)
        self.maxsize(1920, 1080)
        self.attributes('-topmost', True)
        
        # Load saved Theme
        from glint.cli.commands import theme
        saved_theme = theme.load_theme_preference()
        ctk.set_appearance_mode(saved_theme)

        # Set Window Icon
        self._setup_icon()
        
        # Layout
        self.grid_rowconfigure(0, weight=1) # Dashboard
        self.grid_rowconfigure(1, weight=0) # Terminal
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Initialize Utilities
        self.scroll_handler = ScrollHandler(self)
        
        # 2. Dashboard Area
        self.dashboard = Dashboard(self, self, self.scroll_handler)
        self.dashboard.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # Register dashboard with scroll handler so it can check active tabs
        self.scroll_handler.set_dashboard(self.dashboard)
        
        # 3. Terminal Area
        self.term_frame = Terminal(self, self)
        self.term_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        # 4. Setup Global Scrolling
        self.scroll_handler.setup_global_handler()
        self.scroll_handler.bind_recursive(self)
        
        # Initialize Notifier
        self.notifier = Notifier(interval_seconds=1800)
        self.notifier.start()
        
        # Handle closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _setup_icon(self):
        try:
            if os.name == 'nt':
                myappid = 'glint.gui.ver1'
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up two levels (from gui/app.py to glint/) then into assets
            # app.py is in src/glint/gui/
            # assets is in src/glint/assets/
            icon_path = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "assets", "logo.png")
            
            # Fix path resolution: __file__ is src/glint/gui/app.py
            # dirname(__file__) -> src/glint/gui
            # dirname(dirname(__file__)) -> src/glint
            # join(..., "assets", "logo.png") -> src/glint/assets/logo.png
            
            # Let's double check the path logic.
            # If current_dir is d:\ALLProgrammes\glint\src\glint\gui
            # os.path.dirname(current_dir) is d:\ALLProgrammes\glint\src\glint
            # So icon_path should be join(..., "assets", "logo.png")
            
            icon_path = os.path.join(os.path.dirname(current_dir), "assets", "logo.png")

            if os.path.exists(icon_path):
                image = Image.open(icon_path)
                self.icon_image = ImageTk.PhotoImage(image)
                self.iconphoto(False, self.icon_image)
                self.wm_iconbitmap()
            else:
                print(f"Warning: Icon not found at {icon_path}")
        except Exception as e:
            print(f"Error setting icon: {e}")

    def on_closing(self):
        if self.notifier:
            self.notifier.stop()
        self.destroy()

    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current_mode = ctk.get_appearance_mode()
        if current_mode == "Light":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")

if __name__ == "__main__":
    app = GlintApp()
    app.mainloop()
