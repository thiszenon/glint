"""
Database Migration Script
Run this to recreate the database with the new UserActivity table.
"""

from sqlmodel import Session, select, text
from glint.core.database import get_engine
from glint.core.models import Trend, Topic
from glint.utils.url_utils import normalize_url
from glint.utils.relevance import calculate_relevance

def migrate():
    """Add normaized URLS to existing trends."""
    engine = get_engine()

    #step 1: add the column to the database
    with engine.connect() as conn:
        try:
            conn.execute(text("ALTER TABLE trend ADD COLUMN relevance_score FLOAT"))
            
            print("column added successfully ! ")
        except Exception as ex:
            if "duplicate column name" in str(ex).lower():
                print("column already exists.")
            else:
                print(f"Failed to add column: {ex}")
                return
        
        try:
            conn.execute(text("ALTER TABLE trend ADD COLUMN status VARCHAR DEFAULT 'approved'"))
            print("✓ Added status column")
        except Exception as ex:
            if "duplicate column name" in str(ex).lower():
                print("✓ status column already exists")
            else:
                print(f"Failed to add status: {ex}")
                return
        conn.commit()

    #step 2: calculate relevance score for existing trends
    with Session(engine) as session:
        #get all topics
        topics = session.exec(select(Topic)).all()
        topic_map = {topic.id: topic for topic in topics}

        #Get trends without scores
        statement = select(Trend).where((Trend.relevance_score ==None) | (Trend.status ==None))
        trends = session.exec(statement).all()

        print(f"Found {len(trends)} trends to score...")

        for i, trend in enumerate(trends, 1):

            if trend.topic_id and trend.topic_id in topic_map:
                topic = topic_map[trend.topic_id]

                #calculate relevance score
                trend.relevance_score = calculate_relevance(trend, topic)

                #set status
                if trend.relevance_score >=0.3:
                    trend.status = "approved"
                else:
                    trend.status = "rejected"
            else:
                #No topic found 
                trend.relevance_score = 0.0
                trend.status = "rejected"
            #progress indicator
            if i%100 == 0:
                print(f"Processed {i}/{len(trends)} trends...")
        #save all changes
        session.commit()

        #show stats
        approved = sum(1 for trend in trends if trend.status == "approved")
        rejected = sum(1 for trend in trends if trend.status == "rejected")
        print(f"Approved: {approved}, Rejected: {rejected}")
        print(f"rejection rate: {rejected/len(trends)*100:.2f}%")


if __name__== "__main__":
    migrate()
    