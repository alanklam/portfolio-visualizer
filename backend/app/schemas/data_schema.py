from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Dict, Any, List

class PortfolioHolding(BaseModel):
    symbol: str
    security_type: str
    units: float
    last_price: float
    market_value: float
    cost_basis: float
    unrealized_gain_loss: float
    weight: float

class GainLossDetail(BaseModel):
    current_units: float
    market_value: float
    total_cost_basis: float
    adjusted_cost_basis: float
    realized_gain_loss: float
    unrealized_gain_loss: float
    unrealized_gain_loss_pct: float
    dividend_income: float
    option_gain_loss: float
    total_return: float
    total_return_pct: float
    last_price: float
    last_update: datetime

class ChartData(BaseModel):
    chart_type: str
    data: str  # JSON string
    title: str
    last_update: datetime

class PerformanceMetrics(BaseModel):
    annualized_return: float
    volatility: float
    sharpe_ratio: float

class PerformanceData(BaseModel):
    dates: List[str]
    portfolio_values: List[float]
    invested_amounts: List[float]
    metrics: Optional[PerformanceMetrics] 