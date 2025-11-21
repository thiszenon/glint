import threading
import time
from plyer import notification
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Trend
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
                self._fetch_and_notify()
            except Exception as e:
                print(f"Error in notification loop: {e}")
            
            # Sleep in short bursts to allow faster stopping
            for _ in range(self.interval):
                if not self.running:
                    break
                time.sleep(1)

    def _fetch_and_notify(self):
        engine = get_engine()
        new_trends = []
        
        with Session(engine) as session:
            for fetcher in self.fetchers:
                try:
                    trends = fetcher.fetch()
                    for trend in trends:
                        # Check for duplicates
                        statement = select(Trend).where(Trend.url == trend.url)
                        results = session.exec(statement)
                        existing_trend = results.first()
                        
                        if not existing_trend:
                            session.add(trend)
                            new_trends.append(trend)
                except Exception as e:
                    print(f"Error fetching in background: {e}")
            
            session.commit()
            
        if new_trends:
            self.send_notification(
                title="New Tech Trends Found!",
                message=f"Glint found {len(new_trends)} new trends. Check the dashboard."
            )

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
