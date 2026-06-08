from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.prediction import Prediction
from typing import Optional, List

class PredictionCRUD:
    async def create(self, db: AsyncSession, **kwargs) -> Prediction:
        prediction = Prediction(**kwargs)
        db.add(prediction)
        await db.commit()
        await db.refresh(prediction)
        return prediction
    
    async def get_by_id(self, db: AsyncSession, prediction_id: int) -> Optional[Prediction]:
        result = await db.execute(select(Prediction).where(Prediction.id == prediction_id))
        return result.scalar_one_or_none()
    
    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[Prediction]:
        """Получение всех предсказаний пользователя"""
        result = await db.execute(
            select(Prediction).where(Prediction.user_id == user_id)
        )
        return result.scalars().all()
    
    async def update_name(
        self, 
        db: AsyncSession, 
        prediction_id: int, 
        name: str
    ) -> Optional[Prediction]:
        """Обновление имени предсказания"""
        prediction = await self.get_by_id(db, prediction_id)
        if prediction:
            prediction.name = name
            await db.commit()
            await db.refresh(prediction)
        return prediction
    
    async def delete(self, db: AsyncSession, prediction_id: int) -> bool:
        prediction = await self.get_by_id(db, prediction_id)
        if prediction:
            await db.delete(prediction)
            await db.commit()
            return True
        return False