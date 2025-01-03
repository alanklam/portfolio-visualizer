import pytest
import pandas as pd
import numpy as np
from backend.app.utils.data_processor import DataProcessor
from datetime import datetime

class TestDataProcessor:
    def test_standardize_dates(self):
        """Test date standardization."""
        # Test various date formats
        assert DataProcessor.standardize_dates("2024-01-01") == pd.Timestamp("2024-01-01")
        assert DataProcessor.standardize_dates("01/01/2024") == pd.Timestamp("2024-01-01")
        assert DataProcessor.standardize_dates("01/01/24") == pd.Timestamp("2024-01-01")
        
        # Test "as of" dates
        assert DataProcessor.standardize_dates("01/01/2024 as of 12/31/2023") == pd.Timestamp("2024-01-01")
        
        # Test invalid dates
        with pytest.raises(ValueError):
            DataProcessor.standardize_dates("invalid date")

    def test_process_transaction(self):
        """Test transaction processing."""
        # Test stock transaction
        stock_transaction = {
            'date': '2024-01-01',
            'transaction_type': 'BUY',
            'stock': 'aapl',
            'units': '100',
            'price': '150.50',
            'fee': '0.65',
            'security_type': 'STOCK'
        }
        
        processed = DataProcessor.process_transaction(stock_transaction)
        assert processed['transaction_type'] == 'buy'
        assert processed['stock'] == 'AAPL'
        assert processed['units'] == 100.0
        assert processed['price'] == 150.50
        assert processed['fee'] == 0.65
        assert processed['security_type'] == 'stock'
        
        # Test cash equivalent
        cash_transaction = {
            'stock': 'SWVXX',
            'security_type': 'stock'
        }
        processed = DataProcessor.process_transaction(cash_transaction)
        assert processed['security_type'] == 'cash'
        
        # Test missing values
        missing_values = {
            'stock': 'AAPL',
            'transaction_type': 'buy'
        }
        processed = DataProcessor.process_transaction(missing_values)
        assert processed['fee'] == 0.0
        assert processed['units'] == 0.0
        assert processed['price'] == 0.0

    def test_handle_missing_values(self):
        """Test handling of missing values in DataFrame."""
        df = pd.DataFrame([
            {'date': '2024-01-01', 'transaction_type': 'buy', 'stock': 'AAPL', 
             'units': 100, 'price': 150.0, 'fee': None, 'security_type': None},
            {'date': '2024-01-02', 'transaction_type': 'sell', 'stock': 'GOOGL', 
             'units': None, 'price': None, 'fee': 0.65, 'security_type': 'stock'}
        ])
        
        cleaned_df = DataProcessor.handle_missing_values(df)
        
        # Check fee filling
        assert cleaned_df['fee'].isna().sum() == 0
        assert cleaned_df.iloc[0]['fee'] == 0.0
        
        # Check security type filling
        assert cleaned_df['security_type'].isna().sum() == 0
        assert cleaned_df.iloc[0]['security_type'] == 'stock'
        
        # Check critical columns
        assert len(cleaned_df) == 1  # Second row should be dropped due to missing units/price

    def test_validate_data(self):
        """Test data validation."""
        # Valid data
        valid_df = pd.DataFrame([{
            'date': pd.Timestamp('2024-01-01'),
            'transaction_type': 'buy',
            'stock': 'AAPL',
            'units': 100,
            'price': 150.0,
            'fee': 0.65,
            'security_type': 'stock',
            'broker': 'schwab'
        }])
        assert DataProcessor.validate_data(valid_df) == True
        
        # Missing required column
        invalid_df = valid_df.drop('broker', axis=1)
        assert DataProcessor.validate_data(invalid_df) == False
        
        # Invalid transaction type
        invalid_df = valid_df.copy()
        invalid_df['transaction_type'] = 'invalid'
        assert DataProcessor.validate_data(invalid_df) == False
        
        # Invalid security type
        invalid_df = valid_df.copy()
        invalid_df['security_type'] = 'invalid'
        assert DataProcessor.validate_data(invalid_df) == False
        
        # Negative values
        invalid_df = valid_df.copy()
        invalid_df['price'] = -100
        assert DataProcessor.validate_data(invalid_df) == False
        
        # Zero units
        invalid_df = valid_df.copy()
        invalid_df['units'] = 0
        assert DataProcessor.validate_data(invalid_df) == False
        
        # Test adjustment transaction (should allow zero units)
        adjustment_df = valid_df.copy()
        adjustment_df['transaction_type'] = 'adjustment'
        adjustment_df['units'] = 0
        assert DataProcessor.validate_data(adjustment_df) == True 