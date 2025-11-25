import webbrowser
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
        ctk.set_appearance_mode("Light")

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
        
        """# 1. Notifications Area
        self.notif_frame = ctk.CTkScrollableFrame(self, label_text="Latest Trends")
        self.notif_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=5)
        """
        # 1. Creaate a table TabView
        self.dashboard =  ctk.CTkTabview(self)
        self.dashboard.grid(row=0, column=0,sticky= "nsew", padx=10, pady=5)

        # Add tabs on dashboard
        self.dashboard.add("Tools")
        self.dashboard.add("News")
        self.dashboard.add("Current Project")

        #3. Create a scrollable frame for each tab
        self.news_frame = ctk.CTkScrollableFrame(self.dashboard.tab("News"), label_text="News")
        self.news_frame.pack(fill="both", expand=True)

        self.tools_frame = ctk.CTkScrollableFrame(self.dashboard.tab("Tools"), label_text="Tools")
        self.tools_frame.pack(fill="both", expand=True)

        self.project_frame = ctk.CTkScrollableFrame(self.dashboard.tab("Current Project"), label_text="Current Project")
        self.project_frame.pack(fill="both", expand=True)

        
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

    def populate_frame(self,frame,data):
        #clear existing widgets in the specific frame
        for widget in frame.winfo_children():
            widget.destroy()
        
        if not data:
            lbl = ctk.CTkLabel(frame, text="No trends found")
            lbl.pack(pady=20)
            return
        
        for trend, topic_name in data:
            #CARD CONTAINER
            # fg_color 
            card = ctk.CTkFrame(frame,fg_color=("gray90", "gray13"))
            card.pack(fill="x", padx=2, pady=4) # pour plus de space entre les cards

            # 1. TITLE
            title_text = f"[{trend.category.upper()}] {trend.title}"
            title = ctk.CTkLabel(card, text=title_text, anchor="w", font=("Roboto",12,"bold"))
            title.pack(fill="x", padx=10, pady=(10,2))

            #2. DESCRIPTION
            #TODO: tronqué la description si elle depasse
            desc_text = trend.description if trend.description else "No description available"
            if len(desc_text) > 100:
                desc_text = desc_text[:100] + '...'
            desc = ctk.CTkLabel(card, text=desc_text, anchor="w", justify="left", wraplength=300, font=("Roboto",11), text_color=("gray30", "gray70"))
            desc.pack(fill="x", padx=10, pady=(0,5))

            #3. META-INFORMATIONS and Badge information
            meta_frame  = ctk.CTkFrame(card, fg_color="transparent")
            meta_frame.pack(fill="x", padx=10, pady=(0,10))

            # Date 
            date_str = trend.published_at.strftime("%Y-%m-%d %H:%M")
            meta =ctk.CTkLabel(meta_frame, text= f"{trend.source} . {date_str}",font=("Roboto",10), text_color="gray")
            meta.pack(side="left")

            #Right: Container for badge and link
            right_box = ctk.CTkFrame(meta_frame, fg_color="transparent")
            right_box.pack(side="right")

            #Badge (Only if topic_name exists)
            if topic_name : 
                badge = ctk.CTkLabel(right_box, text=topic_name,fg_color="#3B8ED0",text_color="white",font=("Roboto",9,"bold"), corner_radius=6)
                badge.pack(side="top", anchor="e", pady=(0,2))


            #TODO: add a link to the trend
            link = ctk.CTkLabel(right_box, text="See more",font=("Roboto",10,"bold"), text_color=("blue", "#4da6ff"), cursor="hand2")
            link.pack(side="top", anchor="e")
            link.bind("<Button-1>", lambda e, u = trend.url: webbrowser.open(u))

        #end for
    #end populate_frame

    def refresh_notifications(self):
        try:
            engine= get_engine()
            with Session(engine) as session:
                #1.Fetch News
                query_news =select(Trend,Topic.name).join(Topic,isouter=True).where(Trend.category == "news").order_by(Trend.published_at.desc()).limit(10)
                news_trends = session.exec(query_news).all()
                self.populate_frame(self.news_frame,news_trends)

                #2.Fetch Repos
                query_repos = select(Trend,Topic.name).join(Topic,isouter=True).where(Trend.category.in_(["tool","repo"])).order_by(Trend.published_at.desc()).limit(10)
                repos_trends = session.exec(query_repos).all()
                self.populate_frame(self.tools_frame,repos_trends)

                #Update total count for auto-refresh logic
                self.last_trend_count = len(news_trends) + len(repos_trends)
        except Exception as ex:
            print(f"Error refreshing notifications: {ex}")
        
                
                      

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
