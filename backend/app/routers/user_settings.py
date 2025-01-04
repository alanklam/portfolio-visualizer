from fastapi import APIRouter, HTTPException
from ..schemas import UserSettings, UserSettingsBase, PortfolioSettings
from typing import Dict
from datetime import datetime

router = APIRouter(
    tags=["settings"]
)

# In-memory storage for settings (replace with database in production)
user_settings: Dict[str, UserSettings] = {}

@router.get("/", response_model=PortfolioSettings)
async def get_settings():
    """Get user's portfolio settings"""
    if not user_settings:
        return PortfolioSettings(target_weights={})
    return PortfolioSettings(target_weights=user_settings.get("default", {}).target_weights)

@router.post("/", response_model=PortfolioSettings)
async def update_settings(settings: PortfolioSettings):
    """Update user's portfolio settings"""
    try:
        # Validate that weights sum to 1 (100%)
        total_weight = sum(settings.target_weights.values())
        if abs(total_weight - 1.0) > 0.0001:  # Allow small rounding errors
            raise HTTPException(
                status_code=400,
                detail="Target weights must sum to 100%"
            )
        
        # Store settings (in memory for now)
        user_settings["default"] = UserSettings(
            id=1,
            target_weights=settings.target_weights,
            rebalance_threshold=5.0,
            last_update=datetime.now()
        )
        
        return settings
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        ) 