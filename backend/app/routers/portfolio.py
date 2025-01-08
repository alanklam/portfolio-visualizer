from fastapi import APIRouter, HTTPException, Depends
from ..schemas import PortfolioHolding, GainLoss, ChartData
from ..utils.finance_utils import FinanceCalculator
from typing import List, Dict
from datetime import datetime, date, timedelta
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
async def get_allocation(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio allocation chart data"""
    try:
        # First get the user by user_id
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        if not user:
            logger.warning(f"User not found: {current_user.user_id}")
            return ChartData(
                chart_type="pie",
                data=json.dumps({"values": [], "labels": []}),
                title="Portfolio Allocation",
                last_update=datetime.now()
            )

        transactions = db.query(DBTransaction).filter(
            DBTransaction.user_id == user.id
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

@router.get("/performance", response_model=ChartData)
async def get_performance(
    timeframe: str = "1Y",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get portfolio performance chart data"""
    try:
        # First get the user by user_id
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        if not user:
            logger.warning(f"User not found: {current_user.user_id}")
            return ChartData(
                chart_type="line",
                data=json.dumps({"dates": [], "portfolio_value": [], "invested_amount": []}),
                title="Portfolio Performance",
                last_update=datetime.now()
            )

        transactions = db.query(DBTransaction).filter(
            DBTransaction.user_id == user.id
        ).all()
        
        if not transactions:
            return ChartData(
                chart_type="line",
                data=json.dumps({"dates": [], "portfolio_value": [], "invested_amount": []}),
                title="Portfolio Performance",
                last_update=datetime.now()
            )
            
        # Convert to DataFrame
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
        
        # Get start date based on timeframe
        today = date.today()
        if timeframe == "1M":
            start_date = today - timedelta(days=30)
        elif timeframe == "3M":
            start_date = today - timedelta(days=90)
        elif timeframe == "6M":
            start_date = today - timedelta(days=180)
        elif timeframe == "1Y":
            start_date = today - timedelta(days=365)
        elif timeframe == "ALL":
            start_date = df['date'].min()
        else:
            start_date = today - timedelta(days=365)  # Default to 1Y
            
        # Filter transactions by date
        df['date'] = pd.to_datetime(df['date']).dt.date
        df_filtered = df[df['date'] >= start_date]
        
        # Calculate daily portfolio value and invested amount
        dates = pd.date_range(start=start_date, end=today)
        portfolio_values = []
        invested_amounts = []
        
        for current_date in dates:
            current_date = current_date.date()
            # Get transactions up to current date
            transactions_to_date = df[df['date'] <= current_date]
            if not transactions_to_date.empty:
                # Calculate holdings as of this date
                holdings = calculator.calculate_stock_holdings(transactions_to_date, current_date)
                # Sum up market values
                portfolio_value = sum(holding['market_value'] for holding in holdings.values())
                # Sum up invested amount (deposits - withdrawals)
                invested_amount = sum(
                    row['amount'] if row['transaction_type'] == 'transfer' else 0
                    for _, row in transactions_to_date.iterrows()
                )
                
                portfolio_values.append(float(portfolio_value))
                invested_amounts.append(float(invested_amount))
            else:
                portfolio_values.append(0.0)
                invested_amounts.append(0.0)
        
        performance_data = {
            "dates": [d.strftime('%Y-%m-%d') for d in dates],
            "portfolio_value": portfolio_values,
            "invested_amount": invested_amounts
        }
        
        return ChartData(
            chart_type="line",
            data=json.dumps(performance_data),
            title="Portfolio Performance",
            last_update=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error in get_performance: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get performance data: {str(e)}"
        )

@router.get("/annual-returns", response_model=ChartData)
async def get_annual_returns(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get annual returns chart data"""
    try:
        # First get the user by user_id
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        if not user:
            logger.warning(f"User not found: {current_user.user_id}")
            return ChartData(
                chart_type="bar",
                data=json.dumps({"years": [], "returns": []}),
                title="Annual Returns",
                last_update=datetime.now()
            )

        transactions = db.query(DBTransaction).filter(
            DBTransaction.user_id == user.id
        ).all()
        
        if not transactions:
            return ChartData(
                chart_type="bar",
                data=json.dumps({"years": [], "returns": []}),
                title="Annual Returns",
                last_update=datetime.now()
            )
            
        # Convert to DataFrame
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
        
        # Convert dates to datetime
        df['date'] = pd.to_datetime(df['date'])
        
        # Get unique years in the data
        years = sorted(df['date'].dt.year.unique())
        annual_returns = []
        
        for year in years:
            year_start = date(year, 1, 1)
            year_end = date(year, 12, 31)
            
            # Get transactions up to year start and year end
            txns_to_start = df[df['date'].dt.date < year_start]
            txns_to_end = df[df['date'].dt.date <= year_end]
            
            # Calculate portfolio value at start and end of year
            if txns_to_start.empty:
                start_value = 0
            else:
                holdings_start = calculator.calculate_stock_holdings(txns_to_start, year_start)
                start_value = sum(holding['market_value'] for holding in holdings_start.values())
            
            if txns_to_end.empty:
                end_value = 0
            else:
                holdings_end = calculator.calculate_stock_holdings(txns_to_end, year_end)
                end_value = sum(holding['market_value'] for holding in holdings_end.values())
            
            # Calculate net investment for the year
            year_deposits = df[
                (df['date'].dt.date >= year_start) & 
                (df['date'].dt.date <= year_end) & 
                (df['transaction_type'] == 'transfer')
            ]['amount'].sum()
            
            # Calculate return
            if start_value + year_deposits > 0:
                year_return = ((end_value - (start_value + year_deposits)) / (start_value + year_deposits)) * 100
            else:
                year_return = 0 if end_value == 0 else 100
            
            annual_returns.append(float(year_return))
        
        returns_data = {
            "years": [str(year) for year in years],
            "returns": annual_returns
        }
        
        return ChartData(
            chart_type="bar",
            data=json.dumps(returns_data),
            title="Annual Returns",
            last_update=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error in get_annual_returns: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get annual returns data: {str(e)}"
        ) 