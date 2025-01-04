from fastapi import APIRouter, HTTPException
from ..schemas import Portfolio, Transaction, PortfolioStats, ChartData
from ..utils.finance_utils import FinanceCalculator
from typing import List, Dict, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/holdings")
async def get_holdings() -> List[Portfolio]:
    """Get current portfolio holdings"""
    pass

@router.get("/allocation", response_model=ChartData)
async def get_portfolio_allocation(current_only: bool = True) -> ChartData:
    """Get portfolio allocation data for pie chart"""
    try:
        # TODO: Get transactions from database
        transactions = pd.DataFrame()  # Placeholder until database integration
        
        # Calculate current holdings
        holdings = FinanceCalculator.calculate_stock_holdings(transactions)
        
        # Calculate weights
        weights = FinanceCalculator.calculate_portfolio_weights(holdings)
        
        # Create pie chart
        fig = px.pie(
            values=list(weights.values()),
            names=list(weights.keys()),
            title="Portfolio Allocation"
        )
        
        # Update layout for interactivity
        fig.update_traces(
            hoverinfo='label+percent',
            textinfo='value+percent'
        )
        
        return ChartData(
            chart_type="pie",
            data=fig.to_json(),
            title="Portfolio Allocation",
            last_update=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/performance", response_model=ChartData)
async def get_performance_chart(
    timeframe: str = "1Y",
    include_dividends: bool = True
) -> ChartData:
    """Get portfolio performance data for line chart"""
    try:
        # TODO: Get transactions from database
        transactions = pd.DataFrame()  # Placeholder until database integration
        
        # Calculate date range
        end_date = datetime.now()
        if timeframe == "1M":
            start_date = end_date - timedelta(days=30)
        elif timeframe == "3M":
            start_date = end_date - timedelta(days=90)
        elif timeframe == "6M":
            start_date = end_date - timedelta(days=180)
        elif timeframe == "1Y":
            start_date = end_date - timedelta(days=365)
        elif timeframe == "ALL":
            start_date = transactions['date'].min() if not transactions.empty else end_date
        else:
            start_date = end_date - timedelta(days=365)  # Default to 1Y
        
        # Filter transactions by date range
        filtered_txns = transactions[
            (transactions['date'] >= start_date) & 
            (transactions['date'] <= end_date)
        ]
        
        # Calculate daily portfolio values
        date_range = pd.date_range(start=start_date, end=end_date, freq='D')
        portfolio_values = []
        cost_basis_values = []
        
        for date in date_range:
            holdings = FinanceCalculator.calculate_stock_holdings(filtered_txns, date)
            gain_loss = FinanceCalculator.calculate_gain_loss(filtered_txns, None)
            
            # Calculate total portfolio value and cost basis for this date
            total_value = sum(
                holding['units'] * holding['last_price']
                for holding in holdings.values()
            )
            total_cost = sum(
                info['adjusted_cost_basis']
                for info in gain_loss.values()
                if info['last_update'] <= date
            )
            
            portfolio_values.append(total_value)
            cost_basis_values.append(total_cost)
        
        # Create line chart
        fig = go.Figure()
        
        # Add portfolio value line
        fig.add_trace(go.Scatter(
            x=date_range,
            y=portfolio_values,
            mode='lines',
            name='Portfolio Value',
            line=dict(color='blue')
        ))
        
        # Add cost basis line
        fig.add_trace(go.Scatter(
            x=date_range,
            y=cost_basis_values,
            mode='lines',
            name='Adjusted Cost Basis',
            line=dict(color='red', dash='dash')
        ))
        
        # Update layout
        fig.update_layout(
            title="Portfolio Performance",
            xaxis_title="Date",
            yaxis_title="Value ($)",
            hovermode='x unified'
        )
        
        return ChartData(
            chart_type="line",
            data=fig.to_json(),
            title="Portfolio Performance",
            last_update=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/annual-returns", response_model=ChartData)
async def get_annual_returns() -> ChartData:
    """Get annualized returns data for bar chart"""
    try:
        # TODO: Get transactions from database
        transactions = pd.DataFrame()  # Placeholder until database integration
        
        # Calculate gain/loss for all positions
        gain_loss = FinanceCalculator.calculate_gain_loss(transactions)
        
        # Group by year and calculate annual returns
        annual_returns = {}
        for symbol, info in gain_loss.items():
            year = info['last_update'].year
            if year not in annual_returns:
                annual_returns[year] = 0
            
            # Add total return for this position to the year
            annual_returns[year] += info['total_return_pct']
        
        # Create bar chart
        fig = go.Figure(data=[
            go.Bar(
                x=list(annual_returns.keys()),
                y=list(annual_returns.values()),
                text=[f"{val:.1f}%" for val in annual_returns.values()],
                textposition='auto'
            )
        ])
        
        # Update layout
        fig.update_layout(
            title="Annual Portfolio Returns",
            xaxis_title="Year",
            yaxis_title="Return (%)",
            showlegend=False
        )
        
        return ChartData(
            chart_type="bar",
            data=fig.to_json(),
            title="Annual Portfolio Returns",
            last_update=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stats", response_model=PortfolioStats)
async def get_portfolio_stats() -> PortfolioStats:
    """Get overall portfolio statistics"""
    try:
        # TODO: Get transactions from database
        transactions = pd.DataFrame()  # Placeholder until database integration
        
        # Calculate current holdings and gain/loss
        holdings = FinanceCalculator.calculate_stock_holdings(transactions)
        gain_loss = FinanceCalculator.calculate_gain_loss(transactions)
        
        # Calculate total portfolio value
        total_value = sum(
            holding['units'] * holding['last_price']
            for holding in holdings.values()
        )
        
        # Calculate total returns
        total_return = sum(
            info['total_return']
            for info in gain_loss.values()
        )
        
        # Calculate total cost basis
        total_cost = sum(
            info['total_cost_basis']
            for info in gain_loss.values()
        )
        
        return PortfolioStats(
            total_value=total_value,
            total_return=total_return,
            total_return_pct=(total_return / total_cost * 100) if total_cost > 0 else 0,
            num_positions=len(holdings),
            last_update=datetime.now()
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/transactions")
async def get_transactions() -> List[Transaction]:
    """Get all transactions"""
    pass

@router.get("/analysis")
async def get_portfolio_analysis():
    """Get portfolio analysis including weights and recommendations"""
    pass 