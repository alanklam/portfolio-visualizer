from datetime import datetime, timedelta
import jwt
from fastapi import HTTPException
from .config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_DAYS

def create_token(username: str) -> str:
    """Create a new JWT token for a user"""
    expiration = datetime.utcnow() + timedelta(days=JWT_EXPIRATION_DAYS)
    return jwt.encode(
        {"sub": username, "exp": expiration},
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )

def decode_token(token: str) -> str:
    """Decode and validate a JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication token")
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials") 