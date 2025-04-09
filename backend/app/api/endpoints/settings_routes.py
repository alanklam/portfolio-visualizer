from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, List
from ...crud.settings import get_user_settings, update_user_settings
from ..dependencies import get_current_user, get_db  # Changed from ...dependencies
from sqlalchemy.orm import Session
from pydantic import BaseModel
from ...schemas.settings_schema import WeightSetting, WeightSettingsUpdate
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/settings")  # This becomes /api/portfolio/settings
async def read_settings(
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> List[Dict]:
    try:
        if not current_user or not current_user.id:
            logger.error("Settings read attempted without valid user authentication")
            raise HTTPException(status_code=401, detail="Invalid user authentication")

        logger.info(f"Fetching settings for user {current_user.id}")
        settings = get_user_settings(db, current_user.id)
        logger.info(f"Successfully retrieved {len(settings)} settings for user {current_user.id}")
        return settings

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in read_settings for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve settings: {str(e)}"
        )

@router.post("/settings")  # This becomes /api/portfolio/settings
async def update_settings(
    settings: WeightSettingsUpdate,
    current_user = Depends(get_current_user),
    db: Session = Depends(get_db)
) -> Dict:
    try:
        if not current_user or not current_user.id:
            logger.error("Settings update attempted without valid user authentication")
            raise HTTPException(status_code=401, detail="Invalid user authentication")

        logger.info(f"Processing settings update for user {current_user.id} with {len(settings.settings)} items")

        # Check if total weight exceeds 100%
        total_weight = sum(item.target_weight for item in settings.settings)
        logger.info(f"Total weight for settings: {total_weight}")
        
        # If total exceeds 100%, normalize weights
        if total_weight > 1.0:
            logger.warning(f"Total weight ({total_weight}) exceeds 1.0, normalizing weights")
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

        try:
            # Update settings in database
            updated_settings = update_user_settings(db, current_user.id, normalized_settings)
            logger.info(f"Successfully updated settings for user {current_user.id}")

            return {
                "settings": updated_settings,
                "warning": total_weight > 1.0,
                "total_weight": total_weight,
                "normalized": total_weight > 1.0
            }

        except Exception as e:
            logger.error(f"Database error updating settings for user {current_user.id}: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update settings: {str(e)}"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in update_settings for user {current_user.id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"An unexpected error occurred while updating settings: {str(e)}"
        )
