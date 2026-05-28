from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BaseCreate(BaseModel):
    name: str
    N: int
    nY: int
    accuracy: List[float]  # [0.001, 0.005]
    nX: int
    dimension: List[int]  # [400, 60]
    base_path: str  # исходный путь от пользователя
    content_path: str  # путь в статике

class BaseUpdate(BaseModel):
    name: Optional[str] = None
    N: Optional[int] = None
    nY: Optional[int] = None
    accuracy: Optional[List[float]] = None
    nX: Optional[int] = None
    dimension: Optional[List[int]] = None
    trainedModels: Optional[List[str]] = None

class BaseResponse(BaseModel):
    id: int
    name: str
    N: int
    nY: int
    accuracy: List[float]
    nX: int
    dimension: List[int]
    trainedModels: List[str]
    base_path: str
    content_path: str
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class BaseNameResponse(BaseModel):
    id: int
    name: str