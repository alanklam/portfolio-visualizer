from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

try:
    # Create database directory if it doesn't exist
    os.makedirs("database", exist_ok=True)
    logger.info("Database directory verified")
except Exception as e:
    logger.error(f"Error creating database directory: {str(e)}")
    raise

SQLALCHEMY_DATABASE_URL = "sqlite:///database/sqlite.db"

try:
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args={"check_same_thread": False}  # Needed for SQLite
    )
    logger.info("Database engine initialized successfully")
except Exception as e:
    logger.error(f"Error creating database engine: {str(e)}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Initialize database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing database tables: {str(e)}")
        raise
    
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {str(e)}")
        if db.is_active:
            logger.info("Rolling back active transaction")
            db.rollback()
        raise
    finally:
        logger.debug("Closing database session")
        db.close()

def migrate_db():
    """Create or update database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database migration completed successfully")
    except Exception as e:
        logger.error(f"Error during database migration: {str(e)}")
        raise