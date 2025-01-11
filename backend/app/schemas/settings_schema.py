from pydantic import BaseModel
from typing import List

class WeightSetting(BaseModel):
    stock: str
    target_weight: float

    class Config:
        orm_mode = True

class WeightSettingsUpdate(BaseModel):
    settings: List[WeightSetting]

    class Config:
        orm_mode = True
