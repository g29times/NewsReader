from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///./articles.db')

# Create engine
engine = create_engine(
    DATABASE_URL, 
    connect_args={'check_same_thread': False} if 'sqlite' in DATABASE_URL else {}
)

# Create a configured "Session" class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a thread-local session
db_session = scoped_session(SessionLocal)

# Base class for declarative models
Base = declarative_base()

def get_db():
    """
    Dependency that creates a new database session for each request
    """
    db = db_session()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """
    Initialize the database, create all tables
    """
    from ..models import article  # Import models
    Base.metadata.create_all(bind=engine)
