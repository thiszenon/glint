from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from enum import Enum

class TrendStatus(str,Enum):
    """ Status of a trend after relevance scoring"""
    APPROVED = "approved" # score >= threshold
    REJECTED = "rejected" # score < threshold
    
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
    url_normalized: Optional[str]= Field(default=None,index=True)
    content_fingerprint: Optional[str] = Field(default=None,index=True)
    relevance_score: Optional[float] = Field(default=None, index=True)
    status: Optional[str] = Field(default="approved", index=True)
    source: str  # e.g., "github", "hackernews"
    category: str = Field(default="general") # e.g., "repo", "news", "tool"
    published_at: datetime 
    fetched_at: datetime = Field(default_factory=datetime.utcnow)
    is_read: bool = Field(default=False)
    # Foreign key to link to Topic
    topic_id: Optional[int] = Field(default=None, foreign_key="topic.id")

class Project(SQLModel, table = True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title : str
    description: str
    topics_to_watched: str # Comma-separated list of topics
    created_at: datetime = Field(default_factory=datetime.utcnow)

class User(SQLModel, table = True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    local_info: str # informations about the computer of user 
    

class UserConfig(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    notification_start: str = Field(default="09:00") # HH:MM format
    notification_end: str = Field(default="18:00")   # HH:MM format

class UserActivity(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    trend_id: int = Field(foreign_key="trend.id")
    clicked_at: datetime = Field(default_factory=datetime.utcnow)
    time_spent: Optional[int] = Field(default=None)  # Seconds spent reading (for future NLP)
