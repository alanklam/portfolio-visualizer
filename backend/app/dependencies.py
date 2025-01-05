from fastapi import Depends, HTTPException, Header
from sqlalchemy.orm import Session
from .database import get_db
from .models import User
from datetime import datetime
import uuid

async def get_current_user(
    user_id: str = Header(None, alias="X-User-ID"),
    db: Session = Depends(get_db)
):
    if not user_id:
        # Generate a new user ID if none provided
        user_id = str(uuid.uuid4())
    
    # Get or create user
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        user = User(
            user_id=user_id,
            created_at=datetime.now().date()
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user 