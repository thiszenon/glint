import re
import customtkinter as ctk
from glint.core.database import get_engine, create_db_and_tables
from glint.core.models import Trend, Topic
from glint.core.notifier import Notifier
from sqlmodel import Session, select, func
import sys
import io
from contextlib import redirect_stdout
from glint.cli.commands import topics, status, fetch
import os
import tkinter
from PIL import Image, ImageTk

class GlintApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # Initialize DB
        create_db_and_tables()
        
        # Window Setup
        self.title("Glint")
        self.geometry("400x600")
        self.attributes('-topmost', True)  # Pin to top
        self.attributes('-topmost', True)  # Pin to top
        ctk.set_appearance_mode("Dark")

        # Set Window Icon
        try:
            # Fix for Windows Taskbar Icon
            # Windows groups windows by process (python.exe). We need a unique AppUserModelID
            # so the taskbar treats this as a separate application with its own icon.
            if os.name == 'nt':
                myappid = 'glint.gui.ver1' # arbitrary string
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

            # Get absolute path to assets/logo.png
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up one level to glint package, then into assets
            icon_path = os.path.join(os.path.dirname(current_dir), "assets", "logo.png")
            
            if os.path.exists(icon_path):
                # Use Pillow to load the image
                image = Image.open(icon_path)
                self.icon_image = ImageTk.PhotoImage(image) # Keep reference to prevent GC
                self.iconphoto(False, self.icon_image)
                self.wm_iconbitmap() # Try to clear any default bitmap
            else:
                print(f"Warning: Icon not found at {icon_path}")
        except Exception as e:
            print(f"Error setting icon: {e}")
        
        # Layout
        self.grid_rowconfigure(0, weight=1) # Notifications
        self.grid_rowconfigure(1, weight=0) # Terminal
        self.grid_columnconfigure(0, weight=1)
        
        # 1. Notifications Area
        self.notif_frame = ctk.CTkScrollableFrame(self, label_text="Latest Trends")
        self.notif_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        
        # 2. Terminal Area
        self.term_frame = ctk.CTkFrame(self)
        self.term_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=5)
        
        self.output = ctk.CTkTextbox(self.term_frame, height=150, font=("Consolas", 12))
        self.output.pack(fill="x", padx=5, pady=5)
        
        self.welcome_message = "Glint v0.1.0 producted by xipher .\nType 'help' for commands.\n"
        self.output.insert("0.0", self.welcome_message + "> ")
        self.output.configure(state="disabled")
        
        self.input = ctk.CTkEntry(self.term_frame, placeholder_text="Enter command...", font=("Consolas", 12))
        self.input.pack(fill="x", padx=5, pady=5)
        self.input.bind("<Return>", self.process_command)
        
        # Initialize Notifier
        self.notifier = Notifier(interval_seconds=60) # Check every minute
        self.notifier.start()
        
        # State for auto-refresh
        self.last_trend_count = -1
        
        # Load initial data and start auto-refresh
        self.refresh_notifications()
        self.after(5000, self.auto_refresh_loop) # Check for updates every 5 seconds
        
        # Handle closing
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def log(self, message):
        self.output.configure(state="normal")
        self.output.insert("end", f"{message}\n")
        self.output.see("end")
        self.output.configure(state="disabled")

    def strip_ansi(self, text):
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)

    def process_command(self, event):
        cmd_text = self.input.get().strip()
        self.input.delete(0, "end")
        
        if not cmd_text:
            return
        # command to clear the terminal
        if cmd_text.lower() == "clear":
            self.output.configure(state="normal")
            self.output.delete("1.0", "end")
            self.output.insert("0.0", self.welcome_message)
            self.output.configure(state="disabled")
            return

        self.log(f"> {cmd_text}")
        
        parts = cmd_text.split()
        command = parts[0].lower()
        args = parts[1:]
        
        # Capture stdout to redirect to GUI terminal
        f = io.StringIO()
        with redirect_stdout(f):
            try:
                if command == "add":
                    if args:
                        topics.add(args[0])
                    else:
                        print("Usage: add <topic>")
                elif command == "list":
                    topics.list_topics()
                elif command == "status":
                    status.status()
                elif command == "fetch":
                    fetch.fetch()
                    self.refresh_notifications()
                elif command == "help":
                    print("Available commands: add, list, status, fetch, help")
                else:
                    print(f"Unknown command: {command}")
            except Exception as e:
                print(f"Error: {e}")
        
        output_str = f.getvalue()
        if output_str:
            clean_output = self.strip_ansi(output_str.strip())
            self.log(clean_output)
            
    def refresh_notifications(self):
        # Clear existing
        for widget in self.notif_frame.winfo_children():
            widget.destroy()
            
        try:
            engine = get_engine()
            with Session(engine) as session:
                trends = session.exec(select(Trend).order_by(Trend.published_at.desc()).limit(20)).all()
                
                # Update count
                self.last_trend_count = len(trends)
                
                if not trends:
                    lbl = ctk.CTkLabel(self.notif_frame, text="No trends yet.\nRun 'fetch' to get updates.")
                    lbl.pack(pady=20)
                    return
                
                for trend in trends:
                    card = ctk.CTkFrame(self.notif_frame)
                    card.pack(fill="x", pady=2, padx=2)
                    
                    title_text = f"[{trend.category.upper()}] {trend.title}"
                    title = ctk.CTkLabel(card, text=title_text, anchor="w", font=("Roboto", 12, "bold"))
                    title.pack(fill="x", padx=5, pady=(5,0))
                    
                    meta = ctk.CTkLabel(card, text=f"{trend.source} • {trend.published_at.strftime('%H:%M')}", 
                                      anchor="w", font=("Roboto", 10), text_color="gray")
                    meta.pack(fill="x", padx=5, pady=(0,5))
                    
        except Exception as e:
            self.log(f"Error loading trends: {e}")

    def auto_refresh_loop(self):
        try:
            engine = get_engine()
            with Session(engine) as session:
                # Check total count of trends
                count = session.exec(select(func.count(Trend.id))).one()
                
                # If count changed (or we haven't loaded yet), refresh
                # Note: This is a simple check. Ideally we'd check for latest timestamp.
                if count != self.last_trend_count:
                    self.refresh_notifications()
                    self.last_trend_count = count
        except Exception as e:
            print(f"Auto-refresh error: {e}")
            
        self.after(5000, self.auto_refresh_loop)

    def on_closing(self):
        if self.notifier:
            self.notifier.stop()
        self.destroy()

if __name__ == "__main__":
    app = GlintApp()
    app.mainloop()
