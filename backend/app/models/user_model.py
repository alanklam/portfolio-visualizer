from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from ..core.db import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    portfolio = relationship("Portfolio", back_populates="user")
    settings = relationship("UserSettings", back_populates="user") 