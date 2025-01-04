from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List, Dict, Union

class UserSettingsBase(BaseModel):
    target_weights: Dict[str, float]
    rebalance_threshold: float = 5.0  # Default 5% threshold

class UserSettings(UserSettingsBase):
    id: int
    last_update: datetime

    class Config:
        from_attributes = True

class ChartData(BaseModel):
    chart_type: str  # 'pie', 'line', or 'bar'
    data: str       # JSON string of plotly figure
    title: str
    last_update: datetime

class PortfolioStats(BaseModel):
    total_value: float
    total_return: float
    total_return_pct: float
    num_positions: int
    last_update: datetime

class Transaction(BaseModel):
    date: datetime
    transaction_type: str
    stock: str
    units: float
    price: float
    fee: float = 0.0
    security_type: str
    option_type: Optional[str] = None
    broker: str

class Portfolio(BaseModel):
    holdings: Dict[str, Dict[str, Union[float, str, datetime]]]
    stats: PortfolioStats
    last_update: datetime 