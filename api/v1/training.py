from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any

from db.session import get_db
from db.schemas.training import TrainingCreate, TrainingResponse, TrainingStatus
from db.schemas.user import UserResponse
from services.TrainingService import TrainingService
from services.BaseService import BaseService
from core.jwt import get_current_user_jwt

router = APIRouter()

@router.post("/train", response_model=Dict[str, Any])
async def start_training(
    base_id: int,
    model: str,
    background_tasks: BackgroundTasks,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Запуск обучения модели на выбранной базе"""
    # Проверяем базу и права доступа
    base = await BaseService.get_base_by_id(db, base_id)
    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base not found"
        )
    
    if base.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    # Создаём запись в trainings
    training_data = TrainingCreate(model=model, base_id=base_id)
    training = await TrainingService.create_training(db, current_user.id, training_data)
    
    # Конфиг для train.py
    base_config = {
        "name": base.name,
        "N": base.N,
        "nY": base.nY,
        "error": base.error,
        "nX": base.nX,
        "dimension": base.dimension,
        "labelsX": base.labelsX,
        "labelsY": base.labelsY,
    }
    
    # Запускаем обучение в фоне
    background_tasks.add_task(
        TrainingService.run_training,
        user_id=current_user.id,
        training_id=training.id,
        base_name=base.name,
        base_path=base.static_path,
        base_config=base_config,
        model_name=model
    )
    
    return {
        "status": "started",
        "training_id": training.id,
        "message": f"Training started for base '{base.name}' using {model} model"
    }


@router.get("/trainings", response_model=List[TrainingResponse])
async def get_user_trainings(
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Получение истории всех обучений пользователя"""
    return await TrainingService.get_trainings_by_user(db, current_user.id)


@router.get("/trainings/{training_id}/status", response_model=Dict[str, Any])
async def get_training_status(
    training_id: int,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Получение статуса и результатов обучения (если завершено)"""
    training = await TrainingService.get_training_by_id(db, training_id)
    if not training:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Training not found"
        )
    
    base = await BaseService.get_base_by_id(db, training.base_id)
    if base.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    response = {
        "id": training.id,
        "model": training.model,
        "status": training.status,
        "timestamp": training.timestamp,
        "base_id": training.base_id,
        "base_name": base.name
    }
    
    # даем метрики, когда обучение завершено
    if training.status == TrainingStatus.COMPLETED:
        metrics = TrainingService.get_training_metrics(training_id)
        if metrics:
            response["result"] = metrics
    
    return response

# ДЛЯ БЫСТРОГО ПОЛУЧЕНИЯ В СЕЛЕКТОРЫ
@router.get("/bases-with-trainings", response_model=List[Dict[str, Any]])
async def get_bases_with_trainings(
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка баз, по которым было хотя бы одно успешное обучение.
    Используется для селектора в интерфейсе предсказаний.
    """
    bases = await TrainingService.get_bases_with_trainings(db, current_user.id)
    return bases


@router.get("/bases/{base_id}/available-models", response_model=List[str])
async def get_available_models_for_base(
    base_id: int,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Получение списка моделей, обученных на указанной базе.
    Используется для второго селектора в интерфейсе предсказаний.
    """
    models = await TrainingService.get_available_models_for_base(db, base_id, current_user.id)
    return models