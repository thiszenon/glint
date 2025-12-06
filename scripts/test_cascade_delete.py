"""Test script for CASCADE delete functionality."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from glint.core.database import create_db_and_tables, get_engine
from glint.core.models import Topic, Trend, UserActivity
from sqlmodel import Session, select,func
from datetime import datetime

def setup_test_data():
    """Create test topic with trends and activities."""
    print("Setting up test data...")
    engine = get_engine()
    
    with Session(engine) as session:
        # Check if test topic already exists and delete it
        existing_topic = session.exec(select(Topic).where(Topic.name == "test-cascade")).first()
        if existing_topic:
            print("  - Cleaning up existing test data...")
            # Delete old trends and activities
            trends = session.exec(select(Trend).where(Trend.topic_id == existing_topic.id)).all()
            trend_ids = [t.id for t in trends]
            if trend_ids:
                activities = session.exec(select(UserActivity).where(UserActivity.trend_id.in_(trend_ids))).all()
                for activity in activities:
                    session.delete(activity)
            for trend in trends:
                session.delete(trend)
            session.delete(existing_topic)
            session.commit()
        
        # Create test topic
        test_topic = Topic(name="test-cascade", is_active=True)
        session.add(test_topic)
        session.commit()
        session.refresh(test_topic)
        
        # Create test trends
        for i in range(3):
            trend = Trend(
                title=f"Test Trend {i+1}",
                description=f"Test description for trend {i+1}",
                url=f"https://example.com/trend{i+1}",
                source="GitHub",
                category="repo",
                published_at=datetime.utcnow(),
                topic_id=test_topic.id,
                relevance_score=0.8
            )
            session.add(trend)
        
        session.commit()
        
        # Get trends to create activities
        trends = session.exec(
            select(Trend).where(Trend.topic_id == test_topic.id)
        ).all()
        
        # Create user activities
        for trend in trends[:2]:  # Add activities for first 2 trends
            activity = UserActivity(
                trend_id=trend.id,
                clicked_at=datetime.utcnow()
            )
            session.add(activity)
        
        session.commit()
        
        print(f"[OK] Created topic '{test_topic.name}' with {len(trends)} trends")
        print(f"[OK] Created {2} user activity records")
        
        return test_topic.id

def verify_counts(topic_id):
    """Verify counts before deletion."""
    print("\nVerifying counts...")
    engine = get_engine()
    
    with Session(engine) as session:
        # Count trends
        trend_count = session.exec(
            select(func.count(Trend.id)).where(Trend.topic_id == topic_id)
        ).one()
        
        # Get trend IDs
        trends = session.exec(
            select(Trend).where(Trend.topic_id == topic_id)
        ).all()
        trend_ids = [t.id for t in trends]
        
        # Count activities
        activity_count = 0
        if trend_ids:
            activity_count = session.exec(
                select(func.count(UserActivity.id)).where(
                    UserActivity.trend_id.in_(trend_ids)
                )
            ).one()
        
        print(f"  - Trends: {trend_count}")
        print(f"  - Activities: {activity_count}")
        
        return trend_count, activity_count

def test_ml_export():
    """Test ML exporter."""
    print("\n" + "="*60)
    print("TEST 1: ML Data Export")
    print("="*60)
    
    engine = get_engine()
    from glint.utils.ml_exporter import export_topic_data
    
    with Session(engine) as session:
        # Get test topic
        topic = session.exec(select(Topic).where(Topic.name == "test-cascade")).first()
        if not topic:
            print("[ERROR] Test topic not found!")
            return False
        
        # Get trends and activities
        trends = session.exec(select(Trend).where(Trend.topic_id == topic.id)).all()
        trend_ids = [t.id for t in trends]
        activities = []
        if trend_ids:
            activities = session.exec(
                select(UserActivity).where(UserActivity.trend_id.in_(trend_ids))
            ).all()
        
        # Export
        try:
            export_path = export_topic_data(topic, trends, activities)
            print(f"[OK] Exported to: {export_path}")
            
            # Verify file exists
            if export_path.exists():
                # Read and check structure
                import json
                with open(export_path) as f:
                    data = json.load(f)
                
                assert "topic" in data, "Missing 'topic' key"
                assert "trends" in data, "Missing 'trends' key"
                assert "user_activities" in data, "Missing 'user_activities' key"
                assert "export_metadata" in data, "Missing 'export_metadata' key"
                
                print(f"[OK] JSON structure valid")
                print(f"  - Topic: {data['topic']['name']}")
                print(f"  - Trends: {len(data['trends'])}")
                print(f"  - Activities: {len(data['user_activities'])}")
                
                return True
            else:
                print(f"[ERROR] Export file not found: {export_path}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Export failed: {e}")
            import traceback
            traceback.print_exc()
            return False

def test_cascade_delete():
    """Test CASCADE delete functionality."""
    print("\n" + "="*60)
    print("TEST 2: CASCADE Delete")
    print("="*60)
    
    print("\nThis test requires manual interaction.")
    print("Run the following command:")
    print("\n  glint topics delete test-cascade\n")
    print("Expected behavior:")
    print("  1. Shows warning with counts")
    print("  2. Asks for confirmation")
    print("  3. Exports ML data")
    print("  4. Deletes topic + trends + activities")
    print("\n  glint topics delete test-cascade --force\n")
    print("Expected behavior:")
    print("  1. Skips confirmation")
    print("  2. Immediately deletes")

if __name__ == "__main__":
    print("CASCADE Delete Test Suite")
    print("=" * 60)
    
    # Ensure database exists
    create_db_and_tables()
    
    # Setup test data
    topic_id = setup_test_data()
    
    # Verify counts
    trend_count, activity_count = verify_counts(topic_id)
    
    # Test ML export
    export_success = test_ml_export()
    
    # Manual delete test instructions
    test_cascade_delete()
    
    print("\n" + "="*60)
    if export_success:
        print("[OK] All automated tests passed!")
    else:
        print("[ERROR] Some tests failed")
    print("\nRun the manual test above to verify CASCADE delete")
    print("="*60)
