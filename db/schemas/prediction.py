from pydantic import BaseModel
from datetime import datetime

class PredictionCreate(BaseModel):
    input_file: str
    model: str
    results_path: str
    base_id: int

class PredictionResponse(BaseModel):
    id: int
    input_file: str
    model: str
    results_path: str
    timestamp: datetime
    base_id: int
    user_id: int

    class Config:
        from_attributes = True