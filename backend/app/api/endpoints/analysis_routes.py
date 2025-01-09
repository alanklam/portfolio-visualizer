from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.user_model import User
from ...models.transaction_model import Transaction, UserSettings
from ...schemas.data_schema import PortfolioHolding, GainLossDetail, ChartData, PerformanceData
from ...services.analysis_service import FinanceCalculator
from ..dependencies import get_current_user
from datetime import datetime
import pandas as pd
import json
import logging
from typing import Dict

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/holdings", response_model=list[PortfolioHolding])
async def get_holdings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current portfolio holdings"""
    try:
        transactions = db.query(Transaction).filter(
            Transaction.user_id == current_user.id
        ).all()
        
        if not transactions:
            return []
            
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.date.isoformat() if isinstance(t.date, datetime) else t.date,
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

@router.get("/gain-loss", response_model=Dict[str, GainLossDetail])
async def get_gain_loss(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio gain/loss analysis"""
    try:
        transactions = db.query(Transaction).filter(
            Transaction.user_id == current_user.id
        ).all()
        
        if not transactions:
            return {}
            
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.date.isoformat() if isinstance(t.date, datetime) else t.date,
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
async def get_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio allocation chart data"""
    try:
        transactions = db.query(Transaction).filter(
            Transaction.user_id == current_user.id
        ).all()
        
        if not transactions:
            return ChartData(
                chart_type="pie",
                data=json.dumps({"values": [], "labels": []}),
                title="Portfolio Allocation",
                last_update=datetime.now()
            )
            
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.date.isoformat() if isinstance(t.date, datetime) else t.date,
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
        logger.error(f"Error in get_allocation: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get allocation data: {str(e)}"
        )

@router.get("/performance", response_model=PerformanceData)
async def get_performance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio performance metrics and chart data"""
    try:
        transactions = db.query(Transaction).filter(
            Transaction.user_id == current_user.id
        ).all()
        
        if not transactions:
            return PerformanceData(
                dates=[],
                portfolio_values=[],
                invested_amounts=[],
                metrics=None
            )
            
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.date.isoformat() if isinstance(t.date, datetime) else t.date,
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
        return calculator.calculate_performance(df)
        
    except Exception as e:
        logger.error(f"Error in get_performance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch performance data: {str(e)}"
        )

@router.get("/settings")
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's portfolio target weights"""
    try:
        settings = db.query(UserSettings).filter(
            UserSettings.user_id == current_user.id
        ).all()
        
        return {
            "target_weights": {
                s.stock: s.target_weight
                for s in settings
            }
        }
    except Exception as e:
        logger.error(f"Error in get_settings: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch settings: {str(e)}"
        )

@router.post("/settings")
async def update_settings(
    weights: Dict[str, float],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update user's portfolio target weights"""
    try:
        # Delete existing settings
        db.query(UserSettings).filter(
            UserSettings.user_id == current_user.id
        ).delete()
        
        # Add new settings
        for stock, weight in weights.items():
            setting = UserSettings(
                user_id=current_user.id,
                stock=stock,
                target_weight=weight
            )
            db.add(setting)
            
        db.commit()
        return {"message": "Settings updated successfully"}
    except Exception as e:
        logger.error(f"Error in update_settings: {str(e)}")
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        ) 