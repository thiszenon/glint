import threading
import time
from plyer import notification
from sqlmodel import Session, select
from glint.core.database import get_engine
from datetime import datetime
from glint.core.models import Trend, Topic, UserConfig
from glint.core.fetchers import GitHubFetcher, HackerNewsFetcher

class Notifier:
    def __init__(self, interval_seconds=300):
        self.interval = interval_seconds
        self.running = False
        self.thread = None
        self.fetchers = [GitHubFetcher(), HackerNewsFetcher()]

    def start(self):
        if not self.running:
            self.running = True
            self.thread = threading.Thread(target=self._run_loop, daemon=True)
            self.thread.start()

    def stop(self):
        self.running = False

    def _run_loop(self):
        while self.running:
            try:
                # Check schedule
                should_run = True
                engine = get_engine()
                with Session(engine) as session:
                    config = session.exec(select(UserConfig)).first()
                    if config:
                        now = datetime.now().time()
                        start = datetime.strptime(config.notification_start, "%H:%M").time()
                        end = datetime.strptime(config.notification_end, "%H:%M").time()
                        
                        if not (start <= now <= end):
                            should_run = False
                            # print(f"Skipping fetch: Outside schedule ({start} - {end})")

                if should_run:
                    self._fetch_and_notify()
            except Exception as e:
                print(f"Error in notification loop: {e}")
            
            # Sleep in short bursts to allow faster stopping
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

    def _fetch_and_notify(self):
        try:
            engine = get_engine()
            new_trends_count = 0
            
            with Session(engine) as session:
                # Get active topics
                active_topics = session.exec(select(Topic).where(Topic.is_active == True)).all()
                
                for fetcher in self.fetchers:
                    # Pass active topics to fetcher
                    trends = fetcher.fetch(active_topics)
                    
                    for trend in trends:
                        # Check if exists
                        existing = session.exec(select(Trend).where(Trend.url == trend.url)).first()
                        if not existing:
                            session.add(trend)
                            new_trends_count += 1
                
                session.commit()
            
            if new_trends_count > 0:
                self.send_notification(
                    "New Tech Trends",
                    f"Found {new_trends_count} new trends matching your topics."
                )
                
        except Exception as e:
            print(f"Error in notification loop: {e}")

    def send_notification(self, title, message):
        try:
            notification.notify(
                title=title,
                message=message,
                app_name="Glint",
                app_icon=None, # We could add an .ico path here if available
                timeout=10,
            )
        except Exception as e:
            print(f"Failed to send notification: {e}")
