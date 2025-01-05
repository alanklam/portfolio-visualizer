from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Get the root directory (two levels up from this file)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Create database directory if it doesn't exist
db_dir = os.path.join(ROOT_DIR, 'database')
os.makedirs(db_dir, exist_ok=True)

# Create database URL - using absolute path
SQLALCHEMY_DATABASE_URL = f"sqlite:///{os.path.join(db_dir, 'sqlite.db')}"

# Create engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # Needed for SQLite
)

# Create SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create Base class
Base = declarative_base()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 