"""
Utility script to view all trends in the database ordered by latest fetch time.
"""
from sqlmodel import Session, select
from glint.core.database import get_engine
from glint.core.models import Trend
from datetime import datetime


def view_all_trends():
    """Display all trends from the database ordered by latest fetch time."""
    engine = get_engine()
    
    with Session(engine) as session:
        # Query all trends ordered by fetched_at descending (latest first)
        statement = select(Trend).order_by(Trend.fetched_at.desc())
        trends = session.exec(statement).all()
        
        if not trends:
            print("No trends found in the database.")
            return
        
        print(f"\n{'='*100}")
        print(f"Total Trends: {len(trends)}")
        print(f"{'='*100}\n")
        
        for idx, trend in enumerate(trends, 1):
            # Format the fetched_at time to show date and hour
            fetch_time = trend.fetched_at.strftime("%Y-%m-%d %H:%M:%S")
            fetch_hour = trend.fetched_at.strftime("%H:%M")
            
            # Calculate how long ago it was fetched
            time_diff = datetime.utcnow() - trend.fetched_at
            hours_ago = time_diff.total_seconds() / 3600
            
            if hours_ago < 1:
                time_ago = f"{int(time_diff.total_seconds() / 60)} minutes ago"
            elif hours_ago < 24:
                time_ago = f"{int(hours_ago)} hours ago"
            else:
                days_ago = int(hours_ago / 24)
                time_ago = f"{days_ago} days ago"
            
            # Display trend information
            print(f"[{idx}] {trend.title}")
            print(f"    Source: {trend.source} | Category: {trend.category}")
            print(f"    Fetched: {fetch_time} ({time_ago})")
            print(f"    Published: {trend.published_at.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"    Read: {'✓' if trend.is_read else '✗'}")
            print(f"    URL: {trend.url}")
            if trend.description:
                # Truncate description if too long
                desc = trend.description[:100] + "..." if len(trend.description) > 100 else trend.description
                print(f"    Description: {desc}")
            print(f"    {'-'*96}")
        
        # Show summary statistics
        print(f"\n{'='*100}")
        print("Summary:")
        print(f"  Total trends: {len(trends)}")
        print(f"  Read: {sum(1 for t in trends if t.is_read)}")
        print(f"  Unread: {sum(1 for t in trends if not t.is_read)}")
        
        # Group by source
        sources = {}
        for trend in trends:
            sources[trend.source] = sources.get(trend.source, 0) + 1
        
        print(f"\n  By Source:")
        for source, count in sources.items():
            print(f"    {source}: {count}")
        
        # Show latest fetch time
        if trends:
            latest_fetch = trends[0].fetched_at
            print(f"\n  Latest fetch: {latest_fetch.strftime('%Y-%m-%d %H:%M:%S')} ({latest_fetch.strftime('%H:%M')})")
        
        print(f"{'='*100}\n")


if __name__ == "__main__":
    view_all_trends()
