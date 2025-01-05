from fastapi import APIRouter, HTTPException, Depends
from ..schemas import PortfolioHolding, GainLoss, ChartData
from ..utils.finance_utils import FinanceCalculator
from typing import List, Dict
from datetime import datetime, date
import json
import pandas as pd
from ..dependencies import get_current_user
from ..models import User, Transaction as DBTransaction
from sqlalchemy.orm import Session
from ..database import get_db
import logging

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["portfolio"]
)

@router.get("/holdings", response_model=List[PortfolioHolding])
async def get_holdings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current portfolio holdings"""
    try:
        # First get the user by user_id
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        if not user:
            logger.warning(f"User not found: {current_user.user_id}")
            return []

        transactions = db.query(DBTransaction).filter(
            DBTransaction.user_id == user.id
        ).all()
        
        if not transactions:
            return []
            
        # Convert to DataFrame and ensure date type consistency
        df = pd.DataFrame([{
            'date': t.date.isoformat() if isinstance(t.date, (date, datetime)) else t.date,
            'transaction_type': t.transaction_type,
            'stock': t.stock,
            'units': float(t.units) if t.units else 0.0,
            'price': float(t.price) if t.price else 0.0,
            'fee': float(t.fee) if t.fee else 0.0,
            'option_type': t.option_type,
            'security_type': t.security_type,
            'amount': t.amount 
        } for t in transactions])
        
        calculator = FinanceCalculator()
        holdings = calculator.calculate_stock_holdings(df)
        
        return [
            PortfolioHolding(
                symbol=str(symbol),
                security_type=str(data.get("security_type", "")),
                units=float(data.get("units", 0)),
                last_price=float(data.get("last_price", 0)),
                market_value=float(data.get("market_value", 0)),
                cost_basis=float(data.get("cost_basis", 0)),
                unrealized_gain_loss=float(data.get("unrealized_gain_loss", 0)),
                weight=float(data.get("weight", 0))
            )
            for symbol, data in holdings.items()
        ]
    except Exception as e:
        logger.error(f"Error in get_holdings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch holdings: {str(e)}"
        )

@router.get("/gain-loss", response_model=Dict[str, GainLoss])
async def get_gain_loss(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio gain/loss analysis"""
    try:
        # First get the user by user_id
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        if not user:
            logger.warning(f"User not found: {current_user.user_id}")
            return {}

        transactions = db.query(DBTransaction).filter(
            DBTransaction.user_id == user.id
        ).all()
        
        if not transactions:
            return {}
            
        # Convert to DataFrame like in holdings endpoint
        df = pd.DataFrame([{
            'date': t.date.isoformat() if isinstance(t.date, (date, datetime)) else t.date,
            'transaction_type': t.transaction_type,
            'stock': t.stock,
            'units': float(t.units) if t.units else 0.0,
            'price': float(t.price) if t.price else 0.0,
            'fee': float(t.fee) if t.fee else 0.0,
            'option_type': t.option_type,
            'security_type': t.security_type,
            'amount': t.amount
        } for t in transactions])
            
        calculator = FinanceCalculator()
        return calculator.calculate_gain_loss(df)
        
    except Exception as e:
        logger.error(f"Error in get_gain_loss: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch gain/loss data: {str(e)}"
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