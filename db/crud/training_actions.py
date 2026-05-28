from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from db.models.training import Training, TrainingStatus
from typing import Optional, List

class TrainingCRUD:
    async def create(self, db: AsyncSession, **kwargs) -> Training:
        """Создание записи об обучении (pending по умолчанию)"""
        kwargs['status'] = TrainingStatus.PENDING
        training = Training(**kwargs)
        db.add(training)
        await db.commit()
        await db.refresh(training)
        return training
    
    async def get_by_id(self, db: AsyncSession, training_id: int) -> Optional[Training]:
        result = await db.execute(select(Training).where(Training.id == training_id))
        return result.scalar_one_or_none()
    
    async def get_by_user(self, db: AsyncSession, user_id: int) -> List[Training]:
        """Получение всех записей об обучении пользователя"""
        result = await db.execute(
            select(Training).where(Training.user_id == user_id)
        )
        return result.scalars().all()
    
    async def update_status(
        self, 
        db: AsyncSession, 
        training_id: int, 
        status: TrainingStatus
    ) -> Optional[Training]:
        training = await self.get_by_id(db, training_id)
        if training:
            training.status = status
            await db.commit()
            await db.refresh(training)
        return training
    
    async def delete(self, db: AsyncSession, training_id: int) -> bool:
        training = await self.get_by_id(db, training_id)
        if training:
            await db.delete(training)
            await db.commit()
            return True
        return False