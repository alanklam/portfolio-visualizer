from pydantic import BaseModel
from typing import Optional

class UserAuth(BaseModel):
    """Schema for user authentication"""
    username: str
    password: Optional[str] = None

class Token(BaseModel):
    """Schema for JWT token response"""
    token: str
    username: str 