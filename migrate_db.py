"""
Database Migration Script
Run this to recreate the database with the new UserActivity table.
"""

from glint.core.database import get_engine
from glint.core.models import SQLModel

def migrate():
    """Recreate all tables including the new UserActivity table."""
    engine = get_engine()
    
    print("Creating all tables (including UserActivity)...")
    SQLModel.metadata.create_all(engine)
    print("Database migration complete!")
    print("\nNew tables created:")
    print("  - useractivity (for tracking user clicks)")

if __name__ == "__main__":
    migrate()
