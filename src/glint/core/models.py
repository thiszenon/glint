from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel

class Topic(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True, unique=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = Field(default=True)

class Trend(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    description: Optional[str] = None
    url: str
    source: str  # e.g., "github", "hackernews"
    published_at: datetime
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False)
    
    # Foreign key to link to Topic
    topic_id: Optional[int] = Field(default=None, foreign_key="topic.id")
