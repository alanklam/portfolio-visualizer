from pydantic import BaseModel, Field
from typing import Dict, List, Optional
from datetime import datetime

class FileUpload(BaseModel):
    """Schema for file upload request"""
    broker: str = Field(..., description="The broker type (e.g., 'fidelity', 'schwab', 'etrade')")
    files: List[str] = Field(..., description="List of uploaded file names")

class Transaction(BaseModel):
    """Schema for a single transaction"""
    date: datetime
    symbol: str
    security_type: str
    transaction_type: str
    units: float
    price: float
    amount: float
    description: Optional[str] = None

class PortfolioHolding(BaseModel):
    """Schema for a portfolio holding"""
    symbol: str
    security_type: str
    units: float
    last_price: float
    market_value: float
    cost_basis: float
    unrealized_gain_loss: float
    weight: float

class GainLoss(BaseModel):
    """Schema for gain/loss analysis"""
    total_value: float
    total_cost: float
    total_gain_loss: float
    realized_gain_loss: float
    unrealized_gain_loss: float
    dividend_income: float
    option_income: float
    total_return_percent: float

class ChartData(BaseModel):
    """Schema for chart data"""
    chart_type: str = Field(..., description="Type of chart (e.g., 'pie', 'line', 'bar')")
    data: str = Field(..., description="JSON string containing chart data")
    title: str
    last_update: datetime

class UserSettingsBase(BaseModel):
    """Base schema for user settings"""
    target_weights: Dict[str, float] = Field(
        default_factory=dict,
        description="Target portfolio weights as {symbol: weight}"
    )

class UserSettings(UserSettingsBase):
    """Schema for user settings with additional fields"""
    id: int
    rebalance_threshold: float = Field(
        default=5.0,
        description="Threshold (in percent) for rebalancing alerts"
    )
    last_update: datetime

class PortfolioSettings(UserSettingsBase):
    """Schema for portfolio settings response"""
    pass

class UploadResponse(BaseModel):
    """Schema for file upload response"""
    message: str
    files_processed: int
    total_transactions: int 