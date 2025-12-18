import threading
import time
from plyer import notification
from sqlmodel import Session, select
from glint.core.database import get_engine
from datetime import datetime
from glint.core.parallel_fetcher import ParallelFetcher
from glint.utils.url_utils import normalize_url
from glint.utils.relevance import calculate_relevance
from glint.utils.fingerprint import generate_fingerprint

class Notifier:
    def __init__(self, interval_seconds=300):
        self.interval = interval_seconds
        self.running = False
        self.thread = None
        self.coordinator = ParallelFetcher()
        
        # Set App ID on Windows to group notifications under "Glint"
        import os
        if os.name == 'nt':
            try:
                import ctypes
                myappid = 'glint.app.ver1'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
            except Exception:
                pass

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
            new_active_trends_count = 0  # Only count trends from active topics for notification
            
            with Session(engine) as session:
                # Get ALL topics (active and inactive) - inactive are in "standby mode"
                all_topics = session.exec(select(Topic)).all()
                
                if not all_topics:
                    return

                # Get active topic IDs for notification filtering
                active_topic_ids = [t.id for t in all_topics if t.is_active]
                
                # PARALLEL FETCH - All sources at once!
                all_trends = self.coordinator.fetch_all(all_topics)
                
                for trend in all_trends:
                    # Normalize URL
                    normalized_url = normalize_url(trend.url)
                    
                    # Check for URL duplicates
                    existing_trend = session.exec(
                        select(Trend).where(Trend.url_normalized == normalized_url)
                    ).first()
                    
                    if not existing_trend:
                        # Store normalized URL
                        trend.url_normalized = normalized_url
                        
                        # Generate fingerprint
                        trend.content_fingerprint = generate_fingerprint(
                            trend.title,
                            trend.description
                        )
                        
                        # Check for content duplicates
                        fingerprint_match = session.exec(
                            select(Trend).where(
                                Trend.content_fingerprint == trend.content_fingerprint
                            )
                        ).first()
                        
                        if not fingerprint_match:
                            # Find which topic this trend matched
                            matched_topic = next((t for t in all_topics if t.id == trend.topic_id), None)
                            
                            if matched_topic:
                                # Calculate relevance score
                                trend.relevance_score = calculate_relevance(trend, matched_topic)
                                
                                # Set status based on score threshold
                                if trend.relevance_score >= 0.3:
                                    trend.status = "approved"
                                    
                                    # Only notify if linked to an active topic AND approved
                                    if trend.topic_id in active_topic_ids:
                                        new_active_trends_count += 1
                                else:
                                    trend.status = "rejected"
                            else:
                                trend.relevance_score = 0.0
                                trend.status = "rejected"
                            
                            # Save trend (approved or rejected)
                            session.add(trend)
                
                session.commit()
            
            # Only notify about trends from active topics
            if new_active_trends_count > 0:
                self.send_notification(
                    "New Tech Trends",
                    f"Found {new_active_trends_count} new trends matching your active topics."
                )
                
        except Exception as e:
            print(f"Error in notification loop: {e}")

    def send_notification(self, title, message):
        try:
            # Resolve icon path
            import os
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # src/glint/core -> src/glint/assets/logo.png
            icon_path = os.path.join(os.path.dirname(current_dir), "assets", "logo.png")
            
            if not os.path.exists(icon_path):
                icon_path = None
            
            # Windows (nt) requires .ico files for notifications
            # plyer throws a threaded exception if we pass a .png
            if os.name == 'nt' and icon_path and not icon_path.lower().endswith('.ico'):
                # print("Windows requires .ico for notifications. Skipping logo.png.")
                icon_path = None

            try:
                notification.notify(
                    title=title,
                    message=message,
                    app_name="Glint",
                    app_icon=icon_path,
                    timeout=10,
                )
            except Exception as icon_error:
                # Fallback: Try without icon (Windows often requires .ico, fails with .png)
                print(f"Icon load failed ({icon_error}), sending without icon...")
                notification.notify(
                    title=title,
                    message=message,
                    app_name="Glint",
                    app_icon=None,
                    timeout=10,
                )
        except Exception as e:
            print(f"Failed to send notification: {e}")
