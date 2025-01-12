from sqlalchemy.orm import Session
from ..models.transaction_model import UserSettings, Portfolio
from typing import List, Dict

def get_user_settings(db: Session, user_id: int) -> List[Dict]:
    # Get current holdings
    holdings = db.query(Portfolio).filter(
        Portfolio.user_id == user_id,
        Portfolio.total_units > 0  # Only get active positions
    ).all()
    
    # Get existing settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).all()
    settings_dict = {s.stock: s.target_weight for s in settings}
    
    result = []
    for holding in holdings:
        # Initialize target weight if not exists
        if holding.stock not in settings_dict:
            new_setting = UserSettings(
                user_id=user_id,
                stock=holding.stock,
                target_weight=0.0  # Initialize with 0 instead of current weight
            )
            db.add(new_setting)
            settings_dict[holding.stock] = 0.0

    # Commit new settings if any were added
    if len(settings_dict) > len(settings):
        try:
            db.commit()
        except Exception as e:
            print(f"Error committing settings: {e}")
            db.rollback()
            raise
    
    # Build result with just stock and target weight
    for holding in holdings:
        result.append({
            "stock": holding.stock,
            "target_weight": settings_dict.get(holding.stock, 0.0)
        })
    
    return result

def update_user_settings(db: Session, user_id: int, settings: List[Dict]) -> List[Dict]:
    # Remove the delete statement; instead update or create each setting for one stock
    for item in settings:
        existing = db.query(UserSettings).filter(
            UserSettings.user_id == user_id,
            UserSettings.stock == item["stock"]
        ).first()
        if existing:
            existing.target_weight = item["target_weight"]
        else:
            new_setting = UserSettings(
                user_id=user_id,
                stock=item["stock"],
                target_weight=item["target_weight"]
            )
            db.add(new_setting)
    db.commit()
    return get_user_settings(db, user_id)
