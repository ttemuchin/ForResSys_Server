from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.training_actions import TrainingCRUD
from db.schemas.training import TrainingCreate, TrainingUpdate, TrainingResponse, TrainingStatus
from typing import Optional, List

training_crud = TrainingCRUD()

class TrainingService:
    @staticmethod
    async def create_training(
        db: AsyncSession, 
        user_id: int, 
        training_data: TrainingCreate
    ) -> TrainingResponse:
        training = await training_crud.create(
            db,
            user_id=user_id,
            model=training_data.model,
            base_id=training_data.base_id
        )
        return TrainingResponse.model_validate(training)
    
    @staticmethod
    async def get_training_by_id(
        db: AsyncSession, 
        training_id: int
    ) -> Optional[TrainingResponse]:
        training = await training_crud.get_by_id(db, training_id)
        return TrainingResponse.model_validate(training) if training else None
    
    @staticmethod
    async def get_trainings_by_user(
        db: AsyncSession, 
        user_id: int
    ) -> List[TrainingResponse]:
        """Получение всех записей об обучении пользователя"""
        trainings = await training_crud.get_by_user(db, user_id)
        return [TrainingResponse.model_validate(t) for t in trainings]
    
    @staticmethod
    async def update_training_status(
        db: AsyncSession, 
        training_id: int, 
        status: TrainingStatus
    ) -> Optional[TrainingResponse]:
        """Обновление статуса обучения"""
        training = await training_crud.update_status(db, training_id, status)
        return TrainingResponse.model_validate(training) if training else None
    
    @staticmethod
    async def delete_training(db: AsyncSession, training_id: int) -> bool:
        return await training_crud.delete(db, training_id)