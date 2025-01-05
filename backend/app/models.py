from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, unique=True, index=True, nullable=False)
    created_at = Column(Date, nullable=False)
    
    # Relationships
    transactions = relationship("Transaction", back_populates="user")
    portfolio = relationship("Portfolio", back_populates="user")
    settings = relationship("UserSettings", back_populates="user")

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