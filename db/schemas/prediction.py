from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class PredictionCreate(BaseModel):
    name: Optional[str] = None
    input_file: str
    model: str
    results_path: str
    base_id: int

class PredictionUpdate(BaseModel):
    name: Optional[str] = None
    
class PredictionResponse(BaseModel):
    id: int
    name: Optional[str] = None
    input_file: str
    model: str
    results_path: str
    timestamp: datetime
    base_id: int
    user_id: int

    class Config:
        from_attributes = True