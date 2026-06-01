from sqlalchemy.ext.asyncio import AsyncSession
from db.crud.training_actions import TrainingCRUD
from db.schemas.training import TrainingCreate, TrainingResponse, TrainingStatus
from typing import Optional, List, Dict, Any
import asyncio

training_crud = TrainingCRUD()

# Временное хранилище метрик обучения
training_results: Dict[int, Dict[str, Any]] = {}

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
    
    @staticmethod
    async def run_training(
        training_id: int,
        base_name: str,
        base_path: str,
        base_config: dict,
        model_name: str
    ):
        """
        Запуск обучения (фоновый).
        Обновляет статус и сохраняет метрики в словарь.
        """
        try:
            from ml.train import train
            
            # Запускаем обучение, синхронный вызов
            best_loss, weights_path, best_r2, best_mae = train(
                base_name=base_name,
                path_to_base=base_path,
                config=base_config,
                model_name=model_name
            )
            
            training_results[training_id] = {
                "best_loss": best_loss,
                "best_r2": best_r2,
                "best_mae": best_mae,
                "weights_path": weights_path
            }
            
            from db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await TrainingService.update_training_status(db, training_id, TrainingStatus.COMPLETED)
            
            print(f"Training {training_id} completed: loss={best_loss}, r2={best_r2}, mae={best_mae}")
            
        except Exception as e:
            from db.session import AsyncSessionLocal
            async with AsyncSessionLocal() as db:
                await TrainingService.update_training_status(db, training_id, TrainingStatus.FAILED)
            print(f"Training {training_id} FAILED: {str(e)}")
            raise
    
    @staticmethod
    def get_training_metrics(training_id: int) -> Optional[Dict[str, Any]]:
        """Получение метрик обучения из временного хранилища"""
        return training_results.get(training_id)