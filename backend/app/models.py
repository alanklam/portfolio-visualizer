from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, Enum
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, nullable=False)
    transaction_type = Column(String, nullable=False)
    stock = Column(String, nullable=False)
    units = Column(Float)
    price = Column(Float)
    fee = Column(Float)
    option_type = Column(String, nullable=True)
    security_type = Column(String, nullable=False)
    broker = Column(String, nullable=False)

class Portfolio(Base):
    __tablename__ = "portfolio"
    
    id = Column(Integer, primary_key=True, index=True)
    stock = Column(String, nullable=False)
    total_units = Column(Float)
    average_cost = Column(Float)
    current_price = Column(Float)
    last_updated = Column(Date)

class UserSettings(Base):
    __tablename__ = "user_settings"
    
    id = Column(Integer, primary_key=True, index=True)
    stock = Column(String, nullable=False)
    target_weight = Column(Float) 