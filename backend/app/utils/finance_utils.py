from typing import Dict, List, Optional, Any
import pandas as pd
from datetime import datetime, timedelta, date
import yfinance as yf
import warnings

class FinanceCalculator:
    """Utility class for financial calculations"""
    
    POSITION_AFFECTING_TYPES = {
        'buy': 1,           # Regular buy
        'sell': -1,         # Regular sell
        'reinvest': 1,      # Dividend reinvestment
        'split': 1,         # Stock split (units will be additional shares)
        'transfer': 1       # Transfer in (positive units) or out (negative units)
    }
    
    @staticmethod
    def calculate_stock_holdings(transactions: pd.DataFrame, as_of_date: date = None) -> Dict[str, Dict[str, float]]:
        """Calculate current stock holdings based on transaction history."""
        if transactions.empty:
            return {}
        
        if as_of_date is None:
            as_of_date = datetime.now().date()
        
        # Filter transactions up to as_of_date
        transactions = transactions[pd.to_datetime(transactions['date']).dt.date <= as_of_date].copy()
        
        holdings = {}
        total_market_value = 0.0
        
        # Initialize cash position
        holdings['CASH EQUIVALENTS'] = {
            'units': 0.0,
            'security_type': 'cash',
            'cost_basis': 0.0,
            'last_price': 1.0,  # Cash is always $1
            'last_update': as_of_date
        }
        
        # Process transactions in chronological order
        for _, txn in transactions.sort_values('date').iterrows():
            symbol = txn['stock']
            
            # Initialize holding if not exists
            if symbol not in holdings and symbol != 'CASH EQUIVALENTS':
                holdings[symbol] = {
                    'units': 0.0,
                    'security_type': txn['security_type'],
                    'cost_basis': 0.0,
                    'last_price': 0.0,
                    'last_update': txn['date']
                }
            
            # Update units and cost basis based on transaction type
            if txn['transaction_type'] in ['buy', 'reinvest']:
                # Add units and cost basis for the security
                if pd.notna(txn['units']) and pd.notna(txn['price']):
                    holdings[symbol]['units'] += txn['units']
                    holdings[symbol]['cost_basis'] += (txn['units'] * txn['price'] + txn['fee'])
                    
                # Subtract the amount from cash position
                total_cost = abs(txn['amount']) if pd.notna(txn['amount']) else (txn['units'] * txn['price'] + txn['fee'])
                holdings['CASH EQUIVALENTS']['units'] -= total_cost
                
            elif txn['transaction_type'] == 'sell':
                if pd.notna(txn['units']) and pd.notna(txn['price']):
                    # Calculate the portion of cost basis to remove
                    if holdings[symbol]['units'] > 0:
                        cost_per_unit = holdings[symbol]['cost_basis'] / holdings[symbol]['units']
                        holdings[symbol]['cost_basis'] -= (txn['units'] * cost_per_unit)
                    holdings[symbol]['units'] -= txn['units']
                    
                # Add the proceeds to cash position
                proceeds = abs(txn['amount']) if pd.notna(txn['amount']) else (txn['units'] * txn['price'] - txn['fee'])
                holdings['CASH EQUIVALENTS']['units'] += proceeds
                
            elif txn['transaction_type'] == 'transfer':
                # Handle cash transfers
                if txn['security_type'] == 'cash':
                    holdings['CASH EQUIVALENTS']['units'] += txn['amount'] if pd.notna(txn['amount']) else txn['units']
                
            elif txn['transaction_type'] == 'dividend':
                if not txn['transaction_type'] == 'reinvest':  # Only for non-reinvested dividends
                    holdings['CASH EQUIVALENTS']['units'] += abs(txn['amount']) if pd.notna(txn['amount']) else txn['units']
                
            elif txn['transaction_type'] == 'interest':
                holdings['CASH EQUIVALENTS']['units'] += abs(txn['amount']) if pd.notna(txn['amount']) else txn['units']
            
            # Handle option transactions
            elif txn['transaction_type'] in ['sell_to_open', 'sell_to_close', 'buy_to_open', 'buy_to_close']:
                # Option premium received/paid affects cash position
                premium = abs(txn['amount']) if pd.notna(txn['amount']) else (txn['units'] * txn['price'] - txn['fee'])
                if txn['transaction_type'] in ['sell_to_open', 'sell_to_close']:  # Receiving premium
                    holdings['CASH EQUIVALENTS']['units'] += premium
                else:  # buy_to_close, buy_to_open - Paying premium
                    holdings['CASH EQUIVALENTS']['units'] -= premium
            
            # Update last price for non-cash securities
            if symbol not in ['CASH EQUIVALENTS', 'FIXED INCOME'] and holdings[symbol]['units'] > 0:
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        ticker = yf.download(symbol, start=as_of_date - timedelta(days=5), end=as_of_date + timedelta(days=1), progress=False)
                    if not ticker.empty:
                        holdings[symbol]['last_price'] = ticker['Close'].iloc[-1]
                        holdings[symbol]['last_update'] = ticker.index[-1]
                except Exception as e:
                    print(f"Failed to fetch price for {symbol}: {str(e)}")
        
        # Update cash position cost basis
        holdings['CASH EQUIVALENTS']['cost_basis'] = holdings['CASH EQUIVALENTS']['units']
        
        # Remove positions with zero units
        holdings = {k: v for k, v in holdings.items() if v['units'] != 0 or k == 'CASH EQUIVALENTS'}
        
        # Calculate total market value for weight calculation
        for symbol, data in holdings.items():
            market_value = float(data['units']) * float(data['last_price'])
            total_market_value += market_value
            data['market_value'] = market_value
        
        # Add weight to each holding
        for data in holdings.values():
            data['weight'] = (data['market_value'] / total_market_value) if total_market_value > 0 else 0.0
            
            # Ensure all numeric values are float
            for key in ['units', 'cost_basis', 'last_price', 'market_value', 'weight']:
                data[key] = float(data[key])
        
        return holdings
    
    @staticmethod
    def calculate_portfolio_weights(holdings: Dict[str, Dict[str, Any]]) -> Dict[str, float]:
        """
        Calculate current portfolio weights based on holdings.
        
        Args:
            holdings: Dictionary of current holdings
        
        Returns:
            Dictionary with stock symbols as keys and their weights as values
        """
        total_value = sum(
            holding['units'] * holding['last_price']
            for holding in holdings.values()
        )
        
        if total_value == 0:
            return {}
        
        weights = {
            symbol: (holding['units'] * holding['last_price'] / total_value)
            for symbol, holding in holdings.items()
        }
        
        return weights
    
    @staticmethod
    def get_rebalancing_trades(
        holdings: Dict[str, Dict],
        target_weights: Dict[str, float],
        total_value: Optional[float] = None
    ) -> List[Dict]:
        """
        Calculate trades needed to achieve target portfolio weights.
        
        Args:
            holdings: Dictionary of current holdings
            target_weights: Dictionary of target weights for each symbol
            total_value: Optional total portfolio value (if None, will be calculated from holdings)
        
        Returns:
            List of trades needed to rebalance the portfolio
        """
        if total_value is None:
            total_value = sum(
                holding['units'] * holding['last_price']
                for holding in holdings.values()
            )
        
        if total_value == 0:
            return []
        
        current_weights = FinanceCalculator.calculate_portfolio_weights(holdings)
        trades = []
        
        # Calculate required trades for each symbol
        for symbol, target_weight in target_weights.items():
            current_weight = current_weights.get(symbol, 0)
            current_holding = holdings.get(symbol, {'units': 0, 'last_price': 0})
            
            # Calculate target value and current value
            target_value = total_value * target_weight
            current_value = current_holding['units'] * current_holding['last_price']
            
            # Calculate trade size
            value_difference = target_value - current_value
            if abs(value_difference) > 1:  # Use a small threshold to avoid tiny trades
                price = current_holding['last_price']
                if price > 0:
                    units = value_difference / price
                    trades.append({
                        'symbol': symbol,
                        'units': units,
                        'price': price,
                        'action': 'buy' if units > 0 else 'sell'
                    })
        
        return trades
    
    @staticmethod
    def update_holdings_prices(holdings: Dict[str, Dict]) -> Dict[str, Dict]:
        """
        Update holdings with current market prices from Yahoo Finance.
        
        Args:
            holdings: Dictionary of current holdings
        
        Returns:
            Updated holdings dictionary with current prices
        """
        # Get unique symbols excluding cash and fixed income
        symbols = [
            symbol for symbol, holding in holdings.items()
            if holding['security_type'] not in ['cash', 'fixed_income']
        ]
        
        if not symbols:
            return holdings
        
        # Fetch current prices
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                current_prices = yf.download(symbols, period='1d')['Close']
                if len(symbols) == 1:
                    current_prices = pd.Series({symbols[0]: current_prices[-1]})
                else:
                    current_prices = current_prices.iloc[-1]
        except Exception as e:
            print(f"Error fetching prices: {str(e)}")
            return holdings
        
        # Update holdings with current prices
        for symbol, price in current_prices.items():
            if symbol in holdings and pd.notna(price):
                holdings[symbol]['last_price'] = price
                holdings[symbol]['last_update'] = datetime.now()
        
        return holdings
    
    @staticmethod
    def calculate_gain_loss(transactions: pd.DataFrame, current_prices: Dict[str, float] = None) -> Dict[str, Dict[str, Any]]:
        """
        Calculate realized and unrealized gains/losses for all positions.
        
        Args:
            transactions: DataFrame with standardized transaction data
            current_prices: Optional dictionary of current market prices
        
        Returns:
            Dictionary containing gain/loss information for each symbol
        """
        # Get current holdings first
        holdings = FinanceCalculator.calculate_stock_holdings(transactions)
        
        # Initialize gain/loss tracking for each symbol
        gain_loss = {}
        
        # Process each symbol
        for symbol in set(transactions['stock'].unique()):
            symbol_txns = transactions[transactions['stock'] == symbol].sort_values('date')
            
            # Initialize tracking variables
            running_units = 0
            total_cost_basis = 0
            realized_gain_loss = 0
            dividend_income = 0
            option_gain_loss = 0
            
            # Process each transaction
            for _, txn in symbol_txns.iterrows():
                if txn['transaction_type'] in ['buy', 'reinvest']:
                    running_units += txn['units']
                    total_cost_basis += (txn['units'] * txn['price'] + txn['fee'])
                
                elif txn['transaction_type'] == 'sell':
                    if running_units > 0:
                        # Calculate cost basis per unit
                        cost_per_unit = total_cost_basis / running_units
                        # Calculate realized gain/loss
                        realized_gain_loss += (txn['units'] * (txn['price'] - cost_per_unit) - txn['fee'])
                        # Adjust cost basis
                        total_cost_basis -= (txn['units'] * cost_per_unit)
                        running_units -= txn['units']
                
                elif txn['transaction_type'] == 'dividend' and not txn['transaction_type'] == 'reinvest':
                    dividend_income += abs(txn['amount']) if pd.notna(txn['amount']) else txn['units']
                
                elif txn['transaction_type'] in ['sell_to_open', 'sell_to_close', 'buy_to_open', 'buy_to_close']:
                    premium = abs(txn['amount']) if pd.notna(txn['amount']) else (txn['units'] * txn['price'] - txn['fee'])
                    if txn['transaction_type'] in ['sell_to_open', 'sell_to_close']:  # Credit transactions
                        option_gain_loss += premium
                    else:  # buy_to_close, buy_to_open - Debit transactions
                        option_gain_loss -= premium
            
            # Get current holding information
            current_holding = holdings.get(symbol, {
                'units': 0,
                'last_price': 0,
                'last_update': datetime.now()
            })
            
            # Calculate unrealized gain/loss
            market_value = current_holding['units'] * current_holding['last_price']
            unrealized_gain_loss = market_value - total_cost_basis if current_holding['units'] > 0 else 0
            
            # For cash and fixed income, adjusted cost basis equals total cost basis
            adjusted_cost_basis = total_cost_basis
            if symbol not in ['CASH EQUIVALENTS', 'FIXED INCOME']:
                # For stocks, adjust cost basis based on realized gains/losses, dividends, and options
                adjusted_cost_basis = total_cost_basis - realized_gain_loss - dividend_income - option_gain_loss
            
            # Calculate total return
            total_return = realized_gain_loss + unrealized_gain_loss + dividend_income + option_gain_loss
            
            # Store results
            gain_loss[symbol] = {
                'current_units': current_holding['units'],
                'market_value': market_value,
                'total_cost_basis': total_cost_basis,
                'adjusted_cost_basis': adjusted_cost_basis,
                'realized_gain_loss': realized_gain_loss,
                'unrealized_gain_loss': unrealized_gain_loss,
                'unrealized_gain_loss_pct': (unrealized_gain_loss / total_cost_basis * 100) if total_cost_basis > 0 else 0,
                'dividend_income': dividend_income,
                'option_gain_loss': option_gain_loss,
                'total_return': total_return,
                'total_return_pct': (total_return / total_cost_basis * 100) if total_cost_basis > 0 else 0,
                'last_price': current_holding['last_price'],
                'last_update': current_holding['last_update']
            }
        
        return gain_loss 