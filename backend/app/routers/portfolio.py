from fastapi import APIRouter, HTTPException
from ..schemas import PortfolioHolding, GainLoss, ChartData
from ..utils.finance_utils import FinanceCalculator
from typing import List
from datetime import datetime
import json

router = APIRouter(
    tags=["portfolio"]
)

@router.get("/holdings", response_model=List[PortfolioHolding])
async def get_holdings():
    """Get current portfolio holdings"""
    try:
        calculator = FinanceCalculator()
        holdings = calculator.calculate_stock_holdings()
        return [
            PortfolioHolding(
                symbol=symbol,
                security_type=data["security_type"],
                units=data["units"],
                last_price=data["last_price"],
                market_value=data["market_value"],
                cost_basis=data["cost_basis"],
                unrealized_gain_loss=data["unrealized_gain_loss"],
                weight=data["weight"]
            )
            for symbol, data in holdings.items()
        ]
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch holdings: {str(e)}"
        )

@router.get("/gain-loss", response_model=GainLoss)
async def get_gain_loss():
    """Get portfolio gain/loss analysis"""
    try:
        calculator = FinanceCalculator()
        return calculator.calculate_gain_loss()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to calculate gain/loss: {str(e)}"
        )

@router.get("/allocation", response_model=ChartData)
async def get_allocation():
    """Get portfolio allocation chart data"""
    try:
        calculator = FinanceCalculator()
        holdings = calculator.calculate_stock_holdings()
        
        # Prepare data for pie chart
        data = {
            "values": [holding["market_value"] for holding in holdings.values()],
            "labels": list(holdings.keys())
        }
        
        return ChartData(
            chart_type="pie",
            data=json.dumps(data),
            title="Portfolio Allocation",
            last_update=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get allocation data: {str(e)}"
        )

@router.get("/performance", response_model=ChartData)
async def get_performance(timeframe: str = "1Y"):
    """Get portfolio performance chart data"""
    try:
        calculator = FinanceCalculator()
        performance_data = calculator.calculate_performance(timeframe)
        
        return ChartData(
            chart_type="line",
            data=json.dumps(performance_data),
            title="Portfolio Performance",
            last_update=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance data: {str(e)}"
        )

@router.get("/annual-returns", response_model=ChartData)
async def get_annual_returns():
    """Get annual returns chart data"""
    try:
        calculator = FinanceCalculator()
        returns_data = calculator.calculate_annual_returns()
        
        return ChartData(
            chart_type="bar",
            data=json.dumps(returns_data),
            title="Annual Returns",
            last_update=datetime.now()
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get annual returns data: {str(e)}"
        ) 