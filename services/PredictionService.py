from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.prediction_actions import PredictionCRUD
from db.schemas.prediction import PredictionCreate, PredictionResponse
from typing import Optional, List

prediction_crud = PredictionCRUD()

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
        """Получение всех предсказаний пользователя"""
        predictions = await prediction_crud.get_by_user(db, user_id)
        return [PredictionResponse.model_validate(p) for p in predictions]
    
    @staticmethod
    async def delete_prediction(db: AsyncSession, prediction_id: int) -> bool:
        return await prediction_crud.delete(db, prediction_id)