"""ML data exporter for preserving deleted topic data."""

import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from glint.core.models import Topic, Trend, UserActivity


def export_topic_data(
    topic: Topic,
    trends: List[Trend],
    activities: List[UserActivity],
    export_dir: Path = None
) -> Path:
    """
    Export topic data to JSON for ML training before deletion.
    
    Args:
        topic: The topic being deleted
        trends: Associated trends
        activities: Associated user activity records
        export_dir: Optional custom export directory (defaults to .glint/ml_data/)
    
    Returns:
        Path to the exported JSON file
    """
    # Default export directory
    if export_dir is None:
        export_dir = Path.home() / ".glint" / "ml_data"
    
    # Create directory if it doesn't exist
    export_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate filename: {topic_name}_{timestamp}.json
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{topic.name}_{timestamp}.json"
    export_path = export_dir / filename
    
    # Build export data structure
    export_data = {
        "topic": {
            "name": topic.name,
            "created_at": topic.created_at.isoformat(),
            "deleted_at": datetime.utcnow().isoformat(),
            "is_active": topic.is_active
        },
        "trends": [
            {
                "title": trend.title,
                "description": trend.description,
                "url": trend.url,
                "source": trend.source,
                "category": trend.category,
                "relevance_score": trend.relevance_score,
                "status": trend.status,
                "published_at": trend.published_at.isoformat() if trend.published_at else None,
                "fetched_at": trend.fetched_at.isoformat() if trend.fetched_at else None,
                "is_read": trend.is_read
            }
            for trend in trends
        ],
        "user_activities": [
            {
                "trend_id": activity.trend_id,
                "clicked_at": activity.clicked_at.isoformat() if activity.clicked_at else None,
                "time_spent": activity.time_spent
            }
            for activity in activities
        ],
        "export_metadata": {
            "exported_at": datetime.utcnow().isoformat(),
            "trend_count": len(trends),
            "activity_count": len(activities),
            "version": "1.0"
        }
    }
    
    # Write to JSON file
    with open(export_path, 'w', encoding='utf-8') as f:
        json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    return export_path
