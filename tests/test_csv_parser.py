import pytest
import pandas as pd
from backend.app.utils.csv_parser import CSVParser
from datetime import datetime

class TestCSVParser:
    def test_parse_schwab_basic(self, sample_schwab_data):
        """Test basic Schwab CSV parsing functionality."""
        df = CSVParser.parse_schwab(sample_schwab_data)
        
        assert len(df) == 3
        assert list(df.columns) == ['date', 'transaction_type', 'stock', 'units', 
                                  'price', 'fee', 'security_type', 'option_type']
        
        # Test cash equivalent
        cash_row = df[df['stock'] == 'SWVXX'].iloc[0]
        assert cash_row['security_type'] == 'cash'
        assert cash_row['transaction_type'] == 'reinvest'
        
        # Test stock purchase
        stock_row = df[df['stock'] == 'KO'].iloc[0]
        assert stock_row['security_type'] == 'stock'
        assert stock_row['transaction_type'] == 'buy'
        assert stock_row['units'] == 100
        assert stock_row['price'] == 66.00
        
        # Test option transaction
        option_row = df[df['stock'] == 'KO'].iloc[1]
        assert option_row['security_type'] == 'option'
        assert option_row['transaction_type'] == 'sell_to_open'
        assert option_row['option_type'] == 'put'
        assert option_row['fee'] == 0.66

    def test_parse_etrade_basic(self, sample_etrade_data):
        """Test basic E-Trade CSV parsing functionality."""
        df = CSVParser.parse_etrade(sample_etrade_data)
        
        assert len(df) == 2
        
        # Test stock purchase
        stock_row = df[df['security_type'] == 'stock'].iloc[0]
        assert stock_row['stock'] == 'COF'
        assert stock_row['transaction_type'] == 'buy'
        assert stock_row['units'] == 10
        assert stock_row['price'] == 183.20
        
        # Test option transaction
        option_row = df[df['security_type'] == 'option'].iloc[0]
        assert option_row['stock'] == 'COF'
        assert option_row['transaction_type'] == 'sell_to_open'
        assert option_row['option_type'] == 'call'

    def test_parse_fidelity_basic(self, sample_fidelity_data):
        """Test basic Fidelity CSV parsing functionality."""
        df = CSVParser.parse_fidelity(sample_fidelity_data)
        
        assert len(df) == 1
        row = df.iloc[0]
        
        assert row['stock'] == 'NVDA'
        assert row['transaction_type'] == 'buy'
        assert row['units'] == 10
        assert row['price'] == 139.63
        assert row['security_type'] == 'stock'

    @pytest.mark.real_data
    def test_with_real_files(self, real_transaction_files):
        """Test parsing with real transaction files."""
        for broker, file_paths in real_transaction_files.items():
            # Test individual files
            for file_path in file_paths:
                with open(file_path, 'r') as f:
                    content = f.read()
                
                df = CSVParser.parse(content, broker)
                self._validate_parsed_data(df)
    
    @pytest.mark.real_data
    def test_with_combined_files(self, combined_broker_data):
        """Test parsing with combined files from each broker."""
        for broker, content in combined_broker_data.items():
            df = CSVParser.parse(content, broker)
            self._validate_parsed_data(df)
            
            # Additional validations for combined data
            self._validate_combined_data(df, broker)
    
    def _validate_parsed_data(self, df):
        """Common validation for parsed data."""
        # Basic validation
        assert len(df) > 0
        assert all(col in df.columns for col in [
            'date', 'transaction_type', 'stock', 'units', 
            'price', 'fee', 'security_type'
        ])
        
        # Data type validation
        assert df['date'].dtype == 'datetime64[ns]'
        assert df['units'].dtype == 'float64'
        assert df['price'].dtype == 'float64'
        
        # Value validation
        assert df['transaction_type'].isin([
            'buy', 'sell', 'reinvest', 'assigned', 'expired',
            'sell_to_open', 'buy_to_open', 'sell_to_close', 'buy_to_close',
            'adjustment'
        ]).all()
        
        assert df['security_type'].isin(['stock', 'option', 'cash']).all()
    
    def _validate_combined_data(self, df, broker):
        """Additional validations for combined data."""
        # Check date ordering
        assert df['date'].is_monotonic_increasing, f"Dates should be in order for {broker}"
        
        # Check for duplicates
        assert not df.duplicated().any(), f"Found duplicate entries in {broker} data"
        
        # Broker-specific validations
        if broker == 'schwab':
            # Validate option symbols format
            option_rows = df[df['security_type'] == 'option']
            if not option_rows.empty:
                assert option_rows['stock'].str.match(r'^[A-Z]+$').all(), "Invalid option symbol format"
        
        elif broker == 'etrade':
            # Validate adjustment entries have prices
            adj_rows = df[df['transaction_type'] == 'adjustment']
            if not adj_rows.empty:
                assert not adj_rows['price'].isna().any(), "Missing prices in adjustment entries"
        
        elif broker == 'fidelity':
            # Validate margin/cash type is consistent
            assert 'Type' in df.columns, "Missing account type information"

    def test_error_handling(self):
        """Test error handling in CSV parser."""
        # Test invalid broker
        with pytest.raises(ValueError, match="Unsupported broker"):
            CSVParser.parse("", "invalid_broker")
        
        # Test invalid CSV format
        with pytest.raises(Exception):
            CSVParser.parse("invalid,csv,format", "schwab")
        
        # Test empty content
        with pytest.raises(Exception):
            CSVParser.parse("", "schwab") 