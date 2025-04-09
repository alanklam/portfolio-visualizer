import pandas as pd
import numpy as np
from datetime import datetime, timedelta, date
import logging
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import sqlite3
from ..core.cache_config import get_cache_path

logger = logging.getLogger(__name__)

class TransactionManager:
    """Manages transaction preprocessing and caching"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._memory_cache = {}
        self._last_process_time = {}
        self._process_interval = timedelta(days=365)
        self.db_path = get_cache_path()
        self._init_db()
        
    def _init_db(self):
        """Initialize SQLite database for transaction caching"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS transaction_cache (
                        user_id TEXT,
                        date DATE,
                        symbol TEXT,
                        running_units REAL,
                        cost_basis REAL,
                        realized_gl REAL,
                        dividend_income REAL,
                        option_gl REAL,
                        updated_at TIMESTAMP,
                        PRIMARY KEY (user_id, date, symbol)
                    )
                """)
        except Exception as e:
            self.logger.error(f"Error in _init_db initializing transaction cache DB: {e}")
    
    def preprocess_transactions(self, df: pd.DataFrame, user_id: str = None) -> pd.DataFrame:
        """Preprocess transactions with caching"""
        try:
            if user_id is None:
                self.logger.warning("No user_id provided for transaction processing")
                user_id = "default"
                
            # Add user_id validation
            if not isinstance(user_id, str):
                user_id = str(user_id)

            cache_key = (user_id, df.shape[0], df['date'].max())
            current_time = datetime.now()
            
            # Check memory cache
            if (cache_key in self._memory_cache and 
                cache_key in self._last_process_time and
                current_time - self._last_process_time[cache_key] < self._process_interval):
                return self._memory_cache[cache_key]
            
            # Process transactions
            processed_df = self._process_transactions(df)
            
            # Update cache
            self._memory_cache[cache_key] = processed_df
            self._last_process_time[cache_key] = current_time
            
            # Store running totals in SQLite
            self._store_running_totals(processed_df, user_id)
            
            return processed_df
        except Exception as e:
            self.logger.error(f"Error in preprocess_transactions for user {user_id}: {e}")
            raise
    
    def _process_transactions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Process transactions with vectorized operations"""
        try:
            # Convert date to datetime and sort
            df = df.copy()  # Create a copy to avoid modifying original
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values(['date', 'stock'])
            
            # Create efficient date index without keeping the column
            df = df.set_index('date')
            
            # Calculate running totals using vectorized operations
            groups = df.groupby('stock')
            
            running_totals = []
            for symbol, group in groups:
                # Calculate running units and cost basis
                buy_mask = group['transaction_type'].str.lower().isin(['buy', 'reinvest', 'stock_transfer'])
                sell_mask = group['transaction_type'].str.lower() == 'sell'
                
                # First calculate cumulative buys
                buy_units = np.where(buy_mask, group['units'], 0)
                buy_costs = np.where(buy_mask, group['units'] * group['price'] + group['fee'], 0)
                
                # Calculate running totals for buys
                cumulative_buy_units = np.cumsum(buy_units)
                cumulative_buy_costs = np.cumsum(buy_costs)
                
                # Calculate running average cost basis with safe division
                avg_cost = np.zeros_like(cumulative_buy_units, dtype=float)
                nonzero_mask = cumulative_buy_units > 0
                if nonzero_mask.any():
                    avg_cost[nonzero_mask] = (
                        cumulative_buy_costs[nonzero_mask] / 
                        cumulative_buy_units[nonzero_mask]
                    )
                
                # Now handle sells using the running average cost
                sell_units = np.where(sell_mask, group['units'], 0)
                sell_costs = np.where(
                    sell_mask,
                    group['units'] * avg_cost,
                    0
                )
                
                # Calculate final running totals
                running_units = cumulative_buy_units - np.cumsum(sell_units)
                running_cost = cumulative_buy_costs - np.cumsum(sell_costs)
                
                # Add running totals to group
                group_with_totals = group.copy()
                group_with_totals['running_units'] = running_units
                group_with_totals['running_cost'] = running_cost
                group_with_totals['avg_cost'] = avg_cost  # This might be useful for debugging
                
                # Handle NaN values
                group_with_totals['running_cost'] = group_with_totals['running_cost'].fillna(0)
                running_totals.append(group_with_totals)
            
            if not running_totals:
                return df
                
            # Combine all groups and reset index to get date back as a column
            result = pd.concat(running_totals)
            result = result.reset_index()
            
            return result
        except Exception as e:
            self.logger.error(f"Error in _process_transactions: {e}")
            raise
    
    def _store_running_totals(self, df: pd.DataFrame, user_id: str):
        """Store running totals in SQLite cache"""
        try:
            if not user_id:
                self.logger.warning("No user_id provided for storing running totals")
                return

            try:
                # First clean up any old entries for this user
                with sqlite3.connect(self.db_path) as conn:
                    conn.execute("DELETE FROM transaction_cache WHERE user_id = ?", (user_id,))
                    
                # Then store new data
                with sqlite3.connect(self.db_path) as conn:
                    # Prepare data for storage
                    cache_data = []
                    for symbol, group in df.groupby('stock'):
                        latest = group.iloc[-1]
                        # Convert date properly from index
                        if isinstance(latest.name, pd.Timestamp):
                            cache_date = latest.name.date()
                        elif isinstance(latest.name, (datetime, date)):
                            cache_date = latest.name.date() if isinstance(latest.name, datetime) else latest.name
                        else:
                            cache_date = pd.Timestamp(latest['date']).date()

                        cache_data.append({
                            'user_id': user_id,
                            'date': cache_date.isoformat(),
                            'symbol': symbol,
                            'running_units': float(latest['running_units']),
                            'cost_basis': float(latest['running_cost']),
                            'realized_gl': 0.0,  # Calculate if needed
                            'dividend_income': 0.0,  # Calculate if needed
                            'option_gl': 0.0,  # Calculate if needed
                            'updated_at': datetime.now().isoformat()
                        })
                    
                    # Store in database
                    for data in cache_data:
                        conn.execute("""
                            INSERT OR REPLACE INTO transaction_cache 
                            (user_id, date, symbol, running_units, cost_basis, 
                             realized_gl, dividend_income, option_gl, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            data['user_id'], data['date'], data['symbol'], 
                            data['running_units'], data['cost_basis'],
                            data['realized_gl'], data['dividend_income'], 
                            data['option_gl'], data['updated_at']
                        ))
                        
            except Exception as e:
                self.logger.error(f"Error in _store_running_totals for user {user_id}: {e}")
        except Exception as e:
            self.logger.error(f"Error in _store_running_totals for user {user_id}: {e}")
    
    def get_cached_totals(self, user_id: str, symbol: str, as_of_date: date) -> Optional[Dict]:
        """Retrieve cached running totals"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT running_units, cost_basis, realized_gl, 
                           dividend_income, option_gl, updated_at
                    FROM transaction_cache 
                    WHERE user_id = ? AND symbol = ? AND date <= ?
                    ORDER BY date DESC LIMIT 1
                """, (user_id, symbol, as_of_date.isoformat()))
                
                result = cursor.fetchone()
                if result:
                    return {
                        'running_units': result[0],
                        'cost_basis': result[1],
                        'realized_gl': result[2],
                        'dividend_income': result[3],
                        'option_gl': result[4],
                        'last_update': datetime.fromisoformat(result[5])
                    }
                    
        except Exception as e:
            self.logger.error(f"Error in get_cached_totals for user {user_id}, symbol {symbol}: {e}")
        return None
