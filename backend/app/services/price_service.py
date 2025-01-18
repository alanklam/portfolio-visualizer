import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import sqlite3
import logging
import warnings
from pathlib import Path
from ..core.cache_config import get_cache_path

logger = logging.getLogger(__name__)

class PriceManager:
    """Manages price downloads and caching for financial calculations"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._memory_cache = {}
        self._last_download_time = {}
        self._download_interval = timedelta(minutes=15)
        self.db_path = get_cache_path()
        self._init_db()
    
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
                    "SELECT price, updated_at FROM price_cache WHERE symbol = ? AND date = ?",
                    (symbol, as_of_date.isoformat())
                )
                result = cursor.fetchone()
                
                if result and (datetime.now() - datetime.fromisoformat(result[1])) < self._download_interval:
                    self._memory_cache[cache_key] = result[0]
                    self._last_download_time[cache_key] = datetime.fromisoformat(result[1])
                    return result[0]
            
            # If not in cache, download
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
            self.logger.error(f"Error getting price for {symbol}: {e}")
            return 0.0
    
    def get_prices_batch(self, symbols: list, start_date: date, end_date: date) -> pd.DataFrame:
        """Get prices for multiple symbols and date range with caching"""
        try:
            # Initialize result DataFrame
            prices_df = pd.DataFrame()
            symbols_to_download = []
            
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
                    
                    if len(df) == (end_date - start_date).days + 1:
                        # If we have all dates in cache, use cached data
                        prices_df[symbol] = df.set_index('date')['price']
                    else:
                        symbols_to_download.append(symbol)
            
            if symbols_to_download:
                # Download missing data
                downloaded_df = self._download_prices_batch(
                    symbols_to_download,
                    start_date - timedelta(days=5),
                    end_date + timedelta(days=1)
                )
                
                if not downloaded_df.empty:
                    # Update cache with new data
                    with sqlite3.connect(self.db_path) as conn:
                        for symbol in symbols_to_download:
                            if symbol in downloaded_df.columns:
                                for idx, price in downloaded_df[symbol].items():
                                    conn.execute(
                                        "INSERT OR REPLACE INTO price_cache (symbol, date, price, updated_at) VALUES (?, ?, ?, ?)",
                                        (symbol, idx.date().isoformat(), float(price), datetime.now().isoformat())
                                    )
                    
                    # Merge downloaded data with cached data
                    prices_df = pd.concat([prices_df, downloaded_df], axis=1)
            
            return prices_df
            
        except Exception as e:
            self.logger.error(f"Error in batch price download: {e}")
            return pd.DataFrame()
    
    def _download_single_price(self, symbol: str, as_of_date: date) -> float:
        """Download price for a single symbol and date"""
        try:
            end_date = as_of_date + timedelta(days=1)
            start_date = as_of_date - timedelta(days=5)
            
            df = yf.download(
                symbol,
                start=start_date,
                end=end_date,
                progress=False,
                interval='1d'
            )
            
            if df.empty:
                return 0.0
                
            df = df[df.index <= pd.Timestamp(as_of_date)]
            if not df.empty:
                return float(df['Close'].iloc[-1])
                
            return 0.0
            
        except Exception as e:
            self.logger.error(f"Error downloading price for {symbol}: {e}")
            return 0.0
    
    def _download_prices_batch(self, symbols: list, start_date: date, end_date: date) -> pd.DataFrame:
        """Download prices for multiple symbols"""
        try:
            if not symbols:
                return pd.DataFrame()
                
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
            self.logger.error(f"Error in batch download: {e}")
            return pd.DataFrame()
