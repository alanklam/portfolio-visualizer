import pandas as pd
from typing import Dict, Any
from io import StringIO
from datetime import datetime
import yfinance as yf
from .data_processor import DataProcessor
import re

class CSVParser:
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
        
        # Handle option assignments and expirations
        df['security_type'] = 'stock'
        df.loc[df['Description'].str.contains('PUT|CALL', na=False), 'security_type'] = 'option'
        
        # Map action types
        action_map = {
            'Buy': 'buy',
            'Sell': 'sell',
            'Reinvest Shares': 'reinvest',
            'Assigned': 'assigned',
            'Expired': 'expired',
            'Sell to Open': 'sell_to_open',
            'Buy to Open': 'buy_to_open',
            'Sell to Close': 'sell_to_close',
            'Buy to Close': 'buy_to_close'
        }
        
        # Handle special cases for assignments
        df['original_action'] = df['Action']
        df.loc[(df['Action'] == 'Assigned') & (df['option_type'] == 'call'), 'Action'] = 'Sell'
        df.loc[(df['Action'] == 'Assigned') & (df['option_type'] == 'put'), 'Action'] = 'Buy'
        
        # Filter relevant transactions
        df = df[df['Action'].isin(action_map.keys())]
        
        # Extract amount when price is missing
        df.loc[df['Price'].isna() & df['Amount'].notna(), 'Price'] = (
            pd.to_numeric(df['Amount'].str.replace('$', '').str.replace(',', ''), errors='coerce').abs() / 
            pd.to_numeric(df['Quantity'].str.replace(',', ''), errors='coerce')
        )
        
        # Map columns to standard format
        df_mapped = pd.DataFrame({
            'date': pd.to_datetime(df['Date'].str.split(' as of').str[0]),
            'transaction_type': df['Action'].map(action_map),
            'stock': df['Symbol'],
            'units': pd.to_numeric(df['Quantity'].str.replace(',', ''), errors='coerce'),
            'price': pd.to_numeric(df['Price'].str.replace('$', '').str.replace(',', ''), errors='coerce'),
            'fee': pd.to_numeric(df['Fees & Comm'].str.replace('$', '').str.replace(',', ''), errors='coerce').fillna(0),
            'security_type': df['security_type'],
            'option_type': df['option_type']
        })
        
        return df_mapped

    @staticmethod
    def parse_etrade(content: str) -> pd.DataFrame:
        """Parse E-Trade CSV format"""
        df = pd.read_csv(StringIO(content), skiprows=2)  # Skip the account info rows
        
        # Map transaction types
        transaction_map = {
            'Bought': 'buy',
            'Sold': 'sell',
            'Dividend Reinvestment': 'reinvest',
            'Sold Short': 'sell_to_open',
            'Bought To Cover': 'buy_to_close'
        }
        
        # Filter relevant transactions
        df = df[df['TransactionType'].isin(list(transaction_map.keys()) + ['Adjustment'])]
        
        # Handle adjustments by fetching historical prices
        adjustment_rows = df['TransactionType'] == 'Adjustment'
        if adjustment_rows.any():
            for idx in df[adjustment_rows].index:
                symbol = df.loc[idx, 'Symbol']
                date_str = df.loc[idx, 'TransactionDate']
                try:
                    # Convert date to datetime
                    date = pd.to_datetime(date_str)
                    # Fetch historical data
                    ticker = yf.Ticker(symbol)
                    hist = ticker.history(start=date, end=date + pd.Timedelta(days=1))
                    if not hist.empty:
                        df.loc[idx, 'Price'] = hist['Close'].iloc[0]
                except Exception as e:
                    print(f"Failed to fetch historical price for {symbol} on {date_str}: {str(e)}")
        
        # Map columns to standard format
        df_mapped = pd.DataFrame({
            'date': pd.to_datetime(df['TransactionDate']),
            'transaction_type': df['TransactionType'].map(lambda x: transaction_map.get(x, 'adjustment')),
            'stock': df['Symbol'],
            'units': pd.to_numeric(df['Quantity'], errors='coerce'),
            'price': pd.to_numeric(df['Price'], errors='coerce'),
            'fee': pd.to_numeric(df['Commission'], errors='coerce').fillna(0),
            'security_type': df['SecurityType'].map({
                'EQ': 'stock',
                'OPTN': 'option'
            }),
            'option_type': df['Description'].str.extract(r'(\bCall|\bPut\b)', flags=re.IGNORECASE)[0].str.lower()
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
            if 'YOU BOUGHT' in action:
                return 'buy'
            elif 'YOU SOLD' in action:
                return 'sell'
            elif 'REINVESTMENT' in action:
                return 'reinvest'
            elif 'ASSIGNED' in action:
                return 'assigned'
            elif 'EXPIRED' in action:
                return 'expired'
            return None
        
        # Clean up symbol
        df['Symbol'] = df['Symbol'].str.strip()
        
        # Map columns to standard format
        df_mapped = pd.DataFrame({
            'date': pd.to_datetime(df['Run Date']),
            'transaction_type': df['Action'].apply(extract_transaction_type),
            'stock': df['Symbol'],
            'units': pd.to_numeric(df['Quantity'], errors='coerce'),
            'price': pd.to_numeric(df['Price ($)'], errors='coerce'),
            'fee': pd.to_numeric(df['Commission ($)'], errors='coerce').fillna(0),
            'security_type': df['Type'].map(lambda x: 'option' if 'OPTION' in str(x).upper() else 'stock'),
            'option_type': df['Description'].str.extract(r'(\bCall|\bPut\b)', flags=re.IGNORECASE)[0].str.lower()
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