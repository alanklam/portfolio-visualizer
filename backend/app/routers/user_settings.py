from fastapi import APIRouter, HTTPException
from ..schemas import UserSettings, UserSettingsBase
from typing import List

router = APIRouter()

@router.get("/")
async def get_settings() -> List[UserSettings]:
    """Get user portfolio settings"""
    pass

@router.post("/")
async def create_settings(settings: UserSettingsBase):
    """Create new portfolio settings"""
    pass

@router.put("/{stock}")
async def update_settings(stock: str, settings: UserSettingsBase):
    """Update portfolio settings for a stock"""
    pass

@router.delete("/{stock}")
async def delete_settings(stock: str):
    """Delete portfolio settings for a stock"""
    pass 