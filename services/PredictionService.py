from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.prediction_actions import PredictionCRUD
from db.schemas.prediction import PredictionCreate, PredictionResponse
from typing import Optional, List, Dict, Any
from pathlib import Path
import shutil

prediction_crud = PredictionCRUD()

# Временное хранилище
prediction_results: Dict[int, Dict[str, Any]] = {}

class PredictionService:
    @staticmethod
    async def create_prediction(
        db: AsyncSession, 
        user_id: int, 
        prediction_data: PredictionCreate
    ) -> PredictionResponse:
        prediction = await prediction_crud.create(
            db,
            user_id=user_id,
            input_file=prediction_data.input_file,
            model=prediction_data.model,
            results_path=prediction_data.results_path,
            base_id=prediction_data.base_id
        )
        return PredictionResponse.model_validate(prediction)
    
    @staticmethod
    async def get_prediction_by_id(
        db: AsyncSession, 
        prediction_id: int
    ) -> Optional[PredictionResponse]:
        """Получение предсказания по ID"""
        prediction = await prediction_crud.get_by_id(db, prediction_id)
        return PredictionResponse.model_validate(prediction) if prediction else None
    
    @staticmethod
    async def get_predictions_by_user(
        db: AsyncSession, 
        user_id: int
    ) -> List[PredictionResponse]:
        predictions = await prediction_crud.get_by_user(db, user_id)
        return [PredictionResponse.model_validate(p) for p in predictions]
    
    @staticmethod
    async def delete_prediction(db: AsyncSession, prediction_id: int) -> bool:
        return await prediction_crud.delete(db, prediction_id)
    
    @staticmethod
    async def run_prediction(
        prediction_id: int,
        user_id: int,
        file_path: str,
        model_name: str,
        base_name: str,
        base_config: dict,
        mode: str = "test" # "test" / "prod"
    ):
        """
        Запуск предсказания (фоновый).
        Сохраняет результаты во временный файл и метрики в словарь.
        """
        try:
            from ml.predict import predict
            
            output_path, metrics = predict(
                user_id=user_id,
                file_path=file_path,
                model_name=model_name,
                base_name=base_name,
                base_config=base_config,
                mode=mode
            )
            
            # Сохраняем метрики и путь к результатам
            prediction_results[prediction_id] = {
                "output_path": output_path,
                "metrics": metrics,
                "file_path": file_path,
                "model_name": model_name,
                "base_name": base_name
            }
            
            print(f"Prediction {prediction_id} completed")
            
        except Exception as e:
            prediction_results[prediction_id] = {
                "error": str(e)
            }
            print(f"Prediction {prediction_id} FAILED: {str(e)}")
    
    @staticmethod
    def get_prediction_result(prediction_id: int) -> Optional[Dict[str, Any]]:
        """Получение результата предсказания из временного хранилища"""
        return prediction_results.get(prediction_id)
    
    @staticmethod
    async def save_prediction_permanently(
        db: AsyncSession,
        prediction_id: int,
        user_id: int,
        name: str,
        input_filename: str,
        model_name: str,
        base_name: str,
        base_id: int
    ) -> Optional[PredictionResponse]:
        """
        Сохранение результатов предсказания в БД и финальный файл.
        Копирует TEMP.txt в постоянный файл.
        """
        # result = prediction_results.get(prediction_id)
        # if not result or "error" in result:
        #     return None
        
        # temp_path = Path(result["output_path"])
        # if not temp_path.exists():
        #     return None
        result = prediction_results.get(prediction_id)
        if not result or "error" in result:
            print(f"WARNING! No result for prediction_id {prediction_id}")
            return None
        
        temp_path = Path(result["output_path"])
        # print(f"temp_path: {temp_path}")
        
        if not temp_path.exists():
            print(f"WARNING! TEMP file does not exist: {temp_path}")
            return None
        
        # Формируем имя постоянного файла
        output_filename = f"{input_filename}_{model_name}_{base_name}_out.txt"
        permanent_path = temp_path.parent / output_filename
        # print(f"permanent_path: {permanent_path}")
        
        # Копируем временный файл в постоянный
        # shutil.copy2(temp_path, permanent_path)
        try:
            shutil.copy2(temp_path, permanent_path)
            # print(f"File copied to: {permanent_path}")
        except Exception as e:
            # print(f"Copy failed: {e}")
            return None
        
        # Создаём запись в БД
        prediction_data = PredictionCreate(
            name=name,
            input_file=result["file_path"],
            model=model_name,
            results_path=str(permanent_path),
            base_id=base_id
        )
        
        prediction = await PredictionService.create_prediction(db, user_id, prediction_data)
        
        return prediction
    
    @staticmethod
    async def rename_prediction(
        db: AsyncSession,
        prediction_id: int,
        user_id: int,
        new_name: str
    ) -> Optional[PredictionResponse]:
        prediction = await prediction_crud.get_by_id(db, prediction_id)
        if not prediction:
            return None
        
        if prediction.user_id != user_id:
            return None
        
        updated_prediction = await prediction_crud.update_name(db, prediction_id, new_name)
        return PredictionResponse.model_validate(updated_prediction) if updated_prediction else None