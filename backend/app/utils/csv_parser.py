import pandas as pd
from typing import Dict, Any
from io import StringIO
from datetime import datetime, timedelta
import yfinance as yf
from .data_processor import DataProcessor
import re
import warnings

class CSVParser:
    # Constants
    CASH_EQUIVALENTS = ['SWVXX', 'SPAXX']
    FIXED_INCOME_PATTERNS = [
        r'TREAS BILL',
        r'TREASURY BILL',
        r'T-BILL',
        r'TREAS NOTE',
        r'TREASURY NOTE',
        r'T-NOTE',
        r'TREAS BOND',
        r'TREASURY BOND',
        r'T-BOND',
        r'BOND',
        r'CERTIFICATE OF DEPOSIT',
        r'CD\s+\d',  # CD followed by numbers
        r'GOVT\s+SECURITY'
    ]
    
    FIXED_INCOME_ACTION_PATTERNS = [
        r'INTEREST',
        r'REDEMPTION',
        r'MATURED',
        r'CALLED'
    ]

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
        # Check if symbol starts with a digit (common for treasury securities)
        # Examples: 912796ZV4, 91282CJL6
        if re.match(r'^\d', symbol):
            return True
            
        return False

    @staticmethod
    def clean_symbol(symbol: str, security_type: str = None) -> str:
        """Clean up stock symbol, removing option-related information."""
        if pd.isna(symbol):
            return symbol
            
        symbol = str(symbol).strip().upper()
        
        # For options, extract only the underlying symbol
        if security_type == 'option':
            # Common option symbol formats:
            # SPY_011524C500 -> SPY
            # SPY 01/15/24 C500 -> SPY
            # SPY Jan 15 2024 500.0 Call -> SPY
            # SPY 07/07/2023 500 P -> SPY
            # -SPY230120P500 -> SPY
            # TSLA 01/17/2025 430.00 P -> TSLA
            
            # Remove leading dash if present
            symbol = symbol.lstrip('-')
            
            # Remove date patterns
            symbol = re.sub(r'[\s_]\d{2}/?[0-1]\d/?2?\d', '', symbol)
            symbol = re.sub(r'[\s_](Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}\s+\d{4}', '', symbol, flags=re.IGNORECASE)
            symbol = re.sub(r'\d{2}/\d{2}/\d{4}', '', symbol)  # MM/DD/YYYY format
            symbol = re.sub(r'\d{6}[CP]', '', symbol)  # YYMMDD[C/P] format
            
            # Remove strike price and option type
            symbol = re.sub(r'[\s_][CP]\d+(\.\d+)?', '', symbol)
            symbol = re.sub(r'[\s_](Call|Put)', '', symbol, flags=re.IGNORECASE)
            symbol = re.sub(r'[\s_]\d+(\.\d+)?[\s_]?[CP]?', '', symbol)
            
            # Remove any trailing year numbers (e.g. TSLA25 -> TSLA)
            symbol = re.sub(r'\d{2}$', '', symbol)
            
            # Take only the first part (usually the underlying symbol)
            symbol = symbol.split()[0]
        
        return symbol.strip()

    @staticmethod
    def parse_schwab(content: str) -> pd.DataFrame:
        """Parse Charles Schwab CSV format"""
        df = pd.read_csv(StringIO(content))
        
        # Standardize column names
        df.columns = [col.strip('"') for col in df.columns]
        
        # Extract option information from Description
        df['option_type'] = None
        df.loc[df['Description'].str.contains(' C ', na=False), 'option_type'] = 'call'
        df.loc[df['Description'].str.contains(' P ', na=False), 'option_type'] = 'put'
        
        # Handle security types
        df['security_type'] = 'stock'
        df.loc[df['Description'].str.contains('PUT|CALL', na=False), 'security_type'] = 'option'
        
        # Handle fixed income securities with numeric symbols
        fixed_income_mask = df['Symbol'].apply(CSVParser.is_fixed_income_symbol)
        df.loc[fixed_income_mask, 'security_type'] = 'fixed_income'
        df.loc[fixed_income_mask, 'Symbol'] = 'FIXED INCOME'
        
        # Clean symbols for non-fixed-income securities
        df.loc[~fixed_income_mask, 'Symbol'] = df[~fixed_income_mask].apply(
            lambda row: CSVParser.clean_symbol(row['Symbol'], row['security_type']), axis=1
        )
        
        # Handle cash equivalents
        for symbol in CSVParser.CASH_EQUIVALENTS:
            df.loc[df['Symbol'] == symbol, 'security_type'] = 'cash'
            df.loc[df['Symbol'] == symbol, 'Symbol'] = 'CASH EQUIVALENTS'
        
        # Handle money transfers
        transfer_mask = df['Action'] == 'MoneyLink Transfer'
        df.loc[transfer_mask, 'security_type'] = 'cash'
        df.loc[transfer_mask, 'Symbol'] = 'CASH EQUIVALENTS'
        df.loc[transfer_mask, 'Price'] = 1.0
        # Get transfer amount from Amount column if Quantity is missing
        df.loc[transfer_mask & df['Quantity'].isna(), 'Quantity'] = df.loc[transfer_mask & df['Quantity'].isna(), 'Amount'].apply(CSVParser.extract_amount)
        
        # Handle fixed income securities from description
        for pattern in CSVParser.FIXED_INCOME_PATTERNS:
            mask = df['Description'].str.contains(pattern, na=False, case=False)
            df.loc[mask, 'security_type'] = 'fixed_income'
            df.loc[mask, 'Symbol'] = 'FIXED INCOME'
            # For interest payments only, set as cash
            interest_mask = mask & df['Description'].str.contains('INTEREST', na=False, case=False)
            df.loc[interest_mask, 'security_type'] = 'cash'
            df.loc[interest_mask, 'Symbol'] = 'CASH EQUIVALENTS'
        
        # Map action types
        action_map = {
            'Buy': 'buy',
            'Sell': 'sell',
            'Reinvest Shares': 'reinvest',
            'Reinvest Dividend': 'dividend',
            'Assigned': 'assigned',
            'Expired': 'expired',
            'Sell to Open': 'sell_to_open',
            'Buy to Open': 'buy_to_open',
            'Sell to Close': 'sell_to_close',
            'Buy to Close': 'buy_to_close',
            'Qualified Dividend': 'dividend',
            'Bank Interest': 'interest',
            'MoneyLink Transfer': 'transfer',
            'Stock Split': 'split'
        }
        
        # Handle special cases for assignments
        df['original_action'] = df['Action']
        df.loc[(df['Action'] == 'Assigned') & (df['option_type'] == 'call'), 'Action'] = 'Sell'
        df.loc[(df['Action'] == 'Assigned') & (df['option_type'] == 'put'), 'Action'] = 'Buy'
        
        # Filter relevant transactions
        df = df[df['Action'].isin(list(action_map.keys()))]
        
        # Extract amount when price is missing
        df.loc[df['Price'].isna() & df['Amount'].notna(), 'Price'] = (
            pd.to_numeric(df['Amount'].str.replace('$', '').str.replace(',', ''), errors='coerce').abs() / 
            pd.to_numeric(df['Quantity'].str.replace(',', ''), errors='coerce')
        )
        
        # Handle interest and dividend transactions
        df.loc[df['Action'].isin(['Bank Interest', 'Qualified Dividend']), 'Quantity'] = (
            pd.to_numeric(df['Amount'].str.replace('$', '').str.replace(',', ''), errors='coerce')
        )
        df.loc[df['Action'].isin(['Bank Interest', 'Qualified Dividend']), 'Price'] = 1.0
        
        # Convert quantity to numeric
        df['Quantity'] = pd.to_numeric(df['Quantity'].str.replace(',', ''), errors='coerce')
        
        # Handle fixed income units conversion (divide by 100 for buy and sell transactions)
        fixed_income_buy_mask = (df['security_type'] == 'fixed_income') & (df['Action'].isin(['Buy', 'Sell']))
        df.loc[fixed_income_buy_mask, 'Quantity'] = df.loc[fixed_income_buy_mask, 'Quantity'] / 100

        # Map columns to standard format
        df_mapped = pd.DataFrame({
            'date': pd.to_datetime(df['Date'].str.split(' as of').str[0]),
            'transaction_type': df['Action'].map(action_map),
            'stock': df['Symbol'],
            'units': df['Quantity'],
            'price': pd.to_numeric(df['Price'].str.replace('$', '').str.replace(',', ''), errors='coerce'),
            'fee': pd.to_numeric(df['Fees & Comm'].str.replace('$', '').str.replace(',', ''), errors='coerce').fillna(0),
            'security_type': df['security_type'],
            'option_type': df['option_type'],
            'amount': pd.to_numeric(df['Amount'].str.replace('$', '').str.replace(',', ''), errors='coerce')
        })
        
        return df_mapped

    @staticmethod
    def parse_etrade(content: str) -> pd.DataFrame:
        """Parse E-Trade CSV format"""
        df = pd.read_csv(StringIO(content), skiprows=2)  # Skip the account info rows
        
        # Filter out UNKNOWN security types
        df = df[df['SecurityType'] != 'UNKNOWN']
        
        # Map transaction types
        transaction_map = {
            'Bought': 'buy',
            'Sold': 'sell',
            'Dividend Reinvestment': 'reinvest',
            'Dividend': 'dividend',
            'Sold Short': 'sell_to_open',
            'Bought To Open': 'buy_to_open',
            'Sold To Close': 'sell_to_close',
            'Bought To Cover': 'buy_to_close',
            'Adjustment': 'adjustment',
            'Stock Split': 'split',
            'Transfer': 'transfer'
        }
        
        # Filter relevant transactions
        df = df[df['TransactionType'].isin(list(transaction_map.keys()))]
        
        # Map security types
        security_type_map = {
            'EQ': 'stock',
            'OPTN': 'option',
            'FIXED': 'fixed_income',
            'CASH': 'cash'
        }
        df['security_type'] = df['SecurityType'].map(security_type_map)
        
        # Handle fixed income securities with numeric symbols
        fixed_income_mask = df['Symbol'].apply(CSVParser.is_fixed_income_symbol)
        df.loc[fixed_income_mask, 'security_type'] = 'fixed_income'
        df.loc[fixed_income_mask, 'Symbol'] = 'FIXED INCOME'
        
        # Clean symbols for non-fixed-income securities
        df.loc[~fixed_income_mask, 'Symbol'] = df[~fixed_income_mask].apply(
            lambda row: CSVParser.clean_symbol(row['Symbol'], row['security_type']), axis=1
        )
        
        # Handle cash equivalents
        cash_mask = df['security_type'] == 'cash'
        df.loc[cash_mask, 'Symbol'] = 'CASH EQUIVALENTS'
        
        # Handle transfers
        transfer_mask = df['TransactionType'] == 'Transfer'
        df.loc[transfer_mask, 'security_type'] = 'cash'
        df.loc[transfer_mask, 'Symbol'] = 'CASH EQUIVALENTS'
        df.loc[transfer_mask, 'Price'] = 1.0
        # Get transfer amount from Amount column if Quantity is missing
        df.loc[transfer_mask & df['Quantity'].isna(), 'Quantity'] = df.loc[transfer_mask & df['Quantity'].isna(), 'Amount'].apply(CSVParser.extract_amount)
        
        # Convert quantity to numeric
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
        
        # Handle fixed income units conversion (divide by 100 for buy and sold transactions)
        fixed_income_buy_mask = (df['security_type'] == 'fixed_income') & (df['TransactionType'].isin(['Bought','Sold']))
        df.loc[fixed_income_buy_mask, 'Quantity'] = df.loc[fixed_income_buy_mask, 'Quantity'] / 100
        
        # Handle adjustments by fetching historical prices
        adjustment_rows = df['TransactionType'] == 'Adjustment'
        if adjustment_rows.any():
            for idx in df[adjustment_rows].index:
                symbol = df.loc[idx, 'Symbol']
                date_str = df.loc[idx, 'TransactionDate']
                try:
                    # Convert date to datetime
                    date = pd.to_datetime(date_str)
                    # Get the last day of previous month
                    last_day_prev_month = (date.replace(day=1) - timedelta(days=1))
                    
                    # Try to get the price for up to 5 previous days
                    for days_back in range(5):
                        try_date = last_day_prev_month - timedelta(days=days_back)
                        # Fetch historical data with warnings suppressed
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore")
                            ticker = yf.download(symbol, start=try_date, end=try_date + timedelta(days=1), progress=False)
                        if not ticker.empty:
                            df.loc[idx, 'Price'] = ticker['Close'].values[0]
                            break
                except Exception as e:
                    print(f"Failed to fetch historical price for {symbol} on {date_str}: {str(e)}")
        
        # Map columns to standard format
        df_mapped = pd.DataFrame({
            'date': pd.to_datetime(df['TransactionDate']),
            'transaction_type': df['TransactionType'].map(lambda x: transaction_map.get(x, 'adjustment')),
            'stock': df['Symbol'],
            'units': df['Quantity'],
            'price': pd.to_numeric(df['Price'], errors='coerce'),
            'fee': pd.to_numeric(df['Commission'], errors='coerce').fillna(0),
            'security_type': df['security_type'],
            'option_type': df['Description'].str.extract(r'(\bCall|\bPut\b)', flags=re.IGNORECASE)[0].str.lower(),
            'amount': pd.to_numeric(df['Amount'], errors='coerce')
        })
        
        return df_mapped

    @staticmethod
    def parse_fidelity(content: str) -> pd.DataFrame:
        """Parse Fidelity CSV format"""
        # Read until the disclaimer
        content_lines = content.split('\n')
        data_lines = []
        for line in content_lines:
            if line.startswith('"The data and information'):
                break
            data_lines.append(line)
        
        df = pd.read_csv(StringIO('\n'.join(data_lines)))
        
        # Clean up column names
        df.columns = df.columns.str.strip()
        
        # Extract transaction type from Action
        def extract_transaction_type(action):
            action = str(action).upper()
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
            
            for key, value in transaction_map.items():
                if key in action:
                    if isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if sub_key in action:
                                return sub_value
                        return value[None]  # Default case for the main key
                    return value
            
            return None
        
        # Clean up symbol and handle security types
        df['Symbol'] = df['Symbol'].str.strip()
        df['security_type'] = 'stock'  # Default to stock
        
        # Handle options
        option_mask = (df['Type'].str.contains('OPTION', case=False, na=False) |
                      df['Description'].str.contains(r'CALL|PUT', case=False, na=False))
        df.loc[option_mask, 'security_type'] = 'option'
        
        # Extract option type (call/put)
        df['option_type'] = None
        df.loc[df['Description'].str.contains(r'\bCALL\b', case=False, na=False), 'option_type'] = 'call'
        df.loc[df['Description'].str.contains(r'\bPUT\b', case=False, na=False), 'option_type'] = 'put'
        
        # Handle fixed income securities with numeric symbols
        fixed_income_mask = df['Symbol'].apply(CSVParser.is_fixed_income_symbol)
        df.loc[fixed_income_mask, 'security_type'] = 'fixed_income'
        df.loc[fixed_income_mask, 'Symbol'] = 'FIXED INCOME'
        
        # Clean symbols for non-fixed-income securities
        df.loc[~fixed_income_mask, 'Symbol'] = df[~fixed_income_mask].apply(
            lambda row: CSVParser.clean_symbol(row['Symbol'], row['security_type']), axis=1
        )
        
        # Handle cash equivalents
        for symbol in CSVParser.CASH_EQUIVALENTS:
            df.loc[df['Symbol'] == symbol, 'security_type'] = 'cash'
            df.loc[df['Symbol'] == symbol, 'Symbol'] = 'CASH EQUIVALENTS'
        
        # Handle transfers
        transfer_mask = df['Action'].str.contains('TRANSFER', case=False, na=False)
        df.loc[transfer_mask, 'security_type'] = 'cash'
        df.loc[transfer_mask, 'Symbol'] = 'CASH EQUIVALENTS'
        df.loc[transfer_mask, 'Price'] = 1.0
        # Get transfer amount from Amount column if Quantity is missing
        df.loc[transfer_mask & df['Quantity'].isna(), 'Quantity'] = df.loc[transfer_mask & df['Quantity'].isna(), 'Amount ($)'].apply(CSVParser.extract_amount)
        
        # Handle fixed income securities from description
        for pattern in CSVParser.FIXED_INCOME_PATTERNS:
            mask = df['Description'].str.contains(pattern, na=False, case=False)
            df.loc[mask, 'security_type'] = 'fixed_income'
            df.loc[mask, 'Symbol'] = 'FIXED INCOME'
            # For interest payments only, set as cash
            interest_mask = mask & df['Description'].str.contains('INTEREST', na=False, case=False)
            df.loc[interest_mask, 'security_type'] = 'cash'
            df.loc[interest_mask, 'Symbol'] = 'CASH EQUIVALENTS'
        
        # Convert quantity to numeric
        df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
        
        # Handle fixed income units conversion (divide by 100 for buy and sold transactions)
        fixed_income_mask = (df['security_type'] == 'fixed_income') & (df['Action'].str.contains('YOU BOUGHT|YOU SOLD', case=False, na=False))
        df.loc[fixed_income_mask, 'Quantity'] = df.loc[fixed_income_mask, 'Quantity'] / 100
        
        # Map columns to standard format
        df_mapped = pd.DataFrame({
            'date': pd.to_datetime(df['Run Date']),
            'transaction_type': df['Action'].apply(extract_transaction_type),
            'stock': df['Symbol'],
            'units': df['Quantity'],
            'price': pd.to_numeric(df['Price ($)'], errors='coerce'),
            'fee': pd.to_numeric(df['Commission ($)'], errors='coerce').fillna(0),
            'security_type': df['security_type'],
            'option_type': df['Description'].str.extract(r'(\bCall|\bPut\b)', flags=re.IGNORECASE)[0].str.lower(),
            'amount': pd.to_numeric(df['Amount ($)'], errors='coerce')
        })
        
        # Filter out non-trade transactions
        df_mapped = df_mapped[df_mapped['transaction_type'].notna()]
        
        return df_mapped

    @staticmethod
    def standardize_data(df: pd.DataFrame, broker: str) -> pd.DataFrame:
        """Standardize the data format across different brokers"""
        # Add broker information
        df['broker'] = broker
        
        # Handle missing values
        df = DataProcessor.handle_missing_values(df)
        
        # Validate data against schema
        if not DataProcessor.validate_data(df):
            raise ValueError("Data validation failed")
        
        # Sort by date
        df = df.sort_values('date')
        
        # Reset index
        df = df.reset_index(drop=True)
        
        return df

    @staticmethod
    def parse(content: str, broker: str) -> pd.DataFrame:
        """Main entry point for parsing CSV files"""
        parser_map = {
            'schwab': CSVParser.parse_schwab,
            'etrade': CSVParser.parse_etrade,
            'fidelity': CSVParser.parse_fidelity
        }
        
        if broker.lower() not in parser_map:
            raise ValueError(f"Unsupported broker: {broker}")
        
        # Parse broker-specific format
        df = parser_map[broker.lower()](content)
        
        # Standardize the data
        df = CSVParser.standardize_data(df, broker.lower())
        
        return df 