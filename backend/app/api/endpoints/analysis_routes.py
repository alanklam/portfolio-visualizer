from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.user_model import User
from ...models.transaction_model import Transaction, Portfolio
from ...schemas.data_schema import PortfolioHolding, GainLossDetail, ChartData, PerformanceData
from ...services.analysis_service import FinanceCalculator
from ..dependencies import get_current_user
from datetime import datetime, timedelta
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
    """Get current portfolio holdings, todo: cache for 1 minute"""
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
        
        # Update portfolio table
        existing_portfolios = {
            p.stock: p for p in db.query(Portfolio).filter(
                Portfolio.user_id == current_user.id
            ).all()
        }
        
        # Update or create portfolio entries
        for symbol, data in holdings.items():
            if symbol in existing_portfolios:
                portfolio = existing_portfolios[symbol]
                portfolio.total_units = data['units']
                portfolio.average_cost = data['cost_basis'] / data['units'] if data['units'] > 0 else 0
                portfolio.current_price = data['last_price']
                portfolio.last_updated = datetime.now().date()
            else:
                portfolio = Portfolio(
                    user_id=current_user.id,
                    stock=symbol,
                    total_units=data['units'],
                    average_cost=data['cost_basis'] / data['units'] if data['units'] > 0 else 0,
                    current_price=data['last_price'],
                    last_updated=datetime.now().date()
                )
                db.add(portfolio)
        
        try:
            db.commit()
        except Exception as e:
            logger.error(f"Error updating portfolio: {str(e)}")
            db.rollback()
            
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
        if holdings:
            data = {
                "values": [holding.get("market_value", 0) for holding in holdings.values()],
                "labels": list(holdings.keys())
            }
        else:
            data = {
                "values": [],
                "labels": []
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

@router.get("/annual-returns", response_model=dict)
async def get_annual_returns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get annual returns data for the portfolio"""
    try:
        transactions = db.query(Transaction).filter(
            Transaction.user_id == current_user.id
        ).all()
        
        if not transactions:
            return {
                "annual_returns": []
            }
        
        # Convert to DataFrame
        df = pd.DataFrame([{
            'date': t.date.isoformat() if isinstance(t.date, datetime) else t.date,
            'transaction_type': t.transaction_type,
            'stock': t.stock,
            'units': float(t.units) if t.units else 0.0,
            'price': float(t.price) if t.price else 0.0,
            'fee': float(t.fee) if t.fee else 0.0,
            'security_type': t.security_type,
            'amount': t.amount
        } for t in transactions])
        
        calculator = FinanceCalculator()
        
        # Get min and max years from transactions
        df['year'] = pd.to_datetime(df['date']).dt.year
        min_date = df['date'].min() + timedelta(days=7) #add 7 days to avoid empty account
        max_date = df['date'].max()
        start_year = df['year'].min()
        end_year = df['year'].max()
        
        annual_returns = []
        
        for year in range(start_year, end_year + 1):
            start_date = max(datetime(year, 1, 1).date(), min_date)
            end_date = min(datetime(year, 12, 31).date(), max_date)
            
            # Calculate holdings at start and end of year
            price_data1 = calculator.calculate_stock_holdings_batch(df, start_date=start_date - timedelta(days=5), end_date=start_date)
            last_date = sorted(price_data1.keys())[-1]
            start_holdings = price_data1[last_date]
            price_data2 = calculator.calculate_stock_holdings_batch(df, start_date=end_date - timedelta(days=5), end_date=end_date)
            last_date = sorted(price_data2.keys())[-1]
            end_holdings = price_data2[last_date]

            # print("start:", start_holdings)
            # print("end:", end_holdings)
            # Calculate total portfolio values
            start_value = sum(holding['market_value'] for holding in start_holdings.values())
            end_value = sum(holding['market_value'] for holding in end_holdings.values())
            
            # Calculate year return in dollar value
            year_return = end_value - start_value
            
            annual_returns.append({
                'year': year,
                'return': year_return
            })
        
        return {
            "annual_returns": annual_returns
        }
    
    except Exception as e:
        logger.error(f"Error in get_annual_returns: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch annual returns data: {str(e)}"
        )
