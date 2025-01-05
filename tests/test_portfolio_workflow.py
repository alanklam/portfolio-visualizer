import pytest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.models import Transaction as DBTransaction
from datetime import date
import pandas as pd

client = TestClient(app)

def test_portfolio_workflow(db_session, sample_schwab_data):
    # 1. Create a test user and add some transactions
    test_user_id = 1
    transactions = [
        DBTransaction(
            user_id=test_user_id,
            date=date(2024, 11, 8),
            transaction_type="buy",
            stock="KO",
            units=100,
            price=66.00,
            fee=0.0,
            security_type="stock",
            broker="schwab"
        ),
        DBTransaction(
            user_id=test_user_id,
            date=date(2024, 12, 31),
            transaction_type="reinvest",
            stock="SWVXX",
            units=16.19,
            price=1.00,
            fee=0.0,
            security_type="cash",
            broker="schwab"
        )
    ]
    
    for txn in transactions:
        db_session.add(txn)
    db_session.commit()

    # 2. Test portfolio holdings endpoint
    response = client.get("/api/portfolio/holdings")
    assert response.status_code == 200
    holdings = response.json()
    
    # Verify holdings structure
    assert isinstance(holdings, list)
    assert len(holdings) > 0
    
    # Check KO holding
    ko_holding = next((h for h in holdings if h["symbol"] == "KO"), None)
    assert ko_holding is not None
    assert ko_holding["units"] == 100
    assert ko_holding["cost_basis"] == 6600.0
    
    # 3. Test gain/loss endpoint
    response = client.get("/api/portfolio/gain-loss")
    assert response.status_code == 200
    gain_loss = response.json()
    
    # Verify gain/loss structure
    assert "total_value" in gain_loss
    assert "total_cost" in gain_loss
    assert gain_loss["total_cost"] == 6616.19  # KO + SWVXX 

def test_transaction_deduplication(db_session, sample_schwab_data):
    """Test that uploading the same transaction twice doesn't create duplicates"""
    
    # First upload
    test_user_id = 1
    transaction = DBTransaction(
        user_id=test_user_id,
        date=date(2024, 11, 8),
        transaction_type="buy",
        stock="KO",
        units=100,
        price=66.00,
        fee=0.0,
        security_type="stock",
        broker="schwab"
    )
    db_session.add(transaction)
    db_session.commit()
    
    # Try to add the same transaction again
    duplicate = DBTransaction(
        user_id=test_user_id,
        date=date(2024, 11, 8),
        transaction_type="buy",
        stock="KO",
        units=100,
        price=66.00,
        fee=0.0,
        security_type="stock",
        broker="schwab"
    )
    db_session.add(duplicate)
    db_session.commit()
    
    # Query all transactions for this user
    transactions = db_session.query(DBTransaction).filter(
        DBTransaction.user_id == test_user_id,
        DBTransaction.stock == "KO"
    ).all()
    
    # Should only be one transaction
    assert len(transactions) == 1 