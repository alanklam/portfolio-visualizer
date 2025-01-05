from typing import Dict, List
import pandas as pd
from datetime import datetime, date
import numpy as np

class DataProcessor:
    REQUIRED_COLUMNS = [
        'date', 'transaction_type', 'stock', 'units', 
        'price', 'fee', 'security_type', 'broker'
    ]
    
    VALID_TRANSACTION_TYPES = [
        'buy', 'sell', 'reinvest', 'assigned', 'expired',
        'sell_to_open', 'buy_to_open', 'sell_to_close', 'buy_to_close',
        'adjustment', 'dividend', 'interest', 'transfer', 'split'
    ]
    
    VALID_SECURITY_TYPES = ['stock', 'option', 'cash', 'fixed_income']
    VALID_OPTION_TYPES = ['call', 'put', None]  # None for stocks, cash, and fixed income
    
    # Transactions that don't require units or price
    NON_TRADE_TYPES = ['expired', 'dividend', 'interest', 'transfer']
    
    # Transactions that affect cash position
    CASH_AFFECTING_TYPES = ['dividend', 'interest', 'transfer']
    
    @staticmethod
    def standardize_dates(date_str: str, format: str = None) -> date:
        """Convert dates to standard format"""
        try:
            if format:
                dt = pd.to_datetime(date_str, format=format)
            else:
                dt = pd.to_datetime(date_str)
            return dt.date()
        except ValueError as e:
            # Try to handle "as of" dates
            try:
                date_str = date_str.split(' as of')[0]
                return pd.to_datetime(date_str).date()
            except:
                raise ValueError(f"Failed to parse date {date_str}: {str(e)}")

    @staticmethod
    def process_transaction(row: Dict) -> Dict:
        """Process a single transaction row"""
        processed = row.copy()
        
        # Convert numeric values
        for field in ['units', 'price', 'fee']:
            if field in processed and not pd.isna(processed[field]):
                processed[field] = float(processed[field])
            else:
                processed[field] = 0.0
        
        # Standardize transaction type
        if 'transaction_type' in processed:
            processed['transaction_type'] = processed['transaction_type'].lower()
        
        # Standardize security type
        if 'security_type' in processed:
            processed['security_type'] = processed['security_type'].lower()
        
        # Standardize stock symbol
        if 'stock' in processed:
            processed['stock'] = processed['stock'].upper().strip()
        
        # Standardize option type
        if 'option_type' in processed and processed['option_type']:
            processed['option_type'] = processed['option_type'].lower()
        
        # Handle fixed income redemptions and interest
        if processed.get('security_type') == 'fixed_income':
            if processed.get('transaction_type') in ['interest', 'dividend']:
                processed['security_type'] = 'cash'
                processed['price'] = 1.0
            elif 'redemption' in str(processed.get('description', '')).lower():
                processed['security_type'] = 'cash'
                processed['price'] = 1.0
        
        return processed

    @staticmethod
    def handle_missing_values(df: pd.DataFrame) -> pd.DataFrame:
        """Handle missing values in the dataset"""
        df_cleaned = df.copy()
        
        # Fill missing fees with 0
        df_cleaned['fee'] = df_cleaned['fee'].fillna(0)
        
        # Fill missing security type with 'stock'
        df_cleaned['security_type'] = df_cleaned['security_type'].fillna('stock')
        
        # Fill missing option type with None for non-option securities
        df_cleaned.loc[df_cleaned['security_type'] != 'option', 'option_type'] = None
        
        # Handle special cases
        for idx, row in df_cleaned.iterrows():
            # For assigned options, derive price if missing
            if row['transaction_type'] == 'assigned' and pd.isna(row['price']):
                # Extract strike price from description if available
                if 'Description' in df_cleaned.columns:
                    desc = str(row['Description'])
                    import re
                    strike_match = re.search(r'\$(\d+(\.\d+)?)', desc)
                    if strike_match:
                        df_cleaned.loc[idx, 'price'] = float(strike_match.group(1))
            
            # For cash equivalents and fixed income redemptions
            if row['security_type'] in ['cash', 'fixed_income'] and pd.isna(row['price']):
                if row['transaction_type'] in DataProcessor.CASH_AFFECTING_TYPES:
                    df_cleaned.loc[idx, 'price'] = 1.0
            
            # For stock splits
            if row['transaction_type'] == 'split' and pd.isna(row['price']):
                df_cleaned.loc[idx, 'price'] = 0.0
        
        # Drop rows with missing critical values, except for certain transaction types
        critical_columns = ['date', 'transaction_type', 'stock']
        df_cleaned = df_cleaned.dropna(subset=critical_columns)
        
        # Process each row
        df_cleaned = pd.DataFrame([
            DataProcessor.process_transaction(row) 
            for _, row in df_cleaned.iterrows()
        ])
        
        return df_cleaned

    @staticmethod
    def validate_data(df: pd.DataFrame) -> bool:
        """Validate data against schema"""
        try:
            # Check required columns
            missing_cols = set(DataProcessor.REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Validate transaction types
            invalid_types = set(df['transaction_type'].unique()) - set(DataProcessor.VALID_TRANSACTION_TYPES)
            if invalid_types:
                raise ValueError(f"Invalid transaction types found: {invalid_types}")
            
            # Validate security types
            invalid_securities = set(df['security_type'].unique()) - set(DataProcessor.VALID_SECURITY_TYPES)
            if invalid_securities:
                raise ValueError(f"Invalid security types found: {invalid_securities}")
            
            # Validate option types
            if 'option_type' in df.columns:
                invalid_options = set(df['option_type'].unique()) - set(DataProcessor.VALID_OPTION_TYPES)
                if invalid_options:
                    raise ValueError(f"Invalid option types found: {invalid_options}")
            
            # Validate numeric values for trade transactions
            trade_mask = ~df['transaction_type'].isin(DataProcessor.NON_TRADE_TYPES + ['split'])
            
            if (df.loc[trade_mask, 'units'] == 0).any():
                raise ValueError("Found trade transactions with zero units")
            
            if (df.loc[trade_mask, 'price'] < 0).any():
                raise ValueError("Found negative prices")
            
            if (df['fee'] < 0).any():
                raise ValueError("Found negative fees")
            
            # Validate dates
            if df['date'].isnull().any():
                raise ValueError("Found null dates")
            
            return True
            
        except Exception as e:
            print(f"Validation failed: {str(e)}")
            return False 