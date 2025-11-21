import sys
import os
from sqlmodel import Session, select
from glint.core.database import get_engine, create_db_and_tables, get_db_path
from glint.core.models import Trend
from glint.core.fetchers import GitHubFetcher, HackerNewsFetcher

def test_fetchers():
    print("Initializing DB...")
    db_path = get_db_path()
    if db_path.exists():
        try:
            os.remove(db_path)
            print("Deleted existing DB.")
        except Exception as e:
            print(f"Error deleting DB: {e}")
            
    create_db_and_tables()
    
    print("\nTesting GitHubFetcher...")
    gh = GitHubFetcher()
    trends = gh.fetch()
    print(f"Fetched {len(trends)} items from GitHub")
    for t in trends:
        print(f" - {t.title} ({t.url})")

    print("\nTesting HackerNewsFetcher...")
    hn = HackerNewsFetcher()
    trends = hn.fetch()
    print(f"Fetched {len(trends)} items from Hacker News")
    for t in trends:
        print(f" - {t.title} ({t.url})")
        
    print("\nSaving to DB...")
    engine = get_engine()
    with Session(engine) as session:
        for t in trends:
            # Check duplicates
            existing = session.exec(select(Trend).where(Trend.url == t.url)).first()
            if not existing:
                session.add(t)
        session.commit()
        
    print("\nVerifying DB content...")
    with Session(engine) as session:
        all_trends = session.exec(select(Trend)).all()
        print(f"Total trends in DB: {len(all_trends)}")

if __name__ == "__main__":
    test_fetchers()
