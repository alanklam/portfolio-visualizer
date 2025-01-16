import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import yfinance as yf
import logging
import warnings

logger = logging.getLogger(__name__)

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
        self._price_cache = {}  # Cache for storing downloaded prices
        self._last_download_time = None
        self._download_interval = timedelta(minutes=15)  # Refresh cache every 15 minutes
    
    def get_current_price(self, symbol: str, as_of_date: date = None) -> float:
        """Get stock price from Yahoo Finance as of a specific date with caching"""
        try:
            if as_of_date is None:
                as_of_date = datetime.now().date()
            
            # Check cache first
            cache_key = (symbol, as_of_date)
            current_time = datetime.now()
            
            # Return cached price if available and cache is not expired
            if (cache_key in self._price_cache and 
                self._last_download_time and 
                current_time - self._last_download_time < self._download_interval):
                return self._price_cache[cache_key]
            
            # Download data with a 5-day window to handle non-trading days
            # with warnings.catch_warnings():
            #     warnings.simplefilter("ignore")
            end_date = as_of_date + timedelta(days=1)
            start_date = as_of_date - timedelta(days=5)
            
            # ticker = yf.Ticker(symbol)
            # df = ticker.history(start=start_date,end=end_date,interval='1d')
            df = yf.download(symbol, 
                            start=start_date,
                            end=end_date,
                            progress=False,
                            interval='1d')
            
            if df.empty:
                self.logger.warning(f"No price data found for {symbol}")
                return 0.0
            
            # Get the last available price up to as_of_date
            df = df[df.index <= pd.Timestamp(as_of_date)]
            if not df.empty:
                price = df['Close'].iloc[-1]
                # Update cache
                self._price_cache[cache_key] = price
                self._last_download_time = current_time
                return price
            
            return 0.0
                
        except Exception as e:
            self.logger.error(f"Error fetching price for {symbol}: {str(e)}")
            return 0.0
            
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
                        mask = price_series.index <= pd.Timestamp(calc_date)
                        if not price_series.empty and mask.any():
                            data['last_price'] = float(price_series[mask].iloc[-1])
                        else:
                            self.logger.warning(f"No price found for {symbol} on {calc_date}")
                            data['last_price'] = 0.0
                    except Exception as e:
                        self.logger.error(f"Error getting price for {symbol}: {str(e)}")
                        data['last_price'] = 0.0
                else:
                    # Get current price
                    data['last_price'] = self.get_current_price(symbol, calc_date)
            
            market_value = float(data['units']) * float(data['last_price'])
            total_market_value += market_value
            data['market_value'] = market_value
        
        # Calculate weights
        for data in holdings.values():
            data['weight'] = (data['market_value'] / total_market_value) if total_market_value > 0 else 0.0
            for key in ['units', 'cost_basis', 'last_price', 'market_value', 'weight']:
                data[key] = float(data[key])
        
        return holdings

    def calculate_stock_holdings(self, df: pd.DataFrame, as_of_date: date = None) -> dict:
        """Calculate current stock holdings from transaction history"""
        if df.empty:
            return {}
            
        if as_of_date is None:
            as_of_date = datetime.now().date()
            
        # Filter transactions up to as_of_date
        df = df[pd.to_datetime(df['date']).dt.date <= as_of_date].copy()
        
        holdings = {}
        total_market_value = 0.0
        
        # Initialize cash position
        holdings['CASH EQUIVALENTS'] = {
            'units': 0.0,
            'security_type': 'cash',
            'cost_basis': 0.0,
            'last_price': 1.0,
            'last_update': as_of_date
        }
        
        # Process transactions chronologically
        for _, row in df.sort_values('date').iterrows():
            symbol = row['stock']
            transaction_type = row['transaction_type'].lower()
            
            # Initialize holding if not exists
            if symbol not in holdings and symbol != 'CASH EQUIVALENTS':
                holdings[symbol] = {
                    'units': 0.0,
                    'security_type': row['security_type'],
                    'cost_basis': 0.0,
                    'last_price': 0.0,
                    'last_update': row['date']
                }
            
            # Handle different transaction types
            if transaction_type in ['buy', 'reinvest', 'stock_transfer']:  
                if pd.notna(row['units']) and pd.notna(row['price']):
                    holdings[symbol]['units'] += row['units']
                    holdings[symbol]['cost_basis'] += (row['units'] * row['price'] + row['fee'])
                    
                # debit on cash position for purchase (exclude stock_transfer)
                if transaction_type != 'stock_transfer':
                    total_cost = abs(row['amount']) if pd.notna(row['amount']) and row['amount']!=0 else (row['units'] * row['price'] + row['fee'])
                    holdings['CASH EQUIVALENTS']['units'] -= total_cost
                
            elif transaction_type == 'sell':
                if pd.notna(row['units']) and pd.notna(row['price']):
                    if holdings[symbol]['units'] > 0:
                        cost_per_unit = holdings[symbol]['cost_basis'] / holdings[symbol]['units']
                        holdings[symbol]['cost_basis'] -= (row['units'] * cost_per_unit)
                    holdings[symbol]['units'] -= row['units']
                    
                # credit on cash position for sale
                proceeds = abs(row['amount']) if pd.notna(row['amount']) and row['amount'] != 0 else (row['units'] * row['price'] - row['fee'])
                holdings['CASH EQUIVALENTS']['units'] += proceeds
                
            elif transaction_type == 'transfer':
                if row['security_type'] == 'cash':
                    holdings['CASH EQUIVALENTS']['units'] += row['amount'] if pd.notna(row['amount']) and row['amount']!=0 else row['units']
                    
            elif transaction_type == 'dividend':
                holdings['CASH EQUIVALENTS']['units'] += abs(row['amount']) if pd.notna(row['amount']) and row['amount']!=0 else row['units']
                
            elif transaction_type == 'interest':
                holdings['CASH EQUIVALENTS']['units'] += abs(row['amount']) if pd.notna(row['amount']) and row['amount']!=0 else row['units']
                
            # Handle option transactions
            elif transaction_type in ['sell_to_open', 'sell_to_close', 'buy_to_open', 'buy_to_close']:
                premium = abs(row['amount']) if pd.notna(row['amount']) and row['amount']!= 0 else (row['units'] * row['price'] - row['fee'])
                if transaction_type in ['sell_to_open', 'sell_to_close']:
                    holdings['CASH EQUIVALENTS']['units'] += premium
                else:
                    holdings['CASH EQUIVALENTS']['units'] -= premium

            # Fidelity logic, adjust stock units for stock splits
            elif transaction_type == 'split' and row['security_type'] == 'stock':
                if pd.notna(row['units']) and row['units'] != 0:
                    holdings[symbol]['units'] += row['units']
        
        # Update cash position cost basis
        holdings['CASH EQUIVALENTS']['cost_basis'] = holdings['CASH EQUIVALENTS']['units']
        
        # Calculate market values and weights
        holdings = self._calculate_portfolio_values(holdings, calc_date=as_of_date)
        #print("final: ", holdings['CASH EQUIVALENTS']['units'])

        return holdings
        
    def calculate_gain_loss(self, df: pd.DataFrame) -> dict:
        """Calculate realized and unrealized gains/losses for all positions"""
        if df.empty:
            return {}
            
        # Get current holdings first
        holdings = self.calculate_stock_holdings(df)
        
        # Initialize gain/loss tracking
        gain_loss = {}
        
        # Process each symbol
        for symbol in set(df['stock'].unique()):
            symbol_txns = df[df['stock'] == symbol].sort_values('date')
            
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
                        cost_per_unit = total_cost_basis / running_units
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
                'unrealized_gain_loss_pct': (unrealized_gain_loss / total_cost_basis) if total_cost_basis > 0 else 0,
                'dividend_income': dividend_income,
                'option_gain_loss': option_gain_loss,
                'total_return': total_return,
                'total_return_pct': (total_return / total_cost_basis) if total_cost_basis > 0 else 0,
                'last_price': current_holding['last_price'],
                'last_update': current_holding['last_update']
            }
        
        return gain_loss
        
    def calculate_stock_holdings_batch(self, df: pd.DataFrame, start_date: date, end_date: date, freq: str = 'W') -> dict:
        """Calculate stock holdings for multiple dates efficiently using batch price downloads
        
        Args:
            df: Transaction DataFrame
            start_date: Start date for calculations
            end_date: End date for calculations
            freq: Frequency for calculations ('D' for daily, 'W' for weekly, 'M' for monthly)
            
        Returns:
            Dictionary with dates as keys and holdings dictionaries as values
        """
        if df.empty:
            return {}

        # Generate dates at specified frequency
        date_range = pd.date_range(start=start_date, end=end_date, freq=freq)

        if date_range.empty:
            return {}
        
        # Get unique symbols from transactions, keeping FIXED INCOME but excluding CASH
        symbols = set(df['stock'].unique()) - {'CASH EQUIVALENTS'}
        if not symbols:  # If no symbols to price
            self.logger.info("No symbols requiring price data")
            return self._calculate_holdings_without_prices(df, date_range)
            
        # Convert symbols to list and sort for consistency
        # Filter out FIXED INCOME from symbols requiring price download
        price_symbols = sorted(list(symbols - {'FIXED INCOME'}))

        # Batch download prices only for non-fixed income securities
        prices_df = pd.DataFrame()
        if price_symbols:
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    prices_df = yf.download(
                        price_symbols,
                        start=start_date - timedelta(days=5),
                        end=end_date + timedelta(days=1),
                        progress=False,
                        interval='1d',
                        group_by='ticker'
                    )
                    
                # Process prices DataFrame based on number of symbols
                if len(price_symbols) == 1:
                    symbol = price_symbols[0]
                    if isinstance(prices_df, pd.DataFrame) and 'Close' in prices_df.columns:
                        prices_df = pd.DataFrame({symbol: prices_df['Close']})
                else:
                    if isinstance(prices_df, pd.DataFrame) and isinstance(prices_df.columns, pd.MultiIndex):
                        prices_df = prices_df.xs('Close', axis=1, level=1, drop_level=True)
                        
            except Exception as e:
                self.logger.error(f"Error in batch price download: {str(e)}")
                return {}
      
        self.logger.debug(f"Successfully downloaded prices for {len(price_symbols)} symbols")
        
        holdings_by_date = {}
        
        # Calculate holdings for each date
        for calc_date in date_range:
            calc_date = calc_date.date()
 
            # Filter transactions up to this date
            transactions_to_date = df[pd.to_datetime(df['date']).dt.date <= calc_date].copy()
            
            holdings = {}
            total_market_value = 0.0
            
            # Initialize cash position
            holdings['CASH EQUIVALENTS'] = {
                'units': 0.0,
                'security_type': 'cash',
                'cost_basis': 0.0,
                'last_price': 1.0,
                'last_update': calc_date
            }
            
            # Process transactions chronologically
            for _, row in transactions_to_date.sort_values('date').iterrows():
                symbol = row['stock']
                transaction_type = row['transaction_type'].lower()
                
                # Initialize holding if not exists
                if symbol not in holdings and symbol != 'CASH EQUIVALENTS':
                    holdings[symbol] = {
                        'units': 0.0,
                        'security_type': row['security_type'],
                        'cost_basis': 0.0,
                        'last_price': 0.0,
                        'last_update': row['date']
                    }
                
                # Process transaction based on type
                if transaction_type in ['buy', 'reinvest', 'stock_transfer']: 
                    if pd.notna(row['units']) and pd.notna(row['price']):
                        holdings[symbol]['units'] += row['units']
                        holdings[symbol]['cost_basis'] += (row['units'] * row['price'] + row['fee'])
                    if transaction_type != 'stock_transfer':  # Don't affect cash for stock_transfer
                        total_cost = abs(row['amount']) if pd.notna(row['amount']) and row['amount']!=0 else (row['units'] * row['price'] + row['fee'])
                        holdings['CASH EQUIVALENTS']['units'] -= total_cost
                    
                elif transaction_type == 'sell':
                    if pd.notna(row['units']) and pd.notna(row['price']):
                        if holdings[symbol]['units'] > 0:
                            cost_per_unit = holdings[symbol]['cost_basis'] / holdings[symbol]['units']
                            holdings[symbol]['cost_basis'] -= (row['units'] * cost_per_unit)
                        holdings[symbol]['units'] -= row['units']
                    proceeds = abs(row['amount']) if pd.notna(row['amount']) and row['amount'] != 0 else (row['units'] * row['price'] - row['fee'])
                    holdings['CASH EQUIVALENTS']['units'] += proceeds
                    
                elif transaction_type == 'transfer':
                    if row['security_type'] == 'cash':
                        holdings['CASH EQUIVALENTS']['units'] += row['amount'] if pd.notna(row['amount']) and row['amount']!=0 else row['units']
                        
                elif transaction_type == 'dividend':
                    holdings['CASH EQUIVALENTS']['units'] += abs(row['amount']) if pd.notna(row['amount']) and row['amount']!=0 else row['units']
                    
                elif transaction_type == 'interest':
                    holdings['CASH EQUIVALENTS']['units'] += abs(row['amount']) if pd.notna(row['amount']) and row['amount']!=0 else row['units']
                    
                elif transaction_type in ['sell_to_open', 'sell_to_close', 'buy_to_open', 'buy_to_close']:
                    premium = abs(row['amount']) if pd.notna(row['amount']) and row['amount'] != 0 else (row['units'] * row['price'] - row['fee'])
                    if transaction_type in ['sell_to_open', 'sell_to_close']:
                        holdings['CASH EQUIVALENTS']['units'] += premium
                    else:
                        holdings['CASH EQUIVALENTS']['units'] -= premium
            
                # Fidelity logic, adjust stock units for stock splits
                elif transaction_type == 'split' and row['security_type'] == 'stock':
                    if pd.notna(row['units']) and row['units'] != 0:
                        holdings[symbol]['units'] += row['units']

            # Update cash position cost basis
            holdings['CASH EQUIVALENTS']['cost_basis'] = holdings['CASH EQUIVALENTS']['units']
            
            # Calculate market values and weights
            holdings = self._calculate_portfolio_values(holdings, prices_df, calc_date)
            
            holdings_by_date[calc_date] = holdings

        return holdings_by_date
        
    def _calculate_holdings_without_prices(self, df: pd.DataFrame, date_range: pd.DatetimeIndex) -> dict:
        """Helper method to calculate holdings when there are no symbols requiring prices"""
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
        
    def calculate_performance(self, df: pd.DataFrame) -> dict:
        """Calculate portfolio performance metrics over time using weekly intervals"""
        if df.empty:
            return {
                'dates': [],
                'portfolio_values': [],
                'invested_amounts': [],
                'metrics': {}
            }
            
        # Sort transactions by date
        df = df.sort_values('date')
        
        # Get date range
        start_date = pd.to_datetime(df['date'].min()).date()
        end_date = pd.to_datetime(df['date'].max()).date()
        
        # Calculate holdings for all weeks
        holdings_by_date = self.calculate_stock_holdings_batch(df, start_date, end_date, freq='W')
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
        return {
            'dates': [d.strftime('%Y-%m-%d') for d in dates],
            'portfolio_values': [float(np.clip(v, -1e300, 1e300)) for v in values],
            'invested_amounts': [float(np.clip(v, -1e300, 1e300)) for v in invested],
            'metrics': metrics
        }