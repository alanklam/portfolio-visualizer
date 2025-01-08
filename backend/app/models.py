from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from .database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user", cascade="all, delete-orphan")
    portfolio = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    settings = relationship("UserSettings", back_populates="user", cascade="all, delete-orphan")

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    date = Column(Date, nullable=False)
    transaction_type = Column(String, nullable=False)
    stock = Column(String, nullable=False)
    units = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    fee = Column(Float, default=0.0)
    option_type = Column(String, nullable=True)
    security_type = Column(String, nullable=False)
    broker = Column(String, nullable=False)
    amount = Column(Float, nullable=True)
    
    # Relationship
    user = relationship("User", back_populates="transactions")

class Portfolio(Base):
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock = Column(String, nullable=False)
    total_units = Column(Float)
    average_cost = Column(Float)
    current_price = Column(Float)
    last_updated = Column(Date)
    
    # Relationship
    user = relationship("User", back_populates="portfolio")

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    stock = Column(String, nullable=False)
    target_weight = Column(Float)
    
    # Relationship
    user = relationship("User", back_populates="settings") 