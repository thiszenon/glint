"""
Database Migration Script
Run this to recreate the database with the new UserActivity table.
"""

from sqlmodel import Session, select, text
from glint.core.database import get_engine
from glint.core.models import Trend
from glint.utils.url_utils import normalize_url

def migrate():
    """Add normaized URLS to existing trends."""
    engine = get_engine()

    #step 1: add the column to the database
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE trend ADD COLUMN url_normalized VARCHAR"))
            conn.commit()
            print("column added successfully ! ")
        except Exception as ex:
            if "duplicate column name" in str(ex).lower():
                print("column already exists.")
            else:
                print(f"Failed to add column: {ex}")
                return

    with Session(engine) as session:
        #get all trends that don't have normalized URLs
        statement = select(Trend).where((Trend.url_normalized ==None) | (Trend.url_normalized ==""))
        trends = session.exec(statement).all()

        print(f"Found {len(trends)} trends to normalize...")

        for i, trend in enumerate(trends, 1):
            #Normalize the URL
            trend.url_normalized = normalize_url(trend.url)

            #show progress every 100 trends
            if i%100 == 0:
                print(f"Processed {i}/{len(trends)} trends...")

        #save all changes
        session.commit()
        print(f"Migration complete ! Normalized {len(trends)} URLs")

if __name__== "__main__":
    migrate()
    