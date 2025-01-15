from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Form
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.user_model import User
from ...models.transaction_model import Transaction
from ...services.data_service import process_csv_file
from ..dependencies import get_current_user
from datetime import datetime
import pandas as pd
import io

router = APIRouter()

@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    broker: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upload and process a transaction file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")
    
    # Auto-detect broker if 'autodetect' is selected
    if broker.lower() == 'autodetect':
        if any(keyword in file.filename.lower() for keyword in ['schwab', 'fidelity', 'etrade']):
            broker = next(keyword for keyword in ['schwab', 'fidelity', 'etrade'] if keyword in file.filename.lower())
        else:
            raise HTTPException(status_code=400, detail="Broker type could not be determined from the file name. Please specify the broker.")

    if broker.lower() not in ['schwab', 'fidelity', 'etrade']:
        raise HTTPException(status_code=400, detail="Unsupported broker. Must be one of: schwab, fidelity, etrade")
    
    try:
        # Read file contents
        contents = await file.read()
        
        # For E*TRADE, skip the first row as it contains account info
        if broker.lower() == 'etrade':
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')), skiprows=1)
        else:
            df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
        
        # Process the CSV file
        transactions_data = process_csv_file(df, broker=broker.lower())
        
        # Create transaction records
        for data in transactions_data:
            # Check for existing transaction based on user_id, date, stock, transaction_type, units, and amount
            existing_transaction = db.query(Transaction).filter(
                Transaction.user_id == current_user.id,
                Transaction.date == data['date'],
                Transaction.stock == data['stock'],
                Transaction.transaction_type == data['transaction_type'],
                Transaction.security_type == data['security_type'],
                Transaction.option_type == data['option_type'],
                Transaction.amount == data['amount']
            ).first()
            
            # Only add the transaction if it does not already exist
            if not existing_transaction:
                transaction = Transaction(
                    user_id=current_user.id,
                    date=data['date'] if isinstance(data['date'], datetime) else datetime.strptime(str(data['date']), '%Y-%m-%d').date(),
                    stock=data['stock'],
                    transaction_type=data['transaction_type'],
                    units=data.get('units'),
                    price=data.get('price'),
                    fee=data.get('fee', 0),
                    option_type=data.get('option_type'),
                    security_type=data.get('security_type', 'stock'),
                    amount=data.get('amount')
                )
                db.add(transaction)
        
        db.commit()
        return {"message": "File processed successfully"}
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the file: {str(e)}")