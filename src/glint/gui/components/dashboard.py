import customtkinter as ctk
from sqlmodel import Session, select, func
from glint.core.database import get_engine
from glint.core.models import Trend, Topic
from glint.gui.components.trend_card import TrendCard

class Dashboard(ctk.CTkTabview):
    def __init__(self, parent, app, scroll_handler):
        super().__init__(parent)
        self.app = app
        self.scroll_handler = scroll_handler
        
        # Add tabs
        self.add("Tools")
        self.add("News")
        self.add("Current Project")
        
        # Create scrollable frames
        self.news_frame = ctk.CTkScrollableFrame(self.tab("News"), label_text="News")
        self.news_frame.pack(fill="both", expand=True)
        self.scroll_handler.register_frame("News", self.news_frame)
        
        self.tools_frame = ctk.CTkScrollableFrame(self.tab("Tools"), label_text="Tools")
        self.tools_frame.pack(fill="both", expand=True)
        self.scroll_handler.register_frame("Tools", self.tools_frame)
        
        self.project_frame = ctk.CTkScrollableFrame(self.tab("Current Project"), label_text="Current Project")
        self.project_frame.pack(fill="both", expand=True)
        self.scroll_handler.register_frame("Current Project", self.project_frame)
        
        # State
        self.last_trend_count = -1
        self.news_page = 1
        self.tools_page = 1
        self.items_per_page = 20
        self.news_has_more = True
        self.tools_has_more = True
        
        # Start auto-refresh
        self.refresh_notifications()
        self.after(5000, self.auto_refresh_loop)

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
            card = TrendCard.create(frame, trend, topic_name, self.scroll_handler)
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
                if count != self.last_trend_count:
                    self.refresh_notifications()
                    self.last_trend_count = count
        except Exception as e:
            print(f"Auto-refresh error: {e}")
            
        # Check for updates every 10 seconds
        self.after(10000, self.auto_refresh_loop)
