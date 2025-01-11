from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from ..core.db import Base

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    date = Column(Date, nullable=False)
    stock = Column(String, nullable=False)
    transaction_type = Column(String, nullable=False)
    units = Column(Float)
    price = Column(Float)
    fee = Column(Float)
    option_type = Column(String)
    security_type = Column(String)
    amount = Column(Float)
    
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
    target_weight = Column(Float, nullable=False)  # Make sure it's not nullable
    
    __table_args__ = (
        UniqueConstraint('user_id', 'stock', name='unique_user_stock'),
    )
    
    # Relationship
    user = relationship("User", back_populates="settings")