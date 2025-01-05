from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from typing import List
import logging
from ..schemas import FileUpload
from ..utils.csv_parser import CSVParser
import os
import pandas as pd
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import Transaction as DBTransaction
from ..dependencies import get_current_user
from ..models import User
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["upload"]
)

@router.post("/", status_code=201)
async def upload_files(
    broker: str = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload and process transaction files"""
    try:
        logger.info(f"Received upload request for broker: {broker} with {len(files)} files")
        
        # Validate input
        if not files:
            raise HTTPException(
                status_code=400,
                detail="No files provided"
            )
        
        # Get the root directory
        ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        data_dir = os.path.join(ROOT_DIR, "data", "UI_test")
        
        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)
        logger.info(f"Ensuring data directory exists: {data_dir}")
        
        # Save files and get their paths
        file_paths = []
        for file in files:
            if not file.filename.endswith('.csv'):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type for {file.filename}. Only CSV files are supported."
                )
            
            file_path = os.path.join(data_dir, file.filename)
            logger.info(f"Saving file to: {file_path}")
            
            try:
                content = await file.read()
                with open(file_path, "wb") as buffer:
                    buffer.write(content)
                file_paths.append(file_path)
            except Exception as e:
                logger.error(f"Failed to save file {file.filename}: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to save file {file.filename}: {str(e)}"
                )
        
        # Process files based on broker type
        parser = CSVParser()
        all_transactions = []
        
        for file_path in file_paths:
            try:
                logger.info(f"Processing file: {file_path}")
                with open(file_path, 'r') as file:
                    content = file.read()
                
                if broker.lower() == "fidelity":
                    transactions = parser.parse_fidelity(content)
                elif broker.lower() == "schwab":
                    transactions = parser.parse_schwab(content)
                elif broker.lower() == "etrade":
                    transactions = parser.parse_etrade(content)
                else:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Unsupported broker: {broker}"
                    )
                
                logger.info(f"Successfully parsed {len(transactions)} transactions from {file_path}")
                all_transactions.append(transactions)
                
            except pd.errors.EmptyDataError:
                logger.error(f"File is empty: {file_path}")
                raise HTTPException(
                    status_code=400,
                    detail=f"File is empty: {file_path}"
                )
            except pd.errors.ParserError as e:
                logger.error(f"Failed to parse CSV file {file_path}: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid CSV format in {file_path}: {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error processing file {file_path}: {str(e)}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to parse {file_path}: {str(e)}"
                )
        
        # Combine all transactions
        if all_transactions:
            try:
                combined_transactions = pd.concat(all_transactions, ignore_index=True)
                output_path = os.path.join(data_dir, "processed_transactions.csv")
                combined_transactions.to_csv(output_path, index=False)
                logger.info(f"Successfully saved combined transactions to {output_path}")
                
                # After processing files, store transactions in database
                for df in all_transactions:
                    for _, row in df.iterrows():
                        # Check for duplicate transaction
                        existing = db.query(DBTransaction).filter(
                            DBTransaction.user_id == current_user.id,
                            DBTransaction.date == row['date'],
                            DBTransaction.stock == row['stock'],
                            DBTransaction.transaction_type == row['transaction_type'],
                            DBTransaction.units == row['units'],
                            DBTransaction.price == row['price'],
                            DBTransaction.amount == row['amount']
                        ).first()
                        
                        if not existing:
                            transaction = DBTransaction(
                                user_id=current_user.id,
                                date=row['date'],
                                transaction_type=row['transaction_type'],
                                stock=row['stock'],
                                units=row['units'],
                                price=row['price'],
                                fee=row['fee'],
                                option_type=row.get('option_type'),
                                security_type=row['security_type'],
                                broker=broker,
                                amount=row['amount']
                            )
                            db.add(transaction)
                        else:
                            logger.warning(f"Duplicate transaction found for user {current_user.id}: {row}")
                
                db.commit()
                logger.info(f"Successfully stored transactions in database for user {current_user.id}")
                
            except Exception as e:
                db.rollback()
                logger.error(f"Failed to store transactions in database: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to store transactions: {str(e)}"
                )
        
        return {
            "message": "Files uploaded and processed successfully",
            "files_processed": len(file_paths),
            "total_transactions": sum(len(df) for df in all_transactions)
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error during file upload: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Upload failed: {str(e)}"
        ) 