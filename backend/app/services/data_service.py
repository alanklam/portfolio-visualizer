import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional
import os
import re
import warnings
import yfinance as yf
import io

logger = logging.getLogger(__name__)

def process_csv_file(df: pd.DataFrame, broker: str = 'schwab') -> List[Dict[str, Any]]:
    """Process a CSV file and return a list of transaction dictionaries"""
    data_service = DataService()
    
    # Convert DataFrame to list of dictionaries
    transactions = []
    
    if broker.lower() == 'schwab':
        for _, row in df.iterrows():
            transaction = data_service._process_schwab_transaction(row)
            if transaction:
                transactions.append(transaction)
    elif broker.lower() == 'fidelity':
        for _, row in df.iterrows():
            transaction = data_service._process_fidelity_transaction(row)
            if transaction:
                transactions.append(transaction)
    elif broker.lower() == 'etrade':
        for _, row in df.iterrows():
            transaction = data_service._process_etrade_transaction(row)
            if transaction:
                transactions.append(transaction)
    else:
        raise ValueError(f"Unsupported broker: {broker}")
    
    # Convert to DataFrame for validation and standardization
    df_processed = pd.DataFrame(transactions)
    df_processed['broker'] = broker.lower()
    
    # Handle missing values and validate
    df_processed = data_service.handle_missing_values(df_processed)
    if not data_service.validate_data(df_processed):
        raise ValueError("Data validation failed")
    
    return df_processed.to_dict('records')

class DataService:
    # Constants
    REQUIRED_COLUMNS = [
        'date', 'transaction_type', 'stock', 'units', 
        'price', 'fee', 'security_type', 'broker'
    ]
    
    VALID_TRANSACTION_TYPES = [
        'buy', 'sell', 'reinvest', 'assigned', 'expired',
        'sell_to_open', 'buy_to_open', 'sell_to_close', 'buy_to_close',
        'adjustment', 'dividend', 'interest', 'transfer', 'split', 'other'
    ]
    
    VALID_SECURITY_TYPES = ['stock', 'option', 'cash', 'fixed_income']
    VALID_OPTION_TYPES = ['call', 'put', None]
    NON_TRADE_TYPES = ['expired', 'dividend', 'interest', 'transfer']
    CASH_AFFECTING_TYPES = ['dividend', 'interest', 'transfer']

    # Constants from CSVParser
    CASH_EQUIVALENTS = ['SWVXX', 'SPAXX']
    FIXED_INCOME_PATTERNS = [
        r'TREAS BILL', r'TREASURY BILL', r'T-BILL',
        r'TREAS NOTE', r'TREASURY NOTE', r'T-NOTE',
        r'TREAS BOND', r'TREASURY BOND', r'T-BOND',
        r'BOND', r'CERTIFICATE OF DEPOSIT',
        r'CD\s+\d',  # CD followed by numbers
        r'GOVT\s+SECURITY', r'INT', r'INTEREST'
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def extract_amount(amount_str: str) -> float:
        """Extract numeric amount from string, handling currency symbols and commas."""
        if pd.isna(amount_str):
            return 0.0
        return float(str(amount_str).replace('$', '').replace(',', '').strip())

    @staticmethod
    def is_fixed_income_symbol(symbol: str) -> bool:
        """Check if a symbol represents a fixed income security based on its format."""
        if pd.isna(symbol):
            return False
        symbol = str(symbol).strip()
        return bool(re.match(r'^\d', symbol))

    @staticmethod
    def clean_symbol(symbol: str, security_type: str = None) -> str:
        """Clean up stock symbol, removing option-related information."""
        if pd.isna(symbol):
            return symbol
            
        symbol = str(symbol).strip().upper()
        
        if security_type == 'option':
            # Remove leading dash if present
            symbol = symbol.lstrip('-')
            
            # Remove date patterns
            symbol = re.sub(r'[\s_]\d{2}/?[0-1]\d/?2?\d', '', symbol)
            symbol = re.sub(r'[\s_](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{4}', '', symbol, flags=re.IGNORECASE)
            symbol = re.sub(r'\d{2}/\d{2}/\d{4}', '', symbol)
            symbol = re.sub(r'\d{6}[CP]', '', symbol)
            
            # Remove strike price and option type
            symbol = re.sub(r'[\s_][CP]\d+(\.\d+)?', '', symbol)
            symbol = re.sub(r'[\s_](Call|Put)', '', symbol, flags=re.IGNORECASE)
            symbol = re.sub(r'[\s_]\d+(\.\d+)?[\s_]?[CP]?', '', symbol)
            
            # Remove trailing year numbers
            symbol = re.sub(r'\d{2}$', '', symbol)
            
            # Take only the first part
            symbol = symbol.split()[0]
        
        return symbol.strip()

    @staticmethod
    def standardize_dates(date_str: str) -> datetime:
        """Convert various date formats to datetime object."""
        if pd.isna(date_str):
            raise ValueError("Date cannot be null")
            
        # Remove any whitespace
        date_str = str(date_str).strip()
        
        # Handle "MM/DD/YYYY as of MM/DD/YYYY" format
        if ' as of ' in date_str:
            date_str = date_str.split(' as of ')[0]  # Take the first date
            
        try:
            # Try parsing with various formats
            for fmt in ['%m/%d/%Y', '%Y-%m-%d', '%Y/%m/%d']:
                try:
                    return pd.to_datetime(date_str, format=fmt)
                except ValueError:
                    continue
            
            # If none of the specific formats work, try the general parser
            return pd.to_datetime(date_str)
            
        except Exception as e:
            raise ValueError(f"Error parsing date {date_str}: {str(e)}")

    def handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
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
                if 'Description' in df_cleaned.columns:
                    desc = str(row['Description'])
                    strike_match = re.search(r'\$(\d+(\.\d+)?)', desc)
                    if strike_match:
                        df_cleaned.loc[idx, 'price'] = float(strike_match.group(1))
            
            # For cash equivalents and fixed income redemptions
            if row['security_type'] in ['cash', 'fixed_income'] and pd.isna(row['price']):
                if row['transaction_type'] in self.CASH_AFFECTING_TYPES:
                    df_cleaned.loc[idx, 'price'] = 1.0
            
            # For stock splits
            if row['transaction_type'] == 'split' and pd.isna(row['price']):
                df_cleaned.loc[idx, 'price'] = 0.0
        
        # Drop rows with missing critical values
        critical_columns = ['date', 'transaction_type', 'stock']
        df_cleaned = df_cleaned.dropna(subset=critical_columns)
        
        return df_cleaned

    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate data against schema"""
        try:
            # Check required columns
            missing_cols = set(self.REQUIRED_COLUMNS) - set(df.columns)
            if missing_cols:
                raise ValueError(f"Missing required columns: {missing_cols}")
            
            # Validate transaction types
            invalid_types = set(df['transaction_type'].unique()) - set(self.VALID_TRANSACTION_TYPES)
            if invalid_types:
                raise ValueError(f"Invalid transaction types found: {invalid_types}")
            
            # Validate security types
            invalid_securities = set(df['security_type'].unique()) - set(self.VALID_SECURITY_TYPES)
            if invalid_securities:
                raise ValueError(f"Invalid security types found: {invalid_securities}")
            
            # Validate option types
            if 'option_type' in df.columns:
                invalid_options = set(df['option_type'].unique()) - set(self.VALID_OPTION_TYPES)
                if invalid_options:
                    raise ValueError(f"Invalid option types found: {invalid_options}")
            
            # Validate numeric values for trade transactions
            trade_mask = ~df['transaction_type'].isin(self.NON_TRADE_TYPES + ['split'])
            
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
            self.logger.error(f"Validation failed: {str(e)}")
            return False

    def _process_schwab_transaction(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Process Schwab transaction format"""
        # Extract symbol from Description if Symbol is missing
        symbol = str(row.get('Symbol', '')).strip()
        if not symbol:
            symbol = str(row.get('Description', '')).split('(')[-1].strip(')')  # Extract from Description if missing

        # Extract option information from Description
        option_type = None
        description = str(row.get('Description', '')).lower()
        if 'call' in description:
            option_type = 'call'
        elif 'put' in description:
            option_type = 'put'

        # Handle security types
        security_type = 'stock'
        if 'option' in description:
            security_type = 'option'
        elif self.is_fixed_income_symbol(symbol):
            security_type = 'fixed_income'
            symbol = 'FIXED INCOME'  # Set to a standard name for fixed income
        elif symbol in self.CASH_EQUIVALENTS:
            security_type = 'cash'
            symbol = 'CASH EQUIVALENTS'  # Set to a standard name for cash equivalents

        # Clean symbol for non-fixed-income securities
        if security_type != 'fixed_income':
            symbol = self.clean_symbol(symbol, security_type)

        # Handle money transfers
        if row.get('Action') == 'MoneyLink Transfer':
            security_type = 'cash'
            symbol = 'CASH EQUIVALENTS'
            price = 1.0
            quantity = float(row.get('Quantity', 0)) if row.get('Quantity') else 0.0
        else:
            price = float(str(row.get('Price', 0)).replace('$', '').replace(',', ''))
            quantity = float(str(row.get('Quantity', 0)).replace(',', ''))

        # Handle fixed income securities from description
        for pattern in self.FIXED_INCOME_PATTERNS:
            if re.search(pattern, description, re.IGNORECASE):
                security_type = 'fixed_income'
                symbol = 'FIXED INCOME'
                break

        # Handle interest and dividend transactions
        if row.get('Action') in ['Bond Interest', 'Credit Interest', 'Qualified Dividend', 'Qual Div Reinvest']:
            quantity = float(str(row.get('Amount', 0)).replace('$', '').replace(',', ''))
            price = 1.0  # Set price to 1.0 for interest/dividend transactions

        # Handle fixed income units conversion (divide by 100 for buy and sell transactions)
        if security_type == 'fixed_income' and row.get('Action') in ['Buy', 'Sell']:
            quantity /= 100

        # Return the processed transaction
        return {
            'date': self.standardize_dates(row['Date']),
            'stock': symbol,
            'transaction_type': self.map_transaction_type(row['Action']),
            'units': quantity,
            'price': price,
            'fee': float(str(row.get('Fees & Comm', 0)).replace('$', '').replace(',', '')),
            'option_type': option_type,
            'security_type': security_type,
            'amount': float(str(row.get('Amount', 0)).replace('$', '').replace(',', ''))
        }

    def map_transaction_type(self, action: str) -> str:
        """Map Schwab action to standardized transaction type"""
        transaction_map = {
            'BUY': 'buy',
            'SELL': 'sell',
            'REINVEST SHARES': 'reinvest',
            'REINVEST DIVIDEND': 'dividend',
            'EXPIRED': 'expired',
            'SELL TO OPEN': 'sell_to_open',
            'BUY TO OPEN': 'buy_to_open',
            'SELL TO CLOSE': 'sell_to_close',
            'BUY TO CLOSE': 'buy_to_close',
            'QUALIFIED DIVIDEND': 'dividend',
            'QUAL DIV REINVEST': 'dividend',
            'BOND INTEREST': 'interest',
            'CREDIT INTEREST': 'interest',
            'MONEYLINK TRANSFER': 'transfer',
            'STOCK SPLIT': 'split'
        }
        return transaction_map.get(action.upper(), 'other')

    def _process_fidelity_transaction(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Process Fidelity transaction format"""
        action = str(row['Action']).upper()
        
        # Extract transaction type
        transaction_map = {
            'YOU BOUGHT': {
                'OPENING TRANSACTION': 'buy_to_open',
                'CLOSING TRANSACTION': 'buy_to_close',
                None: 'buy'
            },
            'YOU SOLD': {
                'OPENING TRANSACTION': 'sell_to_open',
                'CLOSING TRANSACTION': 'sell_to_close',
                None: 'sell'
            },
            'REINVESTMENT': 'reinvest',
            'DIVIDEND': 'dividend',
            'ASSIGNED': 'assigned',
            'EXPIRED': 'expired',
            'STOCK SPLIT': 'split',
            'TRANSFER': 'transfer'
        }
        
        transaction_type = 'other'
        for key, value in transaction_map.items():
            if key in action:
                if isinstance(value, dict):
                    for sub_key, sub_value in value.items():
                        if sub_key and sub_key in action:
                            transaction_type = sub_value
                            break
                    if transaction_type == 'other':
                        transaction_type = value[None]
                else:
                    transaction_type = value
        
        # Determine security type
        security_type = 'stock'
        description = str(row.get('Description', '')).lower()
        if 'option' in description:
            security_type = 'option'
        elif self.is_fixed_income_symbol(row['Symbol']):
            security_type = 'fixed_income'
        elif row['Symbol'] in self.CASH_EQUIVALENTS:
            security_type = 'cash'
        
        # Clean symbol
        symbol = self.clean_symbol(row['Symbol'], security_type)
        
        # Handle fixed income and cash equivalents
        if security_type == 'fixed_income':
            symbol = 'FIXED INCOME'
        elif security_type == 'cash':
            symbol = 'CASH EQUIVALENTS'
        
        return {
            'date': self.standardize_dates(row['Date']),
            'stock': symbol,
            'transaction_type': transaction_type,
            'units': abs(float(str(row.get('Quantity', 0)).replace(',', ''))),
            'price': float(str(row.get('Price', 0)).replace('$', '').replace(',', '')),
            'fee': float(str(row.get('Commission', 0)).replace('$', '').replace(',', '')),
            'option_type': 'call' if 'call' in description else 'put' if 'put' in description else None,
            'security_type': security_type,
            'amount': float(str(row.get('Amount', 0)).replace('$', '').replace(',', ''))
        }

    def _process_etrade_transaction(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """Process E*TRADE transaction format"""
        action = str(row.get('Transaction Type', '')).upper()
        
        # Map transaction types
        transaction_map = {
            'BOUGHT': 'buy',
            'SOLD': 'sell',
            'DIVIDEND REINVESTMENT': 'reinvest',
            'DIVIDEND': 'dividend',
            'SOLD SHORT': 'sell_to_open',
            'BOUGHT TO OPEN': 'buy_to_open',
            'SOLD TO CLOSE': 'sell_to_close',
            'BOUGHT TO COVER': 'buy_to_close',
            'ADJUSTMENT': 'adjustment',
            'STOCK SPLIT': 'split',
            'TRANSFER': 'transfer'
        }
        transaction_type = transaction_map.get(action, 'other')
        
        # Determine security type
        security_type = 'stock'
        description = str(row.get('Description', '')).lower()
        if 'option' in description:
            security_type = 'option'
        elif self.is_fixed_income_symbol(row['Symbol']):
            security_type = 'fixed_income'
        elif row['Symbol'] in self.CASH_EQUIVALENTS:
            security_type = 'cash'
        
        # Clean symbol
        symbol = self.clean_symbol(row['Symbol'], security_type)
        
        # Handle fixed income and cash equivalents
        if security_type == 'fixed_income':
            symbol = 'FIXED INCOME'
        elif security_type == 'cash':
            symbol = 'CASH EQUIVALENTS'
        
        # Handle adjustments by fetching historical prices
        price = float(str(row.get('Price', 0)).replace('$', '').replace(',', ''))
        if transaction_type == 'adjustment' and price == 0:
            try:
                date = pd.to_datetime(row['Date'])
                last_day_prev_month = (date.replace(day=1) - timedelta(days=1))
                
                for days_back in range(5):
                    try_date = last_day_prev_month - timedelta(days=days_back)
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        ticker = yf.download(symbol, start=try_date, end=try_date + timedelta(days=1), progress=False)
                    if not ticker.empty:
                        price = ticker['Close'].values[0]
                        break
            except Exception as e:
                self.logger.error(f"Failed to fetch historical price for {symbol}: {str(e)}")
        
        return {
            'date': self.standardize_dates(row['Date']),
            'stock': symbol,
            'transaction_type': transaction_type,
            'units': float(str(row.get('Quantity', 0)).replace(',', '')),
            'price': price,
            'fee': float(str(row.get('Commission', 0)).replace('$', '').replace(',', '')),
            'option_type': 'call' if 'call' in description else 'put' if 'put' in description else None,
            'security_type': security_type,
            'amount': float(str(row.get('Net Amount', 0)).replace('$', '').replace(',', ''))
        } 