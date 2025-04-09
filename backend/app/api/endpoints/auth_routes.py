from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from ...core.db import get_db
from ...models.user_model import User
from ..dependencies import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from datetime import datetime, timedelta
from passlib.context import CryptContext
import logging

router = APIRouter()
logger = logging.getLogger(__name__)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against hash"""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error(f"Error in verify_password: {str(e)}")
        return False

def get_password_hash(password: str) -> str:
    """Hash password"""
    try:
        return pwd_context.hash(password)
    except Exception as e:
        logger.error(f"Error in get_password_hash: {str(e)}")
        raise

@router.post("/signup")
async def signup(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Create new user account"""
    try:
        logger.info(f"Processing signup request for username: {form_data.username}")
        
        # Check if username exists
        if db.query(User).filter(User.username == form_data.username).first():
            logger.warning(f"Signup attempt with existing username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already registered"
            )
        
        try:
            # Create new user
            user = User(
                username=form_data.username,
                hashed_password=get_password_hash(form_data.password),
                created_at=datetime.utcnow()
            )
            
            db.add(user)
            db.commit()
            db.refresh(user)
            
            logger.info(f"Successfully created new user: {form_data.username}")
            
        except Exception as e:
            db.rollback()
            logger.error(f"Database error during signup for {form_data.username}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error creating user account"
            )
        
        try:
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.username},
                expires_delta=access_token_expires
            )
            
            logger.info(f"Successfully created access token for new user: {form_data.username}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "username": user.username
            }
            
        except Exception as e:
            logger.error(f"Error creating access token for {form_data.username}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating authentication token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in signup: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during signup"
        )

@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Authenticate user and return token"""
    try:
        logger.info(f"Processing login attempt for username: {form_data.username}")
        
        # Get user
        user = db.query(User).filter(User.username == form_data.username).first()
        if not user:
            logger.warning(f"Login attempt with non-existent username: {form_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Verify password
        if not verify_password(form_data.password, user.hashed_password):
            logger.warning(f"Failed login attempt for user {form_data.username}: Invalid password")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        try:
            # Update last login
            user.last_login = datetime.utcnow()
            db.commit()
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error updating last login for user {form_data.username}: {str(e)}")
            # Don't raise an exception here as this is not critical for login
        
        try:
            # Create access token
            access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
            access_token = create_access_token(
                data={"sub": user.username},
                expires_delta=access_token_expires
            )
            
            logger.info(f"Successful login for user: {form_data.username}")
            
            return {
                "access_token": access_token,
                "token_type": "bearer",
                "username": user.username
            }
            
        except Exception as e:
            logger.error(f"Error creating access token for user {form_data.username}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error generating authentication token"
            )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in login: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred during login"
        )