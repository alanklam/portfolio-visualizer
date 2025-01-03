from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class TransactionBase(BaseModel):
    date: date
    transaction_type: str
    stock: str
    units: float
    price: float
    fee: float
    option_type: Optional[str] = None
    security_type: str
    broker: str

class TransactionCreate(TransactionBase):
    pass

class Transaction(TransactionBase):
    id: int

    class Config:
        orm_mode = True

class PortfolioBase(BaseModel):
    stock: str
    total_units: float
    average_cost: float
    current_price: float
    last_updated: date

class Portfolio(PortfolioBase):
    id: int

    class Config:
        orm_mode = True

class UserSettingsBase(BaseModel):
    stock: str
    target_weight: float

class UserSettings(UserSettingsBase):
    id: int

    class Config:
        orm_mode = True

class FileUpload(BaseModel):
    broker: str
    file_content: str 