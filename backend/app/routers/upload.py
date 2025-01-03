from fastapi import APIRouter, UploadFile, File, HTTPException
from ..schemas import FileUpload, Transaction
from ..utils.csv_parser import CSVParser
from typing import List
import pandas as pd
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db
from fastapi import Depends

router = APIRouter()

@router.post("/", response_model=List[Transaction])
async def upload_file(
    file: UploadFile = File(...),
    broker: str = None,
    db: Session = Depends(get_db)
):
    """Handle file upload and parsing"""
    if not broker:
        raise HTTPException(status_code=400, detail="Broker type is required")
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    try:
        # Read file content
        content = await file.read()
        content_str = content.decode('utf-8')
        
        # Parse and standardize the data
        df = CSVParser.parse(content_str, broker)
        
        # Convert DataFrame to list of transactions
        transactions = []
        for _, row in df.iterrows():
            transaction = models.Transaction(
                date=row['date'],
                transaction_type=row['transaction_type'],
                stock=row['stock'],
                units=row['units'],
                price=row['price'],
                fee=row['fee'],
                security_type=row['security_type'],
                broker=row['broker']
            )
            db.add(transaction)
            transactions.append(transaction)
        
        # Commit to database
        db.commit()
        
        # Refresh to get the IDs
        for transaction in transactions:
            db.refresh(transaction)
        
        return transactions
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/brokers")
async def get_supported_brokers():
    """Return list of supported brokers"""
    return ["Fidelity", "Charles Schwab", "E-Trade"] 