from sqlmodel import SQLModel, create_engine
from pathlib import Path

# Define where the file will live
# We'll default to a relative path for now, but init command will set this up properly
sqlite_file_name = "glint.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"

# We defer engine creation until we know the path, or we use a default
# For CLI usage, we usually want to load the config to find the DB path
# But for simplicity in this step, we'll assume standard location

def get_db_path():
    return Path.home() / ".glint" / "glint.db"

def get_engine():
    db_path = get_db_path()
    sqlite_url = f"sqlite:///{db_path}"
    return create_engine(sqlite_url)

def create_db_and_tables():
    engine = get_engine()
    SQLModel.metadata.create_all(engine)
