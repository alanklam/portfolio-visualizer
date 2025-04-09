import sqlite3
import json
from datetime import datetime, timedelta, date
import logging
from typing import Dict, Optional
from ..core.cache_config import get_cache_path

logger = logging.getLogger(__name__)

class MetricsCache:
    """Cache for portfolio performance metrics"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._memory_cache = {}
        self._last_calc = {}
        self._cache_interval = timedelta(hours=24)  # Cache metrics for 24 hours
        self.db_path = get_cache_path()
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for metrics caching"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS metrics_cache (
                        user_id TEXT,
                        metric_type TEXT,
                        start_date DATE,
                        end_date DATE,
                        metric_data TEXT,
                        updated_at TIMESTAMP,
                        PRIMARY KEY (user_id, metric_type, start_date, end_date)
                    )
                """)
        except Exception as e:
            self.logger.error(f"Error in _init_db initializing metrics cache DB: {e}")
    
    def get(self, user_id: str, metric_type: str, start_date: date, end_date: date) -> Optional[Dict]:
        """Get cached metrics if not expired"""
        try:
            current_time = datetime.now()
            
            # Check memory cache first
            cache_key = (user_id, metric_type, start_date, end_date)
            if (cache_key in self._memory_cache and 
                cache_key in self._last_calc and
                current_time - self._last_calc[cache_key] < self._cache_interval):
                return self._memory_cache[cache_key]
            
            # Check database cache
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    SELECT metric_data, updated_at 
                    FROM metrics_cache 
                    WHERE user_id = ? AND metric_type = ? 
                    AND start_date = ? AND end_date = ?
                """, (user_id, metric_type, start_date.isoformat(), end_date.isoformat()))
                
                result = cursor.fetchone()
                if result and (current_time - datetime.fromisoformat(result[1])) < self._cache_interval:
                    metric_data = json.loads(result[0])
                    self._memory_cache[cache_key] = metric_data
                    self._last_calc[cache_key] = datetime.fromisoformat(result[1])
                    return metric_data
                    
        except Exception as e:
            self.logger.error(f"Error in get retrieving cached metrics for {user_id}/{metric_type}: {e}")
        
        return None
    
    def set(self, user_id: str, metric_type: str, start_date: date, end_date: date, data: Dict):
        """Cache metrics calculation result"""
        try:
            current_time = datetime.now()
            cache_key = (user_id, metric_type, start_date, end_date)
            
            # Update memory cache
            self._memory_cache[cache_key] = data
            self._last_calc[cache_key] = current_time
            
            # Update database cache
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO metrics_cache 
                    (user_id, metric_type, start_date, end_date, metric_data, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user_id, 
                    metric_type,
                    start_date.isoformat(),
                    end_date.isoformat(),
                    json.dumps(data),
                    current_time.isoformat()
                ))
                
        except Exception as e:
            self.logger.error(f"Error in set storing metrics in cache for {user_id}/{metric_type}: {e}")
    
    def clear_expired(self):
        """Clear expired cache entries"""
        try:
            current_time = datetime.now()
            expiry_time = (current_time - self._cache_interval).isoformat()
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM metrics_cache WHERE updated_at < ?", (expiry_time,))
                
            # Clear memory cache
            self._memory_cache = {
                k: v for k, v in self._memory_cache.items()
                if self._last_calc.get(k) and current_time - self._last_calc[k] < self._cache_interval
            }
            self._last_calc = {
                k: v for k, v in self._last_calc.items()
                if current_time - v < self._cache_interval
            }
            
        except Exception as e:
            self.logger.error(f"Error in clear_expired clearing expired cache: {e}")
