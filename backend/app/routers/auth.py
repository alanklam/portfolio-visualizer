from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import jwt
from datetime import datetime, timedelta
from ..database import get_db
from sqlalchemy.orm import Session
from ..models import User
import os

router = APIRouter()

# Use a constant SECRET_KEY or load from environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-here")  # In production, always use env var
ALGORITHM = "HS256"

class UserAuth(BaseModel):
    username: str
    password: Optional[str] = None

class Token(BaseModel):
    token: str
    username: str

def create_token(username: str) -> str:
    expiration = datetime.utcnow() + timedelta(days=7)
    return jwt.encode(
        {"sub": username, "exp": expiration},
        SECRET_KEY,
        algorithm=ALGORITHM
    )

@router.post("/signup", response_model=Token)
def signup(user_auth: UserAuth, db: Session = Depends(get_db)):
    try:
        # Check if username exists
        existing_user = db.query(User).filter(User.username == user_auth.username).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already registered")
        
        # Create new user
        new_user = User(username=user_auth.username)
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Generate token
        token = create_token(new_user.username)
        return {"token": token, "username": new_user.username}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/login", response_model=Token)
def login(user_auth: UserAuth, db: Session = Depends(get_db)):
    try:
        # Find user
        user = db.query(User).filter(User.username == user_auth.username).first()
        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        
        # Generate token
        token = create_token(user.username)
        return {"token": token, "username": user.username}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 