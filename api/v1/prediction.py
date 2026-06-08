from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Dict, Any, Optional
from pathlib import Path

from db.session import get_db
from db.schemas.prediction import PredictionCreate, PredictionResponse
from db.schemas.user import UserResponse
from services.PredictionService import PredictionService
from services.BaseService import BaseService
from services.TrainingService import TrainingService
from core.jwt import get_current_user_jwt
from config import config

router = APIRouter()


@router.post("/predict", response_model=Dict[str, Any])
async def start_prediction(
    background_tasks: BackgroundTasks,
    base_id: int = Form(...),
    model: str = Form(...),
    file: UploadFile = File(...),
    mode: str = Form("test"),
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Запуск предсказания.
    Сохраняет загруженный файл, создаёт запись в временном хранилище,
    возвращает prediction_id для polling.
    """
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
    
    # Проверяем, что модель обучена на этой базе
    available_models = await TrainingService.get_available_models_for_base(db, base_id, current_user.id)
    if model not in available_models:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Model '{model}' is not available for this base"
        )
    
    # Сохраняем загруженный файл во временную директорию
    user_temp_dir = Path(config.STATIC_DIR) / "predictions" / str(current_user.id) / "temp_inputs"
    user_temp_dir.mkdir(parents=True, exist_ok=True)
    
    input_filename = file.filename or "input.txt"
    temp_file_path = user_temp_dir / f"temp_{input_filename}"
    
    try:
        content = await file.read()
        with open(temp_file_path, "wb") as f:
            f.write(content)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to save file: {str(e)}"
        )

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
    
    
    import time
    prediction_id = int(time.time() * 1000) # временный ID для отслеживания предсказания
    
    # Запускаем предсказание в фоне
    background_tasks.add_task(
        PredictionService.run_prediction,
        prediction_id=prediction_id,
        user_id=current_user.id,
        file_path=str(temp_file_path),
        model_name=model,
        base_name=base.name,
        base_config=base_config,
        mode=mode # Определяем режим (test/prod)
        # сейчас передаём из запроса, позже можно автоматически определять или снести нафиг
    )
    
    return {
        "status": "started",
        "prediction_id": prediction_id,
        "message": f"Prediction started with {model} model on base '{base.name}'",
        "mode": mode
    }


@router.get("/{prediction_id}/result", response_model=Dict[str, Any])
async def get_prediction_result(
    prediction_id: int,
    current_user: UserResponse = Depends(get_current_user_jwt)
):
    """
    Получение результата предсказания по ID.
    предполагается  polling на фронтенде.
    """
    result = PredictionService.get_prediction_result(prediction_id)
    
    if not result:
        return {"status": "pending"}
    
    if "error" in result:
        return {
            "status": "failed",
            "error": result["error"]
        }
    
    output_path = Path(result["output_path"])
    content = ""
    if output_path.exists():
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
    
    return {
        "status": "completed",
        "output_path": str(output_path),
        "content": content,
        "metrics": result.get("metrics"),
        "file_path": result.get("file_path"),
        "model_name": result.get("model_name"),
        "base_name": result.get("base_name")
    }


@router.post("/{prediction_id}/save", response_model=PredictionResponse)
async def save_prediction_permanently(
    prediction_id: int,
    base_id: int,
    name: str,
    input_filename: str,
    model_name: str,
    base_name: str,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """
    Сохранение результатов предсказания в БД и в постоянный файл.
    """
    base = await BaseService.get_base_by_id(db, base_id)
    if not base:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base not found"
        )
    
    prediction = await PredictionService.save_prediction_permanently(
        db=db,
        prediction_id=prediction_id,
        user_id=current_user.id,
        name=name,
        input_filename=input_filename,
        model_name=model_name,
        base_name=base_name,
        base_id=base_id
    )
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction result not found or already saved"
        )
    
    return prediction

@router.get("/{prediction_id}/content")
async def get_prediction_content(
    prediction_id: int,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Получение содержимого файла результата предсказания"""
    prediction = await PredictionService.get_prediction_by_id(db, prediction_id)
    if not prediction:
        raise HTTPException(status_code=404, detail="Prediction not found")
    
    base = await BaseService.get_base_by_id(db, prediction.base_id)
    if base.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")
    
    file_path = Path(prediction.results_path)
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Result file not found")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {"content": content}

@router.get("/saved", response_model=List[PredictionResponse])
async def get_user_predictions(
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    """Получение истории сохранённых предсказаний пользователя"""
    predictions = await PredictionService.get_predictions_by_user(db, current_user.id)
    return predictions

@router.patch("/{prediction_id}/rename", response_model=PredictionResponse)
async def rename_prediction(
    prediction_id: int,
    name: str,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    prediction = await PredictionService.rename_prediction(
        db=db,
        prediction_id=prediction_id,
        user_id=current_user.id,
        new_name=name
    )
    
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found or access denied"
        )
    
    return prediction


@router.delete("/{prediction_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_prediction(
    prediction_id: int,
    current_user: UserResponse = Depends(get_current_user_jwt),
    db: AsyncSession = Depends(get_db)
):
    prediction = await PredictionService.get_prediction_by_id(db, prediction_id)
    if not prediction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    if prediction.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )
    
    if prediction.results_path:
        file_path = Path(prediction.results_path)
        if file_path.exists():
            file_path.unlink()
    
    deleted = await PredictionService.delete_prediction(db, prediction_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Prediction not found"
        )
    
    return None