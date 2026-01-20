"""
Database Configuration and Connection
- PostgreSQL connection using SQLAlchemy
- Session management
- Base model for all database models
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./mindspend.db")

# Update URL for psycopg3 driver if using PostgreSQL
if DATABASE_URL and "postgresql://" in DATABASE_URL and "postgresql+psycopg://" not in DATABASE_URL:
    DATABASE_URL = DATABASE_URL.replace("postgresql://", "postgresql+psycopg://")

# Create SQLAlchemy engine
# SQLite-specific configuration for concurrent access
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(
    DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10 if "sqlite" not in DATABASE_URL else 5,  # Connection pool size
    max_overflow=20 if "sqlite" not in DATABASE_URL else 10,  # Max connections above pool_size
    echo=os.getenv("DEBUG", "False").lower() == "true"  # Log SQL queries in debug mode
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()

# Dependency to get database session
def get_db() -> Generator[Session, None, None]:
    """
    Dependency function to get database session.
    Yields a database session and ensures it's closed after use.
    
    Usage in FastAPI:
        @app.get("/items")
        def get_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def init_db():
    """
    Initialize database - create all tables.
    Call this when starting the application.
    """
    Base.metadata.create_all(bind=engine)
    print("✓ Database tables created successfully")

# Drop all tables (use with caution!)
def drop_db():
    """
    Drop all tables from database.
    Use only in development for clean reset.
    """
    Base.metadata.drop_all(bind=engine)
    print("✓ Database tables dropped")
