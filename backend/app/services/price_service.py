import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import sqlite3
import logging
import warnings
import holidays
from pathlib import Path
from ..core.cache_config import get_cache_path

logger = logging.getLogger(__name__)

class PriceManager:
    """Manages price downloads and caching for financial calculations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._memory_cache = {}
        self._last_download_time = {}
        self._download_interval = timedelta(days=365)
        self.db_path = get_cache_path()
        self._init_db()
        self._us_holidays = holidays.US(years=range(2000, datetime.now().year + 2))
    
    def _init_db(self):
        """Initialize SQLite database for price caching"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS price_cache (
                        symbol TEXT,
                        date DATE,
                        price REAL,
                        updated_at TIMESTAMP,
                        PRIMARY KEY (symbol, date)
                    )
                """)
        except Exception as e:
            self.logger.error(f"Error initializing price cache DB: {e}")
            
    def get_price(self, symbol: str, as_of_date: date) -> float:
        """Get price for a single symbol and date with caching"""
        try:
            # Check memory cache first
            cache_key = (symbol, as_of_date)
            current_time = datetime.now()
            
            if (cache_key in self._memory_cache and 
                cache_key in self._last_download_time and
                current_time - self._last_download_time[cache_key] < self._download_interval):
                return self._memory_cache[cache_key]
            
            # Check SQLite cache
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    """
                    SELECT price, updated_at FROM price_cache 
                    WHERE symbol = ? AND date = ? AND 
                    (julianday(updated_at) - julianday(date)) >= 1
                    """,
                    (symbol, as_of_date.isoformat())
                )
                result = cursor.fetchone()
                
                if result:
                    # If price was updated at least 1 day after the date, consider it final
                    self._memory_cache[cache_key] = result[0]
                    self._last_download_time[cache_key] = datetime.fromisoformat(result[1])
                    return result[0]
                
                # Check for non-finalized cached price
                cursor = conn.execute(
                    "SELECT price, updated_at FROM price_cache WHERE symbol = ? AND date = ?",
                    (symbol, as_of_date.isoformat())
                )
                result = cursor.fetchone()
                
                if result and (datetime.now() - datetime.fromisoformat(result[1])) < self._download_interval:
                    self._memory_cache[cache_key] = result[0]
                    self._last_download_time[cache_key] = datetime.fromisoformat(result[1])
                    return result[0]
            
            # If not in cache or cache expired, download
            price = self._download_single_price(symbol, as_of_date)
            
            # Update both caches
            self._memory_cache[cache_key] = price
            self._last_download_time[cache_key] = current_time
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO price_cache (symbol, date, price, updated_at) VALUES (?, ?, ?, ?)",
                    (symbol, as_of_date.isoformat(), price, current_time.isoformat())
                )
            
            return price
            
        except Exception as e:
            self.logger.error(f"Error in get_price for {symbol}: {str(e)}")
            return 0.0
    
    def get_prices_batch(self, symbols: list, start_date: date, end_date: date) -> pd.DataFrame:
        """Get prices for multiple symbols and date range with caching"""
        try:
            # Initialize result DataFrame
            prices_df = pd.DataFrame()
            symbols_to_download = []
            
            # Get required trading days
            required_dates = self._get_trading_days(start_date, end_date)
            
            # Check cache for each symbol
            with sqlite3.connect(self.db_path) as conn:
                for symbol in symbols:
                    query = """
                        SELECT date, price FROM price_cache 
                        WHERE symbol = ? AND date BETWEEN ? AND ?
                        ORDER BY date
                    """
                    df = pd.read_sql_query(
                        query, 
                        conn,
                        params=(symbol, start_date.isoformat(), end_date.isoformat()),
                        parse_dates=['date']
                    )
                    
                    # Check if we have all required trading days
                    if not df.empty:
                        dates_covered = set(df['date'].dt.date)
                        if required_dates.issubset(dates_covered):
                            prices_df[symbol] = df.set_index('date')['price']
                        else:
                            symbols_to_download.append(symbol)
                    else:
                        symbols_to_download.append(symbol)
            
            if symbols_to_download:
                # Download missing data
                downloaded_df = self._download_prices_batch(
                    symbols_to_download,
                    start_date - timedelta(days=5),  # Add buffer for market holidays
                    end_date + timedelta(days=1)
                )
                
                if not downloaded_df.empty:
                    # Update cache with new data
                    current_time = datetime.now().isoformat()
                    with sqlite3.connect(self.db_path) as conn:
                        for symbol in symbols_to_download:
                            if symbol in downloaded_df.columns:
                                for idx, price in downloaded_df[symbol].items():
                                    conn.execute(
                                        "INSERT OR REPLACE INTO price_cache (symbol, date, price, updated_at) VALUES (?, ?, ?, ?)",
                                        (symbol, idx.date().isoformat(), float(price), current_time)
                                    )
                    
                    # Merge downloaded data with cached data
                    prices_df = pd.concat([prices_df, downloaded_df], axis=1)
            
            return prices_df
            
        except Exception as e:
            self.logger.error(f"Error in get_prices_batch: {str(e)}")
            return pd.DataFrame()
    
    def _download_single_price(self, symbol: str, as_of_date: date) -> float:
        """Download price for a single symbol and date"""
        try:
            # If not a trading day, look for the previous trading day
            while not self._is_trading_day(as_of_date):
                as_of_date = as_of_date - timedelta(days=1)
            
            end_date = as_of_date + timedelta(days=1)
            start_date = as_of_date - timedelta(days=5)  # Buffer for holidays

            # Log yf.download parameters
            self.logger.info(f"Calling yf.download with params: symbol={symbol}, start={start_date}, end={end_date}, interval=1d")
            
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False,
                interval='1d'
            )
            
            if df.empty:
                self.logger.warning(f"yf.download returned empty DataFrame for {symbol}")
                return 0.0
                
            df = df[df.index <= pd.Timestamp(as_of_date)]
            if not df.empty:
                return float(df['Close'].iloc[-1])
                
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error in _download_single_price for {symbol}: {str(e)}")
            return 0.0
    
    def _download_prices_batch(self, symbols: list, start_date: date, end_date: date) -> pd.DataFrame:
        """Download prices for multiple symbols"""
        try:
            if not symbols:
                return pd.DataFrame()
                
            # Log yf.download parameters
            self.logger.info(f"Calling yf.download batch with params: symbols={symbols}, start={start_date}, end={end_date}, interval=1d")

            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                df = yf.download(
                    symbols,
                    start=start_date,
                    end=end_date,
                    progress=False,
                    interval='1d',
                    group_by='ticker'
                )
            
            if len(symbols) == 1:
                symbol = symbols[0]
                if isinstance(df, pd.DataFrame) and 'Close' in df.columns:
                    return pd.DataFrame({symbol: df['Close']})
            else:
                if isinstance(df, pd.DataFrame) and isinstance(df.columns, pd.MultiIndex):
                    return df.xs('Close', axis=1, level=1, drop_level=True)
                    
            return df
            
        except Exception as e:
            self.logger.error(f"Error in _download_prices_batch: {str(e)}")
            return pd.DataFrame()
    
    def _is_trading_day(self, day: date) -> bool:
        """Check if given date is a trading day"""
        return (
            day.weekday() < 5 and  # Monday = 0, Friday = 4
            day not in self._us_holidays
        )
        
    def _get_trading_days(self, start_date: date, end_date: date) -> set:
        """Get all trading days between start_date and end_date"""
        business_days = pd.date_range(start=start_date, end=end_date, freq='B')
        return {d.date() for d in business_days if d.date() not in self._us_holidays}
