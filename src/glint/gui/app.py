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
from glint.cli.commands import topics, status, fetch, theme
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
        self.minsize(400, 600)  # Set minimum window size (can't go smaller)
        self.maxsize(1920, 1080)  # Set maximum window size (can't go larger)
        self.attributes('-topmost', True)  # Pin to top
        #load saved Theme
        from glint.cli.commands import theme
        saved_theme = theme.load_theme_preference()
        ctk.set_appearance_mode(saved_theme)

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

        #3. Create scrollable frames for each tab
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

        #history of commands
        self.command_history = [] #store all commands
        self.history_index = -1 #current index of history
        self.input.bind("<Up>", self.history_up)
        self.input.bind("<Down>", self.history_down)
        
        # Initialize Notifier
        self.notifier = Notifier(interval_seconds=1800) # Check every 30 minutes
        self.notifier.start()
        
        # State for auto-refresh
        self.last_trend_count = -1
        
        # Pagination state
        self.news_page = 1
        self.tools_page = 1
        self.items_per_page = 20  # Show 20 items at a time
        self.news_has_more = True
        self.tools_has_more = True
        
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
        self.command_history.append(cmd_text)
        self.history_index = -1

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
                        self.refresh_notifications()  # Refresh to show new topic
                    else:
                        print("Usage: add <topic>")
                        
                elif command == "list":
                    topics.list_topics()
                    
                elif command == "status":
                    status.status()
                    
                elif command == "fetch":
                    fetch.fetch()
                    self.refresh_notifications()
                elif command == "theme":
                    if args:
                        if args[0].lower() in ["dark", "light"]:
                            mode = args[0]
                            theme.save_theme_preference(mode)
                            ctk.set_appearance_mode(mode)
                            print(f"Theme set to {mode} mode")
                        elif args[0] == "show":
                            current = theme.load_theme_preference()
                            print(f"Current theme: {current}")
                        else:
                            print("Usage: theme <dark|light|show>")
                    else:
                        # Toggle if no args
                        self.toggle_theme()

                    
                    
                    
                elif command == "config":
                    self._handle_config_command(args)
                    
                elif command == "help":
                    self._show_help()
                    
                else:
                    print(f"Unknown command: {command}")
                    print("Type 'help' for available commands.")
            except Exception as e:
                print(f"Error: {e}")
        
        output_str = f.getvalue()
        if output_str:
            clean_output = self.strip_ansi(output_str.strip())
            self.log(clean_output)
    
    def _handle_config_command(self, args):
        """Handle config subcommands"""
        from glint.cli.commands import config
        
        if len(args) == 0:
            print("Usage: config <subcommand>")
            print("Subcommands: topics, schedule")
            print("Type 'help' for more details.")
            return
        
        subcommand = args[0].lower()
        subargs = args[1:]
        
        if subcommand == "topics":
            if len(subargs) == 0:
                print("Usage: config topics <list|toggle|delete>")
                return
            
            action = subargs[0].lower()
            
            if action == "list":
                config.list_topics()
                
            elif action == "toggle":
                if len(subargs) < 2:
                    print("Usage: config topics toggle <topic_name>")
                else:
                    config.toggle_topic(subargs[1])
                    self.refresh_notifications()  # Refresh GUI to reflect changes
                    
            elif action == "delete":
                if len(subargs) < 2:
                    print("Usage: config topics delete <topic_name>")
                else:
                    config.delete_topic(subargs[1])
                    self.refresh_notifications()  # Refresh GUI to reflect changes
            else:
                print(f"Unknown topics action: {action}")
                print("Available: list, toggle, delete")
                
        elif subcommand == "schedule":
            if len(subargs) == 0:
                print("Usage: config schedule <set|show>")
                return
            
            action = subargs[0].lower()
            
            if action == "show":
                config.show_schedule()
                
            elif action == "set":
                if len(subargs) < 3:
                    print("Usage: config schedule set <start_time> <end_time>")
                    print("Example: config schedule set 09:00 18:00")
                else:
                    config.set_schedule(subargs[1], subargs[2])
            else:
                print(f"Unknown schedule action: {action}")
                print("Available: set, show")
        else:
            print(f"Unknown config subcommand: {subcommand}")
            print("Available: topics, schedule")
    
    def _show_help(self):
        """Display help information"""
        print("=== Glint Commands ===")
        print("")
        print("Core Commands:")
        print("  add <topic>          - Add a new topic to watch")
        print("  list                 - List all watched topics")
        print("  fetch                - Manually fetch latest trends")
        print("  status               - Show system status")
        print("  clear                - Clear terminal screen")
        print("")
        print("Config Commands:")
        print("  config topics list                    - List all topics with status")
        print("  config topics toggle <topic>          - Toggle topic active/inactive")
        print("  config topics delete <topic>          - Delete a topic")
        print("  config schedule set <start> <end>     - Set notification schedule")
        print("  config schedule show                  - Show notification schedule")
        print("")
        print("Examples:")
        print("  add python")
        print("  config topics toggle python")
        print("  config schedule set 09:00 18:00")
        print("  theme <dark|light|show> - Change or show current theme")


    def create_trend_card(self, parent, trend, topic_name):
        """Factory function to create a single trend card widget."""
        # CARD CONTAINER
        card = ctk.CTkFrame(parent, fg_color=("gray90", "gray13"))
        
        # 1. TITLE
        title_text = f"[{trend.category.upper()}] {trend.title}"
        title = ctk.CTkLabel(card, text=title_text, anchor="w", font=("Roboto", 12, "bold"))
        title.pack(fill="x", padx=10, pady=(10, 2))
        
        # 2. DESCRIPTION
        desc_text = trend.description if trend.description else "No description available"
        if len(desc_text) > 100:
            desc_text = desc_text[:100] + '...'
        desc = ctk.CTkLabel(card, text=desc_text, anchor="w", justify="left", wraplength=300, 
                           font=("Roboto", 11), text_color=("gray30", "gray70"))
        desc.pack(fill="x", padx=10, pady=(0, 5))
        
        # 3. META-INFORMATIONS and Badge information
        meta_frame = ctk.CTkFrame(card, fg_color="transparent")
        meta_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        # Date
        date_str = trend.published_at.strftime("%Y-%m-%d %H:%M")
        meta = ctk.CTkLabel(meta_frame, text=f"{trend.source} . {date_str}", 
                           font=("Roboto", 10), text_color="gray")
        meta.pack(side="left")
        
        # Right: Container for badge and link
        right_box = ctk.CTkFrame(meta_frame, fg_color="transparent")
        right_box.pack(side="right")
        
        # Badge (Only if topic_name exists)
        if topic_name:
            badge = ctk.CTkLabel(right_box, text=topic_name, fg_color="#3B8ED0", 
                                text_color="white", font=("Roboto", 9, "bold"), corner_radius=6)
            badge.pack(side="top", anchor="e", pady=(0, 2))
        
        # Link
        link = ctk.CTkLabel(right_box, text="See more", font=("Roboto", 10, "bold"), 
                           text_color=("blue", "#4da6ff"), cursor="hand2")
        link.pack(side="top", anchor="e")
        link.bind("<Button-1>", lambda e, u=trend.url: webbrowser.open(u))
        
        return card
    
    def populate_frame(self, frame, data, append=False, frame_type=None):
        """Update the data in a scrollable frame."""
        # Clear existing widgets ONLY if not appending
        if not append:
            for widget in frame.winfo_children():
                widget.destroy()
        else:
            # Remove existing "Load More" button if present
            for widget in frame.winfo_children():
                if isinstance(widget, ctk.CTkButton) and widget.cget("text") == "Load More":
                    widget.destroy()
        
        if not data:
            if not append:  # Only show "no trends" if this is initial load
                lbl = ctk.CTkLabel(frame, text="No trends found")
                lbl.pack(pady=20)
            return
        
        for trend, topic_name in data:
            card = self.create_trend_card(frame, trend, topic_name)
            card.pack(fill="x", padx=2, pady=4)
        
        # Add "Load More" button if we got a full page of results
        if len(data) == self.items_per_page and frame_type:
            has_more = self.news_has_more if frame_type == "news" else self.tools_has_more
            if has_more:
                load_more_btn = ctk.CTkButton(
                    frame,
                    text="Load More",
                    command=lambda: self.load_more(frame_type),
                    height=32,
                    width=150,
                    fg_color=("#3B8ED0", "#1F6AA5")
                )
                load_more_btn.pack(pady=10)

    def load_more(self, frame_type):
        """Load more items for a specific frame."""
        if frame_type == "news":
            self.news_page += 1
        elif frame_type == "tools":
            self.tools_page += 1
        
        self.refresh_notifications(append=True)
    
    def refresh_notifications(self, append=False):
        try:
            engine = get_engine()
            with Session(engine) as session:
                # Calculate offsets for pagination
                news_offset = (self.news_page - 1) * self.items_per_page
                tools_offset = (self.tools_page - 1) * self.items_per_page
                
                # 1. Fetch News with pagination
                query_news = (
                    select(Trend, Topic.name)
                    .join(Topic)
                    .where(Trend.category == "news")
                    .where(Topic.is_active == True)
                    .order_by(Trend.published_at.desc())
                    .limit(self.items_per_page)
                    .offset(news_offset)
                )
                news_trends = session.exec(query_news).all()
                self.news_has_more = len(news_trends) == self.items_per_page
                self.populate_frame(self.news_frame, news_trends, append=append, frame_type="news")
                
                # 2. Fetch Tools with pagination
                query_repos = (
                    select(Trend, Topic.name)
                    .join(Topic)
                    .where(Trend.category.in_(["tool", "repo"]))
                    .where(Topic.is_active == True)
                    .order_by(Trend.published_at.desc())
                    .limit(self.items_per_page)
                    .offset(tools_offset)
                )
                repos_trends = session.exec(query_repos).all()
                self.tools_has_more = len(repos_trends) == self.items_per_page
                self.populate_frame(self.tools_frame, repos_trends, append=append, frame_type="tools")
                
                # Update total count for auto-refresh logic
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

    #### TOGGLE THEME FUNCTION
    def toggle_theme(self):
        """Toggle between light and dark themes."""
        current_mode = ctk.get_appearance_mode()

        if current_mode =="Light":
            ctk.set_appearance_mode("Dark")
        else:
            ctk.set_appearance_mode("Light")
    #end toggle_theme

    def history_up(self,event):
        """Navigate up in the command history (older commands) """
        if not self.command_history:
            return "break"
        
        if self.history_index < len(self.command_history) -1:
            self.history_index +=1
            self.input.delete(0, "end")
            self.input.insert(0, self.command_history[-(self.history_index + 1)])
        return "break" # prevent default behavior or anything no needed

    def history_down(self,event):
        """Navigate down in the command history (newer commands) """
        if self.history_index > 0:
            self.history_index -=1
            self.input.delete(0,"end")
            self.input.insert(0, self.command_history[-(self.history_index + 1)])
        elif self.history_index == 0:
            self.history_index = -1
            self.input.delete(0,"end") # clear input
        return "break" # prevent default behavior or anything no needed
    #end history_down
if __name__ == "__main__":
    app = GlintApp()
    app.mainloop()
