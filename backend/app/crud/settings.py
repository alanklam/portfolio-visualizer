from sqlalchemy.orm import Session
from ..models.transaction_model import UserSettings, Portfolio
from typing import List, Dict

def get_user_settings(db: Session, user_id: int) -> List[Dict]:
    # Get current holdings
    holdings = db.query(Portfolio).filter(Portfolio.user_id == user_id).all()
    
    # Get existing settings
    settings = db.query(UserSettings).filter(UserSettings.user_id == user_id).all()
    settings_dict = {s.stock: s.target_weight for s in settings}
    
    # Calculate total portfolio value
    total_value = sum(h.total_units * h.current_price for h in holdings)
    
    result = []
    for holding in holdings:
        current_weight = (holding.total_units * holding.current_price / total_value) if total_value > 0 else 0
        # Initialize target weight if not exists
        if holding.stock not in settings_dict:
            new_setting = UserSettings(
                user_id=user_id,
                stock=holding.stock,
                target_weight=current_weight 
            )
            db.add(new_setting)
            settings_dict[holding.stock] = current_weight
    
    # Commit new settings if any were added
    if len(settings_dict) > len(settings):
        try:
            db.commit()
        except:
            db.rollback()
            raise
    
    # Build result including any newly initialized settings
    for holding in holdings:
        current_weight = (holding.total_units * holding.current_price / total_value) if total_value > 0 else 0
        result.append({
            "stock": holding.stock,
            "current_weight": current_weight,
            "target_weight": settings_dict.get(holding.stock, current_weight) 
        })
    
    return result

def update_user_settings(db: Session, user_id: int, settings: List[Dict]) -> List[Dict]:
    # Delete existing settings
    db.execute(
        UserSettings.__table__.delete().where(UserSettings.user_id == user_id)
    )
    
    # Insert new settings
    new_settings = [
        UserSettings(
            user_id=user_id,
            stock=item["stock"],
            target_weight=item["target_weight"]
        )
        for item in settings
    ]
    
    db.add_all(new_settings)
    db.commit()
    
    return get_user_settings(db, user_id)
