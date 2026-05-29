from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class BaseCreate(BaseModel):
    name: str
    N: int
    nY: int
    error: List[float]  # [0.001, 0.005]
    nX: int
    dimension: List[int]  # [400, 60]
    user_path: str  # исходный путь от пользователя
    static_path: str  # путь в статике

class BaseUpdate(BaseModel):
    name: Optional[str] = None
    N: Optional[int] = None
    nY: Optional[int] = None
    error: Optional[List[float]] = None
    nX: Optional[int] = None
    dimension: Optional[List[int]] = None
    trainedModels: Optional[List[str]] = None

class BaseResponse(BaseModel):
    id: int
    name: str
    N: int
    nY: int
    error: List[float]
    nX: int
    dimension: List[int]
    trainedModels: List[str]
    user_path: str
    static_path: str
    created_at: datetime
    user_id: int

    class Config:
        from_attributes = True

class BaseNameResponse(BaseModel):
    id: int
    name: str