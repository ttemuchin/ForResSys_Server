from pydantic import BaseModel
from datetime import datetime
from enum import Enum

class TrainingStatus(str, Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class TrainingCreate(BaseModel):
    model: str
    base_id: int

class TrainingUpdate(BaseModel):
    status: TrainingStatus

class TrainingResponse(BaseModel):
    id: int
    model: str
    status: TrainingStatus
    timestamp: datetime
    base_id: int
    user_id: int

    class Config:
        from_attributes = True