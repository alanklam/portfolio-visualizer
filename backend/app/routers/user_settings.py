from fastapi import APIRouter, HTTPException, Depends
from ..schemas import UserSettings, UserSettingsBase, PortfolioSettings
from typing import Dict
from datetime import datetime
from ..dependencies import get_current_user
from ..models import User, UserSettings as DBUserSettings
from sqlalchemy.orm import Session
from ..database import get_db

router = APIRouter(
    tags=["settings"]
)

# In-memory storage for settings (replace with database in production)
user_settings: Dict[str, UserSettings] = {}

@router.get("/", response_model=PortfolioSettings)
async def get_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    settings = db.query(DBUserSettings).filter(
        DBUserSettings.user_id == current_user.id
    ).all()
    
    return PortfolioSettings(
        target_weights={
            s.stock: s.target_weight for s in settings
        }
    )

@router.post("/", response_model=PortfolioSettings)
async def update_settings(
    settings: PortfolioSettings,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        # Validate weights
        total_weight = sum(settings.target_weights.values())
        if abs(total_weight - 1.0) > 0.0001:
            raise HTTPException(
                status_code=400,
                detail="Target weights must sum to 100%"
            )
        
        # Delete existing settings
        db.query(DBUserSettings).filter(
            DBUserSettings.user_id == current_user.id
        ).delete()
        
        # Store new settings
        for stock, weight in settings.target_weights.items():
            setting = DBUserSettings(
                user_id=current_user.id,
                stock=stock,
                target_weight=weight
            )
            db.add(setting)
        
        db.commit()
        return settings
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update settings: {str(e)}"
        ) 