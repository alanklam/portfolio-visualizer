from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from ...crud.settings import get_user_settings, update_user_settings
from ..dependencies import get_current_user, get_db  # Changed from ...dependencies
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ...schemas.settings_schema import WeightSetting, WeightSettingsUpdate

router = APIRouter()

@router.get("/settings")  # This becomes /api/portfolio/settings
async def read_settings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict]:
    # Returns array of settings directly
    return get_user_settings(db, current_user.id)

@router.post("/settings")  # This becomes /api/portfolio/settings
async def update_settings(
    settings: WeightSettingsUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    # Check if total weight exceeds 100%
    total_weight = sum(item.target_weight for item in settings.settings)
    
    # If total exceeds 100%, normalize weights
    if total_weight > 1.0:
        normalized_settings = [
            {
                "stock": item.stock,
                "target_weight": item.target_weight / total_weight
            }
            for item in settings.settings
        ]
    else:
        normalized_settings = [
            {
                "stock": item.stock,
                "target_weight": item.target_weight
            }
            for item in settings.settings
        ]
    
    # Always return settings and warning info
    updated_settings = update_user_settings(db, current_user.id, normalized_settings)
    return {
        "settings": updated_settings,
        "warning": total_weight > 1.0,
        "total_weight": total_weight,
        "normalized": total_weight > 1.0
    }
