import pytest
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.database import Base
import os
from typing import Dict, List

# Test database
TEST_DB_URL = "sqlite:///./test.db"

@pytest.fixture(scope="session")
def engine():
    """Create a test database engine."""
    engine = create_engine(TEST_DB_URL)
    Base.metadata.create_all(engine)
    yield engine
    os.remove("./test.db")

@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for a test."""
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def sample_schwab_data():
    """Sample Charles Schwab transaction data."""
    return '''
"Date","Action","Symbol","Description","Quantity","Price","Fees & Comm","Amount"
"12/31/2024","Reinvest Shares","SWVXX","SCHWAB VALUE ADVANTAGE MONEY","16.19","$1.00","","-$16.19"
"11/08/2024","Buy","KO","THE COCA-COLA CO","100","$66.00","","-$6600.00"
"10/25/2024","Sell to Open","KO 11/15/2024 66.00 P","PUT THE COCA-COLA CO $66 EXP 11/15/24","1","$0.53","$0.66","$52.34"
'''

@pytest.fixture
def sample_etrade_data():
    """Sample E-Trade transaction data."""
    return '''
For Account:,#####3333

TransactionDate,TransactionType,SecurityType,Symbol,Quantity,Amount,Price,Commission,Description
11/22/24,Bought,EQ,COF,10,1832.00,183.20,0,CAPITAL ONE FINANCIAL CORP
11/15/24,Sold Short,OPTN,COF Mar 21 '25 $210 Call,-1,506.31,5.07,0.69,COF Mar 21 '25 $210 Call
'''

@pytest.fixture
def sample_fidelity_data():
    """Sample Fidelity transaction data."""
    return '''
Run Date,Account,Action,Symbol,Description,Type,Quantity,Price ($),Commission ($),Fees ($),Accrued Interest ($),Amount ($),Settlement Date
12/27/2024,"Individual" Z03333333," YOU BOUGHT NVIDIA CORPORATION COM (NVDA) (Margin)",NVDA," NVIDIA CORPORATION COM",Margin,10,139.63,,,,-1396.30,
'''

@pytest.fixture
def real_transaction_files():
    """Get paths to real transaction files if they exist."""
    transaction_dir = "data/transactions"
    files: Dict[str, List[str]] = {
        'schwab': [],
        'etrade': [],
        'fidelity': []
    }
    
    if os.path.exists(transaction_dir):
        for file in os.listdir(transaction_dir):
            if file.endswith('.csv'):
                file_path = os.path.join(transaction_dir, file)
                if 'schwab' in file.lower():
                    files['schwab'].append(file_path)
                elif 'etrade' in file.lower():
                    files['etrade'].append(file_path)
                elif 'fidelity' in file.lower():
                    files['fidelity'].append(file_path)
    
    # Only return brokers that have files
    return {k: v for k, v in files.items() if v}

@pytest.fixture
def real_files_exist(real_transaction_files):
    """Check if any real transaction files exist."""
    return len(real_transaction_files) > 0

@pytest.fixture
def combined_broker_data(real_transaction_files):
    """Combine multiple CSV files from the same broker."""
    combined_data = {}
    
    for broker, file_paths in real_transaction_files.items():
        combined_content = []
        for file_path in file_paths:
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    # For the first file, keep the header
                    if not combined_content:
                        combined_content.append(content)
                    else:
                        # For subsequent files, skip the header
                        lines = content.split('\n')
                        # Find where the actual data starts (skip account info, headers, etc.)
                        start_idx = 0
                        for idx, line in enumerate(lines):
                            if any(col in line for col in ['Date', 'TransactionDate', 'Run Date']):
                                start_idx = idx + 1
                                break
                        combined_content.append('\n'.join(lines[start_idx:]))
            except Exception as e:
                print(f"Error reading file {file_path}: {str(e)}")
        
        if combined_content:
            combined_data[broker] = '\n'.join(combined_content)
    
    return combined_data 

@pytest.fixture
def test_user():
    return {
        "id": 1,
        "email": "test@example.com",
        "username": "testuser"
    }

@pytest.fixture
def override_get_current_user():
    """Override the get_current_user dependency"""
    from backend.app.dependencies import get_current_user
    from backend.app.models import User
    
    async def mock_get_current_user():
        return User(id=1, email="test@example.com", username="testuser")
    
    app.dependency_overrides[get_current_user] = mock_get_current_user
    yield
    app.dependency_overrides = {} 