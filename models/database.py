"""Database configuration and session management."""

import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Database URL - defaults to SQLite
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/stupidbookmarks.db")

# Ensure data directory exists for SQLite
if DATABASE_URL.startswith("sqlite"):
    os.makedirs("data", exist_ok=True)

# Create engine
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Initialize database tables."""
    from . import models  # Import here to avoid circular imports
    Base.metadata.create_all(bind=engine)
