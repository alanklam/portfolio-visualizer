import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import logging
from typing import Dict, List, Tuple
from .price_service import PriceManager
from .transaction_service import TransactionManager
from .metrics_service import MetricsCache

logger = logging.getLogger(__name__)

class HoldingsCache:
    """Cache for holdings calculations"""
    def __init__(self):
        self._cache = {}
        self._last_calc = {}
        self._calc_interval = timedelta(minutes=1)  # Cache holdings for 1 minute

    def get(self, key: Tuple[date, str]) -> dict:
        """Get cached holdings if not expired"""
        if key in self._cache and datetime.now() - self._last_calc[key] < self._calc_interval:
            return self._cache[key]
        return None

    def set(self, key: Tuple[date, str], value: dict):
        """Cache holdings calculation result"""
        self._cache[key] = value
        self._last_calc[key] = datetime.now()

    def clear(self):
        """Clear expired cache entries"""
        current_time = datetime.now()
        self._cache = {
            k: v for k, v in self._cache.items()
            if current_time - self._last_calc[k] < self._calc_interval
        }
        self._last_calc = {
            k: v for k, v in self._last_calc.items()
            if current_time - v < self._calc_interval
        }

class TransactionProcessor:
    """Process and optimize transaction calculations"""
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._process_transactions()

    def _process_transactions(self):
        """Pre-process transactions for faster lookup"""
        # Convert date column to datetime if not already
        self.df['date'] = pd.to_datetime(self.df['date'])
        # Sort transactions by date
        self.df = self.df.sort_values('date')
        # Create efficient date index
        self.df.set_index('date', inplace=True, drop=False)
        # Create symbol groups
        self.symbol_groups = self.df.groupby('stock')
        # Store unique symbols
        self.symbols = set(self.df['stock'].unique()) - {'CASH EQUIVALENTS'}

    def get_transactions_until(self, calc_date: date) -> pd.DataFrame:
        """Get transactions up to a specific date efficiently"""
        return self.df[self.df['date'].dt.date <= calc_date]

    def get_symbols_requiring_prices(self) -> List[str]:
        """Get list of symbols requiring price data"""
        return sorted(list(self.symbols - {'FIXED INCOME'}))

class FinanceCalculator:
    """Utility class for financial calculations"""
    
    POSITION_AFFECTING_TYPES = {
        'buy': 1,           # Regular buy
        'sell': -1,         # Regular sell
        'reinvest': 1,      # Dividend reinvestment
        'split': 1,         # Stock split
        'transfer': 1       # Transfer in/out
    }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.price_manager = PriceManager()  # Initialize price manager
        self.holdings_cache = HoldingsCache()
        self.transaction_manager = TransactionManager()  # Add transaction manager
        self.metrics_cache = MetricsCache()

    def get_current_price(self, symbol: str, as_of_date: date = None) -> float:
        """Get stock price from cache or Yahoo Finance"""
        if as_of_date is None:
            as_of_date = datetime.now().date()
        return self.price_manager.get_price(symbol, as_of_date)
    
    def _calculate_portfolio_values(self, holdings: dict, prices_df: pd.DataFrame = None, calc_date: date = None) -> dict:
        """Helper function to calculate portfolio values and weights
        
        Args:
            holdings: Dictionary of holdings
            prices_df: Optional DataFrame of historical prices
            calc_date: Optional date for historical price lookup
            
        Returns:
            Updated holdings dictionary with market values and weights
        """
        # Remove zero positions except cash
        holdings = {k: v for k, v in holdings.items() if v['units'] != 0 or k == 'CASH EQUIVALENTS'}
        
        # Calculate market values
        total_market_value = 0
        for symbol, data in holdings.items():
            if symbol == 'CASH EQUIVALENTS':
                data['last_price'] = 1.0
            elif symbol == 'FIXED INCOME':
                data['last_price'] = 100.0
            else:
                if prices_df is not None and calc_date is not None:
                    # Get historical price from batch data
                    try:
                        price_series = prices_df[symbol] if symbol in prices_df.columns else pd.Series()
                        if not price_series.empty:
                            # Convert calc_date to Timestamp and find the last valid price
                            calc_timestamp = pd.Timestamp(calc_date)
                            valid_prices = price_series[price_series.index <= calc_timestamp]
                            if not valid_prices.empty:
                                data['last_price'] = float(valid_prices.iloc[-1])
                            else:
                                self.logger.warning(f"No price found for {symbol} on {calc_date}")
                                data['last_price'] = 0.0
                        else:
                            self.logger.warning(f"No price series found for {symbol}")
                            data['last_price'] = 0.0
                    except Exception as e:
                        self.logger.error(f"Error getting price for {symbol}: {str(e)}")
                        data['last_price'] = 0.0
                else:
                    # Get current price
                    data['last_price'] = self.price_manager.get_price(symbol, calc_date)
            
            market_value = float(data['units']) * float(data['last_price'])
            total_market_value += market_value
            data['market_value'] = market_value
        
        # Calculate weights
        for data in holdings.values():
            data['weight'] = (data['market_value'] / total_market_value) if total_market_value != 0 else 0.0
            for key in ['units', 'cost_basis', 'last_price', 'market_value', 'weight']:
                data[key] = float(data[key])
        
        return holdings

    def calculate_stock_holdings(self, df: pd.DataFrame, start_date: date = None, end_date: date = None, freq: str = 'D', user_id: str = None) -> dict:
        """Calculate stock holdings for given date(s)
        
        Args:
            df: Transaction DataFrame
            start_date: Start date for calculations. If None, uses current date
            end_date: End date for calculations. If None, uses start_date
            freq: Frequency for calculations ('D' for daily, 'W' for weekly, 'M' for monthly)
                Only used when both start_date and end_date are provided
            user_id: User ID for transaction processing
                
        Returns:
            If only start_date provided: Dictionary of holdings for that date
            If start_date and end_date provided: Dictionary with dates as keys and holdings dictionaries as values
        """
        if df.empty:
            return {} if end_date is None else {start_date: {}}

        if user_id is None:
            self.logger.warning("No user_id provided for holdings calculation")
            user_id = "default"

        # Pre-process transactions
        processed_df = self.transaction_manager.preprocess_transactions(df.copy(), user_id=user_id)

        # Initialize processor with processed transactions
        processor = TransactionProcessor(processed_df)

        # Handle dates
        if start_date is None:
            start_date = datetime.now().date()
        if end_date is None:
            date_range = pd.date_range(start=start_date, end=start_date, freq=freq, inclusive='both')
        else:
            date_range = pd.date_range(start=start_date, end=end_date, freq=freq, inclusive='both')

        if date_range.empty:
            return {}

        # Get symbols requiring prices
        price_symbols = processor.get_symbols_requiring_prices()
        # print("symbols:  ", price_symbols)
        # Get prices in batch
        prices_df = pd.DataFrame()
        if price_symbols:
            try:
                prices_df = self.price_manager.get_prices_batch(
                    price_symbols,
                    start_date - timedelta(days=5),
                    end_date + timedelta(days=1) if end_date else start_date + timedelta(days=1)
                )
                
            except Exception as e:
                self.logger.error(f"Error in batch price download: {str(e)}")
                return {} if end_date is None else {start_date: {}}

        holdings_by_date = {}
        
        # Calculate holdings for each date
        for calc_date in date_range:
            calc_date = calc_date.date()
            
            # Check cache first
            cache_key = (calc_date, 'holdings')
            cached_holdings = self.holdings_cache.get(cache_key)
            if cached_holdings is not None:
                holdings_by_date[calc_date] = cached_holdings
                continue

            # Get transactions up to date efficiently
            transactions_to_date = processor.get_transactions_until(calc_date)
            
            # Calculate holdings
            holdings = self._calculate_holdings_for_date(
                transactions_to_date,
                calc_date,
                prices_df
            )
            
            # Cache the result
            self.holdings_cache.set(cache_key, holdings)
            holdings_by_date[calc_date] = holdings

        # Clear expired cache entries
        self.holdings_cache.clear()

        return holdings_by_date[start_date] if end_date is None else holdings_by_date

    def _calculate_holdings_for_date(self, transactions: pd.DataFrame, calc_date: date, prices_df: pd.DataFrame) -> dict:
        """Calculate holdings for a specific date using vectorized operations where possible"""
        holdings = {
            'CASH EQUIVALENTS': {
                'units': 0.0,
                'security_type': 'cash',
                'cost_basis': 0.0,
                'last_price': 1.0,
                'last_update': calc_date
            }
        }

        # Group transactions by symbol and type for vectorized calculations
        grouped = transactions.groupby(['stock', 'transaction_type'])
        
        # Calculate positions using vectorized operations
        for (symbol, txn_type), group in grouped:
            if symbol not in holdings and symbol != 'CASH EQUIVALENTS':
                holdings[symbol] = {
                    'units': 0.0,
                    'security_type': group.iloc[0]['security_type'],
                    'cost_basis': 0.0,
                    'last_price': 0.0,
                    'last_update': calc_date
                }
            
            if txn_type.lower() in ['buy', 'reinvest', 'stock_transfer']:
                mask = pd.notna(group['units']) & pd.notna(group['price'])
                holdings[symbol]['units'] += group[mask]['units'].sum()
                holdings[symbol]['cost_basis'] += (
                    (group[mask]['units'] * group[mask]['price']).sum() + 
                    group[mask]['fee'].sum()
                )
                
                if txn_type != 'stock_transfer':
                    cash_impact = group.apply(
                        lambda x: abs(x['amount']) if pd.notna(x['amount']) and x['amount']!=0 
                        else (x['units'] * x['price'] + x['fee']),
                        axis=1
                    ).sum()
                    holdings['CASH EQUIVALENTS']['units'] -= cash_impact
            
            elif txn_type.lower() == 'sell':
                mask = pd.notna(group['units']) & pd.notna(group['price'])
                sell_units = group[mask]['units'].sum()
                if sell_units > 0:
                    # Calculate cost basis per unit
                    cost_per_unit = holdings[symbol]['cost_basis'] / holdings[symbol]['units'] if holdings[symbol]['units'] != 0 else 0
                    # Adjust cost basis
                    holdings[symbol]['cost_basis'] -= (sell_units * cost_per_unit)
                    holdings[symbol]['units'] -= sell_units

                # Update cash position with proceeds
                proceeds = group.apply(
                    lambda x: abs(x['amount']) if pd.notna(x['amount']) and x['amount']!=0 
                    else (x['units'] * x['price'] - x['fee']),
                    axis=1
                ).sum()
                holdings['CASH EQUIVALENTS']['units'] += proceeds

            elif txn_type.lower() == 'transfer' and group.iloc[0]['security_type'] == 'cash':
                # Handle cash transfers
                transfer_amount = group.apply(
                    lambda x: x['amount'] if pd.notna(x['amount']) and x['amount']!=0 
                    else x['units'],
                    axis=1
                ).sum()
                holdings['CASH EQUIVALENTS']['units'] += transfer_amount
            
            elif txn_type.lower() in ['dividend', 'interest']:
                # Handle dividend and interest income
                income_amount = group.apply(
                    lambda x: abs(x['amount']) if pd.notna(x['amount']) and x['amount']!=0 
                    else x['units'],
                    axis=1
                ).sum()
                holdings['CASH EQUIVALENTS']['units'] += income_amount
            
            elif txn_type.lower() in ['sell_to_open', 'sell_to_close', 'buy_to_open', 'buy_to_close']:
                # Handle option transactions
                premium = group.apply(
                    lambda x: abs(x['amount']) if pd.notna(x['amount']) and x['amount']!=0 
                    else (x['units'] * x['price'] - x['fee']),
                    axis=1
                ).sum()
                if txn_type.lower() in ['sell_to_open', 'sell_to_close']:
                    holdings['CASH EQUIVALENTS']['units'] += premium
                else:
                    holdings['CASH EQUIVALENTS']['units'] -= premium
            
            elif txn_type.lower() == 'split' and group.iloc[0]['security_type'] == 'stock':
                # Handle stock splits
                split_units = group[pd.notna(group['units']) & (group['units'] != 0)]['units'].sum()
                holdings[symbol]['units'] += split_units

        # Update cash position cost basis
        holdings['CASH EQUIVALENTS']['cost_basis'] = holdings['CASH EQUIVALENTS']['units']
        
        # Calculate market values and weights
        holdings = self._calculate_portfolio_values(holdings, prices_df, calc_date)
        
        return holdings

    def calculate_gain_loss(self, df: pd.DataFrame, user_id: str = None) -> dict:
        """Calculate realized and unrealized gains/losses for all positions"""
        if df.empty:
            return {}
            
        # Pre-process transactions
        processed_df = self.transaction_manager.preprocess_transactions(df.copy(), user_id=user_id)
        
        # Get current holdings first (use single date mode)
        holdings = self.calculate_stock_holdings(processed_df, start_date=datetime.now().date(),user_id=user_id)
        
        # Initialize gain/loss tracking
        gain_loss = {}
        
        # Process each symbol
        for symbol in set(processed_df['stock'].unique()):
            symbol_txns = processed_df[processed_df['stock'] == symbol].sort_values('date')
            
            # Initialize tracking variables
            running_units = 0
            total_cost_basis = 0
            realized_gain_loss = 0
            dividend_income = 0
            option_gain_loss = 0
            
            # Process each transaction
            for _, txn in symbol_txns.iterrows():
                if txn['transaction_type'].lower() in ['buy', 'reinvest', 'stock_transfer']:
                    running_units += txn['units']
                    total_cost_basis += (txn['units'] * txn['price'] + txn['fee'])
                
                elif txn['transaction_type'].lower() == 'sell':
                    if running_units > 0:
                        # Calculate cost basis per unit
                        cost_per_unit = total_cost_basis / running_units if running_units != 0 else 0
                        # Calculate realized gain/loss
                        realized_gain_loss += (txn['units'] * (txn['price'] - cost_per_unit) - txn['fee'])
                        # Adjust cost basis
                        total_cost_basis -= (txn['units'] * cost_per_unit)
                        running_units -= txn['units']
                
                elif txn['transaction_type'].lower() == 'dividend' and txn['transaction_type'].lower() != 'reinvest':
                    dividend_income += abs(txn['amount']) if pd.notna(txn['amount']) else txn['units']
                
                elif txn['transaction_type'].lower() in ['sell_to_open', 'sell_to_close', 'buy_to_open', 'buy_to_close']:
                    premium = abs(txn['amount']) if pd.notna(txn['amount']) else (txn['units'] * txn['price'] - txn['fee'])
                    if txn['transaction_type'].lower() in ['sell_to_open', 'sell_to_close']:  # Credit transactions
                        option_gain_loss += premium
                    else:  # buy_to_close, buy_to_open - Debit transactions
                        option_gain_loss -= premium
            
            # Get current holding information
            current_holding = holdings.get(symbol, {
                'units': 0,
                'last_price': 0,
                'last_update': datetime.now()
            })
            
            # For cash, reset cost basis to units
            if symbol == 'CASH EQUIVALENTS':
                total_cost_basis = current_holding['units']
                
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
                'unrealized_gain_loss_pct': (unrealized_gain_loss / total_cost_basis) if total_cost_basis != 0 else 0,
                'dividend_income': dividend_income,
                'option_gain_loss': option_gain_loss,
                'total_return': total_return,
                'total_return_pct': (total_return / total_cost_basis) if total_cost_basis != 0 else 0,
                'last_price': current_holding['last_price'],
                'last_update': current_holding['last_update']
            }
        
        return gain_loss
        
    def _calculate_holdings_without_prices(self, df: pd.DataFrame, date_range: pd.DatetimeIndex, user_id: str = None) -> dict:
        """Helper method to calculate holdings when there are no symbols requiring prices"""
        if user_id is None:
            self.logger.warning("No user_id provided for holdings calculation")
            user_id = "default"
        
        holdings_by_date = {}
        
        for calc_date in date_range:
            calc_date = calc_date.date()
            transactions_to_date = df[pd.to_datetime(df['date']).dt.date <= calc_date].copy()
            
            holdings = {
                'CASH EQUIVALENTS': {
                    'units': 0.0,
                    'security_type': 'cash',
                    'cost_basis': 0.0,
                    'last_price': 1.0,
                    'market_value': 0.0,
                    'weight': 1.0,
                    'last_update': calc_date
                }
            }
            
            # Process only cash transactions
            for _, row in transactions_to_date.sort_values('date').iterrows():
                if row['security_type'] == 'cash':
                    if row['transaction_type'].lower() in ['transfer', 'dividend', 'interest']:
                        holdings['CASH EQUIVALENTS']['units'] += row['amount'] if pd.notna(row['amount']) else row['units']
            
            holdings['CASH EQUIVALENTS']['cost_basis'] = holdings['CASH EQUIVALENTS']['units']
            holdings['CASH EQUIVALENTS']['market_value'] = holdings['CASH EQUIVALENTS']['units']
            
            holdings_by_date[calc_date] = holdings
            
        return holdings_by_date
        
    def calculate_performance(self, df: pd.DataFrame, user_id: str = None) -> dict:
        """Calculate portfolio performance metrics over time using weekly intervals"""
        if df.empty:
            return {
                'dates': [],
                'portfolio_values': [],
                'invested_amounts': [],
                'metrics': {}
            }
            
        if user_id is None:
            self.logger.warning("No user_id provided for performance calculation")
            user_id = "default"
            
        # Get date range
        start_date = pd.to_datetime(df['date'].min()).date()
        end_date = pd.to_datetime(df['date'].max()).date()
        
        # Check cache first
        cached_metrics = self.metrics_cache.get(user_id, 'performance', start_date, end_date)
        if cached_metrics:
            return cached_metrics
        
        # Sort transactions by date
        df = df.sort_values('date')
        
        # Calculate holdings for all weeks with user_id
        holdings_by_date = self.calculate_stock_holdings(df, start_date, end_date, freq='W', user_id=user_id)
        
        if not holdings_by_date:
            return {
                'dates': [],
                'portfolio_values': [],
                'invested_amounts': [],
                'metrics': {}
            }
        
        # Extract values
        dates = []
        daily_values = []
        daily_invested = []
        
        for calc_date, holdings in sorted(holdings_by_date.items()):
            # Calculate total portfolio value (includes cash, stocks, and fixed income)
            total_value = sum(holding['market_value'] for holding in holdings.values())
            
            # Calculate invested amount up to this date (only cash transfers, and employee stock transfer in Etrade)
            transactions_to_date = df[pd.to_datetime(df['date']).dt.date <= calc_date]
            invested_amount = 0
            for _, txn in transactions_to_date.iterrows():
                if txn['transaction_type'].lower() == 'transfer' and txn['security_type'] == 'cash':
                    transfer_amount = txn['amount'] if pd.notna(txn['amount']) else txn['units']
                    invested_amount += transfer_amount
                elif txn['transaction_type'].lower() == 'stock_transfer':
                    invested_amount += txn['price'] * txn['units']
            
            dates.append(calc_date)
            daily_values.append(float(total_value))  # Ensure float type
            daily_invested.append(float(invested_amount))  # Ensure float type
        
        # Convert to numpy arrays for calculations
        values = np.array(daily_values)
        invested = np.array(daily_invested)
        
        # Calculate metrics
        metrics = {}
        if len(values) > 1:
            # Weekly returns
            weekly_returns = np.diff(values) / values[:-1]
            weekly_returns = weekly_returns[~np.isnan(weekly_returns) & ~np.isinf(weekly_returns)]
            
            # Annualized return (geometric mean)
            if len(weekly_returns) > 0 and not np.any(np.isnan(weekly_returns)) and not np.any(np.isinf(weekly_returns)):
                try:
                    # Calculate cumulative return first
                    cumulative_return = np.prod(1 + weekly_returns)
                    if cumulative_return > 0:
                        # Then take the root
                        annualized_return = cumulative_return ** (52/len(weekly_returns)) - 1
                        # Calculate volatility and Sharpe ratio
                        volatility = np.std(weekly_returns) * np.sqrt(52)
                        sharpe_ratio = (annualized_return - 0.02) / volatility if volatility > 0 else 0
                        
                        # Ensure values are valid and within JSON range
                        if not (np.isnan(annualized_return) or np.isinf(annualized_return)):
                            metrics['annualized_return'] = float(np.clip(annualized_return, -1e300, 1e300))
                        else:
                            metrics['annualized_return'] = 0.0
                            
                        if not (np.isnan(volatility) or np.isinf(volatility)):
                            metrics['volatility'] = float(np.clip(volatility, 0, 1e300))
                        else:
                            metrics['volatility'] = 0.0
                            
                        if not (np.isnan(sharpe_ratio) or np.isinf(sharpe_ratio)):
                            metrics['sharpe_ratio'] = float(np.clip(sharpe_ratio, -1e300, 1e300))
                        else:
                            metrics['sharpe_ratio'] = 0.0
                    else:
                        metrics = {
                            'annualized_return': 0.0,
                            'volatility': 0.0,
                            'sharpe_ratio': 0.0
                        }
                except Exception as e:
                    self.logger.error(f"Error calculating performance metrics: {str(e)}")
                    metrics = {
                        'annualized_return': 0.0,
                        'volatility': 0.0,
                        'sharpe_ratio': 0.0
                    }
            else:
                metrics = {
                    'annualized_return': 0.0,
                    'volatility': 0.0,
                    'sharpe_ratio': 0.0
                }
        
        # Ensure all values are JSON serializable
        result = {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'portfolio_values': [float(np.clip(v, -1e300, 1e300)) for v in values],
            'invested_amounts': [float(np.clip(v, -1e300, 1e300)) for v in invested],
            'metrics': metrics
        }
        
        # Cache the results before returning
        self.metrics_cache.set(user_id, 'performance', start_date, end_date, result)
        
        return result